#!/usr/bin/env python3
"""
Jira Client - Integration with Jira API

This module provides functionality to connect to Jira and process tickets
with specific labels for AI automation.
"""

from jira import JIRA
from typing import List, Dict, Optional
import logging
from config import Config

class JiraClient:
    """Client for interacting with Jira API"""
    
    def __init__(self, server: str = None, username: str = None, token: str = None):
        """Initialize Jira client with credentials"""
        self.server = server or Config.JIRA_URL
        self.username = username or Config.JIRA_USERNAME
        self.token = token or Config.JIRA_TOKEN
        
        if not all([self.server, self.username, self.token]):
            raise ValueError("Jira credentials are required: JIRA_URL, JIRA_USERNAME, JIRA_TOKEN")
        
        # Initialize JIRA client
        try:
            self.jira = JIRA(
                server=self.server,
                basic_auth=(self.username, self.token)
            )
            logging.info(f"Successfully connected to Jira: {self.server}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Jira: {str(e)}")
    
    def get_tickets_with_label(self, label: str = "UseAI") -> List[Dict]:
        """
        Get all tickets with a specific label
        
        Args:
            label: The label to search for (default: "UseAI")
            
        Returns:
            List of ticket dictionaries with relevant information
        """
        try:
            # JQL query to find tickets with the specified label
            jql_query = f'labels = "{label}"'
            
            # Get all issues matching the query
            issues = self.jira.search_issues(
                jql_query,
                maxResults=False,  # Get all results
                expand='names'
            )
            
            tickets = []
            for issue in issues:
                ticket_data = self._extract_ticket_data(issue)
                tickets.append(ticket_data)
            
            logging.info(f"Found {len(tickets)} tickets with label '{label}'")
            return tickets
            
        except Exception as e:
            logging.error(f"Error fetching tickets with label '{label}': {str(e)}")
            raise
    
    def get_ticket_by_key(self, ticket_key: str) -> Optional[Dict]:
        """
        Get a specific ticket by its key
        
        Args:
            ticket_key: The Jira ticket key (e.g., "REP-123")
            
        Returns:
            Dictionary with ticket information or None if not found
        """
        try:
            # Get the specific issue
            issue = self.jira.issue(ticket_key, expand='names')
            
            ticket_data = self._extract_ticket_data(issue)
            
            logging.info(f"Found ticket: {ticket_key}")
            return ticket_data
            
        except Exception as e:
            logging.error(f"Error fetching ticket '{ticket_key}': {str(e)}")
            return None
    
    def _extract_ticket_data(self, issue) -> Dict:
        """
        Extract relevant data from a Jira issue
        
        Args:
            issue: Jira issue object
            
        Returns:
            Dictionary with ticket information
        """
        # Get epic information
        epic_name = None
        epic_key = None
        
        # Try to get epic from different possible fields
        if hasattr(issue.fields, 'parent') and issue.fields.parent:
            # If it's a subtask, the parent might be the epic
            if issue.fields.parent.fields.issuetype.name == 'Epic':
                epic_name = issue.fields.parent.fields.summary
                epic_key = issue.fields.parent.key
        
        # Try custom field for epic link (common field names)
        epic_link_fields = ['customfield_10014', 'customfield_10008', 'epic']
        for field_name in epic_link_fields:
            if hasattr(issue.fields, field_name):
                epic_field = getattr(issue.fields, field_name)
                if epic_field:
                    try:
                        # Try to get the epic issue
                        epic_issue = self.jira.issue(epic_field)
                        epic_name = epic_issue.fields.summary
                        epic_key = epic_issue.key
                        break
                    except:
                        # If epic_field is already the epic name
                        epic_name = str(epic_field)
                        break
        
        # Get labels
        labels = [label for label in issue.fields.labels] if issue.fields.labels else []
        
        ticket_data = {
            'key': issue.key,
            'title': issue.fields.summary,
            'description': issue.fields.description or '',
            'status': issue.fields.status.name,
            'labels': labels,
            'epic_name': epic_name,
            'epic_key': epic_key,
            'issue_type': issue.fields.issuetype.name,
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
            'reporter': issue.fields.reporter.displayName if issue.fields.reporter else None,
            'created': str(issue.fields.created),
            'updated': str(issue.fields.updated),
            'url': f"{self.server}/browse/{issue.key}"
        }
        
        return ticket_data
    
    def get_all_epics(self) -> List[Dict]:
        """
        Get all epics in the project
        
        Returns:
            List of epic dictionaries
        """
        try:
            # JQL query to find all epics
            jql_query = 'type = Epic'
            
            issues = self.jira.search_issues(
                jql_query,
                maxResults=False
            )
            
            epics = []
            for issue in issues:
                epic_data = {
                    'key': issue.key,
                    'name': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'url': f"{self.server}/browse/{issue.key}"
                }
                epics.append(epic_data)
            
            logging.info(f"Found {len(epics)} epics")
            return epics
            
        except Exception as e:
            logging.error(f"Error fetching epics: {str(e)}")
            raise
    
    def process_useai_tickets(self) -> List[Dict]:
        """
        Process all tickets with UseAI label and prepare them for AI processing
        
        Returns:
            List of processed tickets ready for AI automation
        """
        try:
            tickets = self.get_tickets_with_label("UseAI")
            
            processed_tickets = []
            for ticket in tickets:
                # Create objective from title and description
                objective = f"Title: {ticket['title']}"
                if ticket['description']:
                    objective += f"\n\nDescription: {ticket['description']}"
                
                # Get repository name using epic mapping
                repo = Config.get_repo_for_epic(ticket['epic_name'])
                
                processed_ticket = {
                    'jira_key': ticket['key'],
                    'jira_url': ticket['url'],
                    'objective': objective,
                    'repo': repo,
                    'epic_key': ticket['epic_key'],
                    'original_ticket': ticket
                }
                
                processed_tickets.append(processed_ticket)
            
            logging.info(f"Processed {len(processed_tickets)} UseAI tickets")
            return processed_tickets
            
        except Exception as e:
            logging.error(f"Error processing UseAI tickets: {str(e)}")
            raise
    
    def add_comment_to_ticket(self, ticket_key: str, comment_text: str) -> bool:
        """
        Add a comment to a Jira ticket
        
        Args:
            ticket_key: The Jira ticket key (e.g., "REP-123")
            comment_text: The comment text to add
            
        Returns:
            True if comment was added successfully, False otherwise
        """
        try:
            self.jira.add_comment(ticket_key, comment_text)
            logging.info(f"Successfully added comment to ticket {ticket_key}")
            return True
        except Exception as e:
            logging.error(f"Failed to add comment to ticket {ticket_key}: {str(e)}")
            return False
    
    def add_pr_link_comment(self, ticket_key: str, pr_url: str, branch_name: str, repo_name: str) -> bool:
        """
        Add a formatted comment with PR link to a Jira ticket
        
        Args:
            ticket_key: The Jira ticket key
            pr_url: The GitHub pull request URL
            branch_name: The branch name used
            repo_name: The repository name
            
        Returns:
            True if comment was added successfully, False otherwise
        """
        comment_text = f"""🤖 *AI Dev Update*

✅ *Pull Request Created*
• Repository: {repo_name}
• Branch: {branch_name}
• Pull Request: {pr_url}

The AI Dev has completed the automated work for this ticket. Please review the pull request and merge when ready."""

        return self.add_comment_to_ticket(ticket_key, comment_text)
    
    def test_connection(self) -> bool:
        """
        Test the Jira connection
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get user info to test connection
            user = self.jira.myself()
            logging.info(f"Jira connection test successful. User: {user['displayName']}")
            return True
        except Exception as e:
            logging.error(f"Jira connection test failed: {str(e)}")
            return False 