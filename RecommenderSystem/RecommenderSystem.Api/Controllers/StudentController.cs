using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.Student;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Core.DTOs.Student.Analytics;
using RecommenderSystem.Infrastructure.Persistence;
using System.Security.Claims;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class StudentController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IRecommendationService _recommendationService;
    private readonly ICourseAnalysisService _courseAnalysisService;
    private readonly AppDbContext _context;
    private readonly UserManager<AppUser> _userManager;

    public StudentController(
        IMoodleService moodleService,
        IRecommendationService recommendationService,
        ICourseAnalysisService courseAnalysisService,
        AppDbContext context,
        UserManager<AppUser> userManager)
    {
        _moodleService = moodleService;
        _recommendationService = recommendationService;
        _courseAnalysisService = courseAnalysisService;
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

        double calcOverall = 0;
        double calcMax = 0;

        var assignments = userCourse.AssignmentGrades.Select((a, index) =>
        {
            calcOverall += a.Grade ?? 0;
            calcMax += a.MaxGrade ?? 0;

            var diff = index % 2 == 0 ? "Advanced" : "Standard";
            if (index == 1) diff = "Medium";

            return new AssignmentGradeDto
            {
                Id = a.Id,
                Name = a.ItemName,
                Grade = a.Grade,
                MaxGrade = a.MaxGrade,
                Difficulty = diff,
                SubmittedDate = DateTime.Now.AddDays(-index * 7).ToString("MMM dd")
            };
        }).ToList();

        if (calcMax == 0) calcMax = 5.0;

        double finalScore = calcMax > 0 ? Math.Round((calcOverall / calcMax) * 5.0, 1) : 0;

        var result = new CourseDetailsDto
        {
            CourseId = userCourse.Course!.Id,
            Title = userCourse.Course.Title,
            OverallGrade = finalScore,
            MaxGrade = 5.0,
            Assignments = assignments
        };

        return Ok(result);
    }

    /// <summary>
    /// Агрегированная статистика успеваемости студента.
    /// </summary>
    [HttpGet("statistics")]
    public async Task<ActionResult<StudentStatisticsDto>> GetStatistics()
    {
        try
        {
            var moodleUserId = await GetCurrentMoodleUserIdAsync();
            if (moodleUserId == null || moodleUserId == 0)
                return BadRequest("Аккаунт не привязан к Moodle.");

            var userCourses = await _context.UserCourses
                .Include(uc => uc.Course)
                .Include(uc => uc.AssignmentGrades)
                .Where(uc => uc.MoodleStudent!.MoodleUserId == moodleUserId)
                .ToListAsync();

            if (!userCourses.Any())
                return Ok(new StudentStatisticsDto());

            var finalGrades = new List<int>();
            var courseProgress = new List<CourseProgressDto>();

            foreach (var uc in userCourses)
            {
                var assignmentGrades = uc.AssignmentGrades
                    .Where(a => a.MaxGrade != null && a.MaxGrade > 0)
                    .ToList();

                double courseEarned = 0;
                double courseMax = 0;

                if (assignmentGrades.Any())
                {
                    foreach (var g in assignmentGrades)
                    {
                        var gradeVal = g.Grade ?? 0;
                        var maxVal = g.MaxGrade!.Value;
                        if (maxVal <= 0) continue;

                        var normalized = ((double)gradeVal / (double)maxVal) * 5.0;
                        var rounded = (int)Math.Round(normalized, MidpointRounding.AwayFromZero);

                        if (rounded < 2) rounded = 2; 
                        if (rounded > 5) rounded = 5; 

                        finalGrades.Add(rounded);

                        courseEarned += gradeVal;
                        courseMax += maxVal;
                    }
                }
                else if (uc.MaxGrade != null && uc.MaxGrade > 0)
                {
                    var gradeVal = uc.Grade ?? 0;
                    var maxVal = uc.MaxGrade.Value;
                    if (maxVal > 0)
                    {
                        var normalized = ((double)gradeVal / (double)maxVal) * 5.0;
                        var rounded = (int)Math.Round(normalized, MidpointRounding.AwayFromZero);

                        if (rounded < 2) rounded = 2;
                        if (rounded > 5) rounded = 5;

                        finalGrades.Add(rounded);
                        courseEarned = gradeVal;
                        courseMax = maxVal;
                    }
                }

                var coursePct = courseMax > 0 ? (courseEarned / courseMax) * 100.0 : 0;
                courseProgress.Add(new CourseProgressDto
                {
                    CourseTitle = uc.Course?.Title ?? "Unknown",
                    AveragePercentage = Math.Round(coursePct, 1),
                });
            }

            var two = 0;
            var three = 0;
            var four = 0;
            var five = 0;
            var weakCount = 0;

            foreach (var grade in finalGrades)
            {
                if (grade == 2)
                {
                    two++;
                    weakCount++;
                }
                else if (grade == 3)
                {
                    three++;
                    weakCount++;
                }
                else if (grade == 4)
                {
                    four++;
                }
                else if (grade == 5)
                {
                    five++;
                }
            }

            // Высчитываем среднее арифметическое именно из ЦЕЛЫХ оценок
            var overallAvg = finalGrades.Count > 0
                ? Math.Round((double)finalGrades.Sum() / finalGrades.Count, 1)
                : 0;

            return Ok(new StudentStatisticsDto
            {
                TotalGradesCount = finalGrades.Count,
                OverallAverageScore = overallAvg,
                GradeDistribution = new GradeDistributionDto
                {
                    Two = two,
                    Three = three,
                    Four = four,
                    Five = five,
                },
                WeakCount = weakCount,
                CoursesCount = userCourses.Count,
                CourseProgress = courseProgress,
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = "Internal server error", detail = ex.Message });
        }
    }

    /// <summary>
    /// Возвращает контекст курса для инициализации AI-чата.
    /// </summary>
    [HttpGet("courses/{courseId:guid}/context")]
    public async Task<ActionResult<CourseContextDto>> GetCourseContext(Guid courseId)
    {
        try
        {
            var moodleUserId = await GetCurrentMoodleUserIdAsync();
            if (moodleUserId == null || moodleUserId == 0)
                return BadRequest("Аккаунт не привязан к Moodle.");

            var uc = await _context.UserCourses
                .Include(c => c.Course)
                .Include(c => c.AssignmentGrades)
                .FirstOrDefaultAsync(c => c.CourseId == courseId
                                          && c.MoodleStudent!.MoodleUserId == moodleUserId);

            if (uc == null)
                return NotFound("Курс не найден.");

            var weakTopics = new List<string>();
            var strongTopics = new List<string>();
            var topics = uc.Course?.Topics ?? new List<string>();

            double ratio = 0;
            var grades = uc.AssignmentGrades.Where(a => a.MaxGrade != null && a.MaxGrade > 0).ToList();
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

            var recentGrades = grades
                .OrderByDescending(g => g.LastSynced)
                .Take(5)
                .Select(g => new GradeEntryDto
                {
                    ItemName = g.ItemName,
                    Grade = g.Grade,
                    MaxGrade = g.MaxGrade,
                })
                .ToList();

            return Ok(new CourseContextDto
            {
                CourseName = uc.Course?.Title ?? string.Empty,
                WeakTopics = weakTopics,
                StrongTopics = strongTopics,
                RecentGrades = recentGrades,
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = "Internal server error", detail = ex.Message });
        }
    }

    /// <summary>
    /// AI-анализ успеваемости студента по конкретному курсу.
    /// Собирает оценки, теги → отправляет в Python → Groq LLM → возвращает анализ + рекомендации.
    /// </summary>
    [HttpGet("courses/{courseId:guid}/ai-analysis")]
    [ProducesResponseType(typeof(CourseAnalysisResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status503ServiceUnavailable)]
    public async Task<ActionResult<CourseAnalysisResponseDto>> AnalyzeCourse(Guid courseId)
    {
        var moodleUserId = await GetCurrentMoodleUserIdAsync();
        if (moodleUserId == null || moodleUserId == 0)
            return BadRequest("Аккаунт не привязан к Moodle.");

        // Проверяем, что курс существует и привязан к студенту
        var userCourse = await _context.UserCourses
            .Include(uc => uc.Course)
            .FirstOrDefaultAsync(uc => uc.CourseId == courseId
                                       && uc.MoodleStudent!.MoodleUserId == moodleUserId);

        if (userCourse == null)
            return NotFound("Курс не найден или вы не записаны на него.");

        try
        {
            var analysis = await _courseAnalysisService.AnalyzeCourseAsync(moodleUserId.Value, courseId);
            return Ok(analysis);
        }
        catch (Exception)
        {
            // Логируем и возвращаем 503 — сервис недоступен
            return StatusCode(StatusCodes.Status503ServiceUnavailable,
                new ProblemDetails
                {
                    Title = "AI-сервис недоступен",
                    Detail = "Не удалось выполнить анализ курса. Попробуйте позже.",
                    Status = StatusCodes.Status503ServiceUnavailable
                });
        }
    }
}