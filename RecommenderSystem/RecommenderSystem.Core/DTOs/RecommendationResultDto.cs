namespace RecommenderSystem.Core.DTOs;

public class RecommendationResultDto
{
    public int? CourseId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string ResourceType { get; set; } = "article";
    public string? Url { get; set; }
    public double RelevanceScore { get; set; }
    public List<string> Topics { get; set; } = new();
    public string Difficulty { get; set; } = "Standard";
}