using Microsoft.AspNetCore.Mvc;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class StudentController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IRecommendationService _recommendationService;

    public StudentController(IMoodleService moodleService, IRecommendationService recommendationService)
    {
        _moodleService = moodleService;
        _recommendationService = recommendationService;
    }

    // Сценарий: Студент вводит логин -> Получает рекомендации
    [HttpGet("analyze")]
    public async Task<IActionResult> AnalyzeStudent([FromQuery] string username, [FromQuery] int courseId)
    {
        var userId = await _moodleService.GetUserIdByUsernameAsync(username);

        if (userId == null)
        {
            return NotFound($"Студент с логином '{username}' не найден в системе Moodle.");
        }

        var grades = await _moodleService.GetUserGradesAsync(userId.Value, courseId);

        if (grades == null || !grades.Any())
        {
            return NotFound("У вас пока нет оценок по этому курсу.");
        }

        var tags = await _moodleService.GetCourseTagsAsync(courseId);
        foreach (var grade in grades) grade.CourseTags = tags;

        var recommendations = await _recommendationService.GetRecommendationsAsync(userId.Value, grades);

        return Ok(new 
        {
            StudentId = userId,
            Username = username,
            Recommendations = recommendations
        });
    }
}