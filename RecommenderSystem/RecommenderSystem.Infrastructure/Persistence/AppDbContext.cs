using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;

namespace RecommenderSystem.Infrastructure.Persistence;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Course> Courses { get; set; }
    public DbSet<AppUser> Users { get; set; }
    public DbSet<UserCourse> UserCourses { get; set; } 

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Course>().HasIndex(c => c.ExternalId).IsUnique();
        modelBuilder.Entity<AppUser>().HasIndex(u => u.MoodleUserId).IsUnique();

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.User)
            .WithMany(u => u.UserCourses)
            .HasForeignKey(uc => uc.UserId);

        modelBuilder.Entity<UserCourse>()
            .HasOne(uc => uc.Course)
            .WithMany(c => c.UserCourses)
            .HasForeignKey(uc => uc.CourseId);
    }
}