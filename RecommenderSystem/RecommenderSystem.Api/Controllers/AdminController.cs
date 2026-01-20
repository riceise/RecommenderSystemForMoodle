using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore; 
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;

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

        int addedCount = 0;
        int updatedCount = 0;

        foreach (var mCourse in moodleCourses)
        {
            var tagNames = mCourse.Tags.Select(t => t.Name).ToList();
            
            var contentTopics = await _moodleService.GetTopicsWithActivitiesAsync(mCourse.Id);
            
            var allTopics = tagNames.Concat(contentTopics).Distinct().ToList();

            var existingCourse = await _context.Courses
                .FirstOrDefaultAsync(c => c.ExternalId == mCourse.Id.ToString());

            if (existingCourse == null)
            {
                var newCourse = new Course
                {
                    Id = Guid.NewGuid(),
                    ExternalId = mCourse.Id.ToString(),
                    Title = mCourse.Fullname,
                    Description = StripHtml(mCourse.Summary),
                    Platform = "Moodle",
                    Topics = allTopics, 
                    Difficulty = "Beginner" 
                };
                
                if (allTopics.Any(t => t.ToLower().Contains("hard") || t.ToLower().Contains("advanced"))) 
                    newCourse.Difficulty = "Advanced";

                _context.Courses.Add(newCourse);
                addedCount++;
            }
            else
            {
                existingCourse.Title = mCourse.Fullname;
                existingCourse.Description = StripHtml(mCourse.Summary);
                existingCourse.Topics = allTopics;
                updatedCount++;
            }
        }

        await _context.SaveChangesAsync();
        return Ok($"Синхронизация завершена.\nДобавлено: {addedCount}\nОбновлено: {updatedCount}");
    }

    [HttpPost("sync-users-grades")]
    public async Task<IActionResult> SyncUsersAndGrades()
    {
        var courses = await _context.Courses.ToListAsync();
        if (!courses.Any()) return BadRequest("Сначала синхронизируйте курсы!");

        int newUsers = 0;
        int gradesUpdated = 0;

        foreach (var course in courses)
        {
            if (!int.TryParse(course.ExternalId, out int moodleCourseId)) continue;

            var moodleStudents = await _moodleService.GetEnrolledUsersAsync(moodleCourseId);

            foreach (var mStudent in moodleStudents)
            {
                var dbUser = await _context.Users
                    .FirstOrDefaultAsync(u => u.MoodleUserId == mStudent.Id);

                if (dbUser == null)
                {
                    dbUser = new AppUser
                    {
                        MoodleUserId = mStudent.Id,
                        Username = mStudent.Username,
                        Email = mStudent.Email,
                        FullName = mStudent.Fullname
                    };
                    _context.Users.Add(dbUser);
                    await _context.SaveChangesAsync();
                    newUsers++;
                }

                var grades = await _moodleService.GetUserGradesAsync(mStudent.Id, moodleCourseId);

                var finalGradeItem = grades.FirstOrDefault(g => g.ItemType == "course");
                
                double? finalScore = finalGradeItem?.RawGrade;
                double? maxScore = finalGradeItem?.MaxGrade;

                if (finalScore != null)
                {
                    Console.WriteLine($"User {mStudent.Username}: Grade {finalScore}/{maxScore}");
                }

                var userCourse = await _context.UserCourses
                    .FirstOrDefaultAsync(uc => uc.UserId == dbUser.Id && uc.CourseId == course.Id);

                if (userCourse == null)
                {
                    userCourse = new UserCourse
                    {
                        UserId = dbUser.Id,
                        CourseId = course.Id,
                        Grade = finalScore,
                        MaxGrade = maxScore,
                        LastSynced = DateTime.UtcNow
                    };
                    _context.UserCourses.Add(userCourse);
                }
                else
                {
                    userCourse.Grade = finalScore;
                    userCourse.MaxGrade = maxScore;
                    userCourse.LastSynced = DateTime.UtcNow;
                }
                gradesUpdated++;
            }
        }

        await _context.SaveChangesAsync();
        return Ok($"Синхронизация завершена.\nНовых пользователей: {newUsers}\nОценок обновлено: {gradesUpdated}");
    }

    private string StripHtml(string input)
    {
        if (string.IsNullOrEmpty(input)) return string.Empty;
        return System.Text.RegularExpressions.Regex.Replace(input, "<.*?>", String.Empty);
    }
}