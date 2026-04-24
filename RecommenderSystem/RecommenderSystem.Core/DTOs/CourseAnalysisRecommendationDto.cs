namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Отдельная рекомендация в ответе AI-анализа курса.
/// Имена полей — PascalCase, строгое соответствие с Python-сервисом.
/// </summary>
public class CourseAnalysisRecommendationDto
{
    public string SourceKind { get; set; } = "internal";
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string ResourceType { get; set; } = "article";
    public string? Url { get; set; }
    public double RelevanceScore { get; set; }
    public string Difficulty { get; set; } = "Standard";
}
