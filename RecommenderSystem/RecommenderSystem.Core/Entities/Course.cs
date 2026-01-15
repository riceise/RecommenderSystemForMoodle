namespace RecommenderSystem.Core.Entities;

public class Course
{
    public Guid Id { get; set; } // Внутренний ID системы
    public string ExternalId { get; set; } = string.Empty; // ID из Moodle/Coursera ("2", "coursera_py")
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Platform { get; set; } = string.Empty; // "Moodle", "Coursera"
    public string Difficulty { get; set; } = "Beginner";
    
    // Храним теги как строку через запятую или JSON, для простоты - массивом строк (Postgres умеет)
    public List<string> Topics { get; set; } = new(); 
}