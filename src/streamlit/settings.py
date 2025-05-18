import os

from dotenv import load_dotenv


load_dotenv()

class Settings:
    agent_url: str = os.getenv("AGENT_URL")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY")
    graph_id: str = os.getenv("IMAGE_NAME")
    
    
    
settings = Settings()