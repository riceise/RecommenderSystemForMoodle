namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Текст запроса на обновление сложности и тем курса
/// </summary>
public class UpdateCourseRequestDto
{
    public string Difficulty { get; set; } = "Beginner"; 
    public List<string> Topics { get; set; } = new();
}
