using Microsoft.AspNetCore.Identity;

namespace RecommenderSystem.Core.Entities;

public class AppUser : IdentityUser
{
    public int MoodleUserId { get; set; } 
    public string FullName { get; set; } = string.Empty; 
}