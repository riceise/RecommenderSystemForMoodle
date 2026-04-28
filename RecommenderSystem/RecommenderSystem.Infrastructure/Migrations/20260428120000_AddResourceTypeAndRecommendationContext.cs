using System;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using RecommenderSystem.Infrastructure.Persistence;

#nullable disable

namespace RecommenderSystem.Infrastructure.Migrations
{
    [Migration("20260428120000_AddResourceTypeAndRecommendationContext")]
    [DbContext(typeof(AppDbContext))]
    public partial class AddResourceTypeAndRecommendationContext : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<Guid>(
                name: "ContextCourseId",
                table: "AiRecommendationHistory",
                type: "uuid",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ResourceType",
                table: "ExternalCourses",
                type: "text",
                nullable: false,
                defaultValue: "course");

            migrationBuilder.CreateIndex(
                name: "IX_AiRecommendationHistory_ContextCourseId_UserId_CreatedAt",
                table: "AiRecommendationHistory",
                columns: new[] { "ContextCourseId", "UserId", "CreatedAt" });
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_AiRecommendationHistory_ContextCourseId_UserId_CreatedAt",
                table: "AiRecommendationHistory");

            migrationBuilder.DropColumn(
                name: "ContextCourseId",
                table: "AiRecommendationHistory");

            migrationBuilder.DropColumn(
                name: "ResourceType",
                table: "ExternalCourses");
        }
    }
}
