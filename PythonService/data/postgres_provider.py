import os
import pandas as pd
from sqlalchemy import create_engine, text

class PostgresDataProvider:
    def __init__(self):       
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_name = os.getenv("DB_NAME", "recommender_db")
        
        self.connection_string = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}/{db_name}"
        self.engine = create_engine(self.connection_string)

    def get_courses_df(self) -> pd.DataFrame:
        """Загружает все курсы из БД в Pandas DataFrame"""
        query = "SELECT * FROM \"Courses\"" 
        try:
            df = pd.read_sql(query, self.engine)
            
           
            df = df.rename(columns={
                'ExternalId': 'course_id',
                'Title': 'title',
                'Description': 'description',
                'Topics': 'topic' 
            })
            
        
            def topics_to_string(x):
                if isinstance(x, list): return " ".join(x)
                return str(x)
                
            if 'topic' in df.columns:
                 df['topic'] = df['topic'].apply(topics_to_string)

            return df
        except Exception as e:
            print(f"Error reading from Postgres: {e}")
            return pd.DataFrame()

    def get_internal_courses(self) -> list[dict]:
        query = text('SELECT "Id", "Title", "Description", "Platform", "Difficulty", "Topics" FROM "Courses"')
        with self.engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
            return [dict(row) for row in rows]

    def health(self) -> dict:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "ok", "host": os.getenv("DB_HOST", "localhost"), "database": os.getenv("DB_NAME", "recommender_db")}
        except Exception as ex:
            return {
                "status": "down",
                "host": os.getenv("DB_HOST", "localhost"),
                "database": os.getenv("DB_NAME", "recommender_db"),
                "error": str(ex),
            }

    def get_external_courses(self, limit: int = 20) -> list[dict]:
        query = text('SELECT "Id", "Title", "Description", "Platform", "Difficulty", "Topics", "Url", "ResourceType", "SearchQuery", "ConfidenceScore" FROM "ExternalCourses" WHERE "IsActive" = true ORDER BY "ConfidenceScore" DESC, "LastParsedAt" DESC LIMIT :limit')
        with self.engine.connect() as connection:
            rows = connection.execute(query, {"limit": limit}).mappings().all()
            return [dict(row) for row in rows]

    def get_external_courses_for_topics(self, topics: list[str], limit: int = 30) -> list[dict]:
        clean_topics = []
        for topic in topics:
            normalized = str(topic).strip().lower()
            if not normalized:
                continue
            clean_topics.append(normalized)
        clean_topics = list(dict.fromkeys(clean_topics))
        if not clean_topics:
            return []

        clauses = []
        parameters = {"limit": limit}
        for index, topic in enumerate(clean_topics):
            param = f"topic_{index}"
            parameters[param] = f"%{topic}%"
            topic_clauses = [
                f'LOWER("Title") LIKE :{param}',
                f'LOWER("Description") LIKE :{param}',
                f'LOWER("SearchQuery") LIKE :{param}',
                f'LOWER("Topics"::text) LIKE :{param}',
            ]
            for token_index, token in enumerate([part for part in topic.split() if len(part) >= 4][:4]):
                token_param = f"topic_{index}_token_{token_index}"
                parameters[token_param] = f"%{token}%"
                topic_clauses.extend([
                    f'LOWER("Title") LIKE :{token_param}',
                    f'LOWER("Description") LIKE :{token_param}',
                    f'LOWER("SearchQuery") LIKE :{token_param}',
                    f'LOWER("Topics"::text) LIKE :{token_param}',
                ])
            clauses.append(f"({' OR '.join(topic_clauses)})")

        query = text(f'''
            SELECT "Id", "Title", "Description", "Platform", "Difficulty", "Topics",
                   "Url", "ResourceType", "SearchQuery", "ConfidenceScore"
            FROM "ExternalCourses"
            WHERE "IsActive" = true
              AND ({' OR '.join(clauses)})
            ORDER BY "ConfidenceScore" DESC, "LastParsedAt" DESC
            LIMIT :limit
        ''')
        with self.engine.connect() as connection:
            rows = connection.execute(query, parameters).mappings().all()
            return [dict(row) for row in rows]

    def upsert_external_courses(self, courses: list[dict]) -> int:
        if not courses:
            return 0

        import uuid

        upsert_sql = text('''
            INSERT INTO "ExternalCourses"
            ("Id", "Title", "Description", "Platform", "Url", "Difficulty", "Topics", "Language", "ProviderCourseId", "ResourceType", "SearchQuery", "DiscoveryMethod", "ConfidenceScore", "IsActive", "LastParsedAt", "CreatedAt", "UpdatedAt", "MetadataJson")
            VALUES
            (:id, :title, :description, :platform, :url, :difficulty, CAST(:topics AS jsonb), :language, :provider_course_id, :resource_type, :search_query, :discovery_method, :confidence_score, true, NOW(), NOW(), NOW(), :metadata_json)
            ON CONFLICT ("Url")
            DO UPDATE SET
                "Title" = EXCLUDED."Title",
                "Description" = EXCLUDED."Description",
                "Platform" = EXCLUDED."Platform",
                "Difficulty" = EXCLUDED."Difficulty",
                "Topics" = EXCLUDED."Topics",
                "Language" = EXCLUDED."Language",
                "ProviderCourseId" = EXCLUDED."ProviderCourseId",
                "ResourceType" = EXCLUDED."ResourceType",
                "SearchQuery" = EXCLUDED."SearchQuery",
                "DiscoveryMethod" = EXCLUDED."DiscoveryMethod",
                "ConfidenceScore" = EXCLUDED."ConfidenceScore",
                "IsActive" = true,
                "LastParsedAt" = NOW(),
                "UpdatedAt" = NOW(),
                "MetadataJson" = EXCLUDED."MetadataJson"
        ''')

        import json
        count = 0
        with self.engine.begin() as connection:
            for course in courses:
                if not course.get("url"):
                    continue
                connection.execute(upsert_sql, {
                    "id": str(course.get("id") or uuid.uuid4()),
                    "title": course.get("title", ""),
                    "description": course.get("description", ""),
                    "platform": course.get("platform", "External"),
                    "url": course.get("url"),
                    "difficulty": course.get("difficulty", "Standard"),
                    "topics": json.dumps(course.get("topics", []), ensure_ascii=False),
                    "language": course.get("language", "en"),
                    "provider_course_id": course.get("provider_course_id"),
                    "resource_type": course.get("resource_type", "course"),
                    "search_query": course.get("search_query", ""),
                    "discovery_method": course.get("discovery_method", "ollama_search"),
                    "confidence_score": float(course.get("confidence_score", 0.0)),
                    "metadata_json": json.dumps(course.get("metadata", {}), ensure_ascii=False),
                })
                count += 1
        return count

    def deactivate_external_course(self, url: str) -> None:
        if not url:
            return
        query = text('UPDATE "ExternalCourses" SET "IsActive" = false, "UpdatedAt" = NOW() WHERE "Url" = :url')
        with self.engine.begin() as connection:
            connection.execute(query, {"url": url})

    def save_recommendation_history(self, session_id: str, user_id: int, recommendations: list[dict], context_course_id: str | None = None) -> None:
        if not recommendations:
            return
        insert_sql = text('INSERT INTO "AiRecommendationHistory" ("Id", "SessionId", "UserId", "ContextCourseId", "SourceKind", "InternalCourseId", "ExternalCourseId", "TitleSnapshot", "Reason", "RelevanceScore", "CreatedAt") VALUES (:id, :session_id, :user_id, :context_course_id, :source_kind, :internal_course_id, :external_course_id, :title_snapshot, :reason, :relevance_score, NOW())')
        import uuid
        with self.engine.begin() as connection:
            for rec in recommendations:
                connection.execute(insert_sql, {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": user_id,
                    "context_course_id": context_course_id,
                    "source_kind": rec.get("sourceKind", "internal"),
                    "internal_course_id": rec.get("internalCourseId"),
                    "external_course_id": rec.get("externalCourseId"),
                    "title_snapshot": rec.get("Title", ""),
                    "reason": rec.get("Reason", ""),
                    "relevance_score": rec.get("RelevanceScore", 0.0),
                })

    def get_recent_recommendation_history(self, session_id: str, user_id: int, limit: int = 10) -> list[dict]:
        query = text('SELECT "TitleSnapshot", "Reason", "SourceKind", "CreatedAt" FROM "AiRecommendationHistory" WHERE "SessionId" = :session_id AND "UserId" = :user_id ORDER BY "CreatedAt" DESC LIMIT :limit')
        with self.engine.connect() as connection:
            rows = connection.execute(query, {"session_id": session_id, "user_id": user_id, "limit": limit}).mappings().all()
            return [dict(row) for row in rows]

    def get_interactions(self):
        return []
