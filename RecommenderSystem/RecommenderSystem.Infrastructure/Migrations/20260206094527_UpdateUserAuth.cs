using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace RecommenderSystem.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class UpdateUserAuth : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_AspNetUsers_MoodleUserId",
                table: "AspNetUsers");

            migrationBuilder.AddColumn<int>(
                name: "MoodleStudentId",
                table: "UserCourses",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.CreateTable(
                name: "MoodleStudents",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    MoodleUserId = table.Column<int>(type: "integer", nullable: false),
                    Username = table.Column<string>(type: "text", nullable: false),
                    Email = table.Column<string>(type: "text", nullable: false),
                    FullName = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_MoodleStudents", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_UserCourses_MoodleStudentId",
                table: "UserCourses",
                column: "MoodleStudentId");

            migrationBuilder.CreateIndex(
                name: "IX_AspNetUsers_MoodleUserId",
                table: "AspNetUsers",
                column: "MoodleUserId");

            migrationBuilder.CreateIndex(
                name: "IX_MoodleStudents_Email",
                table: "MoodleStudents",
                column: "Email");

            migrationBuilder.AddForeignKey(
                name: "FK_UserCourses_MoodleStudents_MoodleStudentId",
                table: "UserCourses",
                column: "MoodleStudentId",
                principalTable: "MoodleStudents",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_UserCourses_MoodleStudents_MoodleStudentId",
                table: "UserCourses");

            migrationBuilder.DropTable(
                name: "MoodleStudents");

            migrationBuilder.DropIndex(
                name: "IX_UserCourses_MoodleStudentId",
                table: "UserCourses");

            migrationBuilder.DropIndex(
                name: "IX_AspNetUsers_MoodleUserId",
                table: "AspNetUsers");

            migrationBuilder.DropColumn(
                name: "MoodleStudentId",
                table: "UserCourses");

            migrationBuilder.CreateIndex(
                name: "IX_AspNetUsers_MoodleUserId",
                table: "AspNetUsers",
                column: "MoodleUserId",
                unique: true);
        }
    }
}
