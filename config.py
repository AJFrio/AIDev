import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # GitHub API settings
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_API_BASE = 'https://api.github.com'
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4.1-mini'
    
    # Default repository owner
    DEFAULT_REPO_OWNER = 'AJFrio' 