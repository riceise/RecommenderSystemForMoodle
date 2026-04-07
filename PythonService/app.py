import os
import logging
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from schemas.python_bridge import RecommendationRequest, RecommendationResponseWrapper
from schemas.course_analysis import CourseAnalysisRequest, CourseAnalysisResponse
from services.groq_service import GroqService
from services.course_analysis_service import CourseAnalysisGroqService

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
groq_service = GroqService()
course_analysis_service = CourseAnalysisGroqService()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "recommender-python-bridge"})

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        logger.info(f"Processing request for user {user_id}")

        weak_topics, strong_topics = [], []
        all_tags = set(context_tags)

        for g in grades_list:
            raw = g.get("rawGrade") if "rawGrade" in g else g.get("RawGrade")
            max_g = g.get("maxGrade") if "maxGrade" in g else g.get("MaxGrade")
            item_name = g.get("itemName") or g.get("ItemName", "unknown")

            if raw is not None and max_g and float(max_g) > 0:
                ratio = float(raw) / float(max_g)
                if ratio < 0.6:
                    weak_topics.append(item_name)
                elif ratio > 0.85:
                    strong_topics.append(item_name)

        recommendations = groq_service.generate_recommendations(
            user_id=user_id,
            weak_topics=list(set(weak_topics)),
            strong_topics=list(set(strong_topics)),
            course_context=list(all_tags),
            max_results=10
        )

        return jsonify({
            "userId": user_id,
            "recommendations": recommendations
        }), 200

    except Exception as e:
        logger.exception("Internal error in /recommend")
        return jsonify({
            "userId": request.json.get("userId", 0) if request.json else 0,
            "recommendations": groq_service._get_fallback_recommendations()
        }), 200


@app.route('/analyze-course', methods=['POST'])
def analyze_course():
    try:
        req = CourseAnalysisRequest(**request.json)
        logger.info(f"Analyzing course for user {req.userId}, course {req.courseId}")
        response = course_analysis_service.analyze(req)
        return jsonify(response.model_dump()), 200

    except ValueError as e:
        logger.error(f"[analyze-course] Validation error: {e}")
        return jsonify({"error": "Invalid request format", "details": str(e)}), 400
    except Exception as e:
        logger.exception("[analyze-course] Internal error")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        logger.info(f"Chat request from user {data.get('userId')}, message: {data.get('message', '')[:80]}")

        message = data.get("message", "")
        weak_topics = data.get("weakTopics", [])
        strong_topics = data.get("strongTopics", [])
        course_name = data.get("courseName", "")
        grades_summary = data.get("recentGradesSummary", "")

        if not message:
            return jsonify({"error": "message is required"}), 400

        prompt = _build_chat_prompt(message, course_name, weak_topics, strong_topics, grades_summary)

        response = groq_service.client.chat.completions.create(
            model=groq_service.MODEL,
            messages=[
                {"role": "system", "content": _get_chat_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1024,
        )

        raw_reply = response.choices[0].message.content.strip()

        clean_reply = re.sub(r'<think>.*?</think>', '', raw_reply, flags=re.DOTALL).strip()

        return jsonify({"reply": clean_reply}), 200

    except Exception as e:
        logger.exception("[chat] Internal error")
        return jsonify({"reply": "Простите, сервис сейчас перегружен. Попробуйте написать чуть позже!"}), 200


def _get_chat_system_prompt() -> str:
    return """Ты — дружелюбный AI-наставник образовательной платформы NeuroTutor.
Отвечай кратко, по делу, поддерживающе и на русском языке.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА ФОРМАТИРОВАНИЯ:
1. НЕ используй Markdown (никаких **звездочек** для жирности, никаких [скобок](url) для ссылок).
2. Если нужно дать ссылку, пиши её открытым текстом: "название ресурса: https://..."
3. Обязательно делай пустую строку (двойной перенос строки) перед каждым новым пунктом списка. Текст должен быть воздушным и легко читаться.

Никогда не выводи свои внутренние рассуждения <think>, давай сразу готовый ответ студенту."""


def _build_chat_prompt(message: str, course_name: str, weak: list, strong: list, grades: str) -> str:
    parts = []
    if course_name:
        parts.append(f"Курс: {course_name}.")
    if weak:
        parts.append(f"Слабые темы (оценка < 60%): {', '.join(weak)}")
    if strong:
        parts.append(f"Сильные темы (оценка > 85%): {', '.join(strong)}")
    if grades:
        parts.append(f"Последние оценки: {grades}")
    if not weak and not strong and not grades:
        parts.append("Данные об успеваемости пока недоступны.")
    parts.append(f"\nВопрос студента: {message}")
    return "\n".join(parts)


if __name__ == '__main__':
    port = int(os.getenv("PYTHON_SERVICE_PORT", 5001))
    logger.info(f"Starting Python Bridge on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)