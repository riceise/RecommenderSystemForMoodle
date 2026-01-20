

using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.PythonRequests;
using RecommenderSystem.Infrastructure.Interfaces;

namespace RecommenderSystem.Infrastructure.Services;

public class PythonAiService : IPythonAiService
{
    private readonly HttpClient _httpClient;
    private readonly string _pythonUrl;

    public PythonAiService(HttpClient httpClient, IConfiguration configuration)
    {
        _httpClient = httpClient;
        _pythonUrl = configuration["PythonService:Url"] ?? "http://localhost:5000";
    }

    public async Task<List<PythonResponseDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades, List<string> contextTags)
    {
        
        var pythonGrades = grades.Select(g => new PythonGradeDto
        {
            ItemName = g.ItemName,
            RawGrade = g.RawGrade ?? 0,
            MaxGrade = g.MaxGrade ?? 100,
            CourseTags = g.CourseTags.Any() ? g.CourseTags : contextTags
        }).ToList();

        var requestPayload = new PythonRecommendationRequest
        {
            UserId = userId,
            MoodleGrades = pythonGrades
        };

        var json = JsonSerializer.Serialize(requestPayload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        try
        {
            var response = await _httpClient.PostAsync($"{_pythonUrl}/recommend", content);
            response.EnsureSuccessStatusCode();

            var responseString = await response.Content.ReadAsStringAsync();
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            
            return JsonSerializer.Deserialize<List<PythonResponseDto>>(responseString, options) 
                   ?? new List<PythonResponseDto>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Python Bridge Error] {ex.Message}");
            return new List<PythonResponseDto>();
        }
    }

    public async Task TriggerDataReloadAsync()
    {
        try
        {
            await _httpClient.PostAsync($"{_pythonUrl}/reload", null);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Python Reload Error] Failed to notify Python service: {ex.Message}");
        }
    }
}