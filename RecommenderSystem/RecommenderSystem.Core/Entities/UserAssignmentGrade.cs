namespace RecommenderSystem.Core.Entities;

public class UserAssignmentGrade
{
    public int Id { get; set; }
    
    public int UserCourseId { get; set; }
    public UserCourse? UserCourse { get; set; }

    public string ItemName { get; set; } = string.Empty; 
    
    public string ItemModule { get; set; } = string.Empty;
    
    public double? Grade { get; set; }
    public double? MaxGrade { get; set; }
    
    public DateTime LastSynced { get; set; } = DateTime.UtcNow;
}