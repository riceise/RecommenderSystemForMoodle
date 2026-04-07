using System.Text.Json.Serialization;

namespace RecommenderSystem.Core.DTOs.PythonRequests;

/// <summary>
/// Запрос к Python /analyze-course.
/// </summary>
public class CourseAnalysisRequest
{
    [JsonPropertyName("userId")]
    public int UserId { get; set; }

    [JsonPropertyName("courseId")]
    public Guid CourseId { get; set; }

    [JsonPropertyName("grades")]
    public List<CourseGradeEntry> Grades { get; set; } = new();

    [JsonPropertyName("courseTags")]
    public List<string> CourseTags { get; set; } = new();
}

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
