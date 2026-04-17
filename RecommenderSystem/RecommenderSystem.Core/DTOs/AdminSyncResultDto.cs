namespace RecommenderSystem.Core.DTOs;

/// <summary>
/// Результат операции синхронизации с подробной статистикой
/// </summary>
public class AdminSyncResultDto
{
    public bool Success { get; set; }
    public int AddedCount { get; set; }
    public int UpdatedCount { get; set; }
    public int NewStudentsCount { get; set; }
    public int GradesUpdatedCount { get; set; }
    public int AssignmentsUpdatedCount { get; set; }
    public string Message { get; set; } = string.Empty;
}
