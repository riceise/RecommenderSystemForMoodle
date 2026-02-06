namespace RecommenderSystem.Core.Entities;

public class UserCourse
{
    public int Id { get; set; }
    public int MoodleStudentId { get; set; }
    public MoodleStudent? MoodleStudent { get; set; }
    public Guid CourseId { get; set; }
    
    public Course? Course { get; set; } = null!;

    public double? Grade { get; set; }
    
    public double? MaxGrade { get; set; }

    public DateTime LastSynced { get; set; } = DateTime.UtcNow;
}