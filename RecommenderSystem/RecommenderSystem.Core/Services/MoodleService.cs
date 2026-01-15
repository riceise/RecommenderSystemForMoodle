using System.Net.Http.Json;
using Microsoft.Extensions.Configuration;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.Interfaces;
using System.Text.Json.Serialization; 
using System.Text.Json; 

namespace RecommenderSystem.Infrastructure.Services;

public class MoodleService : IMoodleService
{
    private readonly HttpClient _httpClient;
    private readonly string _token;
    
    // Простой кэш в памяти для тегов
    private static readonly Dictionary<int, List<string>> _tagsCache = new();

    public MoodleService(HttpClient httpClient, IConfiguration configuration)
    {
        _httpClient = httpClient;
        
        var baseUrl = configuration["Moodle:Url"];
        _token = configuration["Moodle:Token"] ?? throw new ArgumentNullException("Moodle Token not found in config");

        if (string.IsNullOrEmpty(baseUrl))
        {
            throw new ArgumentNullException("Moodle URL not found in config");
        }

        _httpClient.BaseAddress = new Uri(baseUrl);
    }

    /// <summary>
    /// Получает список оценок пользователя по конкретному курсу
    /// </summary>
    public async Task<List<UserGradeDto>> GetUserGradesAsync(int userId, int courseId)
    {
        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=gradereport_user_get_grade_items" +
                          $"&moodlewsrestformat=json" +
                          $"&userid={userId}" +
                          $"&courseid={courseId}";

        try
        {
            var response = await _httpClient.GetFromJsonAsync<MoodleGradeResponse>(queryParams);

            if (response == null || response.UserGrades == null || !response.UserGrades.Any())
            {
                return new List<UserGradeDto>();
            }

            var userGradeData = response.UserGrades.First();

            var cleanGrades = userGradeData.GradeItems
                .Where(item => item.ItemType == "mod")
                .Select(item => new UserGradeDto
                {
                    ItemName = item.ItemName,
                    ModuleType = item.ItemModule,
                    RawGrade = item.GradeRaw,
                    MaxGrade = item.GradeMax,
                    CourseTags = new List<string>() 
                })
                .ToList();

            return cleanGrades;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MoodleService] Error fetching grades: {ex.Message}");
            return new List<UserGradeDto>();
        }
    }

    /// <summary>
    /// Получает теги курса по его ID
    /// </summary>
    public async Task<List<string>> GetCourseTagsAsync(int courseId)
    {
        if (_tagsCache.ContainsKey(courseId))
        {
            return _tagsCache[courseId];
        }

        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=core_course_get_courses_by_field" +
                          $"&moodlewsrestformat=json" +
                          $"&field=id" +
                          $"&value={courseId}";

        try
        {
            var jsonString = await _httpClient.GetStringAsync(queryParams);
            
            Console.WriteLine($"[DEBUG] Raw JSON for Course {courseId}: {jsonString}");

            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true 
            };

            var response = JsonSerializer.Deserialize<MoodleCourseResponse>(jsonString, options);

            if (response != null && response.Courses != null && response.Courses.Any())
            {
                var course = response.Courses.First();
                
                if (course.Tags == null) 
                {
                    Console.WriteLine($"[WARN] Course {courseId} found, but 'tags' field is NULL.");
                    return new List<string>();
                }

                var tags = course.Tags.Select(t => t.Name).ToList();
                
                Console.WriteLine($"[DEBUG] Extracted tags: {string.Join(", ", tags)}");
                
                _tagsCache[courseId] = tags;
                return tags;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MoodleService] Error fetching tags: {ex.Message}");
        }

        return new List<string>();
    }

    
    /// <summary>
    /// Находит ID пользователя по логину
    /// </summary>
    public async Task<int?> GetUserIdByUsernameAsync(string username)
    {
        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=core_user_get_users" +
                          $"&moodlewsrestformat=json" +
                          $"&criteria[0][key]=username" +
                          $"&criteria[0][value]={username}";

        try
        {
            var response = await _httpClient.GetFromJsonAsync<MoodleUserResponse>(queryParams);

            if (response != null && response.Users != null && response.Users.Any())
            {
                return response.Users.First().Id;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error finding user {username}: {ex.Message}");
        }

        return null;
    }
    
    /// <summary>
    /// Берет все курсы 
    /// </summary>
    public async Task<List<MoodleCourseDto>> GetAllCoursesAsync()
    {
        var queryParams = $"?wstoken={_token}&wsfunction=core_course_get_courses&moodlewsrestformat=json";

        try
        {
            var jsonResponse = await _httpClient.GetStringAsync(queryParams);

            if (jsonResponse.Contains("\"exception\""))
            {
                Console.WriteLine($"[Moodle Error]: {jsonResponse}");
                return new List<MoodleCourseDto>();
            }

            
            var courses = System.Text.Json.JsonSerializer.Deserialize<List<MoodleCourseDto>>(
                jsonResponse, 
                new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true }
            );

            return courses?.Where(c => c.Id > 1).ToList() ?? new List<MoodleCourseDto>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error fetching all courses: {ex.Message}");
            return new List<MoodleCourseDto>();
        }
    }
    
    // ==========================================
    // Внутренние классы для десериализации JSON
    // ==========================================

    #region JSON Models for Grades
    private class MoodleGradeResponse
    {
        public List<MoodleUserGrade>? UserGrades { get; set; }
    }

    private class MoodleUserGrade
    {
        public int CourseId { get; set; }
        public int UserId { get; set; }
        public List<MoodleGradeItem> GradeItems { get; set; } = new();
    }

    private class MoodleGradeItem
    {
        public string ItemName { get; set; } = string.Empty;
        public string ItemType { get; set; } = string.Empty;
        public string ItemModule { get; set; } = string.Empty;
        public double? GradeRaw { get; set; }
        public double? GradeMax { get; set; }
    }
    #endregion

    #region JSON Models for Courses & Tags
    private class MoodleCourseResponse
    {
        [JsonPropertyName("courses")]
        public List<MoodleCourse>? Courses { get; set; }
    }

    private class MoodleCourse
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("fullname")]
        public string Fullname { get; set; } = string.Empty;

        [JsonPropertyName("tags")] 
        public List<MoodleTag> Tags { get; set; } = new();
    }

    private class MoodleTag
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("name")] 
        public string Name { get; set; } = string.Empty;
    }
    
    #endregion

    #region JSON Models for Users
    private class MoodleUserResponse
    {
        public List<MoodleUserRaw>? Users { get; set; }
    }

    private class MoodleUserRaw
    {
        public int Id { get; set; }
        public string Username { get; set; } = string.Empty;
        public string Fullname { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
    }
    #endregion
}