namespace RecommenderSystem.Core.DTOs;

public class UserGradeDto
{
    public string ItemName { get; set; } = string.Empty; 
    public string ModuleType { get; set; } = string.Empty; 
    public double? RawGrade { get; set; }
    public double? MaxGrade { get; set; }
    
    
    public List<string> CourseTags { get; set; } = new(); 
}