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
    
    # Jira settings
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')
    JIRA_TOKEN = os.getenv('JIRA_TOKEN')
    
    # Default repository owner
    DEFAULT_REPO_OWNER = 'AJFrio'
    
    # Epic to Repository Mapping
    # Maps epic names to their corresponding repository names
    EPIC_TO_REPO_MAP = {
        'Builders - Menu Addition': 'threejs-builder',
        'Builder - New': 'threejs-builder',
        'Builders - Menu Issue': 'threejs-builder',
        # Add more mappings here as needed
        # 'Your Epic Name': 'your-repo-name',
    }
    
    # Default repository name for epics not in the mapping
    DEFAULT_REPO_NAME = 'Wholesale-Builder'
    
    # Repository to Owner Mapping
    # Maps repository names to their corresponding GitHub owners/organizations
    REPO_TO_OWNER_MAP = {
        'threejs-builder': 'repfitness',
        # Add more repo-to-owner mappings here as needed
        # 'some-other-repo': 'different-org',
    }
    
    @classmethod
    def use_azure_openai(cls) -> bool:
        """Check if Azure OpenAI is configured"""
        return bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT)
    
    @classmethod
    def get_repo_for_epic(cls, epic_name: str) -> str:
        """
        Get the repository name for a given epic name
        
        Args:
            epic_name: The name of the epic
            
        Returns:
            Repository name mapped to the epic, or default if not found
        """
        if not epic_name:
            return cls.DEFAULT_REPO_NAME
        
        # Try exact match first
        if epic_name in cls.EPIC_TO_REPO_MAP:
            return cls.EPIC_TO_REPO_MAP[epic_name]
        
        # Try case-insensitive match
        epic_lower = epic_name.lower()
        for mapped_epic, repo in cls.EPIC_TO_REPO_MAP.items():
            if mapped_epic.lower() == epic_lower:
                return repo
        
        # Try partial match (if epic name contains any of the mapped epic names)
        for mapped_epic, repo in cls.EPIC_TO_REPO_MAP.items():
            if mapped_epic.lower() in epic_lower or epic_lower in mapped_epic.lower():
                return repo
        
        # Return default if no match found
        return cls.DEFAULT_REPO_NAME
    
    @classmethod
    def get_owner_for_repo(cls, repo_name: str) -> str:
        """
        Get the GitHub owner/organization for a given repository name
        
        Args:
            repo_name: The name of the repository
            
        Returns:
            GitHub owner/organization for the repo, or default owner if not mapped
        """
        if repo_name in cls.REPO_TO_OWNER_MAP:
            return cls.REPO_TO_OWNER_MAP[repo_name]
        
        # Return default owner if no specific mapping found
        return cls.DEFAULT_REPO_OWNER 