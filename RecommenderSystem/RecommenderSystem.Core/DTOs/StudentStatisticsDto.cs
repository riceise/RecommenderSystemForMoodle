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

public class GradeDistributionDto
{
    public int Two { get; set; }
    public int Three { get; set; }
    public int Four { get; set; }
    public int Five { get; set; }
}

public class CourseProgressDto
{
    public string CourseTitle { get; set; } = string.Empty;
    public double AveragePercentage { get; set; }
}
