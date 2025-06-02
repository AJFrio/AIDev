#!/usr/bin/env python3
"""
Secure Jira Webhook Server for AI Assistant

Production-ready Flask server with HTTPS support that listens for Jira webhook events
and automatically triggers the AI assistant for eligible tickets.
"""

from flask import Flask, request, jsonify
import json
import threading
import time
import ssl
import os
from typing import Dict, Any, Optional
from datetime import datetime

from config import Config
from jira_client import JiraClient
from ai_assistant import AIAssistant

app = Flask(__name__)

class SecureJiraWebhookHandler:
    def __init__(self):
        self.jira_client = None
        self.processing_tickets = set()  # Track tickets currently being processed
        self.processed_tickets = set()   # Track tickets already processed
        
        # Initialize Jira client if configured
        if self._is_jira_configured():
            self.jira_client = JiraClient(
                Config.JIRA_URL,
                Config.JIRA_USERNAME, 
                Config.JIRA_API_TOKEN
            )
            
            # Test connection
            if self.jira_client and not self.jira_client.test_connection():
                print("⚠️  Jira connection failed during initialization")
                self.jira_client = None
        else:
            print("⚠️  Jira not configured. Please set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN")
    
    def _is_jira_configured(self) -> bool:
        """Check if Jira configuration is available"""
        return all([
            hasattr(Config, 'JIRA_URL') and Config.JIRA_URL,
            hasattr(Config, 'JIRA_USERNAME') and Config.JIRA_USERNAME,
            hasattr(Config, 'JIRA_API_TOKEN') and Config.JIRA_API_TOKEN
        ])
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Jira webhook data
        
        Args:
            webhook_data: JSON data from Jira webhook
            
        Returns:
            Response dictionary
        """
        try:
            # Extract event information
            webhook_event = webhook_data.get('webhookEvent', '')
            issue_event_type = webhook_data.get('issue_event_type_name', '')
            
            print(f"📨 Received webhook: {webhook_event} - {issue_event_type}")
            
            # We're interested in issue creation events
            if webhook_event == 'jira:issue_created' or issue_event_type == 'issue_created':
                return self._handle_issue_created(webhook_data)
            else:
                return {
                    'status': 'ignored',
                    'reason': f'Event type {webhook_event} not handled'
                }
                
        except Exception as e:
            print(f"❌ Error handling webhook: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _handle_issue_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new issue creation"""
        try:
            # Extract issue information from webhook
            issue = webhook_data.get('issue', {})
            issue_key = issue.get('key', '')
            
            if not issue_key:
                return {
                    'status': 'error',
                    'reason': 'No issue key found in webhook data'
                }
            
            print(f"🎫 New ticket created: {issue_key}")
            
            # Check if we're already processing this ticket
            if issue_key in self.processing_tickets:
                return {
                    'status': 'skipped',
                    'reason': f'Ticket {issue_key} is already being processed'
                }
            
            # Check if we've already processed this ticket
            if issue_key in self.processed_tickets:
                return {
                    'status': 'skipped', 
                    'reason': f'Ticket {issue_key} has already been processed'
                }
            
            # Start processing in background thread
            thread = threading.Thread(
                target=self._process_ticket_async,
                args=(issue_key,),
                daemon=True
            )
            thread.start()
            
            return {
                'status': 'accepted',
                'message': f'Ticket {issue_key} queued for processing'
            }
            
        except Exception as e:
            print(f"❌ Error handling issue creation: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _process_ticket_async(self, ticket_key: str):
        """Process a ticket asynchronously"""
        try:
            # Mark as processing
            self.processing_tickets.add(ticket_key)
            
            print(f"🔄 Processing ticket: {ticket_key}")
            
            # Get ticket details
            if not self.jira_client:
                print("❌ Jira client not available")
                return
            
            ticket_info = self.jira_client.get_ticket_details(ticket_key)
            if not ticket_info:
                print(f"❌ Could not get details for ticket {ticket_key}")
                return
            
            print(f"📋 Ticket details: {ticket_info['summary']} ({ticket_info.get('story_points', 'No')} points)")
            
            # Check if ticket is eligible for automation
            is_eligible, reason = self.jira_client.is_eligible_for_automation(
                ticket_info, 
                max_story_points=Config.MAX_STORY_POINTS_FOR_AUTOMATION
            )
            
            print(f"🔍 Eligibility check: {reason}")
            
            if not is_eligible:
                # Add a comment explaining why it's not eligible
                comment = f"🤖 **AI Assistant** - This ticket is not eligible for automation: {reason}"
                self.jira_client.add_comment(ticket_key, comment)
                return
            
            # Extract information for AI assistant
            objective = ticket_info['description']
            repo_name = ticket_info['labels'][0] if ticket_info['labels'] else None
            
            if not repo_name:
                comment = "🤖 **AI Assistant** - Cannot process: No repository specified in labels"
                self.jira_client.add_comment(ticket_key, comment)
                return
            
            # Add initial comment
            initial_comment = f"""🤖 **AI Assistant** - Starting automation

**Ticket:** {ticket_key}
**Objective:** {objective}
**Repository:** {repo_name}
**Story Points:** {ticket_info.get('story_points', 'Unknown')}

The AI assistant is now working on this task. You'll receive an update when it's complete."""
            
            self.jira_client.add_comment(ticket_key, initial_comment)
            
            # Run AI assistant
            result = self._run_ai_assistant(
                repo_name=repo_name,
                objective=objective,
                ticket_key=ticket_key
            )
            
            # Create final comment with results
            final_comment = self.jira_client.create_pr_comment(
                ticket_key=ticket_key,
                objective=objective,
                pr_url=result.get('pull_request_url'),
                iterations=result.get('iterations', 0),
                modified_files=[f['file_path'] for f in result.get('modified_files', [])],
                success=result.get('success', False)
            )
            
            self.jira_client.add_comment(ticket_key, final_comment)
            
            print(f"✅ Completed processing ticket: {ticket_key}")
            
        except Exception as e:
            print(f"❌ Error processing ticket {ticket_key}: {e}")
            
            # Add error comment to ticket
            if self.jira_client:
                error_comment = f"""🤖 **AI Assistant** - Error occurred

❌ **Status:** Failed
**Error:** {str(e)}

The AI assistant encountered an error while processing this ticket. Please check the server logs for more details."""
                
                self.jira_client.add_comment(ticket_key, error_comment)
        
        finally:
            # Mark as processed
            self.processing_tickets.discard(ticket_key)
            self.processed_tickets.add(ticket_key)
    
    def _run_ai_assistant(self, repo_name: str, objective: str, ticket_key: str) -> Dict[str, Any]:
        """Run the AI assistant with the given parameters"""
        try:
            print(f"🤖 Starting AI assistant for {repo_name} with objective: {objective}")
            
            # Create AI assistant instance
            assistant = AIAssistant(
                repo_owner=Config.DEFAULT_REPO_OWNER,
                repo_name=repo_name,
                objective=f"{ticket_key}: {objective}"  # Include ticket key in objective
            )
            
            # Execute the objective
            result = assistant.execute_objective(
                objective=objective,
                max_iterations=Config.MAX_ITERATIONS_FOR_AUTOMATION,
                create_pr=True
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Error running AI assistant: {e}")
            return {
                'success': False,
                'error': str(e),
                'iterations': 0,
                'modified_files': []
            }

# Global webhook handler
webhook_handler = SecureJiraWebhookHandler()

# Webhook authentication decorator
def authenticate_webhook(f):
    """Decorator to authenticate webhook requests"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for webhook secret if configured
        if hasattr(Config, 'WEBHOOK_SECRET') and Config.WEBHOOK_SECRET:
            auth_header = request.headers.get('Authorization')
            expected_auth = f"Bearer {Config.WEBHOOK_SECRET}"
            
            if auth_header != expected_auth:
                print(f"❌ Unauthorized webhook attempt from {request.remote_addr}")
                return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/jira-webhook', methods=['POST'])
@authenticate_webhook
def jira_webhook():
    """Secure endpoint for Jira webhooks"""
    try:
        # Get JSON data from request
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({
                'status': 'error',
                'error': 'No JSON data received'
            }), 400
        
        # Log the webhook for debugging (but don't log sensitive data)
        print(f"📨 Secure webhook received at {datetime.now()} from {request.remote_addr}")
        
        # Handle the webhook
        result = webhook_handler.handle_webhook(webhook_data)
        
        # Return response
        status_code = 200 if result.get('status') != 'error' else 500
        return jsonify(result), status_code
        
    except Exception as e:
        print(f"❌ Secure webhook endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'jira_connected': webhook_handler.jira_client is not None,
        'processing_tickets': list(webhook_handler.processing_tickets),
        'processed_count': len(webhook_handler.processed_tickets),
        'secure': True,
        'version': '2.0'
    })

@app.route('/test-ticket/<ticket_key>', methods=['POST'])
@authenticate_webhook
def test_ticket_processing(ticket_key: str):
    """Test endpoint to manually trigger ticket processing"""
    try:
        if not webhook_handler.jira_client:
            return jsonify({
                'status': 'error',
                'error': 'Jira client not configured'
            }), 500
        
        # Start processing in background
        thread = threading.Thread(
            target=webhook_handler._process_ticket_async,
            args=(ticket_key,),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'status': 'accepted',
            'message': f'Ticket {ticket_key} queued for processing'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def get_ssl_context():
    """Get SSL context for HTTPS"""
    ssl_cert = getattr(Config, 'SSL_CERT_PATH', None)
    ssl_key = getattr(Config, 'SSL_KEY_PATH', None)
    
    if ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print(f"🔒 Using SSL certificate: {ssl_cert}")
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(ssl_cert, ssl_key)
        return context
    else:
        print("⚠️  SSL certificates not found. Generating self-signed certificate...")
        return 'adhoc'  # Flask will generate a self-signed certificate

if __name__ == '__main__':
    # Determine port and SSL settings
    port = getattr(Config, 'WEBHOOK_PORT', 5000)
    debug_mode = getattr(Config, 'DEBUG_MODE', False)
    
    # Check if SSL is required
    use_ssl = getattr(Config, 'USE_SSL', True)
    
    if use_ssl:
        print("🚀 Starting Secure Jira Webhook Server (HTTPS)")
        print(f"🔒 Secure webhook endpoint: https://localhost:{port}/jira-webhook")
        print(f"🔒 Secure health check: https://localhost:{port}/health")
        print(f"🔒 Secure test endpoint: https://localhost:{port}/test-ticket/<TICKET-KEY>")
        
        # Get SSL context
        ssl_context = get_ssl_context()
        
        # Run with HTTPS
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            ssl_context=ssl_context
        )
    else:
        print("🚀 Starting Jira Webhook Server (HTTP - Development Only)")
        print("⚠️  WARNING: HTTP mode is not secure and should only be used for development!")
        print(f"Webhook endpoint: http://localhost:{port}/jira-webhook")
        print(f"Health check: http://localhost:{port}/health")
        print(f"Test endpoint: http://localhost:{port}/test-ticket/<TICKET-KEY>")
        
        # Run with HTTP
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode
        ) 