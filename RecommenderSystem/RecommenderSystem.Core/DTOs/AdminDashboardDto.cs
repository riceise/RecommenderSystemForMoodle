namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Агрегированная статистика для карточек ключевых показателей эффективности панели администратора
/// </summary>
public class AdminDashboardDto
{
    public int TotalStudents { get; set; }
    public int ActiveCourses { get; set; }
    public int SyncedGradesCount { get; set; }
    public string LastSyncStatus { get; set; } = "Unknown"; 
    public DateTime? LastSyncDate { get; set; }
    public bool PythonServiceOnline { get; set; }
    public int RecommendationsGenerated { get; set; }
    public double AvgResponseTimeMs { get; set; }
}
