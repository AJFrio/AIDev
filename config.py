import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # GitHub API settings
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_API_BASE = 'https://api.github.com'
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    
    # Fallback to regular OpenAI if Azure not configured
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Default repository owner
    DEFAULT_REPO_OWNER = 'AJFrio'
    
    # Jira Integration settings
    JIRA_URL = os.getenv('JIRA_URL')  # e.g., https://yourcompany.atlassian.net
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')  # Your Jira email
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')  # Your Jira API token
    
    # Automation settings
    MAX_STORY_POINTS_FOR_AUTOMATION = float(os.getenv('MAX_STORY_POINTS_FOR_AUTOMATION', '5.0'))
    MAX_ITERATIONS_FOR_AUTOMATION = int(os.getenv('MAX_ITERATIONS_FOR_AUTOMATION', '50'))
    
    # Webhook server settings
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '5000'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # Security settings
    USE_SSL = os.getenv('USE_SSL', 'True').lower() == 'true'
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH')  # Path to SSL certificate file
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH')    # Path to SSL private key file
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')  # Optional webhook authentication secret
    
    @classmethod
    def use_azure_openai(cls) -> bool:
        """Check if Azure OpenAI is configured"""
        return bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT) 