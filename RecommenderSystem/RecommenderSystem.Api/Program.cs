using RecommenderSystem.Core.Interfaces;
using RecommenderSystem.Infrastructure.Services;
using RecommenderSystem.PythonBridge;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Infrastructure.Interfaces;
using RecommenderSystem.Infrastructure.Persistence;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString));


builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddHttpClient<IPythonAiService, PythonAiService>();


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
    var pythonUrl = builder.Configuration["PythonService:Url"];
    client.BaseAddress = new Uri(pythonUrl ?? "http://localhost:5001");
});

var app = builder.Build();


if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("VuePolicy"); 

app.UseAuthorization();

app.MapControllers();

app.Run();