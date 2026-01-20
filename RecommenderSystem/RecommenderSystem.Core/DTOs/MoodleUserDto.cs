
namespace RecommenderSystem.Core.DTOs;

public class MoodleUserDto {
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string Fullname { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
}