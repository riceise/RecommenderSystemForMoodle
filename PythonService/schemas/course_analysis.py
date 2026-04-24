from pydantic import BaseModel, Field
from typing import List, Optional


class GradeEntry(BaseModel):
    ItemName: str = Field(default="", alias="ItemName")
    RawGrade: Optional[float] = None
    MaxGrade: Optional[float] = None


class CourseAnalysisRequest(BaseModel):
    userId: int
    courseId: str
    courseName: str
    grades: List[GradeEntry] = Field(default_factory=list)
    courseTags: List[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    SourceKind: str = "internal"
    Title: str = ""
    Description: str = ""
    ResourceType: str = "article"
    Url: Optional[str] = None
    RelevanceScore: float = 0.5
    Difficulty: str = "Standard"


class CourseAnalysisResponse(BaseModel):
    Analysis: str = ""
    WeakTopics: List[str] = Field(default_factory=list)
    StrongTopics: List[str] = Field(default_factory=list)
    Recommendations: List[RecommendationItem] = Field(default_factory=list)
