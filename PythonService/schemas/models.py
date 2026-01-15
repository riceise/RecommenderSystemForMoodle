from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Course(BaseModel):
    id: str
    title: str
    description: str
    platform: str  # 'moodle', 'coursera', 'edx'
    topics: List[str]
    difficulty: str  # 'beginner', 'intermediate', 'advanced'

class UserProgress(BaseModel):
    user_id: str
    completed_courses: List[str]
    course_grades: Dict[str, float]  # course_id -> grade
    weak_topics: List[str]
    strong_topics: List[str]

class RecommendationRequest(BaseModel):
    user_id: str
    user_data: Optional[Dict[str, Any]] = None  # Если данные уже есть

class RecommendationResponse(BaseModel):
    user_id: str
    recommended_courses: List[Course]
    explanation: str
    confidence_score: float
    recommendation_type: str  # 'content_based', 'collaborative', 'hybrid'