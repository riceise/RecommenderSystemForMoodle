namespace RecommenderSystem.Core.Entities;

public class Course
{
    public Guid Id { get; set; } 
    public string ExternalId { get; set; } = string.Empty; 
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Platform { get; set; } = string.Empty; 
    public string Difficulty { get; set; } = "Beginner";
    public List<string> Topics { get; set; } = new(); 

    public List<UserCourse> UserCourses { get; set; } = new();
}