# Claude Project Terminal

A sophisticated terminal-based development environment that integrates Claude AI for software development, providing comprehensive project management, code generation, file operations, and intelligent conversation capabilities.

## Features

- 🤖 AI-powered code generation and review
- 📁 Project structure management and file operations
- 🔐 Secure secrets management
- 🔍 Intelligent web search integration
- 💬 Persistent chat history
- 🔄 Automatic project backups
- 📊 Token usage tracking

## Prerequisites

- Python 3.8+
- AWS account with appropriate permissions
- Anthropic API key
- Tavily API key

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/claude-project-terminal.git
cd claude-project-terminal
```

2. Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables (see `.env.example`)

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials.

## Usage

### Starting the Terminal

```bash
python dev.py
```

### Available Commands

- `exit`: End the conversation
- `save`: Save chat history
- `clear`: Clear conversation history
- `tokens`: Display token usage
- `search <query>`: Perform a direct web search
- `project new <name>`: Create a new project
- `project switch <name>`: Switch to an existing project
- `project list`: List all projects
- `project structure`: Show current project structure
- `file view <path>`: View file contents
- `file list`: List all files in current project
- `project backup`: Create a backup of the current project

### Project Management

Create a new project:
```bash
project new my-project
```

Switch between projects:
```bash
project switch my-project
```

### File Operations

View file contents:
```bash
file view path/to/file.txt
```

List project files:
```bash
file list
```

## Chat History

Chat histories are automatically saved and can be accessed later. Use the `save` command to manually save the current chat session.

## Token Usage

Monitor your token usage with the `tokens` command to track API consumption and costs.

## Backing Up Projects

Projects are automatically backed up on exit. You can also manually create backups:
```bash
project backup
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
