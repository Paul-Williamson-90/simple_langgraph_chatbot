import os

from dotenv import load_dotenv


load_dotenv()

class Settings:
    agent_url: str = os.getenv("AGENT_URL")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY")
    
    graph_id: str = os.getenv("IMAGE_NAME")
    
    postgres_db: str = os.getenv("POSTGRES_DB")
    postgres_user: str = os.getenv("POSTGRES_USER")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD")
    postgres_host: str = os.getenv("POSTGRES_HOST")
    postgres_port: str = os.getenv("POSTGRES_PORT")
    
    
settings = Settings()