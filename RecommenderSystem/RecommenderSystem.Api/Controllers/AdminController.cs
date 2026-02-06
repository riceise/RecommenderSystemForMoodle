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

        var dbMoodleStudents = await _context.MoodleStudents
            .ToDictionaryAsync(u => u.MoodleUserId);

        var dbUserCoursesList = await _context.UserCourses
            .Include(uc => uc.MoodleStudent)
            .ToListAsync();

        var dbUserCoursesMap = new Dictionary<string, UserCourse>();
        foreach (var uc in dbUserCoursesList)
        {
            if (uc.MoodleStudent != null)
            {
                string key = $"{uc.MoodleStudent.MoodleUserId}_{uc.CourseId}";
                if (!dbUserCoursesMap.ContainsKey(key))
                    dbUserCoursesMap[key] = uc;
            }
        }

        var fetchedUsersBag = new ConcurrentBag<MoodleUserDto>();

        var fetchedGradesBag = new ConcurrentBag<(int MoodleUserId, Guid CourseId, double? Grade, double? Max)>();

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

        var studentsToAdd = new List<MoodleStudent>();
        foreach (var mUser in uniqueFetchedUsers)
        {
            if (!dbMoodleStudents.ContainsKey(mUser.Id))
            {
                var newStudent = new MoodleStudent
                {
                    MoodleUserId = mUser.Id,
                    Username = mUser.Username,
                    Email = mUser.Email,
                    FullName = mUser.Fullname
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

        foreach (var gradeData in fetchedGradesBag)
        {
            if (dbMoodleStudents.TryGetValue(gradeData.MoodleUserId, out var studentEntity))
            {
                string key = $"{gradeData.MoodleUserId}_{gradeData.CourseId}";

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
                        MoodleStudentId = studentEntity.Id,
                        CourseId = gradeData.CourseId,
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

        return Ok(
            $"Синхронизация завершена.\nНовых студентов в базе: {newUsersCount}\nОценок обработано: {gradesUpdatedCount}");
    }

    private string StripHtml(string? input)
    {
        if (string.IsNullOrEmpty(input)) return string.Empty;
        return Regex.Replace(input, "<.*?>", String.Empty);
    }
}