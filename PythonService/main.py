import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Импортируем нашу логику и схемы
from recommender import Recommender
from schemas.input_models import RecommendationRequest

# Загружаем переменные окружения (.env)
load_dotenv()

app = Flask(__name__)

# --- Инициализация системы рекомендаций ---
# Создаем экземпляр один раз при запуске приложения
try:
    recommender_system = Recommender()
    print("INFO: ML System initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize ML System. Error: {e}")
    # Не падаем сразу, чтобы работал хотя бы /health
    recommender_system = None

# --- Эндпоинты ---

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка, что сервис жив"""
    is_ready = recommender_system is not None and recommender_system.is_ready
    return jsonify({
        "status": "healthy", 
        "service": "course-recommender-ai",
        "model_loaded": is_ready
    })

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Основной метод. 
    Принимает JSON от C#, валидирует через Pydantic, запускает ML-логику.
    """
    if not recommender_system:
        return jsonify({"error": "ML System is not initialized"}), 503

    try:
        # 1. Валидация входных данных (Pydantic)
        # Pydantic сам распарсит JSON в объект класса RecommendationRequest
        req_data = RecommendationRequest(**request.json)
        
        user_id = req_data.userId
        # req_data.moodleGrades - это уже список объектов MoodleGrade
        
        print(f"INFO: Processing request for User {user_id} with {len(req_data.moodleGrades)} grades.")

        # 2. Подготовка данных для ML
        # Исправленная строка: преобразуем объекты Pydantic обратно в словари
        # Используем .model_dump() (для Pydantic v2) или .dict() (для v1)
        grades_list = [grade.model_dump() for grade in req_data.moodleGrades]

        # 3. Получение рекомендаций
        recommendations = recommender_system.get_hybrid_recommendations(user_id, grades_list)

        # 4. Возврат ответа в формате, который ждет C#
        return jsonify({
            "userId": user_id,
            "recommendations": recommendations
        })

    except ValueError as ve:
        # Ошибка валидации данных
        print(f"Validation Error: {ve}")
        return jsonify({"error": "Invalid data format", "details": str(ve)}), 400
    except Exception as e:
        # Любая другая ошибка сервера
        print(f"Internal Error: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"INFO: Python Service starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)