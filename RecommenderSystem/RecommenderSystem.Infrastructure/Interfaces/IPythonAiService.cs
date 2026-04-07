using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.PythonRequests;

namespace RecommenderSystem.Infrastructure.Interfaces;

public interface IPythonAiService
{
    Task<List<PythonResponseDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades, List<string> contextTags);
    Task TriggerDataReloadAsync();
    Task<CourseAnalysisResponseDto?> AnalyzeCourseAsync(int moodleUserId, List<UserGradeDto> grades, List<string> courseTags);
    Task<string?> ChatAsync(ChatContextRequest request);
}
