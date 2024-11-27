import os
import json
import re
import shutil
from anthropic import Anthropic, APIStatusError, APIError
from tavily import TavilyClient
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import glob
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize the Anthropic client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
client = Anthropic(api_key=anthropic_api_key)

# Initialize the Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables")
tavily = TavilyClient(api_key=tavily_api_key)

console = Console()

# Token tracking
token_usage = {"input": 0, "output": 0}
MAX_CONTEXT_TOKENS = 200000

# Conversation and project management
conversation_history = []
file_contents = {}
current_project = None
project_structure = {}

SYSTEM_PROMPT = """
You are Claude, an AI assistant powered by Anthropic's Claude-3.5-Sonnet model, specialized in software development and product design. Your capabilities include:

<capabilities>
1. Creating and managing project structures
2. Writing, debugging, and improving code across multiple languages
3. Providing architectural insights and applying design patterns
4. Product design and user experience recommendations
5. Technical documentation and specifications
6. Performance optimization and best practices
7. Security considerations and implementation
8. Code review and improvement suggestions
9. Real-time information gathering through web search
</capabilities>

<file_operations_format>
CRITICAL: ALL code modifications MUST be wrapped in proper file operation commands. Raw code snippets are NOT allowed.
When you need to perform file operations, use the following format:

For creating files:
```file:create
path: relative/path/to/file.ext
content:
Your file content here
```

For editing files:
```file:edit
path: relative/path/to/file.ext
content:
Updated file content here
```

For reading files:
```file:read
path: relative/path/to/file.ext
```

For deleting files:
```file:delete
path: relative/path/to/file.ext
```
</file_operations_format>

<file_operations>
You can perform the following file operations:
1. Create new files and directories
2. Read existing file contents
3. Edit and update files
4. Delete files when necessary
5. Manage project structure
6. Track file changes and versions
</file_operations>

<project_management>
For project management:
1. Maintain clear project structure
2. Track file dependencies
3. Ensure consistent naming conventions
4. Manage configuration files
5. Handle resource files
6. Organize source code
7. Maintain documentation
</project_management>

<code_review_process>
When reviewing code, follow these steps:
1. Understand the context and purpose of the code
2. Check for clarity and readability
3. Identify potential bugs or errors
4. Suggest optimizations or improvements
5. Ensure adherence to best practices and coding standards
6. Consider security implications
7. Provide constructive feedback with explanations
</code_review_process>

<design_principles>
Follow these design principles:
1. User-centered design
2. Clear information architecture
3. Consistent interaction patterns
4. Accessibility considerations
5. Performance optimization
6. Scalable architecture
7. Security by design
</design_principles>

<search_guidelines>
When using search capabilities:
1. Search for up-to-date information about technologies and best practices
2. Verify compatibility and version information
3. Look for recent security advisories or known issues
4. Research market trends and user preferences
5. Find relevant documentation and examples
6. Gather competitive analysis data
</search_guidelines>

Always strive for clarity, efficiency, and best practices in your responses. Maintain project context and file consistency throughout the conversation.

IMPORTANT RULES:
- NEVER show raw code snippets outside of file operation commands
- ALWAYS use the exact format shown above
- Code changes MUST be executed through file operations
- Include the full file content in create/edit operations
- No partial code snippets or examples without proper file operations
- When suggesting code changes, always use file:create for new files or file:edit for existing files
- Do not truncate or abbreviate file content with "..." or similar
- All file paths must be relative to the project root
"""


class ChatHistoryManager:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.history_dir = os.path.join(base_dir, "chat_history")
        os.makedirs(self.history_dir, exist_ok=True)

    def save_chat(
        self, project_name: Optional[str], conversation_history: List[Dict]
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if project_name:
            project_dir = os.path.join(self.history_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            filename = f"chat_{timestamp}.json"
            filepath = os.path.join(project_dir, filename)
        else:
            filename = f"chat_{timestamp}.json"
            filepath = os.path.join(self.history_dir, filename)

        chat_data = {
            "project": project_name,
            "timestamp": timestamp,
            "history": conversation_history,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2)

        md_filename = filepath.replace(".json", ".md")
        self._save_markdown_version(chat_data, md_filename)
        return filepath

    def _save_markdown_version(self, chat_data: Dict, filepath: str) -> None:
        content = "# Claude Design & Development Chat Log\n\n"
        content += f"Project: {chat_data['project'] or 'None'}\n"
        content += f"Date: {chat_data['timestamp']}\n\n"

        for message in chat_data["history"]:
            if message["role"] == "user":
                content += f"## User\n\n{message['content']}\n\n"
            else:
                content += f"## Claude\n\n{message['content']}\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def load_recent_chat(
        self, project_name: Optional[str] = None
    ) -> List[Dict]:
        if project_name:
            project_dir = os.path.join(self.history_dir, project_name)
            if not os.path.exists(project_dir):
                return []
            pattern = os.path.join(project_dir, "chat_*.json")
        else:
            pattern = os.path.join(self.history_dir, "chat_*.json")

        files = glob.glob(pattern)
        if not files:
            return []

        latest_file = max(files, key=os.path.getctime)

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                chat_data = json.load(f)
            return chat_data["history"]
        except Exception as e:
            logging.error(f"Error loading chat history: {str(e)}")
            return []

    def list_chat_history(
        self, project_name: Optional[str] = None
    ) -> List[Dict]:
        if project_name:
            project_dir = os.path.join(self.history_dir, project_name)
            if not os.path.exists(project_dir):
                return []
            pattern = os.path.join(project_dir, "chat_*.json")
        else:
            pattern = os.path.join(self.history_dir, "chat_*.json")

        files = glob.glob(pattern)
        history_files = []

        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
                history_files.append(
                    {
                        "file": os.path.basename(file),
                        "project": chat_data["project"],
                        "timestamp": chat_data["timestamp"],
                        "messages": len(chat_data["history"]),
                    }
                )
            except Exception as e:
                logging.error(f"Error reading chat file {file}: {str(e)}")

        return sorted(history_files, key=lambda x: x["timestamp"], reverse=True)


class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.project_root = None
        self.file_contents = {}
        self.project_structure = {}
        self.chat_history_manager = ChatHistoryManager()

    def init_project(self, project_name: str) -> str:
        self.current_project = project_name
        self.project_root = os.path.join(os.getcwd(), project_name)
        os.makedirs(self.project_root, exist_ok=True)
        self.scan_project()

        global conversation_history
        loaded_history = self.chat_history_manager.load_recent_chat(
            project_name
        )
        if loaded_history:
            conversation_history = loaded_history
            return f"Project '{project_name}' initialized at {self.project_root} with previous chat history loaded"
        return f"Project '{project_name}' initialized at {self.project_root}"

    def scan_project(self) -> None:
        """Scan the project directory and update the structure."""
        self.project_structure = {}
        if self.project_root and os.path.exists(self.project_root):
            for root, dirs, files in os.walk(self.project_root):
                rel_path = os.path.relpath(root, self.project_root)
                if rel_path == ".":
                    self.project_structure["/"] = {"dirs": dirs, "files": files}
                else:
                    self.project_structure[rel_path] = {
                        "dirs": dirs,
                        "files": files,
                    }

    async def create_file(self, path: str, content: str) -> str:
        """Create a new file with the given content."""
        try:
            if not self.current_project:
                raise ValueError("No active project selected")

            # Sanitize the path
            path = os.path.normpath(path)
            if path.startswith(("/", "..")):
                raise ValueError(
                    "Invalid path: must be relative to project root"
                )

            full_path = os.path.join(self.project_root, path)

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write the file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Update internal tracking
            self.file_contents[path] = content
            self.scan_project()

            return f"✓ File created successfully: {path}"

        except Exception as e:
            logging.error(
                f"Error creating file {path}: {str(e)}", exc_info=True
            )
            raise

    async def edit_file(self, path: str, content: str) -> str:
        """Edit an existing file with new content."""
        try:
            if not self.current_project:
                raise ValueError("No active project selected")

            # Sanitize the path
            path = os.path.normpath(path)
            if path.startswith(("/", "..")):
                raise ValueError(
                    "Invalid path: must be relative to project root"
                )

            full_path = os.path.join(self.project_root, path)

            # Check if file exists
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File not found: {path}")

            # Write the updated content
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Update internal tracking
            self.file_contents[path] = content

            return f"✓ File updated successfully: {path}"

        except Exception as e:
            logging.error(f"Error editing file {path}: {str(e)}", exc_info=True)
            raise

    async def read_file(self, path: str) -> str:
        """Read the content of a file."""
        try:
            if path in self.file_contents:
                return self.file_contents[path]

            full_path = os.path.join(self.project_root, path)
            with open(full_path, "r") as f:
                content = f.read()

            self.file_contents[path] = content
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    async def delete_file(self, path: str) -> str:
        """Delete a file from the project."""
        try:
            full_path = os.path.join(self.project_root, path)
            os.remove(full_path)

            if path in self.file_contents:
                del self.file_contents[path]

            self.scan_project()
            return f"File deleted: {path}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    def get_project_files(self) -> List[str]:
        """Get a list of all files in the project."""
        files = []
        for root, _, filenames in os.walk(self.project_root):
            for filename in filenames:
                rel_path = os.path.relpath(
                    os.path.join(root, filename), self.project_root
                )
                files.append(rel_path)
        return files

    def display_project_structure(self) -> None:
        """Display the current project structure."""
        if not self.current_project:
            console.print("No active project.", style="yellow")
            return

        table = Table(title=f"Project Structure: {self.current_project}")
        table.add_column("Path", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Size", style="blue")

        for root, _, files in os.walk(self.project_root):
            rel_path = os.path.relpath(root, self.project_root)
            if rel_path != ".":
                table.add_row(rel_path, "Directory", "")
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                table.add_row(
                    os.path.join(rel_path, file), "File", f"{size:,} bytes"
                )

        console.print(table)


# Initialize project manager
project_manager = ProjectManager()


async def perform_search(query: str) -> Optional[Dict]:
    """Perform a web search using Tavily."""
    try:
        console.print(Panel(f"Searching for: {query}", style="cyan"))
        results = await asyncio.to_thread(
            tavily.qna_search, query=query, search_depth="advanced"
        )
        return results
    except Exception as e:
        console.print(f"Search error: {str(e)}", style="bold red")
        return None


def should_perform_search(text: str) -> bool:
    """Determine if a search would be helpful."""
    search_triggers = [
        "current",
        "latest",
        "recent",
        "new",
        "update",
        "trend",
        "compare",
        "versus",
        "vs",
        "difference between",
        "how to",
        "best practice",
        "example of",
        "tutorial",
    ]
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in search_triggers)


async def retry_with_backoff(func, *args, max_retries=5, initial_delay=1):
    """Execute a function with exponential backoff retry logic."""
    delay = initial_delay
    last_exception = Exception("No retries attempted")

    for attempt in range(max_retries):
        try:
            # Run the synchronous function in a thread pool
            result = await asyncio.to_thread(func, *args)
            return result
        except APIStatusError as e:
            last_exception = e
            if e.status_code in [
                429,
                500,
                502,
                503,
                504,
                529,
            ]:  # Retryable errors
                wait_time = delay * (2**attempt)  # Exponential backoff
                console.print(
                    f"Server error {e.status_code} (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time:.2f} seconds...",
                    style="yellow",
                )
                await asyncio.sleep(wait_time)
                continue
            raise  # Re-raise if it's not a retryable error

    raise last_exception


async def chat_with_claude(user_input: str):
    """Main function to interact with Claude with modern API features."""
    if not isinstance(user_input, str):
        raise ValueError("user_input must be a string")

    try:
        # Add project context to the system prompt
        project_context = ""
        if project_manager.current_project:
            project_context = "\n\nCurrent Project Context:\n"
            project_context += f"Project: {project_manager.current_project}\n"
            project_context += "Files in context:\n"
            for path, content in project_manager.file_contents.items():
                project_context += f"- {path}\n"

        full_system_prompt = SYSTEM_PROMPT + project_context

        # Prepare search results if needed
        if should_perform_search(user_input):
            search_results = await perform_search(user_input)
            if search_results:
                user_input = f"{user_input}\n\nRelevant information:\n{json.dumps(search_results, indent=2)}"

        # Prepare conversation messages
        message_history = []
        for msg in conversation_history:
            message_history.append(
                {"role": msg["role"], "content": msg["content"]}
            )

        # Add current user message
        message_history.append({"role": "user", "content": user_input})

        # Create the API call function
        def make_api_call():
            return client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                messages=message_history,
                system=full_system_prompt,
                temperature=0.7,
                extra_headers={
                    "anthropic-beta": "prompt-caching-2024-07-31",
                    "anthropic-version": "2023-06-01",
                },
            )

        # Execute API call with retry logic
        response = await retry_with_backoff(make_api_call)

        # Update token usage
        token_usage["input"] += response.usage.input_tokens
        token_usage["output"] += response.usage.output_tokens

        # Extract response content
        assistant_response = response.content[0].text

        # Process any file operations in the response
        assistant_response = await process_file_operations(assistant_response)

        # Format code blocks in the response
        formatted_response = format_code_blocks(assistant_response)

        # Display response
        console.print(
            Panel(
                Markdown(formatted_response),
                title=f"Claude's Response (Model: {response.model})",
                border_style="blue",
                expand=False,
            )
        )

        # Update conversation history
        conversation_history.extend(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_response},
            ]
        )

        return assistant_response

    except APIStatusError as e:
        error_msg = ""
        if e.status_code == 429:
            error_msg = (
                "Rate limit exceeded. Please wait a moment before trying again."
            )
        elif e.status_code == 529:
            error_msg = "The server is currently overloaded. Please try again in a few moments."
        elif e.status_code in [500, 502, 503, 504]:
            error_msg = "Server error. Please try again later."
        else:
            error_msg = f"API Error ({e.status_code}): {str(e)}"

        console.print(f"Error in chat: {error_msg}", style="bold red")
        return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        console.print(f"Error in chat: {error_msg}", style="bold red")
        logging.error(f"Unexpected error in chat: {str(e)}", exc_info=True)
        return f"Error: {error_msg}"


async def process_file_operations(response: str) -> str:
    """Process any file operations in Claude's response."""
    # Updated pattern to match the new format
    file_op_patterns = {
        "create": r"```file:create\npath: (.+?)\ncontent:\n(.*?)```",
        "edit": r"```file:edit\npath: (.+?)\ncontent:\n(.*?)```",
        "read": r"```file:read\npath: (.+?)```",
        "delete": r"```file:delete\npath: (.+?)```",
    }

    modified_response = response

    for op_type, pattern in file_op_patterns.items():
        matches = re.finditer(pattern, response, re.DOTALL)
        for match in matches:
            try:
                path = match.group(1).strip()

                if op_type in ["create", "edit"]:
                    content = match.group(2).strip()
                    if op_type == "create":
                        result = await project_manager.create_file(
                            path, content
                        )
                    else:
                        result = await project_manager.edit_file(path, content)
                elif op_type == "read":
                    result = await project_manager.read_file(path)
                else:  # delete
                    result = await project_manager.delete_file(path)

                # Replace the operation block with the result
                op_block = match.group(0)
                result_block = (
                    f"\n### File Operation Result ({op_type}):\n{result}\n"
                )
                modified_response = modified_response.replace(
                    op_block, result_block
                )

                # Log the operation
                logging.info(
                    f"File operation {op_type} completed for path: {path}"
                )

            except Exception as e:
                error_msg = (
                    f"\n### Error in file operation ({op_type}):\n{str(e)}\n"
                )
                modified_response = modified_response.replace(
                    match.group(0), error_msg
                )
                logging.error(
                    f"File operation error ({op_type}): {str(e)}", exc_info=True
                )

    return modified_response


def display_token_usage():
    """Display current token usage statistics and estimated costs."""
    from rich.table import Table
    from rich.panel import Panel
    from rich.box import ROUNDED

    table = Table(box=ROUNDED)
    table.add_column("Type", style="cyan")
    table.add_column("Tokens", style="magenta")
    table.add_column(f"% of Context ({MAX_CONTEXT_TOKENS:,})", style="yellow")
    table.add_column("Cost ($)", style="red")

    # Claude-3 Sonnet pricing per million tokens
    COSTS = {
        "input": 3.00,  # $0.003 per 1k tokens
        "output": 15.00,  # $0.015 per 1k tokens
    }

    total_tokens = token_usage["input"] + token_usage["output"]
    context_percentage = (total_tokens / MAX_CONTEXT_TOKENS) * 100

    # Calculate costs
    input_cost = (token_usage["input"] / 1_000_000) * COSTS["input"]
    output_cost = (token_usage["output"] / 1_000_000) * COSTS["output"]
    total_cost = input_cost + output_cost

    # Add rows for input, output, and total
    table.add_row(
        "Input",
        f"{token_usage['input']:,}",
        f"{(token_usage['input'] / MAX_CONTEXT_TOKENS) * 100:.2f}%",
        f"${input_cost:.4f}",
    )

    table.add_row(
        "Output",
        f"{token_usage['output']:,}",
        f"{(token_usage['output'] / MAX_CONTEXT_TOKENS) * 100:.2f}%",
        f"${output_cost:.4f}",
    )

    table.add_row(
        "Total",
        f"{total_tokens:,}",
        f"{context_percentage:.2f}%",
        f"${total_cost:.4f}",
        style="bold",
    )

    console.print(
        Panel(table, title="Token Usage Statistics", border_style="blue")
    )


def format_code_blocks(text: str) -> str:
    """Format code blocks with syntax highlighting."""

    def replace_code_block(match):
        language = match.group(1) or ""
        code = match.group(2)
        return f"```{language}\n{code}\n```"

    pattern = r"```(\w+)?\n(.*?)```"
    return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)


def save_chat():
    try:
        filepath = project_manager.chat_history_manager.save_chat(
            project_manager.current_project, conversation_history
        )
        return f"Chat saved to: {filepath}"
    except Exception as e:
        logging.error(f"Error saving chat: {str(e)}")
        return f"Error saving chat: {str(e)}"


async def handle_chat_command(command: str):
    parts = command.split()
    if not parts:
        console.print("Invalid chat command", style="bold red")
        return

    action = parts[0].lower()

    if action == "list":
        history_files = project_manager.chat_history_manager.list_chat_history(
            project_manager.current_project
        )
        if history_files:
            table = Table(title="Chat History")
            table.add_column("Date", style="cyan")
            table.add_column("Project", style="blue")
            table.add_column("Messages", style="green")
            table.add_column("File", style="yellow")

            for entry in history_files:
                table.add_row(
                    entry["timestamp"],
                    entry["project"] or "None",
                    str(entry["messages"]),
                    entry["file"],
                )
            console.print(table)
        else:
            console.print("No chat history found", style="yellow")


async def main():
    console.print(
        Panel(
            "Welcome to Claude Project Terminal!\n\n"
            "Commands:\n"
            "- 'exit': End the conversation\n"
            "- 'save': Save chat history\n"
            "- 'clear': Clear conversation history\n"
            "- 'tokens': Display token usage\n"
            "- 'search <query>': Perform a direct web search\n"
            "- 'project new <name>': Create a new project\n"
            "- 'project switch <name>': Switch to an existing project\n"
            "- 'project list': List all projects\n"
            "- 'project structure': Show current project structure\n"
            "- 'file view <path>': View file contents\n"
            "- 'file list': List all files in current project\n"
            "- 'project backup': Create a backup of the current project\n",
            title="Welcome",
            style="bold green",
        )
    )

    session = PromptSession(
        style=Style.from_dict(
            {
                "prompt": "cyan bold",
            }
        )
    )

    while True:
        try:
            # Show current project in prompt if one is active
            prompt = f"{project_manager.current_project + ' > ' if project_manager.current_project else ''}You: "
            user_input = await session.prompt_async(prompt)

            if user_input.lower() == "exit":
                if project_manager.current_project:
                    # Create automatic backup before exit
                    await backup_project()
                console.print("Goodbye!", style="bold green")
                break

            elif user_input.lower() == "save":
                filename = save_chat()
                console.print(f"Chat saved to: {filename}", style="green")
                continue

            elif user_input.lower().startswith("chat "):
                await handle_chat_command(user_input[5:].strip())
                continue

            elif user_input.lower() == "clear":
                conversation_history.clear()
                console.print("Conversation history cleared", style="yellow")
                continue

            elif user_input.lower() == "tokens":
                display_token_usage()
                continue

            elif user_input.lower().startswith("project "):
                await handle_project_command(user_input[8:].strip())
                continue

            elif user_input.lower().startswith("file "):
                await handle_file_command(user_input[5:].strip())
                continue

            elif user_input.lower().startswith("search "):
                query = user_input[7:].strip()
                results = await perform_search(query)
                if results:
                    console.print(
                        Panel(
                            Markdown(json.dumps(results, indent=2)),
                            title="Search Results",
                            style="cyan",
                        )
                    )
                continue
            elif user_input.strip() == "":
                continue

            # Regular chat with Claude
            await chat_with_claude(user_input)
            display_token_usage()
        except EOFError:
            # Handle Ctrl+D gracefully
            console.print(
                "\nReceived EOF (Ctrl+D). Performing cleanup...", style="yellow"
            )
            if project_manager.current_project:
                await backup_project()
            console.print("Goodbye!", style="bold green")
            break
        except KeyboardInterrupt:
            console.print("\nOperation cancelled by user", style="yellow")
            continue
        except Exception as e:
            console.print(f"Error: {str(e)}", style="bold red")
            logging.error(f"Error in main loop: {str(e)}", exc_info=True)


async def handle_project_command(command: str):
    """Handle project-related commands."""
    parts = command.split()
    if not parts:
        console.print("Invalid project command", style="bold red")
        return

    action = parts[0].lower()

    if action == "new":
        if len(parts) < 2:
            console.print("Please specify a project name", style="bold red")
            return
        project_name = parts[1]
        result = project_manager.init_project(project_name)
        console.print(Panel(result, style="green"))

    elif action == "switch":
        if len(parts) < 2:
            console.print("Please specify a project name", style="bold red")
            return
        project_name = parts[1]
        if os.path.exists(os.path.join(os.getcwd(), project_name)):
            result = project_manager.init_project(project_name)
            console.print(Panel(result, style="green"))
        else:
            console.print(
                f"Project '{project_name}' not found", style="bold red"
            )

    elif action == "list":
        projects = [d for d in os.listdir() if os.path.isdir(d)]
        if projects:
            table = Table(title="Available Projects")
            table.add_column("Project Name", style="cyan")
            table.add_column("Status", style="green")

            for project in projects:
                status = (
                    "Active"
                    if project == project_manager.current_project
                    else "-"
                )
                table.add_row(project, status)

            console.print(table)
        else:
            console.print("No projects found", style="yellow")

    elif action == "structure":
        if not project_manager.current_project:
            console.print("No active project", style="bold red")
            return
        project_manager.display_project_structure()

    elif action == "backup":
        if not project_manager.current_project:
            console.print("No active project to backup", style="bold red")
            return
        await backup_project()

    else:
        console.print(f"Unknown project command: {action}", style="bold red")


async def handle_file_command(command: str):
    """Handle file-related commands."""
    if not project_manager.current_project:
        console.print("No active project", style="bold red")
        return

    parts = command.split()
    if not parts:
        console.print("Invalid file command", style="bold red")
        return

    action = parts[0].lower()

    if action == "view":
        if len(parts) < 2:
            console.print("Please specify a file path", style="bold red")
            return
        file_path = " ".join(parts[1:])
        content = await project_manager.read_file(file_path)

        if content.startswith("Error"):
            console.print(content, style="bold red")
        else:
            syntax = Syntax(content, guess_lexer=True)
            console.print(Panel(syntax, title=file_path, border_style="blue"))

    elif action == "list":
        files = project_manager.get_project_files()
        if files:
            table = Table(title="Project Files")
            table.add_column("Path", style="cyan")
            table.add_column("Size", style="blue")

            for file in files:
                full_path = os.path.join(project_manager.project_root, file)
                size = os.path.getsize(full_path)
                table.add_row(file, f"{size:,} bytes")

            console.print(table)
        else:
            console.print("No files in project", style="yellow")

    else:
        console.print(f"Unknown file command: {action}", style="bold red")


async def backup_project():
    """Create a backup of the current project."""
    if not project_manager.current_project:
        return "No active project to backup"

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_manager.current_project}_backup_{timestamp}"
        shutil.make_archive(backup_name, "zip", project_manager.project_root)
        console.print(
            f"Project backup created: {backup_name}.zip", style="green"
        )
        return f"Backup created: {backup_name}.zip"
    except Exception as e:
        console.print(f"Error creating backup: {str(e)}", style="bold red")
        return f"Error creating backup: {str(e)}"


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\nProgram terminated by user", style="bold red")
        if project_manager.current_project:
            asyncio.run(backup_project())
    except Exception as e:
        console.print(f"Fatal error: {str(e)}", style="bold red")
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        console.print("Program finished. Goodbye!", style="bold green")
