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
            return

        self.content_model.fit(self.courses_df)
        print(f"INFO: Models trained on {len(self.courses_df)} courses from DB.")

    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:

        user_data = request.user_data or self._get_user_data_from_moodle(request.user_id)

        lightfm_recs = self._get_lightfm_recommendations(request.user_id, user_data)
        content_recs = self._get_content_recommendations(user_data)

        final_recommendations = self._hybrid_merge(lightfm_recs, content_recs)

        recommended_courses = self._get_course_details(final_recommendations)

        explanation = self.groq_service.generate_explanation(
            request.user_id,
            recommended_courses,
            user_data.get('weak_topics', [])
        )

        return RecommendationResponse(
            user_id=request.user_id,
            recommended_courses=recommended_courses,
            explanation=explanation,
            confidence_score=0.85,
            recommendation_type="hybrid"
        )
    
    def _get_user_data_from_moodle(self, user_id: str) -> Dict[str, Any]:
        return self.data_provider.get_sample_user_data(user_id)

    def _get_lightfm_recommendations(self, user_id: str, user_data: Dict) -> List[Tuple[str, float]]:
        all_course_ids = [course['id'] for course in self.data_provider.get_sample_courses()]
        return self.lightfm_model.recommend(user_id, all_course_ids)

    def _get_content_recommendations(self, user_data: Dict) -> List[Tuple[str, float]]:
        weak_topics = user_data.get('weak_topics', [])
        strong_topics = user_data.get('strong_topics', [])
        return self.content_model.recommend(strong_topics, weak_topics)

    def _hybrid_merge(self, recs1: List[Tuple[str, float]], recs2: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        scores = {}

        for course_id, score in recs1:
            scores[course_id] = scores.get(course_id, 0) + score * 0.6

        for course_id, score in recs2:
            scores[course_id] = scores.get(course_id, 0) + score * 0.4

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def _get_course_details(self, recommendations: List[Tuple[str, float]]) -> List[Course]:
        courses_data = self.data_provider.get_sample_courses()
        course_map = {course['id']: course for course in courses_data}

        recommended_courses = []
        for course_id, score in recommendations[:10]:
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
        weak_topics = []

        for grade in grades:

            raw = grade.get('RawGrade')
            max_g = grade.get('MaxGrade')
            tags = grade.get('CourseTags', [])

            is_fail = False

            if raw is None:
                continue

            if max_g and max_g > 0:
                if (raw / max_g) < 0.6:
                    is_fail = True
            elif raw < 3:
                is_fail = True

            if is_fail:

                if tags:
                    weak_topics.extend(tags)
                else:
                    name = grade.get('ItemName', '').lower()
                    if 'python' in name: weak_topics.append('python')
                    elif 'c#' in name: weak_topics.append('c#')
                    elif 'web' in name: weak_topics.append('web')

        return list(set(weak_topics))