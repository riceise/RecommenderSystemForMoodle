using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;
using System.Collections.Concurrent;
using System.Text.RegularExpressions;
using RecommenderSystem.Core.DTOs;
using System.Net.Http;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AdminController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IMoodleService _moodleService;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IConfiguration _configuration;

    public AdminController(AppDbContext context, IMoodleService moodleService, IHttpClientFactory httpClientFactory, IConfiguration configuration)
    {
        _context = context;
        _moodleService = moodleService;
        _httpClientFactory = httpClientFactory;
        _configuration = configuration;
    }


    [HttpGet("dashboard")]
    public async Task<ActionResult<AdminDashboardDto>> GetDashboardStats()
    {
        var totalStudents = await _context.MoodleStudents.CountAsync();
        var activeCourses = await _context.Courses.CountAsync();
        var syncedGrades = await _context.UserAssignmentGrades.CountAsync();

        var lastSyncedCourse = await _context.UserCourses
            .OrderByDescending(uc => uc.LastSynced)
            .Select(uc => uc.LastSynced)
            .FirstOrDefaultAsync();

        var lastSyncStatus = lastSyncedCourse != default(DateTime) ? "Success" : "Never";
        var lastSyncDate = lastSyncedCourse != default(DateTime) ? lastSyncedCourse : (DateTime?)null;

        bool pythonServiceOnline = false;
        int recommendationsGenerated = 0;
        double avgResponseTimeMs = 0;

        try
        {
            var pythonUrl = _configuration["PythonService:Url"] ?? "http://localhost:5001";
            var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromSeconds(3);
            var response = await client.GetAsync($"{pythonUrl}/health");
            if (response.IsSuccessStatusCode)
            {
                pythonServiceOnline = true;
            }
        }
        catch
        {
            pythonServiceOnline = false;
        }

        return new AdminDashboardDto
        {
            TotalStudents = totalStudents,
            ActiveCourses = activeCourses,
            SyncedGradesCount = syncedGrades,
            LastSyncStatus = lastSyncStatus,
            LastSyncDate = lastSyncDate,
            PythonServiceOnline = pythonServiceOnline,
            RecommendationsGenerated = recommendationsGenerated,
            AvgResponseTimeMs = avgResponseTimeMs
        };
    }

    

    [HttpGet("courses")]
    public async Task<ActionResult<List<CourseAdminDto>>> GetCourses()
    {
        var courses = await _context.Courses
            .Select(c => new CourseAdminDto
            {
                Id = c.Id,
                Title = c.Title,
                Platform = c.Platform,
                Topics = c.Topics,
                Difficulty = c.Difficulty
            })
            .ToListAsync();

        return courses;
    }

    

    [HttpPut("courses/{id}")]
    public async Task<IActionResult> UpdateCourse(Guid id, [FromBody] UpdateCourseRequestDto request)
    {
        var course = await _context.Courses.FindAsync(id);
        if (course == null) return NotFound("Course not found.");

        var validDifficulties = new[] { "Beginner", "Standard", "Advanced" };
        if (!validDifficulties.Contains(request.Difficulty))
            return BadRequest("Invalid difficulty value.");

        course.Difficulty = request.Difficulty;
        course.Topics = request.Topics ?? new List<string>();

        await _context.SaveChangesAsync();
        return Ok(new { message = "Course updated successfully." });
    }


    [HttpGet("activity")]
    public async Task<ActionResult<List<ActivityDataDto>>> GetActivity()
    {
        var now = DateTime.UtcNow;
        var activityData = new List<ActivityDataDto>();

        for (int i = 6; i >= 0; i--)
        {
            var date = now.Date.AddDays(-i);
            var nextDate = date.AddDays(1);

            var registrations = await _context.UserCourses
                .CountAsync(uc => uc.LastSynced >= date && uc.LastSynced < nextDate);

            var gradesReceived = await _context.UserAssignmentGrades
                .CountAsync(g => g.LastSynced >= date && g.LastSynced < nextDate);

            activityData.Add(new ActivityDataDto
            {
                Date = date.ToString("yyyy-MM-dd"),
                Registrations = registrations,
                GradesReceived = gradesReceived
            });
        }

        return activityData;
    }


    [HttpPost("sync-all-courses")]
    public async Task<ActionResult<AdminSyncResultDto>> SyncAllCoursesFromMoodle()
    {
        var moodleCourses = await _moodleService.GetAllCoursesAsync();
        if (!moodleCourses.Any()) return Ok(new AdminSyncResultDto { Success = true, Message = "В Moodle курсов не найдено." });


        var existingCourses = await _context.Courses
            .ToDictionaryAsync(c => c.ExternalId);


        var enrichedCourses = new ConcurrentBag<(MoodleCourseDto Course, List<string> Topics)>();

        var semaphore = new SemaphoreSlim(10);

        var processingTasks = moodleCourses.Select(async mCourse =>
        {
            await semaphore.WaitAsync();
            try
            {
                var contentTopics = await _moodleService.GetTopicsWithActivitiesAsync(mCourse.Id);
                enrichedCourses.Add((mCourse, contentTopics));
            }
            finally
            {
                semaphore.Release();
            }
        });

        await Task.WhenAll(processingTasks);

        int addedCount = 0;
        int updatedCount = 0;

        foreach (var item in enrichedCourses)
        {
            var mCourse = item.Course;
            var contentTopics = item.Topics;

            var tagNames = mCourse.Tags.Select(t => t.Name).ToList();
            var allTopics = tagNames.Concat(contentTopics).Distinct().ToList();

            string difficulty = "Beginner";
            if (allTopics.Any(t => t.ToLower().Contains("hard") || t.ToLower().Contains("advanced")))
                difficulty = "Advanced";

            if (existingCourses.TryGetValue(mCourse.Id.ToString(), out var dbCourse))
            {
                dbCourse.Title = mCourse.Fullname;
                dbCourse.Description = StripHtml(mCourse.Summary);
                dbCourse.Topics = allTopics;
                // dbCourse.Difficulty = difficulty; потом надо будет обновить логику 
                updatedCount++;
            }
            else
            {
                var newCourse = new Course
                {
                    Id = Guid.NewGuid(),
                    ExternalId = mCourse.Id.ToString(),
                    Title = mCourse.Fullname,
                    Description = StripHtml(mCourse.Summary),
                    Platform = "Moodle",
                    Topics = allTopics,
                    Difficulty = difficulty
                };
                _context.Courses.Add(newCourse);
                addedCount++;
            }
        }

        await _context.SaveChangesAsync();

        var message = $"Синхронизация завершена.\nДобавлено: {addedCount}\nОбновлено: {updatedCount}";
        return Ok(new AdminSyncResultDto
        {
            Success = true,
            AddedCount = addedCount,
            UpdatedCount = updatedCount,
            Message = message
        });
    }

    [HttpPost("sync-users-grades")]
    public async Task<ActionResult<AdminSyncResultDto>> SyncUsersAndGrades()
    {
        var dbCourses = await _context.Courses.ToListAsync();
        if (!dbCourses.Any()) return BadRequest("Сначала синхронизируйте курсы!");

        var dbMoodleStudents = await _context.MoodleStudents
            .ToDictionaryAsync(u => u.MoodleUserId);

        var dbUserCoursesList = await _context.UserCourses
            .Include(uc => uc.MoodleStudent)
            .Include(uc => uc.AssignmentGrades) 
            .ToListAsync();

        var dbUserCoursesMap = new Dictionary<string, UserCourse>();
        foreach (var uc in dbUserCoursesList)
        {
            if (uc.MoodleStudent != null)
            {
                string key = $"{uc.MoodleStudent.MoodleUserId}_{uc.CourseId}";
                dbUserCoursesMap[key] = uc;
            }
        }

        var fetchedUsersBag = new ConcurrentBag<MoodleUserDto>();
        var fetchedGradesBag = new ConcurrentBag<(int MoodleUserId, Guid CourseId, List<UserGradeDto> Grades)>();

        var semaphore = new SemaphoreSlim(10);

        var tasks = dbCourses.Select(async course =>
        {
            if (!int.TryParse(course.ExternalId, out int moodleCourseId)) return;

            await semaphore.WaitAsync();
            try
            {
                var moodleStudents = await _moodleService.GetEnrolledUsersAsync(moodleCourseId);

                foreach (var student in moodleStudents)
                {
                    fetchedUsersBag.Add(student);

                    var grades = await _moodleService.GetUserGradesAsync(student.Id, moodleCourseId);
                    if (grades.Any())
                    {
                        fetchedGradesBag.Add((student.Id, course.Id, grades));
                    }
                }
            }
            finally
            {
                semaphore.Release();
            }
        });

        await Task.WhenAll(tasks);

        int newUsersCount = 0;
        var uniqueFetchedUsers = fetchedUsersBag.GroupBy(u => u.Id).Select(g => g.First()).ToList();
        var studentsToAdd = new List<MoodleStudent>();
        foreach (var mUser in uniqueFetchedUsers)
        {
            if (!dbMoodleStudents.ContainsKey(mUser.Id))
            {
                var newStudent = new MoodleStudent
                {
                    MoodleUserId = mUser.Id, Username = mUser.Username, Email = mUser.Email, FullName = mUser.Fullname
                };
                studentsToAdd.Add(newStudent);
                dbMoodleStudents[mUser.Id] = newStudent;
            }
        }

        if (studentsToAdd.Any())
        {
            await _context.MoodleStudents.AddRangeAsync(studentsToAdd);
            await _context.SaveChangesAsync();
            newUsersCount = studentsToAdd.Count;
        }

        int gradesUpdatedCount = 0;
        int assignmentsUpdatedCount = 0;

        foreach (var gradeData in fetchedGradesBag)
        {
            if (dbMoodleStudents.TryGetValue(gradeData.MoodleUserId, out var studentEntity))
            {
                string key = $"{gradeData.MoodleUserId}_{gradeData.CourseId}";
                var finalGrade = gradeData.Grades.FirstOrDefault(g => g.ItemType == "course");
                var assignmentGrades = gradeData.Grades.Where(g => g.ItemType == "mod").ToList(); // Задания и тесты

                if (!dbUserCoursesMap.TryGetValue(key, out var userCourse))
                {
                    userCourse = new UserCourse
                    {
                        MoodleStudentId = studentEntity.Id,
                        CourseId = gradeData.CourseId,
                        AssignmentGrades = new List<UserAssignmentGrade>()
                    };
                    _context.UserCourses.Add(userCourse);
                    dbUserCoursesMap[key] = userCourse;
                }

                if (finalGrade != null)
                {
                    userCourse.Grade = finalGrade.RawGrade;
                    userCourse.MaxGrade = finalGrade.MaxGrade;
                }

                userCourse.LastSynced = DateTime.UtcNow;
                gradesUpdatedCount++;

                foreach (var ag in assignmentGrades)
                {
                    var existingAssign = userCourse.AssignmentGrades.FirstOrDefault(a => a.ItemName == ag.ItemName);
                    if (existingAssign != null)
                    {
                        existingAssign.Grade = ag.RawGrade;
                        existingAssign.MaxGrade = ag.MaxGrade;
                        existingAssign.LastSynced = DateTime.UtcNow;
                    }
                    else
                    {
                        userCourse.AssignmentGrades.Add(new UserAssignmentGrade
                        {
                            ItemName = ag.ItemName,
                            ItemModule = ag.ItemModule,
                            Grade = ag.RawGrade,
                            MaxGrade = ag.MaxGrade
                        });
                    }

                    assignmentsUpdatedCount++;
                }
            }
        }

        await _context.SaveChangesAsync();

        var message = $"Синхронизация завершена.\nНовых студентов: {newUsersCount}\nКурсов обновлено: {gradesUpdatedCount}\nОценок за задания сохранено: {assignmentsUpdatedCount}";
        return Ok(new AdminSyncResultDto
        {
            Success = true,
            NewStudentsCount = newUsersCount,
            UpdatedCount = gradesUpdatedCount,
            GradesUpdatedCount = gradesUpdatedCount,
            AssignmentsUpdatedCount = assignmentsUpdatedCount,
            Message = message
        });
    }

    private string StripHtml(string? input)
    {
        if (string.IsNullOrEmpty(input)) return string.Empty;
        return Regex.Replace(input, "<.*?>", String.Empty);
    }
}