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
        self._cache = {}  
    
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
        
        cache_key = f"{user_id}:{sorted(weak_topics)}:{sorted(strong_topics)}"
        if cache_key in self._cache:
            logger.info(f"Cache hit for user {user_id}")
            return self._cache[cache_key]
        
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
            
            self._cache[cache_key] = recommendations
            return recommendations
            
        except Exception as e:
            logger.error(f"[GroqService] Error: {e}")
            return self._get_fallback_recommendations()
    
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
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        return [{
            "Title": "Персональный план обучения",
            "Description": "AI подготовит рекомендации после анализа вашей статистики. Выполните ещё несколько заданий для точных советов.",
            "ResourceType": "course",
            "Url": None,
            "RelevanceScore": 0.7,
            "Topics": ["general", "planning"],
            "Difficulty": "Standard"
        }]