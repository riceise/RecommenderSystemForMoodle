namespace RecommenderSystem.Core.Entities;

public class AiRecommendationHistory
{
    public Guid Id { get; set; }
    public string SessionId { get; set; } = string.Empty;
    public int UserId { get; set; }
    public Guid? ContextCourseId { get; set; }
    public string SourceKind { get; set; } = "internal";
    public Guid? InternalCourseId { get; set; }
    public Course? InternalCourse { get; set; }
    public Guid? ExternalCourseId { get; set; }
    public ExternalCourse? ExternalCourse { get; set; }
    public string TitleSnapshot { get; set; } = string.Empty;
    public string Reason { get; set; } = string.Empty;
    public double RelevanceScore { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
