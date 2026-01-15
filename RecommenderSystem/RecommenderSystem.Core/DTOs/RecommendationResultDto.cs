namespace RecommenderSystem.Core.DTOs;

public class RecommendationResultDto
{
    public string CourseId { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public double Score { get; set; } // Уверенность модели (0.0 - 1.0)
    public string Reason { get; set; } = string.Empty; // "Рекомендуем, так как вы завалили C#"
}