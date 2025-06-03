# AI Coding Assistant with GitHub and Jira Integration

An intelligent coding assistant that connects to GitHub repositories and Jira tickets, using OpenAI's language models to help complete programming tasks, fix bugs, and implement features automatically.

## Features

- 🔗 **GitHub Integration**: Connects to any GitHub repository via the GitHub API
- 🎫 **Jira Integration**: Automatically processes Jira tickets with "UseAI" label
- 🤖 **AI-Powered**: Uses OpenAI's GPT models for intelligent code analysis and generation
- 🛠️ **Function Calling**: Uses OpenAI's native function calling for reliable tool execution
- 📁 **Repository Navigation**: Can explore directory structures and understand codebase organization
- ✏️ **File Editing**: Can read and modify files directly in GitHub repositories
- 🔄 **Iterative Approach**: Works through tasks step-by-step until completion
- 🌿 **Branch Safety**: Creates dedicated branches for all changes, protecting your main branch
- 🔀 **Pull Request Creation**: Automatically creates pull requests for review
- 🎯 **Automated Workflow**: Process multiple Jira tickets automatically

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd AIDev
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your API keys:
   - `GITHUB_TOKEN`: Your GitHub personal access token
   - `OPENAI_API_KEY`: Your OpenAI API key (or Azure OpenAI credentials)
   - `JIRA_URL`: Your Jira instance URL (optional, for Jira integration)
   - `JIRA_USERNAME`: Your Jira username (optional)
   - `JIRA_TOKEN`: Your Jira API token (optional)

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with the following permissions:
   - `repo` (Full control of private repositories)
   - `public_repo` (Access public repositories)
3. Copy the token and add it to your `.env` file

## Azure OpenAI Setup (Preferred)

If you're using Azure OpenAI Service:

1. Go to your Azure OpenAI resource in the Azure portal
2. Copy the following values:
   - **Endpoint**: Your resource endpoint URL
   - **API Key**: One of your access keys
   - **Deployment Name**: The name of your deployed model
3. Add them to your `.env` file:
   ```
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

## OpenAI API Key Setup (Alternative)

If you're using regular OpenAI instead of Azure:

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key and add it to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   ```

**Note:** The system will automatically use Azure OpenAI if configured, otherwise it falls back to regular OpenAI.

## Jira Integration Setup (Optional)

To enable automatic processing of Jira tickets:

1. Go to your Jira instance → Profile → Personal Access Tokens
2. Create a new API token
3. Add the following to your `.env` file:
   ```
   JIRA_URL=https://your-company.atlassian.net
   JIRA_USERNAME=your_email@company.com
   JIRA_TOKEN=your_jira_api_token_here
   ```

### How Jira Integration Works

1. **Label-Based Processing**: The system looks for tickets with the "UseAI" label
2. **Epic as Repository**: Uses the epic name associated with the ticket as the repository name
3. **Title + Description as Objective**: Combines the ticket title and description to create the AI objective
4. **Automatic Processing**: Processes all matching tickets in batch mode
5. **Bidirectional Linking**: Automatically adds comments to Jira tickets with GitHub PR links

### Repository Mapping System

The Jira integration includes a mapping system to connect Jira epics to the correct GitHub repositories and owners:

#### Epic-to-Repository Mapping

Epic names are mapped to specific repository names using the `EPIC_TO_REPO_MAP` in `config.py`:

```python
EPIC_TO_REPO_MAP = {
    'Builders - Menu Addition': 'threejs-builder',
    'User Management System': 'user-auth-api',
    'Mobile App Features': 'mobile-app',
    # Add more mappings as needed
}
```

**Features:**
- **Exact Matching**: Epic names that exactly match the map keys use the specified repository
- **Case Insensitive**: Matching is case-insensitive for flexibility
- **Partial Matching**: Epic names that contain or are contained within mapped epic names will match (e.g., "Builders Menu" would match "Builders - Menu Addition")
- **Default Fallback**: Unmapped epics use the `DEFAULT_REPO_NAME` from config

#### Repository-to-Owner Mapping

Different repositories can have different owners using the `REPO_TO_OWNER_MAP`:

```python
REPO_TO_OWNER_MAP = {
    'threejs-builder': 'repfitness',
    'company-website': 'company-org',
    # Other repos use DEFAULT_OWNER (AJFrio)
}
```

**How it works:**
- Repositories listed in the map use their specified owner
- Unlisted repositories use the `DEFAULT_OWNER` (AJFrio)
- This allows working with repositories across different GitHub organizations

#### Mapping Process Flow

1. **Epic Extraction**: Get the epic name from the Jira ticket
2. **Repository Resolution**: 
   - Check `EPIC_TO_REPO_MAP` for exact match
   - If no exact match, try case-insensitive matching
   - If still no match, try partial matching (substring matching)
   - If no match found, use `DEFAULT_REPO_NAME`
3. **Owner Resolution**:
   - Check `REPO_TO_OWNER_MAP` for the repository
   - If found, use the mapped owner
   - If not found, use `DEFAULT_OWNER`
4. **Final Result**: `owner/repository` (e.g., `repfitness/threejs-builder`)

#### Example Mapping Scenarios

| Epic Name | Mapped Repository | Repository Owner | Final GitHub Repo |
|-----------|------------------|------------------|-------------------|
| "Builders - Menu Addition" | threejs-builder | repfitness | repfitness/threejs-builder |
| "User Management System" | user-auth-api | AJFrio | AJFrio/user-auth-api |
| "Unmapped Epic Name" | my-default-repo | AJFrio | AJFrio/my-default-repo |

#### Managing Mappings

Use the included utility script to manage your epic mappings:

```bash
# View current mappings and available epics
python manage_epic_mappings.py

# Add a new mapping interactively
python manage_epic_mappings.py --add

# List all epics in your Jira project
python manage_epic_mappings.py --list-epics
```

**Benefits of Repository Mapping:**
- ✅ **Multi-Organization Support**: Work with repositories across different GitHub organizations
- ✅ **Flexible Epic Names**: Don't need exact epic-to-repo name matching
- ✅ **Easy Configuration**: Simple dictionary-based configuration
- ✅ **Partial Matching**: Handles variations in epic naming through substring matching
- ✅ **Default Fallbacks**: Graceful handling of unmapped epics

## Usage

### Basic Usage

```bash
# Process a specific repository with an objective
python main.py <repo-name> "<objective>"

# Process all Jira tickets with UseAI label
python main.py --jira-mode

# Test Jira connection
python main.py --test-jira
```

**🔒 Safety First:** The assistant automatically creates a new branch for all changes, keeping your main branch safe!

### Examples

```bash
# Add error handling to API endpoints
python main.py my-web-app "Add proper error handling to all API endpoints"

# Fix failing tests
python main.py my-project "Fix the failing unit tests in the test_utils.py file"

# Refactor code
python main.py my-library "Refactor the database connection code to use connection pooling"

# Add a new feature
python main.py my-app "Add user authentication using JWT tokens"

# Use a custom branch name
python main.py my-app "Add logging functionality" --branch feature/logging

# Skip pull request creation
python main.py my-app "Fix typos" --no-pr
```

### Command Line Options

- `--owner`: Specify repository owner (default: AJFrio)
- `--max-iterations`: Set maximum iterations (default: 100)
- `--github-token`: Override GitHub token from command line
- `--branch`: Custom branch name (default: auto-generated with timestamp)
- `--no-pr`: Skip creating a pull request when finished
- `--verbose`: Enable detailed output
- `--jira-mode`: Process all Jira tickets with UseAI label
- `--test-jira`: Test Jira connection and exit
- `--help`: Show help message

### Advanced Usage

```bash
# Work on someone else's repository
python main.py some-repo "Fix the memory leak in the cache module" --owner other-user

# Increase iteration limit for complex tasks
python main.py complex-project "Implement the entire user management system" --max-iterations 50

# Use custom branch and skip PR
python main.py my-repo "Quick fix for production" --branch hotfix/urgent --no-pr

# Use verbose mode for debugging
python main.py my-repo "Debug the authentication flow" --verbose
```

### Jira Integration Examples

```bash
# Process all Jira tickets with UseAI label
python main.py --jira-mode

# Process Jira tickets with verbose output
python main.py --jira-mode --verbose

# Process Jira tickets without creating pull requests
python main.py --jira-mode --no-pr

# Process Jira tickets with a custom branch name for all tickets
python main.py --jira-mode --branch feature/jira-automation

# Test your Jira connection
python main.py --test-jira
```

**Note**: When using `--jira-mode`, branch names automatically include the ticket number (e.g., `ai-dev-REP-123-20241201-143022`) unless you specify a custom branch with `--branch`.

## How It Works

1. **Branch Creation**: Creates a new branch (auto-named with descriptive name or custom name)
2. **Repository Analysis**: Fetches the repository structure from the new branch
3. **AI Planning**: An OpenAI model analyzes the objective and creates a plan
4. **Function Calling**: The AI uses OpenAI's native function calling to execute tools:
   - Navigate directories (`change_dir`)
   - Read file contents (`read_file`)
   - List directory contents (`get_directory`)
   - Update files (`update_file`)
   - Signal completion (`finish_task`)
5. **Iterative Process**: The AI continues working until the objective is complete
6. **Safe Commits**: All changes are committed to the dedicated branch
7. **Pull Request**: Automatically creates a PR for code review (unless `--no-pr` is used)

## Branch and PR Management

### Automatic Branch Creation
- Default branch name: `ai-dev-YYYYMMDD-HHMMSS`
- Custom branch names can be specified with `--branch`
- Branches are created from the repository's default branch

### Pull Request Creation
- Automatically created when task completes (unless `--no-pr` is used)
- Includes detailed description with:
  - Original objective
  - Branch name and iteration count
  - AI's final summary
- Ready for code review and merge

### Safety Benefits
- ✅ Main branch remains untouched
- ✅ All changes are reviewable before merge
- ✅ Easy to rollback if needed
- ✅ Collaboration-friendly workflow

## Available Tools

The AI Dev has access to these tools:

### `get_directory`
Retrieves the contents of the current directory, showing files and subdirectories.

### `read_file`
Reads the complete contents of a specified file.

### `update_file`
Updates a file with new content and commits the changes to the working branch.

### `change_dir`
Changes the current working directory for navigation.

### `finish_task`
Signals task completion and exits the coding loop. Requires a summary of what was accomplished and success status.

## Project Structure

```
AIDev/
├── main.py                    # Main entry point
├── config.py                  # Configuration management
├── ai_assistant.py           # Core AI assistant logic
├── ai_tools.py               # Tool implementations
├── github_client.py          # GitHub API client
├── jira_client.py            # Jira API client
├── manage_epic_mappings.py   # Epic-to-repo mapping utility
├── requirements.txt          # Python dependencies
├── env.example              # Environment variable template
├── LICENSE                  # MIT license
├── README.md               # Project documentation
└── tests/                  # Test files
    ├── test_jira_tickets.py
    ├── test_jira_comments.py
    ├── test_branch_naming.py
    ├── test_jira_connection.py
    ├── test_example.py
    └── debug_env_loading.py
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main.py       │───▶│  AIAssistant     │───▶│  OpenAI API     │
│  (Entry Point)  │    │  (Orchestrator)  │    │  (LLM)          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GitHubClient   │◀───│    AITools       │───▶│     Config      │
│  (API Client)   │    │  (Tool Handler)  │    │  (Settings)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                     ┌──────────────────┐    ┌─────────────────┐
                     │   GitHub Repo    │    │   JiraClient    │
                     │  (Branch-based)  │    │  (API Client)   │
                     └──────────────────┘    └─────────────────┘
```

## Configuration

The system uses the following configuration:

- **GitHub API**: `https://api.github.com`
- **OpenAI Model**: `gpt-4-turbo-preview` (configurable in `config.py`)
- **Default Owner**: `AJFrio` (configurable in `config.py`)
- **Branch Strategy**: Creates new branch for each run

## Error Handling

The assistant includes comprehensive error handling for:

- Invalid GitHub tokens or repository access
- OpenAI API errors or rate limits
- Network connectivity issues
- File encoding problems
- Malformed tool calls
- Branch creation conflicts

## Limitations

- Requires valid GitHub and OpenAI API access
- Limited by OpenAI's token limits per request
- Cannot create new files (only read and update existing ones)
- Works with text files only (no binary file support)
- Subject to GitHub API rate limits

## Workflow Examples

### Standard Workflow
1. Run: `python main.py my-repo "Add validation to user input"`
2. Assistant creates branch: `ai-dev-20241201-143022`
3. AI makes changes and commits to the branch
4. Pull request created automatically
5. Review and merge the PR

### Custom Branch Workflow
1. Run: `python main.py my-repo "Add caching" --branch feature/redis-cache`
2. Assistant creates branch: `feature/redis-cache`
3. AI makes changes to the custom branch
4. Pull request created from `feature/redis-cache` to `main`

### No-PR Workflow
1. Run: `python main.py my-repo "Quick fix" --no-pr`
2. Assistant creates branch and makes changes
3. No pull request created
4. You can manually create PR or merge as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Testing

Test files are located in the `tests/` directory:

```bash
# Test Jira connection and view tickets
python tests/test_jira_tickets.py

# Test Jira comment functionality  
python tests/test_jira_comments.py

# Test branch naming for Jira mode
python tests/test_branch_naming.py

# Debug environment variable loading
python tests/debug_env_loading.py

# Test basic Jira connection
python tests/test_jira_connection.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the GitHub Issues page
2. Review the error messages in verbose mode
3. Ensure your API keys are correctly configured
4. Verify repository permissions

## Jira Workflow

### Setting Up Jira Tickets for AI Processing

1. **Create a Jira Ticket**: Create any type of ticket (Story, Task, Bug, etc.)
2. **Add UseAI Label**: Add the label "UseAI" to the ticket
3. **Link to Epic**: Associate the ticket with an Epic (the Epic name will be used as the repository name)
4. **Add Description**: Provide a clear title and description of what needs to be done
5. **Run AI Processing**: Use `python main.py --jira-mode` to process all UseAI tickets

### Example Jira Ticket Setup

```
Title: Add input validation to user registration form
Epic: user-management-system
Labels: UseAI, frontend, validation
Description: 
Add client-side and server-side validation to the user registration form.
Requirements:
- Email format validation
- Password strength requirements
- Confirm password matching
- Display appropriate error messages
```

This will automatically:
- Use "user-management-system" as the repository name
- Create the objective from title + description
- Process the ticket and create a pull request
- Add a comment to the Jira ticket with the PR link
- Create bidirectional linking between Jira and GitHub

## Future Enhancements

- [x] JIRA integration for ticket management
- [ ] Support for creating new files
- [ ] Multi-repository operations
- [ ] Custom tool plugins
- [ ] Web interface
- [ ] Batch processing capabilities
- [ ] Draft PR support
- [ ] Merge conflict resolution
- [ ] Jira ticket status updates
- [ ] Custom Jira field mapping 