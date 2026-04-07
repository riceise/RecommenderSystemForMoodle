from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import numpy as np
from typing import List, Dict, Tuple, Optional
from services.groq_service import GroqService


class ContentBasedRecommender:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.groq_service = GroqService()
        self.course_embeddings = None
        self.course_ids = None
        
    def fit(self, courses: List[Dict]):
        self.course_ids = [course['id'] for course in courses]

        texts = []
        for course in courses:
            text = f"{course['title']} {course['description']} {' '.join(course.get('topics', []))}"
            texts.append(text)

        self.course_embeddings = self.groq_service.generate_embeddings(texts)
    
    def recommend(self, user_topics: List[str], user_weak_topics: List[str], num_recs: int = 10) -> List[Tuple[str, float]]:
        if self.course_embeddings is None:
            raise ValueError("Модель не обучена. Сначала вызовите fit()")

        query_text = " ".join(user_weak_topics)
        query_embedding = self.groq_service.generate_embeddings([query_text])[0]

        similarities = cosine_similarity([query_embedding], self.course_embeddings)[0]

        recommendations = list(zip(self.course_ids, similarities))
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:num_recs]