import os
import subprocess
import json
import logging
from anthropic import Anthropic
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, api_key, log_file=None):
        self.client = Anthropic(api_key=api_key)
        self.conversation_history = []
        
        # Get model from environment or use default
        self.model = os.getenv("AI_MODEL", "claude-sonnet-4-5")
        logger.info(f"Using model: {self.model}")
        
        # Load system prompt from file or use default
        prompt_file = Path(__file__).parent / "system-prompt.txt"
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                self.system_prompt = f.read()
            logger.info(f"Loaded system prompt from: {prompt_file}")
        else:
            self.system_prompt = self._get_default_prompt()
            # Create the file with default prompt
            with open(prompt_file, 'w') as f:
                f.write(self.system_prompt)
            logger.info(f"Created default system prompt at: {prompt_file}")
        
        # Set up conversation log file
        if log_file is None:
            log_dir = Path.home() / "ai-agent-logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write header to log file
        self._log_to_file(f"=== AI Agent Conversation Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        self.tools = [
            {
                "name": "run_bash",
                "description": "Execute a bash command on the server. Returns stdout, stderr, and exit code. Use this to run any Linux command, install packages, manage processes, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file. Returns the full file content as text.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute path to the file"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Create or overwrite a file with content. Creates parent directories if needed.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_directory",
                "description": "List files and directories in a given path with details (size, permissions, modified time).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to list (defaults to current directory)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search_files",
                "description": "Search for files by name pattern or search for text content within files.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory to search in"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (filename or text content)"
                        },
                        "search_type": {
                            "type": "string",
                            "description": "Either 'filename' or 'content'",
                            "enum": ["filename", "content"]
                        }
                    },
                    "required": ["path", "pattern", "search_type"]
                }
            }
        ]
    
    def _log_to_file(self, message):
        """Write a message to the conversation log file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    
    def execute_tool(self, tool_name, tool_input):
        """Execute a tool and return the result"""
        try:
            if tool_name == "run_bash":
                logger.info(f"Executing command: {tool_input['command']}")
                
                # Set up proper environment with full PATH
                env = os.environ.copy()
                env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
                
                result = subprocess.run(
                    tool_input["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=os.path.expanduser("~"),
                    env=env
                )
                output = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                }
                self._log_to_file(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {json.dumps(output)}\n")
                return output
            
            elif tool_name == "read_file":
                path = os.path.expanduser(tool_input["path"])
                logger.info(f"Reading file: {path}")
                with open(path, 'r') as f:
                    content = f.read()
                output = {"content": content, "path": path}
                self._log_to_file(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"path\": \"{path}\", \"content_length\": {len(content)}}}\n")
                return output
            
            elif tool_name == "write_file":
                path = os.path.expanduser(tool_input["path"])
                logger.info(f"Writing file: {path}")
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
                with open(path, 'w') as f:
                    f.write(tool_input["content"])
                output = {"success": True, "path": path}
                self._log_to_file(f"TOOL: {tool_name}\n  Input: {{\"path\": \"{path}\", \"content_length\": {len(tool_input['content'])}}}\n  Result: {json.dumps(output)}\n")
                return output
            
            elif tool_name == "list_directory":
                path = os.path.expanduser(tool_input["path"])
                logger.info(f"Listing directory: {path}")
                result = subprocess.run(
                    ["ls", "-lah", path],
                    capture_output=True,
                    text=True
                )
                output = {"listing": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
                self._log_to_file(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"exit_code\": {result.returncode}, \"items\": {len(result.stdout.splitlines())}}}\n")
                return output
            
            elif tool_name == "search_files":
                path = os.path.expanduser(tool_input["path"])
                pattern = tool_input["pattern"]
                search_type = tool_input["search_type"]
                
                if search_type == "filename":
                    cmd = f"find {path} -name '*{pattern}*' 2>/dev/null"
                else:
                    cmd = f"grep -r '{pattern}' {path} 2>/dev/null"
                
                logger.info(f"Searching: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                output = {"results": result.stdout}
                self._log_to_file(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"matches\": {len(result.stdout.splitlines())}}}\n")
                return output
        
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 60 seconds"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    def chat(self, user_message):
        """Main agent loop"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"User message: {user_message}")
        
        # Log user message
        self._log_to_file(f"\n[{timestamp}] USER: {user_message}\n")
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response_text = ""
        
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=self.tools,
                messages=self.conversation_history,
                system=self.system_prompt
            )
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                
                if response_text:
                    logger.info(f"Agent response: {response_text}")
                    self._log_to_file(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AGENT: {response_text}\n")
                
                return response_text if response_text else "Task completed"
            
            elif response.stop_reason == "tool_use":
                tool_results = []
                
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        
                        logger.info(f"Executing tool: {tool_name}")
                        self._log_to_file(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TOOL: {tool_name}\n")
                        self._log_to_file(f"  Input: {json.dumps(tool_input, indent=2)}\n")
                        
                        result = self.execute_tool(tool_name, tool_input)
                        
                        self._log_to_file(f"  Result: {json.dumps(result, indent=2)}\n")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps(result)
                        })
                
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation reset")
        self._log_to_file(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === CONVERSATION RESET ===\n")


if __name__ == "__main__":
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY='your-key-here'")
        exit(1)
    
    agent = AIAgent(api_key)
    
    print("=" * 60)
    print("AI AGENT STARTED")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your message to interact with the agent")
    print("  - Type 'exit' or 'quit' to stop")
    print("  - Type 'reset' to clear conversation history")
    print(f"\nLogs: {agent.log_file}")
    print("\n" + "=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("Conversation reset")
                continue
            
            if not user_input.strip():
                continue
            
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\nError: {e}")
