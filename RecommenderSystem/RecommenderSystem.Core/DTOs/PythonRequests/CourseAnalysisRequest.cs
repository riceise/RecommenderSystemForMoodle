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
    
    [JsonPropertyName("courseName")]
    public string CourseName { get; set; } = string.Empty;
    
    [JsonPropertyName("grades")]
    public List<CourseGradeEntry> Grades { get; set; } = new();

    [JsonPropertyName("courseTags")]
    public List<string> CourseTags { get; set; } = new();
}