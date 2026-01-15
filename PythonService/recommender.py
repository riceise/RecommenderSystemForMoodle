from typing import List, Dict, Any
from models.lightfm_model import LightFMRecommender
from models.content_based import ContentBasedRecommender
from services.groq_service import GroqService
from schemas.models import RecommendationRequest, RecommendationResponse, Course
from data.sample_data import SampleDataProvider
from services.moodle_service import MoodleService
from data.postgres_provider import PostgresDataProvider 


class Recommender:
    def __init__(self):
        self.lightfm_model = LightFMRecommender()
        self.content_model = ContentBasedRecommender()
        self.groq_service = GroqService()
        self.data_provider = SampleDataProvider()
        self.moodle_service = MoodleService()
        self.data_provider = PostgresDataProvider() 
        self._initialize_data()
        
    def _initialize_data(self):
        print("Loading data from PostgreSQL...")
        self.courses_df = self.data_provider.get_courses_df()
        
        if self.courses_df.empty:
            print("WARNING: Database is empty! Using fallback/sample data logic if needed.")
            # Тут можно вернуть старый SampleData как запасной вариант
            return

        self.content_model.fit(self.courses_df)
        print(f"INFO: Models trained on {len(self.courses_df)} courses from DB.")
        
    def _initialize_with_sample_data(self):
        """Инициализация с примерными данными для тестирования"""
        # Загружаем примерные данные
        courses = self.data_provider.get_sample_courses()
        interactions = self.data_provider.get_sample_interactions()
        user_features = self.data_provider.get_sample_user_features()
        item_features = self.data_provider.get_sample_item_features()
        
        # Обучаем LightFM модель
        self.lightfm_model.prepare_dataset(interactions, user_features, item_features)
        self.lightfm_model.train(epochs=10)
        
        # Обучаем Content-based модель
        self.content_model.fit(courses)
    
    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Основной метод получения рекомендаций"""
        
        # Получаем данные пользователя
        user_data = request.user_data or self._get_user_data_from_moodle(request.user_id)
        
        # Получаем рекомендации от разных моделей
        lightfm_recs = self._get_lightfm_recommendations(request.user_id, user_data)
        content_recs = self._get_content_recommendations(user_data)
        
        # Объединяем рекомендации (гибридный подход)
        final_recommendations = self._hybrid_merge(lightfm_recs, content_recs)
        
        # Получаем курсы для рекомендаций
        recommended_courses = self._get_course_details(final_recommendations)
        
        # Генерируем объяснение с помощью Groq
        explanation = self.groq_service.generate_explanation(
            request.user_id, 
            recommended_courses,
            user_data.get('weak_topics', [])
        )
        
        return RecommendationResponse(
            user_id=request.user_id,
            recommended_courses=recommended_courses,
            explanation=explanation,
            confidence_score=0.85,  # Можно вычислять на основе моделей
            recommendation_type="hybrid"
        )
    
    def _get_user_data_from_moodle(self, user_id: str) -> Dict[str, Any]:
        """Получение данных пользователя из Moodle"""
        # Заглушка - в реальности будет интеграция с Moodle API
        return self.data_provider.get_sample_user_data(user_id)
    
    def _get_lightfm_recommendations(self, user_id: str, user_data: Dict) -> List[Tuple[str, float]]:
        """Рекомендации от LightFM модели"""
        all_course_ids = [course['id'] for course in self.data_provider.get_sample_courses()]
        return self.lightfm_model.recommend(user_id, all_course_ids)
    
    def _get_content_recommendations(self, user_data: Dict) -> List[Tuple[str, float]]:
        """Рекомендации от Content-based модели"""
        weak_topics = user_data.get('weak_topics', [])
        strong_topics = user_data.get('strong_topics', [])
        return self.content_model.recommend(strong_topics, weak_topics)
    
    def _hybrid_merge(self, recs1: List[Tuple[str, float]], recs2: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Объединение рекомендаций от разных моделей"""
        # Простая стратегия: усреднение оценок
        scores = {}
        
        for course_id, score in recs1:
            scores[course_id] = scores.get(course_id, 0) + score * 0.6  # Вес для LightFM
        
        for course_id, score in recs2:
            scores[course_id] = scores.get(course_id, 0) + score * 0.4  # Вес для Content-based
        
        # Сортируем по итоговой оценке
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    def _get_course_details(self, recommendations: List[Tuple[str, float]]) -> List[Course]:
        """Получение детальной информации о рекомендованных курсах"""
        courses_data = self.data_provider.get_sample_courses()
        course_map = {course['id']: course for course in courses_data}
        
        recommended_courses = []
        for course_id, score in recommendations[:10]:  # Топ-10 рекомендаций
            if course_id in course_map:
                course_data = course_map[course_id]
                recommended_courses.append(Course(
                    id=course_data['id'],
                    title=course_data['title'],
                    description=course_data['description'],
                    platform=course_data['platform'],
                    topics=course_data['topics'],
                    difficulty=course_data['difficulty']
                ))
        
        return recommended_courses

    def _extract_weak_topics(self, grades: List[Dict]) -> List[str]:
        """
        Превращает плохие оценки в список тем, используя теги от Moodle.
        """
        weak_topics = []

        for grade in grades:

            raw = grade.get('RawGrade')
            max_g = grade.get('MaxGrade')
            tags = grade.get('CourseTags', []) 

            is_fail = False

            if raw is None:
                continue

            if max_g and max_g > 0:
                if (raw / max_g) < 0.6: # Порог 60%
                    is_fail = True
            elif raw < 3: # Если 5-балльная шкала
                is_fail = True

            if is_fail:
                
                if tags:
                    weak_topics.extend(tags)
                else:
                    name = grade.get('ItemName', '').lower()
                    if 'python' in name: weak_topics.append('python')
                    elif 'c#' in name: weak_topics.append('c#')
                    elif 'web' in name: weak_topics.append('web')

        return list(set(weak_topics)) # Убираем дубликаты