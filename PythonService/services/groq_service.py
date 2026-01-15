import groq
from utils.config import config
from typing import List, Dict

class GroqService:
    def __init__(self):
        self.client = groq.Groq(api_key=config.GROQ_API_KEY)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Генерация эмбеддингов для текстов"""
        try:
            # Используем Groq для генерации эмбеддингов
            # Note: Groq может не иметь прямого embedding API, используем альтернативу
            # Временно используем sentence-transformers
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(texts).tolist()
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Fallback: возвращаем случайные эмбеддинги
            return [[0.1] * 384 for _ in texts]
    
    def generate_explanation(self, user_id: str, recommended_courses: List, weak_topics: List[str]) -> str:
        """Генерация объяснения рекомендаций с помощью LLM"""
        try:
            course_titles = [course.title for course in recommended_courses[:3]]
            weak_topics_str = ", ".join(weak_topics[:5])
            
            prompt = f"""
            Пользователь {user_id} показал слабые результаты в следующих темах: {weak_topics_str}.
            Рекомендованные курсы: {', '.join(course_titles)}.
            
            Объясни кратко и понятно на русском языке, почему именно эти курсы были рекомендованы.
            Сосредоточься на том, как курсы помогут улучшить знания в слабых темах.
            Ответ должен быть не более 100 слов.
            """
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return "Рекомендации основаны на ваших учебных результатах и помогут улучшить знания в слабых темах."