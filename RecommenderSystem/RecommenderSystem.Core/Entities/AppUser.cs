namespace RecommenderSystem.Core.Entities;

public class AppUser
{
    public int Id { get; set; } 
    public int MoodleUserId { get; set; } 
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
}