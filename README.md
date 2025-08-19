

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
