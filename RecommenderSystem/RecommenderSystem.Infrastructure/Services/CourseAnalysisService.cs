using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;

namespace RecommenderSystem.Infrastructure.Services;

/// <summary>
/// Оркестратор AI-анализа курса:
/// 1. Извлекает оценки студента из БД (UserAssignmentGrade) по курсу.
/// 2. Запрашивает теги курса из Moodle.
/// 3. Вызывает Python-сервис через IPythonAiService.AnalyzeCourseAsync.
/// 4. Возвращает fallback при недоступности Python.
/// </summary>
public class CourseAnalysisService : ICourseAnalysisService
{
    private readonly AppDbContext _context;
    private readonly IMoodleService _moodleService;
    private readonly IPythonAiService _pythonAiService;
    private readonly ILogger<CourseAnalysisService> _logger;

    public CourseAnalysisService(
        AppDbContext context,
        IMoodleService moodleService,
        IPythonAiService pythonAiService,
        ILogger<CourseAnalysisService> logger)
    {
        _context = context;
        _moodleService = moodleService;
        _pythonAiService = pythonAiService;
        _logger = logger;
    }

    public async Task<CourseAnalysisResponseDto> AnalyzeCourseAsync(int moodleUserId, Guid courseId)
    { 
        var course = await _context.Courses.FirstOrDefaultAsync(c => c.Id == courseId);
        if (course == null)
        {
            _logger.LogWarning("Course {CourseId} not found in DB", courseId);
            return BuildFallbackResponse("Неизвестный курс");
        }

        var assignmentGrades = await _context.UserAssignmentGrades
            .Where(ag => ag.UserCourseId != null
                         && _context.UserCourses
                             .Any(uc => uc.Id == ag.UserCourseId
                                     && uc.MoodleStudent!.MoodleUserId == moodleUserId
                                     && uc.CourseId == courseId))
            .Select(ag => new UserGradeDto
            {
                ItemName = ag.ItemName,
                RawGrade = ag.Grade,
                MaxGrade = ag.MaxGrade
            })
            .ToListAsync();

        if (!assignmentGrades.Any())
        {
            _logger.LogInformation("No grades in DB for user {UserId} course {CourseId}, fetching from Moodle",
                moodleUserId, courseId);

            if (int.TryParse(course.ExternalId, out var moodleCourseId))
            {
                var moodleGrades = await _moodleService.GetUserGradesAsync(moodleUserId, moodleCourseId);
                assignmentGrades = moodleGrades.Select(g => new UserGradeDto
                {
                    ItemName = g.ItemName,
                    RawGrade = g.RawGrade,
                    MaxGrade = g.MaxGrade
                }).ToList();
            }
        }

        var courseTags = new List<string>();
        if (int.TryParse(course.ExternalId, out var moodleCourseIdForTags))
        {
            try
            {
                courseTags = await _moodleService.GetCourseTagsAsync(moodleCourseIdForTags);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to fetch Moodle tags for course {CourseId}", courseId);
            }
        }

        if (course.Topics is { Count: > 0 })
        {
            courseTags = courseTags.Concat(course.Topics).Distinct().ToList();
        }

        var pythonResult = await _pythonAiService.AnalyzeCourseAsync(moodleUserId, course.Title, assignmentGrades, courseTags);

        if (pythonResult != null)
        {
            return pythonResult;
        }

        _logger.LogWarning("Python service unavailable, returning fallback analysis for user {UserId} course {CourseId}",
            moodleUserId, courseId);

        return BuildFallbackResponse(course.Title);
    }

    /// <summary>
    /// Формирует fallback-ответ при недоступности Python/Groq.
    /// </summary>
    private static CourseAnalysisResponseDto BuildFallbackResponse(string courseTitle)
    {
        return new CourseAnalysisResponseDto
        {
            Analysis = $"Не удалось выполнить AI-анализ по курсу «{courseTitle}». Сервис временно недоступен. Попробуйте позже.",
            WeakTopics = new List<string>(),
            StrongTopics = new List<string>(),
            Recommendations = new List<CourseAnalysisRecommendationDto>
            {
                new()
                {
                    Title = "Повторите материалы курса",
                    Description = $"Пересмотрите лекции и практические задания по курсу «{courseTitle}». Обратитесь к преподавателю за консультацией.",
                    ResourceType = "article",
                    Url = null,
                    RelevanceScore = 0.5,
                    Difficulty = "Standard"
                }
            }
        };
    }
}
