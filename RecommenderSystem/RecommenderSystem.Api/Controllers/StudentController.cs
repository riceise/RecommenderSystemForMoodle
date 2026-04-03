using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.DTOs.Student;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Infrastructure.Persistence;
using System.Security.Claims;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize] 
public class StudentController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IRecommendationService _recommendationService;
    private readonly AppDbContext _context;
    private readonly UserManager<AppUser> _userManager;
    public StudentController(
        IMoodleService moodleService, 
        IRecommendationService recommendationService,
        AppDbContext context,
        UserManager<AppUser> userManager)
    {
        _moodleService = moodleService;
        _recommendationService = recommendationService;
        _context = context;
        _userManager = userManager;
    }

    private async Task<int?> GetCurrentMoodleUserIdAsync()
    {
        var email = User.FindFirstValue(ClaimTypes.Email);
        if (string.IsNullOrEmpty(email)) return null;

        var user = await _userManager.FindByEmailAsync(email);
        return user?.MoodleUserId;
    }

    //Получить все курсы для Дашборда
    [HttpGet("courses")]
    public async Task<ActionResult<List<CourseSummaryDto>>> GetMyCourses()
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        
        if (moodleUserId == null || moodleUserId == 0)
            return BadRequest("Ваш аккаунт не привязан к системе Moodle.");

        var userCourses = await _context.UserCourses
            .Include(uc => uc.Course)
            .Where(uc => uc.MoodleStudent!.MoodleUserId == moodleUserId)
            .Select(uc => new CourseSummaryDto
            {
                Id = uc.Course!.Id,
                Title = uc.Course.Title,
                OverallGrade = uc.Grade,
                MaxGrade = uc.MaxGrade
            })
            .ToListAsync();

        return Ok(userCourses);
    }

    //Получить детали курса
    [HttpGet("courses/{courseId}")]
    public async Task<ActionResult<CourseDetailsDto>> GetCourseDetails(Guid courseId)
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        if (moodleUserId == null || moodleUserId == 0) return BadRequest("Аккаунт не привязан к Moodle.");

        var userCourse = await _context.UserCourses
            .Include(uc => uc.Course)
            .Include(uc => uc.AssignmentGrades)
            .FirstOrDefaultAsync(uc => uc.CourseId == courseId && uc.MoodleStudent!.MoodleUserId == moodleUserId);

        if (userCourse == null) return NotFound("Курс не найден.");

        var result = new CourseDetailsDto
        {
            CourseId = userCourse.Course!.Id,
            Title = userCourse.Course.Title,
            Assignments = userCourse.AssignmentGrades.Select(a => new AssignmentGradeDto
            {
                Id = a.Id,
                Name = a.ItemName,
                Grade = a.Grade,
                MaxGrade = a.MaxGrade
            }).ToList()
        };

        return Ok(result);
    }

    [HttpGet("analyze")]
    public async Task<IActionResult> AnalyzeStudent([FromQuery] int courseId)
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        if (moodleUserId == null || moodleUserId == 0) return BadRequest("Аккаунт не привязан к Moodle.");

        var grades = await _moodleService.GetUserGradesAsync(moodleUserId.Value, courseId);

        if (grades == null || !grades.Any())
        {
            return NotFound("У вас пока нет оценок по этому курсу.");
        }

        var courseTags = await _moodleService.GetCourseTagsAsync(courseId);
        var topicTags = await _moodleService.GetTopicsWithActivitiesAsync(courseId);
        
        var allContextTags = courseTags.Concat(topicTags).Distinct().ToList();

        var recommendations = await _recommendationService.GetRecommendationsAsync(moodleUserId.Value, grades, allContextTags);

        return Ok(new 
        {
            StudentId = moodleUserId,
            Recommendations = recommendations
        });
    }
}