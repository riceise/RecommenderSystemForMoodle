using System.Text.Json.Serialization;


namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class PythonResponseDto
{
    [JsonPropertyName("internalCourseId")]
    public Guid? InternalCourseId { get; set; }

    [JsonPropertyName("externalCourseId")]
    public Guid? ExternalCourseId { get; set; }

    [JsonPropertyName("sourceKind")]
    public string SourceKind { get; set; } = "internal";

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("resourceType")]
    public string ResourceType { get; set; } = "course";

    [JsonPropertyName("url")]
    public string? Url { get; set; }

    [JsonPropertyName("relevanceScore")]
    public double RelevanceScore { get; set; }

    [JsonPropertyName("topics")]
    public List<string> Topics { get; set; } = new();

    [JsonPropertyName("difficulty")]
    public string Difficulty { get; set; } = "Standard";

    [JsonPropertyName("reason")]
    public string Reason { get; set; } = string.Empty;
}