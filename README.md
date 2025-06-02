# AI Coding Assistant with GitHub Integration

An intelligent coding assistant that connects to GitHub repositories and uses OpenAI's language models to help complete programming tasks, fix bugs, and implement features.

## Features

- 🔗 **GitHub Integration**: Connects to any GitHub repository via the GitHub API
- 🤖 **AI-Powered**: Uses OpenAI's GPT models for intelligent code analysis and generation
- 🛠️ **Function Calling**: Uses OpenAI's native function calling for reliable tool execution
- 📁 **Repository Navigation**: Can explore directory structures and understand codebase organization
- ✏️ **File Editing**: Can read and modify files directly in GitHub repositories
- 🔄 **Iterative Approach**: Works through tasks step-by-step until completion
- 🌿 **Branch Safety**: Creates dedicated branches for all changes, protecting your main branch
- 🔀 **Pull Request Creation**: Automatically creates pull requests for review
- 🎫 **Jira Integration**: Webhook-based automation for Jira tickets (see [JIRA_INTEGRATION.md](JIRA_INTEGRATION.md))

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
   - `OPENAI_API_KEY`: Your OpenAI API key

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

## Usage

### Basic Usage

```bash
python main.py <repo-name> "<objective>"
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
- `--max-iterations`: Set maximum iterations (default: 20)
- `--github-token`: Override GitHub token from command line
- `--branch`: Custom branch name (default: auto-generated with timestamp)
- `--no-pr`: Skip creating a pull request when finished
- `--verbose`: Enable detailed output
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
- Default branch name: `ai-assistant-YYYYMMDD-HHMMSS`
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

The AI assistant has access to these tools:

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
                                │
                                ▼
                     ┌──────────────────┐
                     │   GitHub Repo    │
                     │  (Branch-based)  │
                     └──────────────────┘
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
2. Assistant creates branch: `ai-assistant-20241201-143022`
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the GitHub Issues page
2. Review the error messages in verbose mode
3. Ensure your API keys are correctly configured
4. Verify repository permissions

## Jira Integration

The AI Assistant now includes full Jira integration! See [JIRA_INTEGRATION.md](JIRA_INTEGRATION.md) for detailed setup instructions.

**Key Features:**
- Automatic processing of Jira tickets ≤ 5 story points
- Uses ticket description as AI objective
- Uses first label as repository name
- Posts status updates and PR links back to Jira
- Webhook-based real-time automation

## Future Enhancements

- [x] ~~JIRA integration for ticket management~~ ✅ **COMPLETED**
- [ ] Support for creating new files
- [ ] Multi-repository operations
- [ ] Custom tool plugins
- [ ] Web interface
- [ ] Batch processing capabilities
- [ ] Draft PR support
- [ ] Merge conflict resolution 