using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;
using System.Collections.Concurrent;
using System.Text.RegularExpressions;
using RecommenderSystem.Core.DTOs;

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AdminController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IMoodleService _moodleService;

    public AdminController(AppDbContext context, IMoodleService moodleService)
    {
        _context = context;
        _moodleService = moodleService;
    }

    [HttpPost("sync-all-courses")]
    public async Task<IActionResult> SyncAllCoursesFromMoodle()
    {
        var moodleCourses = await _moodleService.GetAllCoursesAsync();
        if (!moodleCourses.Any()) return Ok("В Moodle курсов не найдено.");

       
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

        return Ok($"Синхронизация завершена.\nДобавлено: {addedCount}\nОбновлено: {updatedCount}");
    }

    [HttpPost("sync-users-grades")]
    public async Task<IActionResult> SyncUsersAndGrades()
    {
        var dbCourses = await _context.Courses.ToListAsync();
        if (!dbCourses.Any()) return BadRequest("Сначала синхронизируйте курсы!");

        var dbUsers = await _context.Users.ToDictionaryAsync(u => u.MoodleUserId);

        var dbUserCoursesList = await _context.UserCourses
            .Include(uc => uc.User)
            .ToListAsync();
            
        var dbUserCoursesMap = new Dictionary<string, UserCourse>();
        foreach(var uc in dbUserCoursesList)
        {
            if (uc.User != null)
            {
                string key = $"{uc.User.MoodleUserId}_{uc.CourseId}";
                if(!dbUserCoursesMap.ContainsKey(key))
                    dbUserCoursesMap[key] = uc;
            }
        }

        var fetchedUsersBag = new ConcurrentBag<MoodleUserDto>();
        var fetchedGradesBag = new ConcurrentBag<(int MoodleUserId, Guid CourseGuid, double? Grade, double? Max)>();

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
                    var finalGrade = grades.FirstOrDefault(g => g.ItemType == "course");

                    if (finalGrade != null)
                    {
                        fetchedGradesBag.Add((student.Id, course.Id, finalGrade.RawGrade, finalGrade.MaxGrade));
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
        
        var uniqueFetchedUsers = fetchedUsersBag
            .GroupBy(u => u.Id)
            .Select(g => g.First())
            .ToList();

        var usersToAdd = new List<AppUser>();

        foreach (var mUser in uniqueFetchedUsers)
        {
            if (!dbUsers.ContainsKey(mUser.Id))
            {
                var newUser = new AppUser
                {
                    MoodleUserId = mUser.Id,
                    Username = mUser.Username,
                    Email = mUser.Email,
                    FullName = mUser.Fullname
                };
                usersToAdd.Add(newUser);
                dbUsers[mUser.Id] = newUser; 
            }
        }

        if (usersToAdd.Any())
        {
            await _context.Users.AddRangeAsync(usersToAdd);
            await _context.SaveChangesAsync(); 
            newUsersCount = usersToAdd.Count;
        }

        int gradesUpdatedCount = 0;

        foreach (var gradeData in fetchedGradesBag)
        {
            if (dbUsers.TryGetValue(gradeData.MoodleUserId, out var userEntity))
            {
                string key = $"{gradeData.MoodleUserId}_{gradeData.CourseGuid}";

                if (dbUserCoursesMap.TryGetValue(key, out var existingUserCourse))
                {
                    existingUserCourse.Grade = gradeData.Grade;
                    existingUserCourse.MaxGrade = gradeData.Max;
                    existingUserCourse.LastSynced = DateTime.UtcNow;
                }
                else
                {
                    var newUserCourse = new UserCourse
                    {
                        UserId = userEntity.Id,
                        CourseId = gradeData.CourseGuid,
                        Grade = gradeData.Grade,
                        MaxGrade = gradeData.Max,
                        LastSynced = DateTime.UtcNow
                    };
                    _context.UserCourses.Add(newUserCourse);
                }
                gradesUpdatedCount++;
            }
        }

        await _context.SaveChangesAsync();

        return Ok($"Синхронизация завершена.\nНовых пользователей: {newUsersCount}\nОценок обработано: {gradesUpdatedCount}");
    }

    private string StripHtml(string? input)
    {
        if (string.IsNullOrEmpty(input)) return string.Empty;
        return Regex.Replace(input, "<.*?>", String.Empty);
    }
}