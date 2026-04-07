namespace RecommenderSystem.Core.DTOs.Student.Analytics;

public class StudentAnalyticsDto
{
    public InsightDto KnowledgeGap { get; set; } = new();
    public InsightDto Strength { get; set; } = new();
    public List<LearningPathItemDto> RecommendedPath { get; set; } = new();
    public List<SkillMetricDto> Skills { get; set; } = new();
    public RecoveryPlanDto RecoveryPlan { get; set; } = new();
}