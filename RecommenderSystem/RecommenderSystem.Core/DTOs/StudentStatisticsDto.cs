using System.Text.Json.Serialization;

namespace RecommenderSystem.Core.DTOs;

public class StudentStatisticsDto
{
    public int TotalGradesCount { get; set; }
    public double OverallAverageScore { get; set; }
    public GradeDistributionDto GradeDistribution { get; set; } = new();
    public int WeakCount { get; set; }
    public int CoursesCount { get; set; }
    public List<CourseProgressDto> CourseProgress { get; set; } = new();
}