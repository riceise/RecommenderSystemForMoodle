namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Данные курса для административной таблицы управления
/// </summary>
public class CourseAdminDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Platform { get; set; } = string.Empty;
    public List<string> Topics { get; set; } = new();
    public string Difficulty { get; set; } = "Beginner";
}
