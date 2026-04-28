using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;

namespace RecommenderSystem.Infrastructure.Persistence;

public class AppDbContext : IdentityDbContext<AppUser>
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Course> Courses { get; set; }
    public DbSet<ExternalCourse> ExternalCourses { get; set; }
    public DbSet<AiRecommendationHistory> AiRecommendationHistory { get; set; }
    public DbSet<UserCourse> UserCourses { get; set; } 
    public DbSet<MoodleStudent> MoodleStudents { get; set; }
    public DbSet<UserAssignmentGrade> UserAssignmentGrades { get; set; }
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Course>().HasIndex(c => c.ExternalId).IsUnique();
        modelBuilder.Entity<ExternalCourse>().HasIndex(c => c.Url).IsUnique();
        modelBuilder.Entity<MoodleStudent>().HasIndex(m => m.Email); 
        modelBuilder.Entity<AppUser>().HasIndex(u => u.MoodleUserId);

        modelBuilder.Entity<ExternalCourse>()
            .Property(c => c.Topics)
            .HasColumnType("jsonb");

        modelBuilder.Entity<AiRecommendationHistory>()
            .HasIndex(x => new { x.SessionId, x.UserId, x.CreatedAt });

        modelBuilder.Entity<AiRecommendationHistory>()
            .HasIndex(x => new { x.ContextCourseId, x.UserId, x.CreatedAt });

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.MoodleStudent)
            .WithMany(ms => ms.UserCourses)
            .HasForeignKey(uc => uc.MoodleStudentId); 

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.Course)
            .WithMany(c => c.UserCourses)
            .HasForeignKey(uc => uc.CourseId);

        modelBuilder.Entity<AiRecommendationHistory>()
            .HasOne(x => x.InternalCourse)
            .WithMany()
            .HasForeignKey(x => x.InternalCourseId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<AiRecommendationHistory>()
            .HasOne(x => x.ExternalCourse)
            .WithMany()
            .HasForeignKey(x => x.ExternalCourseId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
