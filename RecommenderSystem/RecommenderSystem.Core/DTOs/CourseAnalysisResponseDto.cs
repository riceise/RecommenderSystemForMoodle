namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Полный ответ AI-анализа успеваемости по курсу.
/// Возвращается клиенту (Vue.js).
/// </summary>
public class CourseAnalysisResponseDto
{
    /// <summary>Текстовый анализ успеваемости (на русском).</summary>
    public string Analysis { get; set; } = string.Empty;

    /// <summary>Слабые темы студента (оценка &lt; 60%).</summary>
    public List<string> WeakTopics { get; set; } = new();

    /// <summary>Сильные темы студента (оценка &gt; 85%).</summary>
    public List<string> StrongTopics { get; set; } = new();

    /// <summary>Персональные рекомендации от Groq LLM.</summary>
    public List<CourseAnalysisRecommendationDto> Recommendations { get; set; } = new();
}
