namespace RecommenderSystem.Core.DTOs.Student.Analytics;

public class RecoveryPlanDto
{
    public bool IsEmergency { get; set; }
    public string PredictedGrade { get; set; } = string.Empty;
    public string TargetGrade { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}