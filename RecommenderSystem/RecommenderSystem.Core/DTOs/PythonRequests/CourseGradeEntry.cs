using System.Text.Json.Serialization;

namespace RecommenderSystem.Core.DTOs.PythonRequests;

/// <summary>
/// Одна оценка в запросе анализа курса.
/// </summary>
public class CourseGradeEntry
{
    [JsonPropertyName("ItemName")]
    public string ItemName { get; set; } = string.Empty;

    [JsonPropertyName("RawGrade")]
    public double? RawGrade { get; set; }

    [JsonPropertyName("MaxGrade")]
    public double? MaxGrade { get; set; }
}