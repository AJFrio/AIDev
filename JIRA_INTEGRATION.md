# Jira Integration for AI Assistant

This document explains how to set up and use the Jira integration that automatically triggers the AI Assistant when new tickets are created.

## Overview

The Jira integration provides a fully automated development workflow:

1. **New Jira ticket created** → Webhook triggered
2. **Eligibility check** → Story points ≤ 5, has description & labels
3. **AI Assistant runs** → Uses description as objective, first label as repo
4. **Pull request created** → AI commits changes to dedicated branch
5. **Jira updated** → Comment added with PR link and details

## Prerequisites

- Jira Cloud instance with admin access
- GitHub repository with proper access tokens
- Server/hosting environment to run the webhook server
- Valid Azure OpenAI or OpenAI API credentials

## Installation

1. Install additional dependencies:
   ```bash
   pip install flask atlassian-python-api
   ```

2. Update your `.env` file with Jira configuration:
   ```env
   # Jira Integration Configuration
   JIRA_URL=https://yourcompany.atlassian.net
   JIRA_USERNAME=your.email@company.com
   JIRA_API_TOKEN=your_jira_api_token_here
   
   # Automation Settings
   MAX_STORY_POINTS_FOR_AUTOMATION=5.0
   MAX_ITERATIONS_FOR_AUTOMATION=50
   
   # Webhook Server Settings
   WEBHOOK_PORT=5000
   DEBUG_MODE=false
   ```

## Jira Setup

### 1. Create API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Give it a label (e.g., "AI Assistant Integration")
4. Copy the token and add it to your `.env` file

### 2. Configure Webhook

1. In Jira, go to **Settings** → **System** → **Webhooks**
2. Click **Create a Webhook**
3. Configure:
   - **Name**: AI Assistant Webhook
   - **Status**: Enabled
   - **URL**: `http://your-server-ip:5000/jira-webhook`
   - **Events**: Select "Issue Created"
   - **JQL Filter**: (Optional) Add filters if needed

### 3. Custom Fields (if needed)

The system automatically detects story points from common custom fields:
- `customfield_10016` (most common)
- `customfield_10004`
- `customfield_10002`

If your story points field is different, you may need to update `jira_client.py`.

## Usage

### 1. Start the Webhook Server

```bash
python jira_webhook_server.py
```

The server will start on the configured port (default: 5000) and display:
```
🚀 Starting Jira Webhook Server
Webhook endpoint: http://localhost:5000/jira-webhook
Health check: http://localhost:5000/health
Test endpoint: http://localhost:5000/test-ticket/<TICKET-KEY>
```

### 2. Create Eligible Tickets

For a ticket to be automatically processed, it must:

✅ **Have story points ≤ 5** (configurable)
✅ **Have a description** (used as the AI objective)
✅ **Have at least one label** (first label used as repository name)

#### Example Ticket:
- **Summary**: "Add blue color option to button component"
- **Description**: "Add a blue color variant to the button component in the design system. The button should support both light and dark themes."
- **Story Points**: 3
- **Labels**: `design-system`, `ui-components`
- **Repository**: `design-system` (from first label)

### 3. Monitor Processing

The webhook server provides several endpoints for monitoring:

- **Health Check**: `GET /health`
  ```json
  {
    "status": "healthy",
    "jira_connected": true,
    "processing_tickets": ["PROJ-123"],
    "processed_count": 5
  }
  ```

- **Manual Testing**: `POST /test-ticket/<TICKET-KEY>`
  ```bash
  curl -X POST http://localhost:5000/test-ticket/PROJ-123
  ```

## Workflow Details

### Eligibility Checking

When a new ticket is created, the system checks:

1. **Story Points**: Must be ≤ configured maximum
2. **Description**: Must be present and non-empty
3. **Labels**: Must have at least one label (for repository identification)

Ineligible tickets receive a comment explaining why they can't be automated.

### Processing Flow

For eligible tickets:

1. **Initial Comment**: Posted to ticket with processing status
2. **Branch Creation**: New branch created (e.g., `ai-dev/add-blue-button-option`)
3. **AI Execution**: AI Assistant works on the objective
4. **Pull Request**: Created with detailed changes
5. **Final Comment**: Posted with PR link and results

### Example Comments

**Initial Comment:**
```
🤖 AI Assistant - Starting automation

Ticket: PROJ-123
Objective: Add blue color option to button component
Repository: design-system
Story Points: 3

The AI assistant is now working on this task. You'll receive an update when it's complete.
```

**Final Comment:**
```
🤖 AI Assistant Update

Status: ✅ Success
Objective: Add blue color option to button component
Iterations: 8

Pull Request: https://github.com/user/design-system/pull/456

Files Modified:
• src/components/Button.js
• src/styles/button.css
• stories/Button.stories.js

The AI assistant has completed the task and created a pull request for review. Please check the PR description for detailed changes.

Automated by AI Assistant for ticket PROJ-123
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_STORY_POINTS_FOR_AUTOMATION` | 5.0 | Maximum story points for auto-processing |
| `MAX_ITERATIONS_FOR_AUTOMATION` | 50 | Maximum AI iterations per ticket |
| `WEBHOOK_PORT` | 5000 | Port for webhook server |
| `DEBUG_MODE` | false | Enable Flask debug mode |

### Repository Mapping

The system uses the **first label** as the repository name. You can set up a mapping system:

- Label: `web-app` → Repository: `company-website`
- Label: `api` → Repository: `backend-api`
- Label: `mobile` → Repository: `mobile-app`

## Testing

### Test Integration Components

```bash
python test_jira_integration.py
```

This tests:
- Configuration validation
- Jira API connection
- Ticket eligibility logic
- Comment formatting

### Test Specific Ticket

```bash
curl -X POST http://localhost:5000/test-ticket/PROJ-123
```

### Test Webhook Locally

Use tools like [ngrok](https://ngrok.com/) to expose your local server:

```bash
# Install ngrok
ngrok http 5000

# Use the provided URL in Jira webhook configuration
# e.g., https://abc123.ngrok.io/jira-webhook
```

## Security Considerations

1. **API Tokens**: Store securely, rotate regularly
2. **Webhook Authentication**: Consider adding webhook authentication
3. **Network Security**: Restrict webhook server access
4. **GitHub Permissions**: Use minimal required scopes
5. **Resource Limits**: Monitor AI usage and costs

## Troubleshooting

### Common Issues

**Webhook not triggering:**
- Check Jira webhook configuration
- Verify URL is accessible from Jira
- Check server logs for errors

**Tickets not being processed:**
- Verify eligibility criteria (story points, description, labels)
- Check Jira API connection
- Review server logs

**AI Assistant failures:**
- Check OpenAI API credentials
- Verify GitHub token permissions
- Review repository access

### Debug Commands

```bash
# Check Jira connection
python test_jira_integration.py

# Check webhook server health
curl http://localhost:5000/health

# View server logs
python jira_webhook_server.py  # Run with DEBUG_MODE=true
```

## Advanced Configuration

### Custom Story Points Field

If your Jira uses a different custom field for story points, update `jira_client.py`:

```python
def _get_story_points(self, fields: Dict[str, Any]) -> Optional[float]:
    story_point_fields = [
        'customfield_YOUR_FIELD',  # Add your custom field ID
        'customfield_10016',       # Keep existing fallbacks
        # ... other fields
    ]
```

### Webhook Authentication

Add webhook authentication by modifying the webhook endpoint:

```python
@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    # Add authentication check
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {Config.WEBHOOK_SECRET}":
        return jsonify({'error': 'Unauthorized'}), 401
    
    # ... rest of the handler
```

### Custom Processing Logic

Extend the processing logic by modifying `JiraWebhookHandler._process_ticket_async()`:

```python
def _process_ticket_async(self, ticket_key: str):
    # Add custom business logic
    if self._is_critical_ticket(ticket_info):
        # Handle critical tickets differently
        pass
    
    # Add custom notifications
    self._notify_team(ticket_key, "processing_started")
    
    # ... existing logic
```

## Production Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "jira_webhook_server.py"]
```

### Environment Setup

Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 jira_webhook_server:app
```

### Monitoring

Set up monitoring for:
- Server uptime
- Webhook response times
- Processing success/failure rates
- AI API usage and costs

This integration creates a powerful automated development workflow that can significantly speed up handling of small development tasks! 