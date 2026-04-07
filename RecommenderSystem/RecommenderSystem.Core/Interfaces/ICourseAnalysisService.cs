using RecommenderSystem.Core.DTOs;

namespace RecommenderSystem.Core.Interfaces;

/// <summary>
/// Сервис AI-анализа успеваемости по конкретному курсу.
/// Оркестрирует: БД → Moodle → Python → Groq → ответ.
/// </summary>
public interface ICourseAnalysisService
{
    /// <summary>
    /// Выполняет AI-анализ успеваемости студента по указанному курсу.
    /// </summary>
    /// <param name="moodleUserId">Moodle User ID (из JWT)</param>
    /// <param name="courseId">ID курса в нашей БД (Guid)</param>
    /// <returns>Полный анализ с рекомендациями</returns>
    Task<CourseAnalysisResponseDto> AnalyzeCourseAsync(int moodleUserId, Guid courseId);
}
