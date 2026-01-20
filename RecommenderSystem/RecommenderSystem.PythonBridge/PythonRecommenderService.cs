using System.Net.Http.Json;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.PythonBridge;

public class PythonRecommenderService : IRecommendationService
{
    private readonly HttpClient _httpClient;

    public PythonRecommenderService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<List<RecommendationResultDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades, List<string> contextTags)
    {
       
        var pythonGrades = grades.Select(g => new
        {
            ItemName = g.ItemName,
            RawGrade = g.RawGrade ?? 0,
            MaxGrade = g.MaxGrade ?? 100,
            CourseTags = contextTags 
        }).ToList();

        var payload = new
        {
            userId = userId,
            moodleGrades = pythonGrades
        };

        
        var response = await _httpClient.PostAsJsonAsync("/recommend", payload);
        
        response.EnsureSuccessStatusCode();

        
        try 
        {
            var result = await response.Content.ReadFromJsonAsync<List<RecommendationResultDto>>();
            return result ?? new List<RecommendationResultDto>();
        }
        catch
        {
            var wrapper = await response.Content.ReadFromJsonAsync<PythonResponseWrapper>();
            return wrapper?.Recommendations ?? new List<RecommendationResultDto>();
        }
    }

    private class PythonResponseWrapper
    {
        public int UserId { get; set; }
        public List<RecommendationResultDto> Recommendations { get; set; }
    }
}