using Microsoft.AspNetCore.Mvc;
using RecommenderSystem.Core.DTOs;
using RecommenderSystem.Core.DTOs.PythonRequests;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Interfaces;
using RecommenderSystem.Infrastructure.Services; // Для IPythonAiService

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RecommendationsController : ControllerBase
{
    private readonly IMoodleService _moodleService;
    private readonly IPythonAiService _pythonService;

    public RecommendationsController(IMoodleService moodleService, IPythonAiService pythonService)
    {
        _moodleService = moodleService;
        _pythonService = pythonService;
    }

    [HttpGet("{username}")]
    public async Task<IActionResult> GetRecommendations(string username)
    {
        var userId = await _moodleService.GetUserIdByUsernameAsync(username);
        if (userId == null) return NotFound("User not found in Moodle");

       
        int courseId = 2; 

        var grades = await _moodleService.GetUserGradesAsync(userId.Value, courseId);
        
        var courseTags = await _moodleService.GetCourseTagsAsync(courseId);
        var topicTags = await _moodleService.GetTopicsWithActivitiesAsync(courseId);
        
        var allContextTags = courseTags.Concat(topicTags).Distinct().ToList();

        if (!grades.Any())
            return Ok(new List<PythonResponseDto>());

        var recommendations = await _pythonService.GetRecommendationsAsync(userId.Value, grades, allContextTags);

        return Ok(recommendations);
    }
}