using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace RecommenderSystem.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddExternalCoursesAndAiRecommendationHistory : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "ExternalCourses",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: false),
                    Platform = table.Column<string>(type: "text", nullable: false),
                    Url = table.Column<string>(type: "text", nullable: false),
                    Difficulty = table.Column<string>(type: "text", nullable: false),
                    Topics = table.Column<List<string>>(type: "jsonb", nullable: false),
                    Language = table.Column<string>(type: "text", nullable: false),
                    ProviderCourseId = table.Column<string>(type: "text", nullable: true),
                    SearchQuery = table.Column<string>(type: "text", nullable: false),
                    DiscoveryMethod = table.Column<string>(type: "text", nullable: false),
                    ConfidenceScore = table.Column<double>(type: "double precision", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    LastParsedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    MetadataJson = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ExternalCourses", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AiRecommendationHistory",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    SessionId = table.Column<string>(type: "text", nullable: false),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    SourceKind = table.Column<string>(type: "text", nullable: false),
                    InternalCourseId = table.Column<Guid>(type: "uuid", nullable: true),
                    ExternalCourseId = table.Column<Guid>(type: "uuid", nullable: true),
                    TitleSnapshot = table.Column<string>(type: "text", nullable: false),
                    Reason = table.Column<string>(type: "text", nullable: false),
                    RelevanceScore = table.Column<double>(type: "double precision", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AiRecommendationHistory", x => x.Id);
                    table.ForeignKey(
                        name: "FK_AiRecommendationHistory_Courses_InternalCourseId",
                        column: x => x.InternalCourseId,
                        principalTable: "Courses",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_AiRecommendationHistory_ExternalCourses_ExternalCourseId",
                        column: x => x.ExternalCourseId,
                        principalTable: "ExternalCourses",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                });

            migrationBuilder.CreateIndex(
                name: "IX_AiRecommendationHistory_ExternalCourseId",
                table: "AiRecommendationHistory",
                column: "ExternalCourseId");

            migrationBuilder.CreateIndex(
                name: "IX_AiRecommendationHistory_InternalCourseId",
                table: "AiRecommendationHistory",
                column: "InternalCourseId");

            migrationBuilder.CreateIndex(
                name: "IX_AiRecommendationHistory_SessionId_UserId_CreatedAt",
                table: "AiRecommendationHistory",
                columns: new[] { "SessionId", "UserId", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_ExternalCourses_Url",
                table: "ExternalCourses",
                column: "Url",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "AiRecommendationHistory");

            migrationBuilder.DropTable(
                name: "ExternalCourses");
        }
    }
}
