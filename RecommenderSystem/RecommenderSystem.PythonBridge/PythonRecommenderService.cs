using System.Net.Http.Json;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.PythonBridge;

public class PythonRecommenderService : IRecommendationService
{
    private readonly HttpClient _httpClient;

    // HttpClient будет создан автоматически и настроен в Program.cs
    public PythonRecommenderService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<List<RecommendationResultDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades)
    {
        // 1. Формируем запрос, который ждет Python (смотри свой main.py)
        var payload = new
        {
            userId = userId,
            moodleGrades = grades
        };

        // 2. Отправляем POST запрос на localhost:5001/recommend
        var response = await _httpClient.PostAsJsonAsync("/recommend", payload);

        // 3. Если ошибка - выбрасываем исключение
        response.EnsureSuccessStatusCode();

        // 4. Читаем ответ
        var result = await response.Content.ReadFromJsonAsync<PythonResponseWrapper>();
        
        return result?.Recommendations ?? new List<RecommendationResultDto>();
    }

    // Вспомогательный класс для парсинга JSON ответа от Python
    // (Потому что Python возвращает { "userId": 1, "recommendations": [...] })
    private class PythonResponseWrapper
    {
        public int UserId { get; set; }
        public List<RecommendationResultDto> Recommendations { get; set; }
    }
}