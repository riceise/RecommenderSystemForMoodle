import os
import json
import logging
import re
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

    def _extract_json_from_markdown(self, text: str) -> dict:
        text = text.strip()

        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text_to_parse = match.group(1).strip()
        else:
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                text_to_parse = text[start_idx:end_idx + 1]
            else:
                text_to_parse = text

        try:
            return json.loads(text_to_parse)
        except json.JSONDecodeError as e:
            logger.error(f"Не удалось распарсить JSON. Ошибка: {e}. Сырой текст ИИ:\n{text}")
            return {"recommendations": []}

    def generate_recommendations(
            self,
            user_id: int,
            weak_topics: List[str],
            strong_topics: List[str],
            course_context: List[str],
            max_results: int = 10
    ) -> List[Dict[str, Any]]:

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
                max_tokens=4048
            )

            raw_content = response.choices[0].message.content.strip()

            clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

            result = self._extract_json_from_markdown(clean_content)
            recommendations = self._normalize_output(result.get("recommendations", []))

            if not recommendations:
                return self._get_fallback_recommendations()

            self._cache[cache_key] = recommendations
            return recommendations

        except Exception as e:
            logger.error(f"[GroqService.recommendations] Error: {e}")
            return self._get_fallback_recommendations()

    def _get_system_prompt(self) -> str:
        return """Ты — AI-ассистент образовательной платформы RecommenderSystem.
Отвечай ТОЛЬКО в формате строгого JSON. Твой ответ должен быть валидным JSON объектом.
Формат:
{
  "recommendations": [
    {
      "Title": "Название материала",
      "Description": "Описание того, почему это поможет на русском языке",
      "ResourceType": "article",
      "Url": "https://example.com",
      "RelevanceScore": 0.95,
      "Topics": ["тема"],
      "Difficulty": "Standard"
    }
  ]
}
Допустимые ResourceType: "article", "video", "course", "exercise"."""

    def _build_prompt(self, user_id: int, weak: List[str], strong: List[str], context: List[str], max_results: int) -> str:
        context_str = ', '.join(context[:15]) if context else 'C#, .NET, Веб-разработка'

        return f"""
Студент #{user_id}. 
Контекст обучения (Названия курсов и технологии): {context_str}.

🔴 Слабые темы (оценка < 60%): {', '.join(weak) or 'не выявлены'}
🟢 Сильные темы (оценка > 90%): {', '.join(strong) or 'не выявлены'}

ЗАДАЧА: Подбери {max_results} персональных обучающих материалов для слабых тем.

ВАЖНЫЕ ПРАВИЛА:
1. СТРОГО соблюдай технологический стек из контекста! Если в контексте указан C#, предлагай материалы ТОЛЬКО по C# и .NET. Никакой Java, Python или C++!
2. Ищи реальные статьи (Хабр, Metanit, Microsoft Learn) и курсы (Stepik, YouTube).
3. Верни результат строго в JSON формате.
"""

    def _normalize_output(self, items: List[Dict]) -> List[Dict[str, Any]]:
        valid_types = {"article", "video", "course", "exercise"}
        valid_diff = {"Beginner", "Standard", "Advanced"}
        result = []

        for item in items:
            try:
                r_type = str(item.get("ResourceType", "")).lower()
                diff = str(item.get("Difficulty", "")).capitalize()

                result.append({
                    "CourseId": item.get("CourseId"),
                    "Title": str(item.get("Title", "Без названия"))[:200],
                    "Description": str(item.get("Description", ""))[:500],
                    "ResourceType": r_type if r_type in valid_types else "article",
                    "Url": item.get("Url") or "https://moodle.org",
                    "RelevanceScore": max(0.0, min(1.0, float(item.get("RelevanceScore", 0.8)))),
                    "Topics": [str(t).lower() for t in item.get("Topics", []) if t][:10],
                    "Difficulty": diff if diff in valid_diff else "Standard"
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
            "Url": "https://moodle.org",
            "RelevanceScore": 0.7,
            "Topics": ["general"],
            "Difficulty": "Standard"
        }]