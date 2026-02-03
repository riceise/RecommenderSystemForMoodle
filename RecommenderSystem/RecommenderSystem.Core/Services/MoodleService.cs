using System.Collections.Concurrent;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Configuration;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.Interfaces;

namespace RecommenderSystem.Core.Services;

public class MoodleService : IMoodleService
{
    private readonly HttpClient _httpClient;
    private readonly string _token;

    private static readonly ConcurrentDictionary<int, List<string>> _tagsCache = new();

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
    /// Получает все курсы из Moodle с параллельной подгрузкой тегов
    /// </summary>
    public async Task<List<MoodleCourseDto>> GetAllCoursesAsync()
    {
        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=core_course_get_courses" +
                          $"&moodlewsrestformat=json";
        
        List<MoodleCourseDto> resultCourses = new();

        try
        {
            var jsonString = await _httpClient.GetStringAsync(queryParams);
            
            if (string.IsNullOrEmpty(jsonString) || jsonString.Contains("\"exception\""))
            {
                Console.WriteLine($"[Moodle API Error/Empty]: {jsonString}");
                return resultCourses;
            }

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var jsonNode = JsonNode.Parse(jsonString);

            if (jsonNode is JsonArray)
            {
                var rawCourses = JsonSerializer.Deserialize<List<MoodleCourseRaw>>(jsonString, options);
                resultCourses = MapRawToDto(rawCourses);
            }
            else if (jsonNode is JsonObject jsonObj && jsonObj.ContainsKey("courses"))
            {
                var wrapper = JsonSerializer.Deserialize<MoodleCourseListResponse>(jsonString, options);
                resultCourses = MapRawToDto(wrapper?.Courses);
            }

            if (!resultCourses.Any()) return resultCourses;
            
            var semaphore = new SemaphoreSlim(20);
            var tasks = resultCourses.Select(async course =>
            {
                await semaphore.WaitAsync();
                try
                {
                    if (course.Tags == null || !course.Tags.Any())
                    {
                        var tagStrings = await GetCourseTagsAsync(course.Id);
                        course.Tags = tagStrings.Select(t => new MoodleTagDto { Name = t }).ToList();
                    }
                }
                finally
                {
                    semaphore.Release();
                }
            });

            await Task.WhenAll(tasks);

            return resultCourses;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Critical Error] GetAllCoursesAsync failed: {ex.Message}");
            return new List<MoodleCourseDto>();
        }
    }

    private List<MoodleCourseDto> MapRawToDto(List<MoodleCourseRaw>? rawList)
    {
        if (rawList == null) return new List<MoodleCourseDto>();

        return rawList
            .Where(c => c.Id > 1)
            .Select(c => new MoodleCourseDto
            {
                Id = c.Id,
                Fullname = c.Fullname ?? "Unnamed Course",
                Shortname = c.Shortname ?? "",
                Summary = c.Summary ?? "",
                Tags = new List<MoodleTagDto>()
            })
            .ToList();
    }

    public async Task<List<string>> GetCourseTagsAsync(int courseId)
    {
        if (_tagsCache.TryGetValue(courseId, out var cachedTags)) return cachedTags;

        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=core_tag_get_item_tags" +
                          $"&moodlewsrestformat=json" +
                          $"&component=core" +
                          $"&itemtype=course" +
                          $"&itemid={courseId}";

        try
        {
            var jsonResponse = await _httpClient.GetStringAsync(queryParams);

            if (jsonResponse.Contains("\"exception\"")) return new List<string>();

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var response = JsonSerializer.Deserialize<MoodleTagResponse>(jsonResponse, options);

            if (response != null && response.Tags != null)
            {
                var result = response.Tags.Select(t => t.Name).ToList();
                _tagsCache[courseId] = result; 
                return result;
            }
        }
        catch(Exception ex)
        {
            Console.WriteLine($"[Tag Warning] Failed to fetch tags for course {courseId}: {ex.Message}");
        }

        return new List<string>();
    }

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

            if (response?.UserGrades == null || !response.UserGrades.Any())
                return new List<UserGradeDto>();

            var userGradeData = response.UserGrades.First();

            return userGradeData.GradeItems
                .Select(item => new UserGradeDto
                {
                    ItemName = item.ItemName ?? "Итоговая оценка",
                    ItemModule = item.ItemModule,
                    ItemType = item.ItemType,
                    RawGrade = item.GradeRaw,
                    MaxGrade = item.GradeMax
                })
                .ToList();
        }
        catch
        {
            return new List<UserGradeDto>();
        }
    }

    public async Task<int?> GetUserIdByUsernameAsync(string username)
    {
        var queryParams = $"?wstoken={_token}&wsfunction=core_user_get_users&moodlewsrestformat=json&criteria[0][key]=username&criteria[0][value]={username}";
        try
        {
            var response = await _httpClient.GetFromJsonAsync<MoodleUserResponse>(queryParams);
            return response?.Users?.FirstOrDefault()?.Id;
        }
        catch
        {
            return null;
        }
    }

    public async Task<List<MoodleUserDto>> GetEnrolledUsersAsync(int courseId)
    {
        var queryParams = $"?wstoken={_token}&wsfunction=core_enrol_get_enrolled_users&moodlewsrestformat=json&courseid={courseId}";

        try
        {
            var jsonResponse = await _httpClient.GetStringAsync(queryParams);
            if (jsonResponse.Contains("\"exception\"")) return new List<MoodleUserDto>();

            var users = JsonSerializer.Deserialize<List<MoodleEnrolledUserDto>>(jsonResponse);

            return users?.Select(u => new MoodleUserDto
            {
                Id = u.Id,
                Username = u.Username,
                Fullname = u.Fullname,
                Email = u.Email
            }).ToList() ?? new List<MoodleUserDto>();
        }
        catch
        {
            return new List<MoodleUserDto>();
        }
    }

    public async Task<List<string>> GetTopicsWithActivitiesAsync(int courseId)
    {
        var queryParams = $"?wstoken={_token}" +
                          $"&wsfunction=core_course_get_contents" +
                          $"&moodlewsrestformat=json" +
                          $"&courseid={courseId}";

        try
        {
            var jsonString = await _httpClient.GetStringAsync(queryParams);
            if (jsonString.Contains("\"exception\"")) return new List<string>();

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var sections = JsonSerializer.Deserialize<List<MoodleSection>>(jsonString, options);

            if (sections == null) return new List<string>();

            return sections
                .Where(section => section.Modules.Any(mod => mod.ModName == "quiz" || mod.ModName == "assign"))
                .Select(section => section.Name)
                .Where(name => !string.IsNullOrWhiteSpace(name))
                .ToList();
        }
        catch
        {
            return new List<string>();
        }
    }

    /// <summary>
    /// Внутренние классы для десериализации JSON
    /// <summary>
    #region JSON Models for GetAllCourses (Internal)

    private class MoodleCourseRaw
    {
        [JsonPropertyName("id")] 
        public int Id { get; set; }
        [JsonPropertyName("fullname")] 
        public string? Fullname { get; set; }
        [JsonPropertyName("shortname")] 
        public string? Shortname { get; set; }
        [JsonPropertyName("summary")] 
        public string? Summary { get; set; }
    }

    private class MoodleCourseListResponse
    {
        [JsonPropertyName("courses")] 
        public List<MoodleCourseRaw> Courses { get; set; } = new();
        [JsonPropertyName("warnings")] 
        public List<object>? Warnings { get; set; }
    }

    #endregion

    #region JSON Models for Grades
    private class MoodleGradeResponse
    {
        [JsonPropertyName("usergrades")] 
        public List<MoodleUserGrade>? UserGrades { get; set; }
    }
    private class MoodleUserGrade
    {
        [JsonPropertyName("courseid")] 
        public int CourseId { get; set; }
        [JsonPropertyName("userid")] 
        public int UserId { get; set; }
        [JsonPropertyName("gradeitems")] 
        public List<MoodleGradeItem> GradeItems { get; set; } = new();
    }
    private class MoodleGradeItem
    {
        [JsonPropertyName("itemname")] 
        public string ItemName { get; set; } = string.Empty;
        [JsonPropertyName("itemtype")] 
        public string ItemType { get; set; } = string.Empty;
        [JsonPropertyName("itemmodule")] 
        public string ItemModule { get; set; } = string.Empty;
        [JsonPropertyName("graderaw")]
        public double? GradeRaw { get; set; }
        [JsonPropertyName("grademax")] 
        public double? GradeMax { get; set; }
    }
    #endregion

    #region JSON Models for Tags

    private class MoodleTagResponse
    {
        [JsonPropertyName("tags")] 
        public List<MoodleItemTag>? Tags { get; set; }
    }

    private class MoodleItemTag
    {
        [JsonPropertyName("id")] 
        public int Id { get; set; }
        [JsonPropertyName("rawname")] 
        public string? RawName { get; set; }
        [JsonPropertyName("displayname")] 
        public string? DisplayName { get; set; }
        public string Name => !string.IsNullOrEmpty(DisplayName) ? DisplayName : (RawName ?? "");
    }

    #endregion

    #region JSON Models for Users
    private class MoodleUserResponse
    {
        [JsonPropertyName("users")] 
        public List<MoodleUserRaw>? Users { get; set; }
    }
    private class MoodleUserRaw
    {
        [JsonPropertyName("id")] 
        public int Id { get; set; }
        [JsonPropertyName("username")] 
        public string Username { get; set; } = string.Empty;
        [JsonPropertyName("fullname")]
        public string Fullname { get; set; } = string.Empty;
        [JsonPropertyName("email")]
        public string Email { get; set; } = string.Empty;
    }
    private class MoodleEnrolledUserDto
    {
        [JsonPropertyName("id")] public int Id { get; set; }
        [JsonPropertyName("username")] public string Username { get; set; } = string.Empty;
        [JsonPropertyName("fullname")] public string Fullname { get; set; } = string.Empty;
        [JsonPropertyName("email")] public string Email { get; set; } = string.Empty;
    }
    #endregion
    
    #region JSON Models for Course Content
    private class MoodleSection 
    { 
        [JsonPropertyName("name")] 
        public string Name { get; set; } = "";
        [JsonPropertyName("modules")] 
        public List<MoodleModule> Modules { get; set; } = new();
    }

    private class MoodleModule
    {
        [JsonPropertyName("modname")] 
        public string ModName { get; set; } = "";
    }
    #endregion

}