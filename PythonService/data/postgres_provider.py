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

    def get_interactions(self):
        return []