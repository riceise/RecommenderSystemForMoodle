using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.PythonRequests;
using RecommenderSystem.Infrastructure.Interfaces;

namespace RecommenderSystem.Infrastructure.Services;

public class PythonAiService : IPythonAiService
{
    private readonly HttpClient _httpClient;
    private readonly string _pythonUrl;
    private readonly ILogger<PythonAiService> _logger;

    public PythonAiService(HttpClient httpClient, IConfiguration configuration, ILogger<PythonAiService> logger)
    {
        _httpClient = httpClient;
        _pythonUrl = configuration["PythonService:Url"] ?? "http://localhost:5000";
        _logger = logger;
    }

    public async Task<List<PythonResponseDto>> GetRecommendationsAsync(int userId, List<UserGradeDto> grades, List<string> contextTags)
    {

        var pythonGrades = grades.Select(g => new PythonGradeDto
        {
            ItemName = g.ItemName,
            RawGrade = g.RawGrade ?? 0,
            MaxGrade = g.MaxGrade ?? 100,
            CourseTags = contextTags
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
            _logger.LogError(ex, "[Python Bridge Error] Failed to get recommendations");
            return new List<PythonResponseDto>();
        }
    }

    /// <summary>
    /// Вызывает Python POST /analyze-course для AI-анализа успеваемости по конкретному курсу.
    /// </summary>
    public async Task<CourseAnalysisResponseDto?> AnalyzeCourseAsync(
        int moodleUserId,
        List<UserGradeDto> grades,
        List<string> courseTags)
    {
        var requestPayload = new CourseAnalysisRequest
        {
            UserId = moodleUserId,
            Grades = grades.Select(g => new CourseGradeEntry
            {
                ItemName = g.ItemName,
                RawGrade = g.RawGrade,
                MaxGrade = g.MaxGrade
            }).ToList(),
            CourseTags = courseTags
        };

        var json = JsonSerializer.Serialize(requestPayload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        try
        {
            var response = await _httpClient.PostAsync($"{_pythonUrl}/analyze-course", content);
            response.EnsureSuccessStatusCode();

            var responseString = await response.Content.ReadAsStringAsync();
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

            return JsonSerializer.Deserialize<CourseAnalysisResponseDto>(responseString, options);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "[Python Bridge Error] Failed to analyze course for user {UserId}", moodleUserId);
            return null;
        }
        catch (TaskCanceledException ex)
        {
            _logger.LogError(ex, "[Python Bridge Timeout] Analysis timed out for user {UserId}", moodleUserId);
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[Python Bridge Error] Unexpected error for user {UserId}", moodleUserId);
            return null;
        }
    }

    public async Task<string?> ChatAsync(ChatContextRequest request)
    {
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        try
        {
            var response = await _httpClient.PostAsync($"{_pythonUrl}/chat", content);
            response.EnsureSuccessStatusCode();

            var responseString = await response.Content.ReadAsStringAsync();
            var doc = JsonDocument.Parse(responseString);
            return doc.RootElement.TryGetProperty("reply", out var replyProp)
                ? replyProp.GetString()
                : "Не удалось получить ответ от AI.";
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "[Python Bridge Error] Chat request failed for user {UserId}", request.UserId);
            return null;
        }
        catch (TaskCanceledException ex)
        {
            _logger.LogError(ex, "[Python Bridge Timeout] Chat timed out for user {UserId}", request.UserId);
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[Python Bridge Error] Unexpected chat error for user {UserId}", request.UserId);
            return null;
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
            _logger.LogError(ex, "[Python Reload Error] Failed to notify Python service");
        }
    }
}