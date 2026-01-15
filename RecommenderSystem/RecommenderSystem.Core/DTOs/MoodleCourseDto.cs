namespace RecommenderSystem.Core.DTOs;

public class MoodleCourseDto
{
    public int Id { get; set; }
    public string Fullname { get; set; } = string.Empty; 
    public string Shortname { get; set; } = string.Empty; 
    public string Summary { get; set; } = string.Empty;  
    
    public List<MoodleTagDto> Tags { get; set; } = new(); 

}