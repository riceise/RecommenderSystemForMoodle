using System.Text.Json.Serialization;


namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class PythonRecommendationRequest
{
    [JsonPropertyName("userId")]
    public int UserId { get; set; }

    [JsonPropertyName("moodleGrades")]
    public List<PythonGradeDto> MoodleGrades { get; set; } = new();
}
