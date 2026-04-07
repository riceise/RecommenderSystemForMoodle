namespace RecommenderSystem.Core.DTOs.Student.Analytics;

public class LearningPathItemDto
{
    public string Type { get; set; } = "Quiz"; // "Video", "Quiz", "Sandbox"
    public string Title { get; set; } = string.Empty;
}