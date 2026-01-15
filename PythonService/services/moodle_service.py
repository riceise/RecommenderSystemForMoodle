import requests
from typing import List, Dict, Any
from config import config

class MoodleService:
    def __init__(self):
        # Формируем полный URL к API. 
        # Если в конфиге http://localhost/moodle/, то добавляем путь к скрипту
        base_url = config.MOODLE_API_URL.rstrip('/')
        self.api_endpoint = f"{base_url}/webservice/rest/server.php"
        self.token = config.MOODLE_API_TOKEN

    def get_user_grades(self, user_id: int, course_id: int = None) -> List[Dict[str, Any]]:
        """
        Получает оценки пользователя.
        Использует функцию Moodle API: gradereport_user_get_grade_items
        """
        params = {
            'wstoken': self.token,
            'wsfunction': 'gradereport_user_get_grade_items',
            'moodlewsrestformat': 'json',
            'userid': user_id
        }
        
        if course_id:
            params['courseid'] = course_id

        try:
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if 'exception' in data:
                print(f"ERROR Moodle API: {data['message']}")
                return []

            # Moodle возвращает { "usergrades": [ ... ] }
            # Нам нужен список gradeitems из первого элемента
            if 'usergrades' in data and len(data['usergrades']) > 0:
                return data['usergrades'][0].get('gradeitems', [])
            
            return []

        except Exception as e:
            print(f"Connection error to Moodle: {e}")
            return []

    def analyze_student_performance(self, user_id: int) -> Dict[str, Any]:
        """
        Анализирует оценки и возвращает профиль студента:
        - Слабые темы (где оценка < 60%)
        - Сильные темы
        """
        # Получаем оценки по всем курсам (или можно передать конкретный course_id)
        # В данном примере берем все доступные оценки юзера
        raw_grades = self.get_user_grades(user_id)
        
        weak_topics = []
        strong_topics = []
        course_grades = {}

        for item in raw_grades:
            # Нас интересуют только модули (тесты, задания), а не "Всего за курс"
            if item['itemtype'] != 'mod':
                continue

            name = item['itemname'] # Название теста, например "Тест по Python Cycles"
            grade = item['graderaw'] # Оценка (число)
            max_grade = item['grademax'] # Максимум (обычно 10.0 или 100.0)

            if grade is None:
                continue # Студент еще не проходил

            # Считаем процент успешности
            percentage = (grade / max_grade) * 100 if max_grade > 0 else 0

            # Простая логика определения темы по названию теста
            # В идеале здесь нужен NLP или маппинг ID_теста -> Тема
            topic = self._extract_topic_from_name(name)

            if percentage < 60:
                if topic: weak_topics.append(topic)
            elif percentage > 85:
                if topic: strong_topics.append(topic)

            # Сохраняем оценку
            course_grades[name] = percentage

        return {
            "user_id": str(user_id),
            "course_grades": course_grades,
            "weak_topics": list(set(weak_topics)),   # Удаляем дубликаты
            "strong_topics": list(set(strong_topics))
        }

    def _extract_topic_from_name(self, name: str) -> str:
        """Пытается угадать тему из названия теста"""
        name_lower = name.lower()
        if 'python' in name_lower: return 'Python'
        if 'web' in name_lower or 'html' in name_lower: return 'Web Development'
        if 'sql' in name_lower or 'баз' in name_lower: return 'Databases'
        if 'c#' in name_lower: return 'C#'
        if 'algorithm' in name_lower: return 'Algorithms'
        return name # Если не угадали, возвращаем название как есть