import os
import logging
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from schemas.python_bridge import RecommendationRequest, RecommendationResponseWrapper, ChatRequest
from schemas.course_analysis import CourseAnalysisRequest, CourseAnalysisResponse
from services.groq_service import GroqService
from services.course_analysis_service import CourseAnalysisGroqService
from services.external_course_service import ExternalCourseService
from data.postgres_provider import PostgresDataProvider
from utils.config import config

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
groq_service = GroqService()
course_analysis_service = CourseAnalysisGroqService()
postgres_provider = PostgresDataProvider()
external_course_service = ExternalCourseService()
chat_memory: dict[str, dict] = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "recommender-python-bridge"})


@app.route('/health/dependencies', methods=['GET'])
def dependency_health():
    run_probe = str(request.args.get("probe", "false")).lower() == "true"
    groq_status = "ok" if config.GROQ_API_KEY else "missing_api_key"
    return jsonify({
        "status": "ok",
        "service": "recommender-python-bridge",
        "dependencies": {
            "groq": {
                "status": groq_status,
                "model": getattr(groq_service, "MODEL", None),
            },
            "ollama": external_course_service.ollama.health(run_probe=run_probe),
            "searxng": external_course_service.search.health(),
            "postgres": postgres_provider.health(),
        },
    })

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        req = RecommendationRequest(**data)
        session_id = req.sessionId or (f"rec-{req.userId}-{req.courseId}" if req.courseId else f"rec-{req.userId}")
        logger.info("Processing recommendation request for user %s session %s", req.userId, session_id)

        weak_topics, strong_topics = [], []
        all_tags = set(req.contextTags)
        if req.courseName:
            all_tags.add(req.courseName)

        has_grade_data = False
        for g in req.moodleGrades:
            raw = g.RawGrade
            max_g = g.MaxGrade
            item_name = g.ItemName or "unknown"
            all_tags.update(g.CourseTags)

            if raw is not None and max_g and float(max_g) > 0:
                has_grade_data = True
                ratio = float(raw) / float(max_g)
                if ratio < 0.6:
                    weak_topics.append(item_name)
                elif ratio > 0.85:
                    strong_topics.append(item_name)

        weak_topics = list(dict.fromkeys(weak_topics))
        strong_topics = list(dict.fromkeys(strong_topics))
        if not has_grade_data and not weak_topics:
            weak_topics = list(dict.fromkeys([tag for tag in all_tags if str(tag).strip()]))

        search_topics = list(dict.fromkeys(weak_topics + list(all_tags)))
        external_courses = external_course_service.discover_and_load_relevant_resources(
            search_topics,
            course_name=req.courseName,
            weak_topics=weak_topics,
            improvement_topics=[],
            course_tags=list(all_tags),
        )

        internal_courses = _select_internal_courses(list(all_tags), weak_topics, limit=1)
        combined_courses = internal_courses + external_courses

        recommendations = groq_service.generate_hybrid_recommendations(
            user_id=req.userId,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            candidate_courses=combined_courses,
            session_id=session_id,
            course_name=req.courseName,
        )

        postgres_provider.save_recommendation_history(session_id, req.userId, recommendations, req.courseId)

        return jsonify(RecommendationResponseWrapper(userId=req.userId, recommendations=recommendations).model_dump()), 200

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
        data = request.json or {}
        req = ChatRequest(**data)
        session_id = req.sessionId or (f"chat-{req.userId}-{req.courseId}" if req.courseId else f"chat-{req.userId}")
        logger.info(f"Chat request from user {req.userId}, message: {req.message[:80]}")

        if not req.message:
            return jsonify({"error": "message is required"}), 400

        memory = chat_memory.setdefault(session_id, {"messages": []})

        prompt = _build_chat_prompt(req.message, req.courseName, req.weakTopics, req.strongTopics, req.recentGradesSummary, memory.get("messages", []))

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

        memory["messages"].append({"role": "user", "content": req.message})
        memory["messages"].append({"role": "assistant", "content": clean_reply})
        memory["messages"] = memory["messages"][-10:]

        return jsonify({"reply": clean_reply}), 200

    except Exception as e:
        logger.exception("[chat] Internal error")
        return jsonify({"reply": "Простите, сервис сейчас перегружен. Попробуйте написать чуть позже!"}), 200


@app.route('/external-search/discover', methods=['POST'])
def discover_external_courses():
    try:
        data = request.json or {}
        weak_topics = data.get("weakTopics", [])
        if not weak_topics:
            return jsonify({"error": "weakTopics is required"}), 400

        result = external_course_service.discover_courses(weak_topics, force_refresh=bool(data.get("forceRefresh", False)))
        return jsonify(result), 200
    except Exception as ex:
        logger.exception("[external-search/discover] Internal error")
        return jsonify({"error": "External search failed", "details": str(ex)}), 500


def _get_chat_system_prompt() -> str:
    return """Ты — дружелюбный AI-наставник образовательной платформы NeuroTutor.
Отвечай кратко, по делу, поддерживающе и на русском языке.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА ФОРМАТИРОВАНИЯ:
1. НЕ используй Markdown (никаких **звездочек** для жирности, никаких [скобок](url) для ссылок).
2. Если нужно дать ссылку, пиши её открытым текстом: "название ресурса: https://..."
3. Обязательно делай пустую строку (двойной перенос строки) перед каждым новым пунктом списка. Текст должен быть воздушным и легко читаться.

Никогда не выводи свои внутренние рассуждения <think>, давай сразу готовый ответ студенту."""


def _build_chat_prompt(message: str, course_name: str, weak: list, strong: list, grades: str, history: list) -> str:
    parts = []
    if course_name:
        parts.append(f"Курс: {course_name}.")
    if weak:
        parts.append(f"Слабые темы (оценка < 60%): {', '.join(weak)}")
    if strong:
        parts.append(f"Сильные темы (оценка > 85%): {', '.join(strong)}")
    if grades:
        parts.append(f"Последние оценки: {grades}")
    if history:
        short_history = " | ".join([f"{m.get('role')}: {m.get('content', '')[:80]}" for m in history[-4:]])
        parts.append(f"Контекст диалога: {short_history}")
    if not weak and not strong and not grades:
        parts.append("Данные об успеваемости пока недоступны.")
    parts.append(f"\nВопрос студента: {message}")
    return "\n".join(parts)


def _score_course(course: dict, weak_topics: list[str], all_tags: list[str]) -> float:
    topic_blob = " ".join((course.get("Topics") or []) if isinstance(course.get("Topics"), list) else [str(course.get("Topics") or "")]).lower()
    title_blob = f"{course.get('Title', '')} {course.get('Description', '')} {course.get('SearchQuery', '')}".lower()
    score = 0.3
    for topic in weak_topics:
        t = topic.lower()
        if t in topic_blob or t in title_blob:
            score += 0.3
    for tag in all_tags[:10]:
        t = tag.lower()
        if t in topic_blob or t in title_blob:
            score += 0.05
    return min(score, 0.99)


def _select_internal_courses(all_tags: list[str], weak_topics: list[str], limit: int = 2) -> list[dict]:
    courses = postgres_provider.get_internal_courses()
    ranked = []
    for course in courses:
        score = _score_course(course, weak_topics, all_tags)
        if (weak_topics or all_tags) and score <= 0.3:
            continue
        ranked.append({
            "sourceKind": "internal",
            "internalCourseId": str(course.get("Id")),
            "Title": course.get("Title", ""),
            "Description": course.get("Description", ""),
            "Platform": course.get("Platform", "Moodle"),
            "Difficulty": course.get("Difficulty", "Standard"),
            "Topics": course.get("Topics") or [],
            "Url": None,
            "ResourceType": "course",
            "RelevanceScore": score,
        })
    ranked.sort(key=lambda x: x["RelevanceScore"], reverse=True)
    return ranked[:limit]


if __name__ == '__main__':
    port = int(os.getenv("PYTHON_SERVICE_PORT", 5001))
    logger.info(f"Starting Python Bridge on port {port}")
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
