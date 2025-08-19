

# AI Coding Agent

![AI Coding Agent](https://img.shields.io/badge/AI-Coding_Agent-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

An intelligent AI-powered coding assistant that implements the **Perceive → Reason → Act → Learn** cycle to help developers with coding tasks. This system integrates multiple LLM providers, specialized tools, safety mechanisms, and adaptive learning capabilities.

## 🌟 Features

### Core Functionality
- **Agent Loop**: Implements complete Perceive → Reason → Act → Learn cycle
- **Natural Language Processing**: Understands and executes complex user commands
- **Multi-Provider LLM Support**: OpenAI, Groq, and Ollama with automatic fallbacks
- **21 Integrated Tools**: File operations, Git commands, code analysis, testing, and more

### Safety Mechanisms
- **Preview System**: Shows changes before execution
- **Approval Workflow**: Requires user confirmation for destructive operations
- **Backup Capabilities**: Automatic backup creation before modifications
- **Rollback Options**: Restore previous states when needed

### Learning System
- **Preference Learning**: Remembers user preferences
- **Pattern Recognition**: Identifies common patterns in requests
- **Adaptive Behavior**: Adjusts responses based on feedback
- **Session Tracking**: Maintains context across interactions

### User Interface
- **Rich Terminal Interface**: Professional CLI with syntax highlighting
- **Progress Indicators**: Visual feedback for long operations
- **Formatted Output**: Tables, code blocks, and structured data
- **Error Handling**: Clear error messages with recovery suggestions

### ♦️ Architecture

<img width="500" height="700" alt="image" src="https://github.com/user-attachments/assets/8f36f139-1abb-4e64-b965-7beeb34e279d" />

## 📒 Architecture Overview
# AI Coding Agent - Architecture Overview

## System Flow Diagram

The AI Coding Agent follows a cyclic process that enables it to assist with coding tasks effectively. The architecture is designed around the Perceive-Reason-Act-Learn loop, with integrated safety mechanisms and learning capabilities.

### Components and Flow

1. **User Input**: The user provides a command or request in natural language.
2. **Perceive**: The agent gathers the current state of the system, including file contents, git status, and relevant context.
3. **Reason**: The agent uses an LLM to analyze the user's request and the current state to formulate a plan of action.
4. **LLM Provider**: The agent selects an LLM provider (Primary or Fallback) to process the reasoning step. This ensures reliability even if the primary provider is unavailable.
5. **Process Plan**: The LLM generates a structured plan, breaking down the request into executable steps.
6. **Select Tools**: Based on the plan, the agent selects the appropriate tools from its registry (e.g., file operations, git commands, code analysis).
7. **Preview & Approve**: Before executing potentially destructive operations, the agent previews the changes and requests user approval. This is a critical safety feature.
8. **Execute Tools**: The agent executes the selected tools to perform the planned actions (e.g., creating files, running tests, committing changes).
9. **Display Results**: The results of the tool execution are displayed to the user in a formatted and readable way, including syntax highlighting for code.
10. **Learn & Adapt**: The agent learns from the interaction, updating its understanding of user preferences and common patterns.
11. **Update Memory**: The learning outcomes are stored in the agent's memory for future reference, enabling continuous improvement.

### Component Classes

- **Core Components (Blue)**: User Input, Perceive, Reason, Display Results. These form the essential loop of the agent.
- **LLM Components (Green)**: LLM Provider, Process Plan, Fallback Mode. These handle the language understanding and generation.
- **Tool Components (Orange)**: Select Tools, Preview & Approve, Execute Tools. These manage the execution of actions with safety checks.
- **Learning Components (Purple)**: Learn & Adapt, Update Memory. These enable the agent to improve over time.

### Key Features

- **Multi-Provider LLM Support**: The agent can switch between primary and fallback LLM providers to ensure reliability.
- **Safety Mechanisms**: The preview and approval step prevents unintended changes to the codebase.
- **Learning System**: The agent adapts to user preferences and patterns, providing more personalized assistance over time.
- **Rich Output**: Results are displayed with formatting and syntax highlighting for better readability.

This architecture ensures that the AI Coding Agent is both powerful and safe, making it a valuable tool for developers.


## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Git
- API keys for at least one LLM provider (OpenAI, Groq, or Ollama)

### Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/santhoshkrishnan30/AI-Coding-Agent.git
cd AI-Coding-Agent
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env file with your API keys and preferences
```

5. Run the agent
```bash
python src/main_enhanced.py
```

## 📂 Project Structure

```
AI-CODING-AGENT/
├── .agent_backups/       # Backup files created by the agent
├── docs/                 # Documentation
├── examples/             # Example scripts and commands
├── src/                  # Source code
│   ├── agent/            # Core agent implementation
│   ├── config/              # LLM provider integrations
│   ├── tools/            # Tool implementations
│   ├── memory/           # Memory and state management
│   ├── interface/               # Terminal interface
│   └── main.py
|   └── main_enhanced.py         # Entry point
├── verification/         # Verification and testing files
├── .env                  # Environment variables
├── config.yaml           # Configuration settings
└── requirements.txt      # Python dependencies
```

## 💻 Usage Examples

### Basic File Operations
```bash
$ agent "What does this authentication module do?"
$ agent "Add error handling to the login function"
$ agent "Find all TODO comments in the codebase"
```

### Git Operations
```bash
$ agent "Review my recent changes and suggest improvements"
$ agent "Create a commit with a good message for these changes"
$ agent "Show me what changed between feature branch and main"
```

### Code Analysis and Testing
```bash
$ agent "Run the tests and fix any failures you find"
$ agent "Check if this API endpoint has proper validation"
$ agent "Refactor this function to be more readable"
```

### Complex Workflows
```bash
$ agent "Help me add a new user registration endpoint"
$ agent "Update the database schema and migrate existing data"
$ agent "Deploy this feature to staging environment"
```

## 🔒 Safety Framework

The agent implements several safety mechanisms to ensure it operates responsibly:

1. **Preview Before Action**
   - Shows exactly what will change before making modifications
   - Provides clear summaries of planned operations
   - Allows users to approve, modify, or reject suggestions

2. **Reversible Operations**
   - Maintains operation history for rollback capability
   - Uses git for change tracking
   - Creates automatic backups before destructive operations

3. **Graduated Autonomy**
   - Starts with high user involvement, reduces over time
   - Learns user preferences and trust patterns
   - Provides granular control over agent permissions

## 🔧 Configuration

The agent can be configured through the `config.yaml` file:

```yaml
# Example configuration
agent:
  name: "AI Coding Agent"
  mode: "interactive"  # interactive, autonomous, or safe
  
llm:
  primary_provider: "openai"
  fallback_providers: ["groq", "ollama"]
  
tools:
  enabled:
    - file_operations
    - git_tools
    - code_analysis
    - testing
  
safety:
  approval_required: true
  backup_before_write: true
  rollback_enabled: true
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- OpenAI for their API services
- Groq for fast inference capabilities
- Ollama for local model support
- All contributors and testers who helped improve this tool
