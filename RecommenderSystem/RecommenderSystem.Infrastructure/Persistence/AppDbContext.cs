using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;

namespace RecommenderSystem.Infrastructure.Persistence;

public class AppDbContext : IdentityDbContext<AppUser>
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Course> Courses { get; set; }
    public DbSet<UserCourse> UserCourses { get; set; } 
    public DbSet<MoodleStudent> MoodleStudents { get; set; }
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Course>().HasIndex(c => c.ExternalId).IsUnique();
        modelBuilder.Entity<MoodleStudent>().HasIndex(m => m.Email); 
        modelBuilder.Entity<AppUser>().HasIndex(u => u.MoodleUserId);

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.MoodleStudent)
            .WithMany(ms => ms.UserCourses)
            .HasForeignKey(uc => uc.MoodleStudentId); 

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.Course)
            .WithMany(c => c.UserCourses)
            .HasForeignKey(uc => uc.CourseId);
    }
}