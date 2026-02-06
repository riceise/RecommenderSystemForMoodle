using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.DTOs.Auth;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Services;
using RecommenderSystem.Infrastructure.Persistence; 

namespace RecommenderSystem.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly UserManager<AppUser> _userManager;
    private readonly TokenService _tokenService;
    private readonly AppDbContext _context; 

    public AuthController(UserManager<AppUser> userManager, TokenService tokenService, AppDbContext context)
    {
        _userManager = userManager;
        _tokenService = tokenService;
        _context = context;
    }

    [HttpPost("register")]
    public async Task<ActionResult<AuthResponseDto>> Register(RegisterDto dto)
    {
        if (await _userManager.FindByEmailAsync(dto.Email) != null)
            return BadRequest("Такой Email уже зарегистрирован");
        
        var linkedStudent = await _context.MoodleStudents
            .FirstOrDefaultAsync(m => 
                m.Email.ToLower() == dto.Email.ToLower() && 
                m.FullName.ToLower() == dto.FullName.ToLower());

        int moodleUserId = 0;
        
        if (linkedStudent != null)
        {
            moodleUserId = linkedStudent.MoodleUserId;
        }
        else 
        {
            moodleUserId = 0;
        }

        var user = new AppUser
        {
            UserName = dto.Email, 
            Email = dto.Email,
            FullName = dto.FullName,
            MoodleUserId = moodleUserId 
        };

        var result = await _userManager.CreateAsync(user, dto.Password);

        if (!result.Succeeded) return BadRequest(result.Errors);

        return new AuthResponseDto
        {
            Email = user.Email,
            Token = _tokenService.CreateToken(user),
            UserId = user.Id
        };
    }

    [HttpPost("login")]
    public async Task<ActionResult<AuthResponseDto>> Login(LoginDto dto)
    {
        var user = await _userManager.FindByEmailAsync(dto.Email);

        if (user == null) return Unauthorized("Неверный email");

        var result = await _userManager.CheckPasswordAsync(user, dto.Password);

        if (!result) return Unauthorized("Неверный пароль");

        return new AuthResponseDto
        {
            Email = user.Email,
            Token = _tokenService.CreateToken(user),
            UserId = user.Id
        };
    }
}