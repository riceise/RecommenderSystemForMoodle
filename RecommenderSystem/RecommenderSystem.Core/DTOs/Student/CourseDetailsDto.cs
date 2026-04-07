namespace RecommenderSystem.Core.DTOs.Student;

public class CourseDetailsDto
{
    public Guid CourseId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string CourseMeta { get; set; } = "Advanced Computer Science track • Semester 2, 2024";
    public double OverallGrade { get; set; }
    public double MaxGrade { get; set; }
    public List<AssignmentGradeDto> Assignments { get; set; } = new();
}