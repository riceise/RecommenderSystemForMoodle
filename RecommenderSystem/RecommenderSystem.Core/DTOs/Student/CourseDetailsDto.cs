namespace RecommenderSystem.Core.DTOs.Student;

public class CourseDetailsDto
{
    public Guid CourseId { get; set; }
    public string Title { get; set; } = string.Empty;
    public List<AssignmentGradeDto> Assignments { get; set; } = new();
}