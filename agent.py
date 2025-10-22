import os
import subprocess
import json
import logging
from anthropic import Anthropic
from datetime import datetime
from pathlib import Path

# Optional OpenAI import for Ollama support
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Optional Gemini import
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, api_key, log_file=None):
        # Get configuration from environment
        self.model = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
        
        # Initialize clients based on provider
        self.client = None
        self.anthropic_client = None
        self.openai_client = None
        self.gemini_client = None
        
        if self.provider == "anthropic":
            if not self.anthropic_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            self.client = Anthropic(api_key=self.anthropic_key)
            self.anthropic_client = self.client
        
        elif self.provider == "ollama":
            if not HAS_OPENAI:
                raise ImportError("OpenAI library required for Ollama. Install: pip install openai")
            self.client = OpenAI(base_url=self.ollama_url, api_key="ollama")
            self.openai_client = self.client
        
        elif self.provider == "gemini":
            if not HAS_GEMINI:
                raise ImportError("Gemini library required. Install: pip install google-generativeai")
            if not self.gemini_key:
                raise ValueError("GEMINI_API_KEY not found")
            genai.configure(api_key=self.gemini_key)
            self.gemini_client = genai.GenerativeModel(self.model)
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Set up fallback clients if keys available
        if self.anthropic_key and not self.anthropic_client:
            self.anthropic_client = Anthropic(api_key=self.anthropic_key)
        
        logger.info(f"Using provider: {self.provider}")
        logger.info(f"Using model: {self.model}")
        
        self.conversation_history = []
        
        logger.info(f"Active provider: {self.provider}")
        logger.info(f"Using model: {self.model}")
        
        # Load system prompt
        prompt_file = Path(__file__).parent / "system-prompt.txt"
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                self.system_prompt = f.read()
            logger.info(f"Loaded system prompt from: {prompt_file}")
        else:
            self.system_prompt = self._get_default_prompt()
            with open(prompt_file, 'w') as f:
                f.write(self.system_prompt)
            logger.info(f"Created default system prompt at: {prompt_file}")
        
        # Set up logging structure
        if log_file is None:
            # Use project-relative logs directory
            project_root = Path(__file__).parent
            log_dir = project_root / "logs"
            transcripts_dir = log_dir / "transcripts"
            actions_dir = log_dir / "actions"
            
            # Create directories
            transcripts_dir.mkdir(parents=True, exist_ok=True)
            actions_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up log files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.transcript_file = transcripts_dir / f"conversation_{timestamp}.log"
            self.actions_file = actions_dir / f"actions_{timestamp}.log"
        else:
            # Legacy support for custom log file paths
            self.transcript_file = Path(log_file)
            self.actions_file = Path(log_file).parent / f"actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.transcript_file.parent.mkdir(parents=True, exist_ok=True)
            self.actions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write headers to log files
        self._log_to_transcript(f"=== AI Agent Conversation Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        self._log_to_transcript(f"Provider: {self.provider}, Model: {self.model}\n\n")
        
        self._log_to_actions(f"=== AI Agent Actions Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        self._log_to_actions(f"Provider: {self.provider}, Model: {self.model}\n\n")
        
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
    
    def _get_default_prompt(self):
        return """You are an AI assistant with full access to an Ubuntu Linux server. You have complete control and can execute any command.

**YOUR CAPABILITIES:**
- Execute any bash command using the run_bash tool
- Read and write files anywhere on the system
- Install packages with apt (use sudo)
- Manage services with systemctl (use sudo)
- Search for files and content
- Full sudo access (passwordless)

**YOUR ENVIRONMENT:**
- Ubuntu Linux server
- Full PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
- You have root-level access via sudo

**HOW TO OPERATE:**
1. User asks you to do something
2. You use tools to accomplish it
3. Always use sudo for system operations (apt, systemctl, etc.)
4. Always verify your actions worked by checking output and exit codes
5. Be helpful and proactive - if something fails, try to fix it
6. You are running on a real Ubuntu server with full capabilities

**YOUR RESPONSIBILITIES:**
- Execute commands directly - don't ask for permission
- Use sudo when needed (apt install, systemctl, etc.)
- When executing commands, check the output and exit codes to ensure success
- If something requires elevated privileges, use sudo
- Be direct and efficient

**IMPORTANT:** If a sudo command fails because passwordless sudo isn't configured, inform the user they need to configure passwordless sudo or run the command manually."""

    def _log_to_file(self, message):
        """Write a message to the conversation log file (legacy support)"""
        try:
            with open(self.transcript_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            logger.error(f"Failed to write to transcript file: {e}")
    
    def _log_to_transcript(self, message):
        """Write a message to the transcript log file"""
        try:
            with open(self.transcript_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            logger.error(f"Failed to write to transcript file: {e}")
    
    def _log_to_actions(self, message):
        """Write a message to the actions log file"""
        try:
            with open(self.actions_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            logger.error(f"Failed to write to actions file: {e}")
    
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
                # Log to transcript (conversation history)
                self._log_to_transcript(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {json.dumps(output)}\n")
                # Log to actions (command execution details)
                self._log_to_actions(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] COMMAND: {tool_input['command']}\n")
                self._log_to_actions(f"  Exit Code: {result.returncode}\n")
                if result.stdout:
                    self._log_to_actions(f"  Output: {result.stdout}\n")
                if result.stderr:
                    self._log_to_actions(f"  Error: {result.stderr}\n")
                self._log_to_actions(f"\n")
                return output
            
            elif tool_name == "read_file":
                path = os.path.expanduser(tool_input["path"])
                logger.info(f"Reading file: {path}")
                with open(path, 'r') as f:
                    content = f.read()
                output = {"content": content, "path": path}
                # Log to transcript
                self._log_to_transcript(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"path\": \"{path}\", \"content_length\": {len(content)}}}\n")
                # Log to actions
                self._log_to_actions(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FILE_READ: {path}\n")
                self._log_to_actions(f"  Content Length: {len(content)} characters\n\n")
                return output
            
            elif tool_name == "write_file":
                path = os.path.expanduser(tool_input["path"])
                logger.info(f"Writing file: {path}")
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
                with open(path, 'w') as f:
                    f.write(tool_input["content"])
                output = {"success": True, "path": path}
                # Log to transcript
                self._log_to_transcript(f"TOOL: {tool_name}\n  Input: {{\"path\": \"{path}\", \"content_length\": {len(tool_input['content'])}}}\n  Result: {json.dumps(output)}\n")
                # Log to actions
                self._log_to_actions(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FILE_WRITE: {path}\n")
                self._log_to_actions(f"  Content Length: {len(tool_input['content'])} characters\n")
                self._log_to_actions(f"  Success: {output['success']}\n\n")
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
                # Log to transcript
                self._log_to_transcript(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"exit_code\": {result.returncode}, \"items\": {len(result.stdout.splitlines())}}}\n")
                # Log to actions
                self._log_to_actions(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DIRECTORY_LIST: {path}\n")
                self._log_to_actions(f"  Items Found: {len(result.stdout.splitlines())}\n")
                self._log_to_actions(f"  Exit Code: {result.returncode}\n\n")
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
                # Log to transcript
                self._log_to_transcript(f"TOOL: {tool_name}\n  Input: {json.dumps(tool_input)}\n  Result: {{\"matches\": {len(result.stdout.splitlines())}}}\n")
                # Log to actions
                self._log_to_actions(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SEARCH: {search_type} for '{pattern}' in {path}\n")
                self._log_to_actions(f"  Command: {cmd}\n")
                self._log_to_actions(f"  Matches Found: {len(result.stdout.splitlines())}\n\n")
                return output
        
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 60 seconds"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    def chat(self, user_message):
        """Send a message and get response with tool execution"""
        self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] USER: {user_message}\n")
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Try primary provider with fallback
        try:
            if self.provider == "anthropic":
                return self._chat_anthropic()
            elif self.provider == "gemini":
                return self._chat_gemini()
            elif self.provider == "ollama":
                # Test Ollama connectivity
                try:
                    import requests
                    test_response = requests.get(
                        self.ollama_url.replace('/v1', '/api/tags'),
                        timeout=5
                    )
                    if test_response.status_code == 200:
                        logger.info(f"Using Ollama at {self.ollama_url}")
                        return self._chat_ollama()
                    else:
                        raise Exception(f"Ollama health check failed: {test_response.status_code}")
                except Exception as e:
                    logger.warning(f"Ollama connection failed: {e}")
                    if self.anthropic_client:
                        logger.info("Falling back to Anthropic")
                        return self._chat_anthropic()
                    else:
                        raise Exception(f"Ollama unavailable and no Anthropic fallback: {e}")
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
                
        except Exception as e:
            # Last resort fallback
            if self.anthropic_client and self.provider != "anthropic":
                logger.error(f"Primary provider failed: {e}")
                logger.info("Attempting Anthropic fallback")
                return self._chat_anthropic()
            else:
                raise
    
    def _chat_anthropic(self):
        """Chat using Anthropic API"""
        response_text = ""
        
        while True:
            response = self.anthropic_client.messages.create(
                model=self.model if "claude" in self.model else "claude-sonnet-4-5",
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
                    logger.info(f"Agent response: {response_text[:100]}...")
                    self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AGENT: {response_text}\n")
                
                return response_text if response_text else "Task completed"
            
            elif response.stop_reason == "tool_use":
                tool_results = []
                
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        
                        logger.info(f"Executing tool: {tool_name}")
                        self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TOOL: {tool_name}\n")
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
    
    def _chat_gemini(self):
        """Chat using Gemini API"""
        try:
            # Convert conversation history to Gemini format
            # Gemini doesn't support tools in the same way, so we'll use a simpler approach
            conversation_text = self.system_prompt + "\n\n"
            
            for msg in self.conversation_history:
                if msg["role"] == "user":
                    conversation_text += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    conversation_text += f"Assistant: {msg['content']}\n"
            
            conversation_text += "Assistant: "
            
            # Generate response
            response = self.gemini_client.generate_content(
                conversation_text,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,
                    temperature=0.7,
                )
            )
            
            response_text = response.text if response.text else "I apologize, but I couldn't generate a response."
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            logger.info(f"Agent response: {response_text[:100]}...")
            self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AGENT: {response_text}\n")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            # Fallback to Anthropic if available
            if self.anthropic_client:
                logger.info("Gemini failed, falling back to Anthropic")
                return self._chat_anthropic()
            else:
                raise
    
    def _chat_ollama(self):
        """Chat using Ollama (OpenAI-compatible API)"""
        # Convert tools to OpenAI format
        openai_tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in self.tools]
        
        # Convert conversation history to OpenAI format
        openai_messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.conversation_history:
            if isinstance(msg.get("content"), str):
                openai_messages.append({"role": msg["role"], "content": msg["content"]})
        
        max_iterations = 10
        for iteration in range(max_iterations):
            try:
                response = self.ollama_client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    tools=openai_tools,
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                
                # Handle tool calls
                if message.tool_calls:
                    openai_messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in message.tool_calls
                        ]
                    })
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_input = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Executing tool: {tool_name}")
                        self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TOOL: {tool_name}\n")
                        self._log_to_file(f"  Input: {json.dumps(tool_input, indent=2)}\n")
                        
                        result = self.execute_tool(tool_name, tool_input)
                        
                        self._log_to_file(f"  Result: {json.dumps(result, indent=2)}\n")
                        
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                else:
                    # No more tool calls, return final response
                    response_text = message.content or ""
                    if response_text:
                        logger.info(f"Agent response: {response_text[:100]}...")
                        self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AGENT: {response_text}\n")
                    return response_text if response_text else "Task completed"
                    
            except Exception as e:
                logger.error(f"Ollama error on iteration {iteration}: {e}")
                if self.anthropic_client:
                    logger.info("Ollama failed, falling back to Anthropic")
                    return self._chat_anthropic()
                else:
                    raise
        
        return "Maximum iterations reached"
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation reset")
        self._log_to_transcript(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === CONVERSATION RESET ===\n")
    
    def switch_provider(self, new_provider, new_model=None):
        """Switch to a different LLM provider"""
        try:
            old_provider = self.provider
            old_model = self.model
            
            # Update provider and model
            self.provider = new_provider
            if new_model:
                self.model = new_model
            
            # Reinitialize clients based on new provider
            if self.provider == "anthropic":
                if not self.anthropic_key:
                    raise ValueError("ANTHROPIC_API_KEY not found")
                self.client = Anthropic(api_key=self.anthropic_key)
                self.anthropic_client = self.client
            
            elif self.provider == "gemini":
                if not HAS_GEMINI:
                    raise ImportError("Gemini library required. Install: pip install google-generativeai")
                if not self.gemini_key:
                    raise ValueError("GEMINI_API_KEY not found")
                genai.configure(api_key=self.gemini_key)
                self.gemini_client = genai.GenerativeModel(self.model)
            
            elif self.provider == "ollama":
                if not HAS_OPENAI:
                    raise ImportError("OpenAI library required for Ollama. Install: pip install openai")
                self.client = OpenAI(base_url=self.ollama_url, api_key="ollama")
                self.openai_client = self.client
            
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
            
            logger.info(f"Switched from {old_provider} to {self.provider}")
            logger.info(f"Model: {self.model}")
            self._log_to_transcript(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === PROVIDER SWITCHED: {old_provider} -> {self.provider} (Model: {self.model}) ===\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch provider: {e}")
            # Revert to original provider
            self.provider = old_provider
            self.model = old_model
            raise
    
    def get_provider_info(self):
        """Get current provider and model information"""
        return {
            "provider": self.provider,
            "model": self.model,
            "has_anthropic": bool(self.anthropic_key),
            "has_gemini": bool(self.gemini_key),
            "has_openai": bool(self.openai_key),
            "has_ollama": True  # Assume Ollama is available if configured
        }


if __name__ == "__main__":
    api_key = os.getenv("ANTHROPIC_API_KEY")
    provider = os.getenv("AI_PROVIDER", "anthropic")
    
    if provider == "anthropic" and not api_key:
        print("Error: Set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY='your-key-here'")
        exit(1)
    
    agent = AIAgent(api_key if api_key else None)
    
    print("=" * 60)
    print("AI AGENT STARTED")
    print("=" * 60)
    print(f"\nProvider: {agent.provider}")
    print(f"Model: {agent.model}")
    if agent.anthropic_client and agent.provider == "ollama":
        print("Fallback: Anthropic (if Ollama fails)")
    print("\nCommands:")
    print("  - Type your message to interact with the agent")
    print("  - Type 'exit' or 'quit' to stop")
    print("  - Type 'reset' to clear conversation history")
    print(f"\nTranscripts: {agent.transcript_file}")
    print(f"Actions: {agent.actions_file}")
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
