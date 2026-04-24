import os
import json
import logging
from typing import List, Dict, Any, Tuple
from groq import Groq
from dotenv import load_dotenv

from schemas.course_analysis import (
    CourseAnalysisRequest,
    CourseAnalysisResponse,
    RecommendationItem,
)
from data.postgres_provider import PostgresDataProvider
from services.external_course_service import ExternalCourseService

load_dotenv()
logger = logging.getLogger(__name__)


class CourseAnalysisGroqService:

    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    WEAK_THRESHOLD = 0.6
    STRONG_THRESHOLD = 0.85

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        self.client = Groq(api_key=api_key)
        self.external_course_service = ExternalCourseService()
        self.postgres_provider = PostgresDataProvider()

    def analyze(self, request: CourseAnalysisRequest) -> CourseAnalysisResponse:
        weak_topics, strong_topics, all_topics = self._analyze_grades(request.grades, request.courseTags)

        if not request.grades:
            logger.warning("No grades provided for user %s, course %s", request.userId, request.courseId)
            return self._build_fallback_response()

        external_candidates = self._discover_external_courses(weak_topics, request.courseTags)

        try:
            prompt = self._build_prompt(
                user_id=request.userId,
                course_id=request.courseId,
                course_name=request.courseName,
                weak_topics=weak_topics,
                strong_topics=strong_topics,
                all_topics=all_topics,
                grades=request.grades,
                external_candidates=external_candidates,
            )

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content.strip()
            logger.info("Groq raw response for user %s: %s", request.userId, raw_content[:200])

            parsed = json.loads(raw_content)
            return self._normalize_response(parsed, weak_topics, strong_topics, external_candidates)

        except Exception as e:
            logger.error("[CourseAnalysisGroqService] Error for user %s: %s", request.userId, e)
            return self._build_fallback_response(external_candidates)

    def _analyze_grades(
        self,
        grades: List[Any],
        course_tags: List[str],
    ) -> Tuple[List[str], List[str], List[str]]:
        weak: list[str] = []
        strong: list[str] = []
        all_topics: set[str] = set(course_tags)

        for grade in grades:
            raw = getattr(grade, "RawGrade", None) or getattr(grade, "raw_grade", None)
            max_g = getattr(grade, "MaxGrade", None) or getattr(grade, "max_grade", None)
            item_name = getattr(grade, "ItemName", None) or getattr(grade, "item_name", "Unknown")

            if raw is None or max_g is None or max_g == 0:
                all_topics.add(item_name.lower())
                continue

            ratio = raw / max_g
            all_topics.add(item_name.lower())

            if ratio < self.WEAK_THRESHOLD:
                weak.append(item_name)
            elif ratio > self.STRONG_THRESHOLD:
                strong.append(item_name)

        if course_tags and weak:
            weak = list(set(course_tags))
        if course_tags and strong:
            strong = list(set(course_tags))

        return list(set(weak)), list(set(strong)), list(all_topics)

    def _get_system_prompt(self) -> str:
        return """Ты — AI-ассистент образовательной платформы RecommenderSystem.
Твоя задача — проанализировать успеваемость студента по КОНКРЕТНОМУ КУРСУ и дать персональные рекомендации.

КРИТИЧЕСКИЕ ТРЕБОВАНИЯ К ФОРМАТУ:
1. Ответь ТОЛЬКО валидным JSON-объектом. НИКАКОГО markdown, HTML, обратных кавычек (```) или пояснений.
2. JSON должен содержать ровно 4 ключа: "Analysis", "WeakTopics", "StrongTopics", "Recommendations".
3. "Analysis" — краткий (2-3 предложения) анализ успеваемости НА РУССКОМ ЯЗЫКЕ.
4. "WeakTopics" — массив строк: названия тем/заданий, где студент набрал < 60%.
5. "StrongTopics" — массив строк: названия тем/заданий, где студент набрал > 85%.
6. Ссылки должны быть существующими
7. "Recommendations" — массив из 3-5 объектов. Каждый объект содержит:
   - "Title" (string): название ресурса
   - "Description" (string): краткое описание НА РУССКОМ, КАК ИМЕННО это поможет
   - "ResourceType" (string): один из "article", "video", "course", "exercise"
   - "Url" (string или null): ссылка на ресурс (если есть)
   - "RelevanceScore" (number от 0.0 до 1.0): релевантность
   - "Difficulty" (string): один из "Beginner", "Standard", "Advanced"

НЕ добавляй никакого текста до или после JSON."""

    def _build_prompt(
        self,
        user_id: int,
        course_id: str,
        course_name: str,
        weak_topics: List[str],
        strong_topics: List[str],
        all_topics: List[str],
        grades: List[Any],
        external_candidates: List[Dict[str, Any]],
    ) -> str:
        grades_summary = []
        for g in grades:
            raw = getattr(g, "RawGrade", None) or getattr(g, "raw_grade", None)
            max_g = getattr(g, "MaxGrade", None) or getattr(g, "max_grade", None)
            name = getattr(g, "ItemName", None) or getattr(g, "item_name", "Unknown")
            pct = f"{(raw / max_g * 100):.0f}%" if max_g and max_g > 0 and raw is not None else "N/A"
            grades_summary.append(f"  - {name}: {pct}")

        grades_text = "\n".join(grades_summary) if grades_summary else "  (нет данных)"

        external_text = []
        for course in external_candidates[:4]:
            external_text.append(
                f"  - {course.get('Title', 'Без названия')} | {course.get('Platform', 'External')} | {course.get('Difficulty', 'Standard')} | {', '.join(course.get('Topics', [])[:5])} | {course.get('Url', '')}"
            )
        external_block = "\n".join(external_text) if external_text else "  - внешние курсы пока не найдены"

        return f"""Студент #{user_id}, курс ID: {course_id}.

ВНИМАНИЕ: Рекомендации должны СТРОГО соответствовать технологическому стеку курса (например, если курс по C# и Веб-разработке, КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ предлагать материалы по Python, Java, C++ и другим нерелевантным языкам).
📊 Оценки по заданиям:
{grades_text}

🔴 Слабые темы (оценка < 60%): {', '.join(weak_topics) or 'не выявлены'}
🟢 Сильные темы (оценка > 85%): {', '.join(strong_topics) or 'не выявлены'}
📁 Все темы курса: {', '.join(all_topics[:15]) or 'общий курс'}

🌐 Найденные внешние курсы через локальный поиск:
{external_block}

ЗАДАЧА:
1. Дай краткий анализ успеваемости (2-3 предложения на русском).
2. Обязательно используй найденные внешние курсы, если они релевантны слабым темам.
3. Подбери 3-5 конкретных рекомендаций для закрытия пробелов.
4. Если используешь внешний курс, сохрани его Url в ответе.
5. Для каждой рекомендации объясни, КАК ИМЕННО она поможет улучшить результат.
6. Рекомендации должны быть конкретными: статьи, видео, упражнения, внешние курсы."""

    def _normalize_response(
        self,
        parsed: Dict[str, Any],
        weak_topics: List[str],
        strong_topics: List[str],
        external_candidates: List[Dict[str, Any]],
    ) -> CourseAnalysisResponse:
        valid_types = {"article", "video", "course", "exercise"}
        valid_diff = {"Beginner", "Standard", "Advanced"}

        recs_raw = parsed.get("Recommendations", [])
        recommendations = []

        for item in recs_raw:
            try:
                source_kind = "external" if item.get("Url") and any(c.get("Url") == item.get("Url") for c in external_candidates) else "internal"
                rec = RecommendationItem(
                    SourceKind=source_kind,
                    Title=str(item.get("Title", "Без названия"))[:200],
                    Description=str(item.get("Description", ""))[:500],
                    ResourceType=item.get("ResourceType", "article") if item.get("ResourceType") in valid_types else "article",
                    Url=item.get("Url"),
                    RelevanceScore=max(0.0, min(1.0, float(item.get("RelevanceScore", 0.5)))),
                    Difficulty=item.get("Difficulty", "Standard") if item.get("Difficulty") in valid_diff else "Standard",
                )
                recommendations.append(rec)
            except (ValueError, TypeError) as e:
                logger.warning("Skip malformed recommendation item: %s", e)
                continue

        if not recommendations and external_candidates:
            recommendations = self._build_external_fallback_recommendations(external_candidates)

        recommendations = recommendations[:5]

        return CourseAnalysisResponse(
            Analysis=str(parsed.get("Analysis", ""))[:1000],
            WeakTopics=parsed.get("WeakTopics", weak_topics),
            StrongTopics=parsed.get("StrongTopics", strong_topics),
            Recommendations=recommendations,
        )

    def _build_fallback_response(self, external_candidates: List[Dict[str, Any]] | None = None) -> CourseAnalysisResponse:
        fallback_recommendations = [
            RecommendationItem(
                SourceKind="internal",
                Title="Повторите материалы курса",
                Description="Пересмотрите лекции и выполните практические задания. Обратитесь к преподавателю за консультацией.",
                ResourceType="article",
                Url=None,
                RelevanceScore=0.5,
                Difficulty="Standard",
            )
        ]

        if external_candidates:
            fallback_recommendations.extend(self._build_external_fallback_recommendations(external_candidates)[:2])

        return CourseAnalysisResponse(
            Analysis="Не удалось выполнить AI-анализ. Сервис временно недоступен. Попробуйте повторить запрос позже.",
            WeakTopics=[],
            StrongTopics=[],
            Recommendations=fallback_recommendations,
        )

    def _discover_external_courses(self, weak_topics: List[str], course_tags: List[str]) -> List[Dict[str, Any]]:
        search_topics = list(dict.fromkeys((weak_topics or []) + (course_tags or [])))[:5]
        if not search_topics:
            return []

        try:
            discovery_result = self.external_course_service.discover_courses(search_topics)
            logger.info(
                "External discovery finished for topics %s: saved=%s, queries=%s",
                search_topics,
                discovery_result.get("saved", 0),
                discovery_result.get("queries", []),
            )
        except Exception as ex:
            logger.warning("External discovery failed during course analysis: %s", ex)

        candidates = self.postgres_provider.get_external_courses(limit=10)
        ranked = []
        for course in candidates:
            score = self._score_external_course(course, search_topics)
            ranked.append({
                "Title": course.get("Title", ""),
                "Description": course.get("Description", ""),
                "Platform": course.get("Platform", "External"),
                "Difficulty": course.get("Difficulty", "Standard"),
                "Topics": course.get("Topics") or [],
                "Url": course.get("Url"),
                "RelevanceScore": score,
            })

        ranked.sort(key=lambda x: x.get("RelevanceScore", 0), reverse=True)
        return ranked[:4]

    def _score_external_course(self, course: Dict[str, Any], topics: List[str]) -> float:
        text = f"{course.get('Title', '')} {course.get('Description', '')} {' '.join(course.get('Topics') or [])}".lower()
        score = float(course.get("ConfidenceScore") or 0.2)
        for topic in topics:
            if topic.lower() in text:
                score += 0.25
        return min(score, 0.99)

    def _build_external_fallback_recommendations(self, external_candidates: List[Dict[str, Any]]) -> List[RecommendationItem]:
        results: List[RecommendationItem] = []
        for course in external_candidates[:3]:
            results.append(RecommendationItem(
                SourceKind="external",
                Title=str(course.get("Title", "Внешний курс"))[:200],
                Description=str(course.get("Description", "Этот внешний курс найден локальной моделью и может помочь закрыть пробелы по теме."))[:500],
                ResourceType="course",
                Url=course.get("Url"),
                RelevanceScore=max(0.0, min(1.0, float(course.get("RelevanceScore", 0.6)))),
                Difficulty=str(course.get("Difficulty", "Standard")),
            ))
        return results
