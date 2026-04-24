from pydantic import BaseModel, Field
from typing import List, Optional

class MoodleGradeInput(BaseModel):
    ItemName: str
    RawGrade: Optional[float] = None
    MaxGrade: Optional[float] = None
    CourseTags: List[str] = Field(default_factory=list)

class RecommendationRequest(BaseModel):
    userId: int
    sessionId: str = ""
    contextTags: List[str] = Field(default_factory=list)
    moodleGrades: List[MoodleGradeInput]

class RecommendationResultDto(BaseModel):
    internalCourseId: Optional[str] = None
    externalCourseId: Optional[str] = None
    sourceKind: str = "internal"
    Title: str
    Description: str
    ResourceType: str = "article"  
    Url: Optional[str] = None
    RelevanceScore: float = Field(default=0.5, ge=0.0, le=1.0)
    Topics: List[str] = Field(default_factory=list)
    Difficulty: str = "Standard"  
    Reason: str = ""

class RecommendationResponseWrapper(BaseModel):
    userId: int
    recommendations: List[RecommendationResultDto]


class ChatRequest(BaseModel):
    userId: int
    sessionId: str = ""
    message: str
    context: str = "course"
    courseName: str = ""
    weakTopics: List[str] = Field(default_factory=list)
    strongTopics: List[str] = Field(default_factory=list)
    recentGradesSummary: str = ""