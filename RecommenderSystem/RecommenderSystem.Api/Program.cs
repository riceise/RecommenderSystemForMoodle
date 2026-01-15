using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Services;
using RecommenderSystem.PythonBridge;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Infrastructure.Persistence;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString));

// --- 1. Регистрация сервисов ---

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Настраиваем CORS (чтобы Vue мог слать запросы)
builder.Services.AddCors(options =>
{
    options.AddPolicy("VuePolicy", policy =>
    {
        policy.WithOrigins("http://localhost:5173") 
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

// --- 2. Регистрация сервисов (Infrastructure & PythonBridge) ---
builder.Services.AddHttpClient<IMoodleService, MoodleService>();

// Регистрируем PythonRecommenderService и HttpClient для него
builder.Services.AddHttpClient<IRecommendationService, PythonRecommenderService>(client =>
{
    var pythonUrl = builder.Configuration["PythonService:Url"];
    client.BaseAddress = new Uri(pythonUrl ?? "http://localhost:5001");
});

var app = builder.Build();

// --- 3. Pipeline ---

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("VuePolicy"); 

app.UseAuthorization();

app.MapControllers();

app.Run();