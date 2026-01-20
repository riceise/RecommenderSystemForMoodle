using RecommenderSystem.Core.DTOs;

namespace RecommenderSystem.Core.Interfaces;

public interface IMoodleService
{
    /// <summary>
    /// Получает список оценок пользователя по конкретному курсу из Moodle.
    /// </summary>
    /// <param name="userId">ID пользователя в Moodle (mdl_user.id)</param>
    /// <param name="courseId">ID курса в Moodle (mdl_course.id)</param>
    /// <returns>Список оценок (тесты, задания)</returns>
    Task<List<UserGradeDto>> GetUserGradesAsync(int userId, int courseId);
    Task<List<string>> GetCourseTagsAsync(int courseId);
    
    // Находит ID пользователя по его логину
    Task<int?> GetUserIdByUsernameAsync(string username);
    
    // Берет все курсы 
    Task<List<MoodleCourseDto>> GetAllCoursesAsync();
    
    Task<List<MoodleUserDto>> GetEnrolledUsersAsync(int courseId);


}