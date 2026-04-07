from pydantic import BaseModel, Field
from typing import List, Optional

class MoodleGradeInput(BaseModel):
    ItemName: str
    RawGrade: Optional[float] = None
    MaxGrade: Optional[float] = None
    CourseTags: List[str] = Field(default_factory=list)

class RecommendationRequest(BaseModel):
    userId: int
    moodleGrades: List[MoodleGradeInput]

class RecommendationResultDto(BaseModel):
    CourseId: Optional[int] = None
    Title: str
    Description: str
    ResourceType: str = "article"  
    Url: Optional[str] = None
    RelevanceScore: float = Field(default=0.5, ge=0.0, le=1.0)
    Topics: List[str] = Field(default_factory=list)
    Difficulty: str = "Standard"  

class RecommendationResponseWrapper(BaseModel):
    userId: int
    recommendations: List[RecommendationResultDto]