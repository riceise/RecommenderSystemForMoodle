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

    // Заполенениие базы курсами
    [HttpPost("sync-all-courses")]
    public async Task<IActionResult> SyncAllCoursesFromMoodle()
    {
        var moodleCourses = await _moodleService.GetAllCoursesAsync();

        if (!moodleCourses.Any())
        {
            return Ok("В Moodle курсов не найдено.");
        }

        int addedCount = 0;
        int updatedCount = 0;

        foreach (var mCourse in moodleCourses)
        {

            var tagNames = await _moodleService.GetCourseTagsAsync(mCourse.Id);
            
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
                    Topics = tagNames, 
                    Difficulty = "Beginner" 
                };
                
                if (tagNames.Contains("hard") || tagNames.Contains("advanced")) 
                    newCourse.Difficulty = "Advanced";

                _context.Courses.Add(newCourse);
                addedCount++;
            }
            else
            {
                existingCourse.Title = mCourse.Fullname;
                existingCourse.Topics = tagNames; 
                
                updatedCount++;
            }
        }

        await _context.SaveChangesAsync();

        return Ok($"Синхронизация завершена.\nДобавлено: {addedCount}\nОбновлено: {updatedCount}\nВсего в Moodle: {moodleCourses.Count}");
    }

    private string StripHtml(string input)
    {
        if (string.IsNullOrEmpty(input)) return string.Empty;
        return System.Text.RegularExpressions.Regex.Replace(input, "<.*?>", String.Empty);
    }
}