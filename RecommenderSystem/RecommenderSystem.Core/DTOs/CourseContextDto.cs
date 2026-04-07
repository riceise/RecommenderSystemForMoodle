using System.Text.Json.Serialization;

namespace RecommenderSystem.Core.DTOs;

public class CourseContextDto
{
    public string CourseName { get; set; } = string.Empty;
    public List<string> WeakTopics { get; set; } = new();
    public List<string> StrongTopics { get; set; } = new();
    public List<GradeEntryDto> RecentGrades { get; set; } = new();
}

public class GradeEntryDto
{
    public string ItemName { get; set; } = string.Empty;
    public double? Grade { get; set; }
    public double? MaxGrade { get; set; }
}
