namespace RecommenderSystem.Core.DTOs;

public class UserGradeDto
{
    public string ItemName { get; set; } = string.Empty;
    public string ItemModule { get; set; } = string.Empty; 
    public string ItemType { get; set; } = string.Empty;   
    public double? RawGrade { get; set; } // Сама оценка
    public double? MaxGrade { get; set; } // Максимум
}