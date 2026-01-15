from pydantic import BaseModel
from typing import List, Optional

class MoodleGrade(BaseModel):
    ItemName: str
    ModuleType: str
    RawGrade: Optional[float] = None
    MaxGrade: Optional[float] = None
    CourseTags: List[str] = []

class RecommendationRequest(BaseModel):
    userId: int
    moodleGrades: List[MoodleGrade]