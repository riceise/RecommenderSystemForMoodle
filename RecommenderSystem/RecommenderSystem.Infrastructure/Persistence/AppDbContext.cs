using Microsoft.EntityFrameworkCore;
using RecommenderSystem.Core.Entities;

namespace RecommenderSystem.Infrastructure.Persistence;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Course> Courses { get; set; }
    public DbSet<AppUser> Users { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        modelBuilder.Entity<Course>().HasIndex(c => c.ExternalId).IsUnique();
        modelBuilder.Entity<AppUser>().HasIndex(u => u.MoodleUserId).IsUnique();
    }
}