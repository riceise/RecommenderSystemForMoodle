using Microsoft.AspNetCore.Mvc;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RecommendationsController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IRecommendationService _recommendationService;

    public RecommendationsController(
        IMoodleService moodleService, 
        IRecommendationService recommendationService)
    {
        _moodleService = moodleService;
        _recommendationService = recommendationService;
    }

    // Маршрут: GET /api/Recommendations/user/3/course/2
    [HttpGet("user/{userId}/course/{courseId}")]
    public async Task<IActionResult> GetRecommendations(int userId, int courseId)
    {
        // 1. Получаем оценки (Grades)
        var grades = await _moodleService.GetUserGradesAsync(userId, courseId);

        if (grades == null || !grades.Any())
        {
            // Если оценок нет, может быть стоит вернуть "общие" рекомендации?
            // Но пока вернем 404
            return NotFound("Оценки не найдены или пользователь не существует.");
        }

        // 2. Получаем теги курса (Tags)
        // Например: ["c#", "backend", "web"]
        var tags = await _moodleService.GetCourseTagsAsync(courseId);

        // 3. Обогащаем данные
        // Добавляем теги курса к каждой оценке, чтобы Python знал контекст.
        // (Python увидит: "Ага, он завалил тест 'Переменные', и этот тест относится к теме 'c#'")
        foreach (var grade in grades)
        {
            grade.CourseTags = tags;
        }

        // 4. Отправляем богатые данные в Python
        var recommendations = await _recommendationService.GetRecommendationsAsync(userId, grades);

        return Ok(recommendations);
    }
}