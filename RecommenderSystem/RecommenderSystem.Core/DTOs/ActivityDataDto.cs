namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// 7-ми дневная статистика
/// </summary>
public class ActivityDataDto
{
    public string Date { get; set; } = string.Empty; 
    public int Registrations { get; set; }
    public int GradesReceived { get; set; }
}
