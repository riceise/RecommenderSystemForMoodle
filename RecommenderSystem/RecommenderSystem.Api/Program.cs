using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Identity;
using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Services;
using RecommenderSystem.PythonBridge;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using RecommenderSystem.Core.Entities;
using RecommenderSystem.Core.Services;
using RecommenderSystem.Infrastructure.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString));

builder.Services.AddIdentity<AppUser, IdentityRole>(options =>
    {
        options.Password.RequireDigit = false;
        options.Password.RequireLowercase = false;
        options.Password.RequireUppercase = false;
        options.Password.RequireNonAlphanumeric = false;
        options.Password.RequiredLength = 4; // Для тестов можно попроще
        options.User.RequireUniqueEmail = true;
    })
    .AddEntityFrameworkStores<AppDbContext>()
    .AddDefaultTokenProviders();

builder.Services.AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
    })
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["JwtSettings:Issuer"],
            ValidAudience = builder.Configuration["JwtSettings:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["JwtSettings:Key"]))
        };
    });

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    // 1. Определяем схему безопасности (JWT)
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        In = ParameterLocation.Header,
        Description = "Введите токен в формате: Bearer {ваш_токен}",
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        BearerFormat = "JWT",
        Scheme = "Bearer"
    });

    // 2. Применяем эту схему ко всем запросам
    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            new string[] {}
        }
    });
});

// Python AI service — HTTP client с таймаутом для долгих Groq-запросов
builder.Services.AddHttpClient<IPythonAiService, PythonAiService>(client =>
{
    var pythonUrl = builder.Configuration["PythonService:Url"] ?? "http://localhost:5001";
    client.BaseAddress = new Uri(pythonUrl);
    client.Timeout = TimeSpan.FromSeconds(120); // Groq может отвечать долго
});

builder.Services.AddScoped<TokenService>();
builder.Services.AddScoped<ICourseAnalysisService, CourseAnalysisService>();


builder.Services.AddCors(options =>
{
    options.AddPolicy("VuePolicy", policy =>
    {
        policy.WithOrigins("http://localhost:5173") 
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

builder.Services.AddHttpClient<IMoodleService, MoodleService>();

builder.Services.AddHttpClient<IRecommendationService, PythonRecommenderService>(client =>
{
    var pythonUrl = builder.Configuration["PythonService:Url"] ?? "http://localhost:5001";
    client.BaseAddress = new Uri(pythonUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
});
// NOTE: Removed duplicate AddScoped<IRecommendationService> — AddHttpClient already registers it.

var app = builder.Build();


if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("VuePolicy"); 

app.UseAuthentication(); 
app.UseAuthorization();

app.MapControllers();

app.Run();