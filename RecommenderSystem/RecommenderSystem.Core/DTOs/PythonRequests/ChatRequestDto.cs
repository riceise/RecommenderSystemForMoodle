using System.Text.Json.Serialization;

namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class ChatRequestDto
{
    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("context")]
    public string Context { get; set; } = "course";

    [JsonPropertyName("courseId")]
    public Guid? CourseId { get; set; }

    [JsonPropertyName("contextData")]
    public ChatContextPayload? ContextData { get; set; }
}

public class ChatContextPayload
{
    [JsonPropertyName("courseName")]
    public string CourseName { get; set; } = string.Empty;

    [JsonPropertyName("weakTopics")]
    public List<string> WeakTopics { get; set; } = new();

    [JsonPropertyName("strongTopics")]
    public List<string> StrongTopics { get; set; } = new();

    [JsonPropertyName("recentGrades")]
    public List<GradeEntryDto> RecentGrades { get; set; } = new();
}

public class ChatContextRequest
{
    [JsonPropertyName("userId")]
    public int UserId { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("context")]
    public string Context { get; set; } = "course";

    [JsonPropertyName("courseName")]
    public string CourseName { get; set; } = string.Empty;

    [JsonPropertyName("weakTopics")]
    public List<string> WeakTopics { get; set; } = new();

    [JsonPropertyName("strongTopics")]
    public List<string> StrongTopics { get; set; } = new();

    [JsonPropertyName("recentGradesSummary")]
    public string RecentGradesSummary { get; set; } = string.Empty;
}
