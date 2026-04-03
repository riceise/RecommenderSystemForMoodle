namespace RecommenderSystem.Core.DTOs.Student;

public class CourseSummaryDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public double? OverallGrade { get; set; }
    public double? MaxGrade { get; set; }
}