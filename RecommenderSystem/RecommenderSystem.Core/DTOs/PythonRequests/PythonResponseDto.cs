using System.Text.Json.Serialization;


namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class PythonResponseDto
{
    [JsonPropertyName("course_id")]
    public int CourseId { get; set; } 

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("provider")]
    public string Provider { get; set; } = string.Empty;

    [JsonPropertyName("similarity_score")]
    public double Score { get; set; }

    [JsonPropertyName("reason")]
    public string Reason { get; set; } = string.Empty;
}