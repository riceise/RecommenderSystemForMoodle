namespace RecommenderSystem.Core.Entities;

public class ExternalCourse
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Platform { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public string Difficulty { get; set; } = "Beginner";
    public List<string> Topics { get; set; } = new();
    public string Language { get; set; } = "en";
    public string? ProviderCourseId { get; set; }
    public string SearchQuery { get; set; } = string.Empty;
    public string DiscoveryMethod { get; set; } = "ollama_search";
    public double ConfidenceScore { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime LastParsedAt { get; set; } = DateTime.UtcNow;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public string? MetadataJson { get; set; }
}