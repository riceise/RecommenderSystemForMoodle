using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.PythonRequests;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RecommendationsController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IPythonAiService _pythonService;
    private readonly IRecommendationService _recommendationService;
    private readonly UserManager<AppUser> _userManager;
    private readonly AppDbContext _context;

    public RecommendationsController(
        IMoodleService moodleService, 
        IPythonAiService pythonService, 
        IRecommendationService recommendationService, 
        UserManager<AppUser> userManager,
        AppDbContext context)
    {
        _recommendationService = recommendationService;
        _moodleService = moodleService;
        _pythonService = pythonService;
        _userManager = userManager;
        _context = context;
    }

    private async Task<int?> GetCurrentMoodleUserIdAsync()
    {
        var email = User.FindFirstValue(ClaimTypes.Email);
        if (string.IsNullOrEmpty(email)) return null;

        var user = await _userManager.FindByEmailAsync(email);
        return user?.MoodleUserId;
    }

    [HttpGet("{username}")]
    public async Task<IActionResult> GetRecommendations(string username)
    {
        var userId = await _moodleService.GetUserIdByUsernameAsync(username);
        if (userId == null) return NotFound("User not found in Moodle");

        int courseId = 2; 

        var grades = await _moodleService.GetUserGradesAsync(userId.Value, courseId);
        var courseTags = await _moodleService.GetCourseTagsAsync(courseId);
        var topicTags = await _moodleService.GetTopicsWithActivitiesAsync(courseId);
        
        var allContextTags = courseTags.Concat(topicTags).Distinct().ToList();

        if (!grades.Any())
            return Ok(new List<PythonResponseDto>());

        var recommendations = await _pythonService.GetRecommendationsAsync(userId.Value, grades, allContextTags);

        return Ok(recommendations);
    }

    [HttpPost("chat")]
    [Authorize]
    public async Task<IActionResult> ChatWithAI([FromBody] ChatRequestDto request)
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        if (moodleUserId == null || moodleUserId == 0)
            return BadRequest("Аккаунт не привязан к Moodle.");

        var weakTopics = new List<string>();
        var strongTopics = new List<string>();
        var courseName = string.Empty;
        var gradesSummary = string.Empty;

        if (request.ContextData != null)
        {
            courseName = request.ContextData.CourseName;
            weakTopics = request.ContextData.WeakTopics;
            strongTopics = request.ContextData.StrongTopics;
            gradesSummary = string.Join(", ", request.ContextData.RecentGrades
                .Select(g => $"{g.ItemName}: {g.Grade}/{g.MaxGrade}"));
        }
        else if (request.CourseId.HasValue)
        {
            var uc = await _context.UserCourses
                .Include(c => c.Course)
                .Include(c => c.AssignmentGrades)
                .FirstOrDefaultAsync(c => c.CourseId == request.CourseId.Value
                                       && c.MoodleStudent!.MoodleUserId == moodleUserId);

            if (uc != null)
            {
                courseName = uc.Course?.Title ?? string.Empty;
                var topics = uc.Course?.Topics ?? new List<string>();
                var grades = uc.AssignmentGrades.Where(a => a.MaxGrade != null && a.MaxGrade > 0).ToList();

                double ratio = 0;
                if (grades.Any())
                {
                    var earned = grades.Sum(a => a.Grade ?? 0);
                    var max = grades.Sum(a => a.MaxGrade ?? 0);
                    if (max > 0) ratio = earned / max;
                }
                else if (uc.MaxGrade != null && uc.MaxGrade > 0)
                {
                    ratio = (uc.Grade ?? 0) / uc.MaxGrade.Value;
                }

                if (ratio < 0.6) weakTopics = topics;
                else if (ratio >= 0.85) strongTopics = topics;
            }
        }
        else
        {
            var userCourses = await _context.UserCourses
                .Include(uc => uc.Course)
                .Include(uc => uc.AssignmentGrades)
                .Where(uc => uc.MoodleStudent!.MoodleUserId == moodleUserId)
                .ToListAsync();

            foreach (var uc in userCourses)
            {
                var topics = uc.Course?.Topics ?? new List<string>();
                if (!topics.Any()) continue;

                double overallRatio = 0;
                var grades = uc.AssignmentGrades.Where(a => a.MaxGrade != null && a.MaxGrade > 0).ToList();
                if (grades.Any())
                {
                    var earned = grades.Sum(a => a.Grade ?? 0);
                    var max = grades.Sum(a => a.MaxGrade ?? 0);
                    if (max > 0) overallRatio = earned / max;
                }
                else if (uc.MaxGrade != null && uc.MaxGrade > 0)
                {
                    overallRatio = (uc.Grade ?? 0) / uc.MaxGrade.Value;
                }

                if (overallRatio < 0.6)
                    weakTopics.AddRange(topics);
                else if (overallRatio >= 0.85)
                    strongTopics.AddRange(topics);
            }
        }

        var chatRequest = new ChatContextRequest
        {
            UserId = moodleUserId.Value,
            SessionId = string.IsNullOrWhiteSpace(request.SessionId)
                ? (request.CourseId.HasValue ? $"chat-{moodleUserId.Value}-{request.CourseId.Value}" : $"chat-{moodleUserId.Value}")
                : request.SessionId,
            Message = request.Message,
            Context = request.Context,
            CourseId = request.CourseId,
            CourseName = courseName,
            WeakTopics = weakTopics.Distinct().ToList(),
            StrongTopics = strongTopics.Distinct().ToList(),
            RecentGradesSummary = gradesSummary,
        };

        var reply = await _pythonService.ChatAsync(chatRequest);

        if (reply == null)
            return StatusCode(503, new { reply = "AI-сервис временно недоступен. Попробуйте позже." });

        return Ok(new { reply });
    }
    
    [HttpGet("recommendations")]
    public async Task<IActionResult> GetPersonalizedRecommendations()
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        if (moodleUserId == null || moodleUserId == 0)
            return BadRequest("Аккаунт не привязан к Moodle.");

        var userCoursesQuery = _context.UserCourses
            .Include(uc => uc.Course)
            .Where(uc => uc.MoodleStudent!.MoodleUserId == moodleUserId);

        var contextTags = await userCoursesQuery
            .SelectMany(uc => uc.Course.Topics ?? new List<string>())
            .ToListAsync();

        var courseTitles = await userCoursesQuery
            .Select(uc => uc.Course.Title)
            .Where(title => !string.IsNullOrEmpty(title))
            .ToListAsync();

        contextTags.AddRange(courseTitles!);
        contextTags = contextTags.Distinct().ToList();

        var grades = await _context.UserCourses
            .Include(uc => uc.AssignmentGrades)
            .Where(uc => uc.MoodleStudent!.MoodleUserId == moodleUserId)
            .SelectMany(uc => uc.AssignmentGrades)
            .Select(a => new UserGradeDto
            {
                ItemName = a.ItemName,
                RawGrade = a.Grade,
                MaxGrade = a.MaxGrade
            })
            .ToListAsync();

        var recommendations = await _recommendationService.GetRecommendationsAsync(
            moodleUserId.Value,
            grades,
            contextTags
        );

        return Ok(recommendations);
    }
}
