using RecommenderSystem.Core.DTOs;

namespace RecommenderSystem.Core.Interfaces;

public interface IRecommendationService
{
    // Метод принимает ID юзера и СПИСОК его оценок, а возвращает рекомендации
    Task<List<RecommendationResultDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades);
}