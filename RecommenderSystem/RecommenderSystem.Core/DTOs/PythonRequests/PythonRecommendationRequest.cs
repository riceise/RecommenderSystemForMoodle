using System.Text.Json.Serialization;


namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class PythonRecommendationRequest
{
    [JsonPropertyName("userId")]
    public int UserId { get; set; }

    [JsonPropertyName("sessionId")]
    public string SessionId { get; set; } = string.Empty;

    [JsonPropertyName("contextTags")]
    public List<string> ContextTags { get; set; } = new();

    [JsonPropertyName("moodleGrades")]
    public List<PythonGradeDto> MoodleGrades { get; set; } = new();
}
