#!/usr/bin/env python3
"""
Jira Client for AI Assistant Integration

Handles Jira API interactions including reading ticket details and posting comments.
"""

import requests
from typing import Dict, Any, Optional, List
from atlassian import Jira
import json

class JiraClient:
    def __init__(self, jira_url: str, username: str, api_token: str):
        """
        Initialize Jira client
        
        Args:
            jira_url: Base URL for your Jira instance (e.g., https://yourcompany.atlassian.net)
            username: Your Jira username/email
            api_token: Your Jira API token
        """
        self.jira_url = jira_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        
        # Initialize the Atlassian Jira client
        try:
            self.jira = Jira(
                url=jira_url,
                username=username,
                password=api_token,
                cloud=True
            )
            print(f"✅ Connected to Jira: {jira_url}")
        except Exception as e:
            print(f"❌ Failed to connect to Jira: {e}")
            self.jira = None
    
    def get_ticket_details(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a Jira ticket
        
        Args:
            ticket_key: Jira ticket key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary with ticket details or None if error
        """
        try:
            if not self.jira:
                return None
                
            # Get the issue details
            issue = self.jira.issue(ticket_key)
            
            # Extract relevant information
            fields = issue['fields']
            ticket_info = {
                'key': issue['key'],
                'summary': fields.get('summary', ''),
                'description': fields.get('description', ''),
                'story_points': self._get_story_points(fields),
                'labels': fields.get('labels', []),
                'status': fields.get('status', {}).get('name', 'Unknown'),
                'assignee': self._get_assignee(fields),
                'reporter': self._get_reporter(fields),
                'issue_type': fields.get('issuetype', {}).get('name', 'Unknown'),
                'project_key': fields.get('project', {}).get('key', ''),
                'url': f"{self.jira_url}/browse/{issue['key']}"
            }
            
            return ticket_info
            
        except Exception as e:
            print(f"❌ Error getting ticket details for {ticket_key}: {e}")
            return None
    
    def _get_story_points(self, fields: Dict[str, Any]) -> Optional[float]:
        """Extract story points from ticket fields"""
        # Story points can be in different custom fields depending on Jira setup
        story_point_fields = [
            'customfield_10016',  # Common Jira Cloud field
            'customfield_10004',  # Another common field
            'customfield_10002',  # Yet another common field
            'storyPoints',        # If using standard field name
        ]
        
        for field in story_point_fields:
            value = fields.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _get_assignee(self, fields: Dict[str, Any]) -> Optional[str]:
        """Extract assignee from ticket fields"""
        assignee = fields.get('assignee')
        if assignee:
            return assignee.get('displayName', assignee.get('name', 'Unknown'))
        return None
    
    def _get_reporter(self, fields: Dict[str, Any]) -> Optional[str]:
        """Extract reporter from ticket fields"""
        reporter = fields.get('reporter')
        if reporter:
            return reporter.get('displayName', reporter.get('name', 'Unknown'))
        return None
    
    def add_comment(self, ticket_key: str, comment: str) -> bool:
        """
        Add a comment to a Jira ticket
        
        Args:
            ticket_key: Jira ticket key (e.g., 'PROJ-123')
            comment: Comment text to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.jira:
                print("❌ Jira client not initialized")
                return False
                
            self.jira.issue_add_comment(ticket_key, comment)
            print(f"✅ Added comment to {ticket_key}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding comment to {ticket_key}: {e}")
            return False
    
    def is_eligible_for_automation(self, ticket_info: Dict[str, Any], max_story_points: float = 5.0) -> tuple[bool, str]:
        """
        Check if a ticket is eligible for AI automation
        
        Args:
            ticket_info: Ticket information from get_ticket_details()
            max_story_points: Maximum story points for automation
            
        Returns:
            Tuple of (is_eligible, reason)
        """
        # Check if we have a description
        if not ticket_info.get('description'):
            return False, "No description provided"
        
        # Check if we have labels (for repo identification)
        if not ticket_info.get('labels'):
            return False, "No labels provided (need repo name as first label)"
        
        # Check story points
        story_points = ticket_info.get('story_points')
        if story_points is None:
            return False, "No story points assigned"
        
        if story_points > max_story_points:
            return False, f"Story points ({story_points}) exceed maximum ({max_story_points})"
        
        return True, f"Eligible: {story_points} story points, has description and labels"
    
    def create_pr_comment(self, ticket_key: str, objective: str, pr_url: str, 
                         iterations: int, modified_files: List[str], success: bool) -> str:
        """
        Create a formatted comment for the Jira ticket with PR information
        
        Args:
            ticket_key: Jira ticket key
            objective: The objective that was completed
            pr_url: URL of the created pull request
            iterations: Number of AI iterations
            modified_files: List of files that were modified
            success: Whether the task was successful
            
        Returns:
            Formatted comment string
        """
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"
        
        comment = f"""🤖 **AI Assistant Update**

**Status:** {status_emoji} {status_text}
**Objective:** {objective}
**Iterations:** {iterations}

"""
        
        if pr_url:
            comment += f"**Pull Request:** {pr_url}\n\n"
        
        if modified_files:
            comment += "**Files Modified:**\n"
            for file_path in modified_files:
                comment += f"• `{file_path}`\n"
            comment += "\n"
        
        if success:
            comment += "The AI assistant has completed the task and created a pull request for review. Please check the PR description for detailed changes."
        else:
            comment += "The AI assistant encountered issues while working on this task. Please check the logs for more information."
        
        comment += f"\n\n*Automated by AI Assistant for ticket {ticket_key}*"
        
        return comment
    
    def test_connection(self) -> bool:
        """
        Test the Jira connection
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            if not self.jira:
                return False
                
            # Try to get user info as a connection test
            myself = self.jira.myself()
            print(f"✅ Jira connection test successful. Connected as: {myself.get('displayName', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Jira connection test failed: {e}")
            return False 