namespace RecommenderSystem.Core.DTOs.Student;

public class AssignmentGradeDto
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public double? Grade { get; set; }
    public double? MaxGrade { get; set; }
}