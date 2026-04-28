import os
import json
import logging
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GroqService:
    
    MODEL="qwen/qwen3-32b" 
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        self.client = Groq(api_key=api_key)
    
    def generate_recommendations(
        self,
        user_id: int,
        weak_topics: List[str],
        strong_topics: List[str],
        course_context: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Генерирует рекомендации в формате RecommendationResultDto"""
        
        if not weak_topics and not strong_topics:
            return self._get_fallback_recommendations()
        
        prompt = self._build_prompt(user_id, weak_topics, strong_topics, course_context, max_results)
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4048,
                response_format={"type": "json_object"}  
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            recommendations = self._normalize_output(result.get("recommendations", []))
            return recommendations
            
        except Exception as e:
            logger.error(f"[GroqService] Error: {e}")
            return self._get_fallback_recommendations()

    def generate_hybrid_recommendations(
        self,
        user_id: int,
        weak_topics: List[str],
        strong_topics: List[str],
        candidate_courses: List[Dict[str, Any]],
        session_id: str,
        course_name: str = "",
    ) -> List[Dict[str, Any]]:
        if not candidate_courses:
            return self._get_fallback_recommendations()

        prompt = self._build_hybrid_prompt(user_id, session_id, weak_topics, strong_topics, candidate_courses, course_name)
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._get_hybrid_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            return self._normalize_hybrid_output(result.get("recommendations", []), candidate_courses)
        except Exception as e:
            logger.error(f"[GroqService] Hybrid generation error: {e}")
            return self._build_template_recommendations(candidate_courses, weak_topics)
    
    def _get_system_prompt(self) -> str:
        return """Ты — AI-ассистент образовательной платформы RecommenderSystem.
Отвечай ТОЛЬКО в формате строгого JSON с ключом "recommendations".
Каждый элемент должен содержать поля: Title, Description, ResourceType, Url, RelevanceScore, Topics, Difficulty.
Все описания — на русском языке. Не более 10 рекомендаций."""

    def _build_prompt(self, user_id: int, weak: List[str], strong: List[str], context: List[str], max_results: int) -> str:
        return f"""
Студент #{user_id}. Контекст курса: {', '.join(context[:10]) or 'общий курс'}.
🔴 Слабые темы (оценка < 60%): {', '.join(weak) or 'не выявлены'}
🟢 Сильные темы (оценка > 90%): {', '.join(strong) or 'не выявлены'}

ЗАДАЧА: Подбери {max_results} персональных материалов, которые:
1. Помогают закрыть пробелы в слабых темах
2. Опционально: углубляют сильные стороны
3. Соответствуют уровню студента

Для каждой рекомендации укажи, КАК ИМЕННО она поможет улучшить результат.
"""

    def _normalize_output(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """Приводит ответ Groq к формату RecommendationResultDto"""
        valid_types = {"article", "video", "course", "exercise"}
        valid_diff = {"Beginner", "Standard", "Advanced"}
        result = []
        
        for item in items:
            try:
                result.append({
                    "CourseId": item.get("CourseId"),
                    "Title": str(item.get("Title", "Без названия"))[:200],
                    "Description": str(item.get("Description", ""))[:500],
                    "ResourceType": item.get("ResourceType") if item.get("ResourceType") in valid_types else "article",
                    "Url": item.get("Url"),
                    "RelevanceScore": max(0.0, min(1.0, float(item.get("RelevanceScore", 0.5)))),
                    "Topics": [str(t).lower() for t in item.get("Topics", []) if t][:10],
                    "Difficulty": item.get("Difficulty") if item.get("Difficulty") in valid_diff else "Standard"
                })
            except Exception as e:
                logger.warning(f"Skip malformed item: {e}")
                continue
        return result

    def _get_hybrid_system_prompt(self) -> str:
        return """Ты — AI-ассистент NeuroTutor. Твоя задача — не придумывать новые курсы, а объяснять уже подобранные 4 курса.
Отвечай ТОЛЬКО JSON-объектом с ключом recommendations.
Каждый элемент recommendations должен содержать: internalCourseId, externalCourseId, sourceKind, Title, Description, ResourceType, Url, RelevanceScore, Topics, Difficulty, Reason.
Description и Reason пиши на русском языке. Нельзя добавлять курсы, которых нет во входном списке."""

    def _build_hybrid_prompt(self, user_id: int, session_id: str, weak: List[str], strong: List[str], candidate_courses: List[Dict[str, Any]], course_name: str = "") -> str:
        payload = {
            "student": {
                "userId": user_id,
                "sessionId": session_id,
                "courseName": course_name,
                "weakTopics": weak,
                "strongTopics": strong,
            },
            "recommendations": candidate_courses,
            "instructions": {
                "language": "ru",
                "rules": [
                    "use_only_input_courses",
                    "explain_match_to_weak_topics",
                    "mark_external_courses_as_supplementary_if_needed"
                ]
            }
        }
        return json.dumps(payload, ensure_ascii=False)

    def _normalize_hybrid_output(self, items: List[Dict], candidate_courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_title = {c.get("Title"): c for c in candidate_courses}
        normalized = []
        for item in items:
            title = item.get("Title")
            base = by_title.get(title)
            if not base:
                continue
            normalized.append({
                "internalCourseId": base.get("internalCourseId"),
                "externalCourseId": base.get("externalCourseId"),
                "sourceKind": base.get("sourceKind", item.get("sourceKind", "internal")),
                "Title": title,
                "Description": str(item.get("Description", base.get("Description", "")))[:500],
                "ResourceType": item.get("ResourceType", base.get("ResourceType", "course")),
                "Url": base.get("Url"),
                "RelevanceScore": max(0.0, min(1.0, float(item.get("RelevanceScore", base.get("RelevanceScore", 0.5))))),
                "Topics": base.get("Topics", []),
                "Difficulty": item.get("Difficulty", base.get("Difficulty", "Standard")),
                "Reason": str(item.get("Reason", "Рекомендация сформирована на основе слабых тем студента."))[:500],
            })
        if not normalized:
            return self._build_template_recommendations(candidate_courses, [])
        return normalized[:4]

    def _build_template_recommendations(self, candidate_courses: List[Dict[str, Any]], weak_topics: List[str]) -> List[Dict[str, Any]]:
        result = []
        for course in candidate_courses[:4]:
            topics = course.get("Topics", []) or []
            overlap = [topic for topic in weak_topics if topic.lower() in " ".join([str(t).lower() for t in topics])]
            result.append({
                "internalCourseId": course.get("internalCourseId"),
                "externalCourseId": course.get("externalCourseId"),
                "sourceKind": course.get("sourceKind", "internal"),
                "Title": course.get("Title", "Без названия"),
                "Description": f"Курс поможет проработать темы: {', '.join(overlap or topics[:3] or ['базовые навыки'])}.",
                "ResourceType": course.get("ResourceType", "course"),
                "Url": course.get("Url"),
                "RelevanceScore": course.get("RelevanceScore", 0.5),
                "Topics": topics,
                "Difficulty": course.get("Difficulty", "Standard"),
                "Reason": f"Подходит студенту, потому что связан со слабыми темами: {', '.join(overlap or weak_topics[:2] or ['общая подготовка'])}."
            })
        return result
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        return [{
            "internalCourseId": None,
            "externalCourseId": None,
            "sourceKind": "internal",
            "Title": "Персональный план обучения",
            "Description": "AI подготовит рекомендации после анализа вашей статистики. Выполните ещё несколько заданий для точных советов.",
            "ResourceType": "course",
            "Url": None,
            "RelevanceScore": 0.7,
            "Topics": ["general", "planning"],
            "Difficulty": "Standard",
            "Reason": "Недостаточно данных для персонализированной рекомендации."
        }]
