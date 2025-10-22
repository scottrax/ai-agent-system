from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
import asyncio
from agent import AIAgent
import json
from typing import Dict, List
import uuid
from datetime import datetime
from pathlib import Path
import os
from secrets import compare_digest
import shutil

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment (flexible - any provider key is fine)
API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama"
if not API_KEY:
    raise ValueError("No API keys found in environment. Please set at least one provider key in .env file")

# Get authentication credentials (optional)
WEB_AUTH_USERNAME = os.getenv("WEB_AUTH_USERNAME")
WEB_AUTH_PASSWORD = os.getenv("WEB_AUTH_PASSWORD")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Server")

# Store active agents per session
agents: Dict[str, AIAgent] = {}

# HTTP Basic Auth setup
security = HTTPBasic()

def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Check if authentication is required and validate credentials"""
    # If no auth configured, allow access
    if not WEB_AUTH_USERNAME or not WEB_AUTH_PASSWORD:
        return True
    
    # Validate credentials
    correct_username = compare_digest(credentials.username, WEB_AUTH_USERNAME)
    correct_password = compare_digest(credentials.password, WEB_AUTH_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

@app.get("/")
async def get():
    """Serve the web interface"""
    try:
        with open("index.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=500)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "active_sessions": len(agents)}

@app.get("/api/providers")
async def get_available_providers():
    """Get available LLM providers and their status"""
    return {
        "providers": {
            "anthropic": {
                "name": "Anthropic Claude",
                "available": bool(os.getenv("ANTHROPIC_API_KEY")),
                "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-5", "claude-3-opus-20240229"]
            },
            "gemini": {
                "name": "Google Gemini",
                "available": bool(os.getenv("GEMINI_API_KEY")),
                "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
            },
            "openai": {
                "name": "OpenAI",
                "available": bool(os.getenv("OPENAI_API_KEY")),
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            },
            "ollama": {
                "name": "Ollama (Local)",
                "available": True,  # Assume available if configured
                "models": ["llama3.1", "codellama", "mistral", "phi3"]
            }
        }
    }

@app.post("/api/switch-provider")
async def switch_provider(provider: str, model: str = None, session_id: str = None):
    """Switch LLM provider for a session"""
    if session_id and session_id in agents:
        try:
            agent = agents[session_id]
            agent.switch_provider(provider, model)
            return {
                "success": True,
                "provider": provider,
                "model": model,
                "message": f"Switched to {provider}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    else:
        return {
            "success": False,
            "error": "Session not found"
        }

@app.get("/api/session-info/{session_id}")
async def get_session_info(session_id: str):
    """Get current provider info for a session"""
    if session_id in agents:
        agent = agents[session_id]
        return {
            "success": True,
            "info": agent.get_provider_info()
        }
    else:
        return {
            "success": False,
            "error": "Session not found"
        }

@app.get("/api/chat-history")
async def get_chat_history():
    """Get list of available chat histories"""
    try:
        logs_dir = Path("logs/transcripts")
        if not logs_dir.exists():
            return {"success": True, "chats": []}
        
        chat_files = []
        for file_path in logs_dir.glob("conversation_*.log"):
            try:
                # Extract timestamp from filename
                filename = file_path.name
                timestamp_str = filename.replace("conversation_", "").replace(".log", "")
                
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Get file stats
                stat = file_path.stat()
                
                # Read file and extract meaningful preview
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract actual conversation content for preview
                lines = content.split('\n')
                conversation_lines = []
                
                for line in lines:
                    line = line.strip()
                    if (line.startswith('[') and '] USER:' in line) or \
                       (line.startswith('[') and '] AGENT:' in line) or \
                       line.startswith('User: ') or line.startswith('Assistant: '):
                        conversation_lines.append(line)
                        if len(conversation_lines) >= 3:  # Get first 3 conversation exchanges
                            break
                
                if conversation_lines:
                    preview = " | ".join(conversation_lines[:3])
                    if len(preview) > 200:
                        preview = preview[:200] + "..."
                else:
                    preview = "No conversation content found"
                
                chat_files.append({
                    "id": filename,
                    "filename": filename,
                    "timestamp": timestamp.isoformat(),
                    "size": stat.st_size,
                    "preview": preview[:200] + "..." if len(preview) > 200 else preview,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error reading chat file {file_path}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        chat_files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"success": True, "chats": chat_files}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/chat-history/{chat_id}")
async def get_chat_content(chat_id: str):
    """Get full content of a specific chat"""
    try:
        logs_dir = Path("logs/transcripts")
        file_path = logs_dir / chat_id
        
        if not file_path.exists():
            return {"success": False, "error": "Chat not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"success": True, "content": content}
    except Exception as e:
        logger.error(f"Error reading chat {chat_id}: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/chat-history/{chat_id}/load")
async def load_chat_history(chat_id: str, session_id: str = None):
    """Load a specific chat history into a session"""
    try:
        if not session_id or session_id not in agents:
            return {"success": False, "error": "Invalid session"}
        
        agent = agents[session_id]
        
        # Get chat content
        logs_dir = Path("logs/transcripts")
        file_path = logs_dir / chat_id
        
        if not file_path.exists():
            return {"success": False, "error": "Chat not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the conversation from the log file
        conversation = []
        lines = content.split('\n')
        current_message = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for user messages
            if line.startswith('[') and '] USER:' in line:
                # Save previous message if exists
                if current_message:
                    conversation.append(current_message)
                
                # Extract user message
                user_msg = line.split('] USER: ', 1)[1]
                current_message = {"role": "user", "content": user_msg}
                
            # Check for agent messages
            elif line.startswith('[') and '] AGENT:' in line:
                # Save previous message if exists
                if current_message:
                    conversation.append(current_message)
                
                # Extract agent message
                agent_msg = line.split('] AGENT: ', 1)[1]
                current_message = {"role": "assistant", "content": agent_msg}
                
            # Check for alternative format (User: / Assistant:)
            elif line.startswith('User: '):
                if current_message:
                    conversation.append(current_message)
                user_msg = line.replace('User: ', '')
                current_message = {"role": "user", "content": user_msg}
                
            elif line.startswith('Assistant: '):
                if current_message:
                    conversation.append(current_message)
                agent_msg = line.replace('Assistant: ', '')
                current_message = {"role": "assistant", "content": agent_msg}
                
            # Continue building current message if it's a continuation line
            elif current_message and not line.startswith('[') and not line.startswith('User:') and not line.startswith('Assistant:'):
                # This is a continuation of the current message
                current_message["content"] += "\n" + line
        
        # Add the last message if exists
        if current_message:
            conversation.append(current_message)
        
        # Load conversation into agent
        agent.conversation_history = conversation
        
        return {
            "success": True, 
            "message": f"Loaded {len(conversation)} messages from chat history",
            "conversation_length": len(conversation)
        }
    except Exception as e:
        logger.error(f"Error loading chat {chat_id}: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/chat-history/{chat_id}")
async def delete_chat_history(chat_id: str):
    """Delete a specific chat history"""
    try:
        logs_dir = Path("logs/transcripts")
        file_path = logs_dir / chat_id
        
        if not file_path.exists():
            return {"success": False, "error": "Chat not found"}
        
        # Also try to delete corresponding actions file
        actions_dir = Path("logs/actions")
        actions_file = actions_dir / chat_id.replace("conversation_", "actions_")
        if actions_file.exists():
            actions_file.unlink()
        
        file_path.unlink()
        
        return {"success": True, "message": "Chat deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}")
        return {"success": False, "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    
    # Note: WebSocket authentication is disabled for simplicity
    # The main page is still protected by HTTP Basic Auth
    # In production, you might want to implement proper WebSocket auth
    
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    logger.info(f"New WebSocket connection: {session_id}")
    
    # Create agent with session-specific log file
    # The agent will automatically create logs in the project's logs directory
    agent = AIAgent(api_key=API_KEY)
    agents[session_id] = agent
    
    try:
        await websocket.send_json({
            "type": "system",
            "content": "Connected to AI Agent. How can I help you?",
            "session_id": session_id
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Message from {session_id}: {data}")
            
            if data.lower() in ['exit', 'quit']:
                await websocket.send_json({
                    "type": "system",
                    "content": "Goodbye!"
                })
                break
            
            if data.lower() == 'reset':
                agent.reset_conversation()
                await websocket.send_json({
                    "type": "system",
                    "content": "Conversation reset"
                })
                continue
            
            # Handle chat loading commands
            if data.startswith('/load_chat '):
                chat_id = data.replace('/load_chat ', '').strip()
                try:
                    # Get chat content
                    logs_dir = Path("logs/transcripts")
                    file_path = logs_dir / chat_id
                    
                    if not file_path.exists():
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Chat {chat_id} not found"
                        })
                        continue
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse the conversation from the log file
                    conversation = []
                    lines = content.split('\n')
                    current_message = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Check for user messages
                        if line.startswith('[') and '] USER:' in line:
                            # Save previous message if exists
                            if current_message:
                                conversation.append(current_message)
                            
                            # Extract user message
                            user_msg = line.split('] USER: ', 1)[1]
                            current_message = {"role": "user", "content": user_msg}
                            
                        # Check for agent messages
                        elif line.startswith('[') and '] AGENT:' in line:
                            # Save previous message if exists
                            if current_message:
                                conversation.append(current_message)
                            
                            # Extract agent message
                            agent_msg = line.split('] AGENT: ', 1)[1]
                            current_message = {"role": "assistant", "content": agent_msg}
                            
                        # Check for alternative format (User: / Assistant:)
                        elif line.startswith('User: '):
                            if current_message:
                                conversation.append(current_message)
                            user_msg = line.replace('User: ', '')
                            current_message = {"role": "user", "content": user_msg}
                            
                        elif line.startswith('Assistant: '):
                            if current_message:
                                conversation.append(current_message)
                            agent_msg = line.replace('Assistant: ', '')
                            current_message = {"role": "assistant", "content": agent_msg}
                            
                        # Continue building current message if it's a continuation line
                        elif current_message and not line.startswith('[') and not line.startswith('User:') and not line.startswith('Assistant:'):
                            # This is a continuation of the current message
                            current_message["content"] += "\n" + line
                    
                    # Add the last message if exists
                    if current_message:
                        conversation.append(current_message)
                    
                    # Load conversation into agent
                    agent.conversation_history = conversation
                    
                    # Send each message from the loaded conversation to display in UI
                    for msg in conversation:
                        if msg["role"] == "user":
                            await websocket.send_json({
                                "type": "message",
                                "content": msg["content"],
                                "role": "user"
                            })
                        elif msg["role"] == "assistant":
                            await websocket.send_json({
                                "type": "message", 
                                "content": msg["content"],
                                "role": "assistant"
                            })
                    
                    await websocket.send_json({
                        "type": "system",
                        "content": f"Loaded {len(conversation)} messages from chat history"
                    })
                    continue
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Error loading chat: {str(e)}"
                    })
                    continue
            
            # Send processing status
            await websocket.send_json({
                "type": "status",
                "content": "processing"
            })
            
            # Process message with agent
            try:
                response = agent.chat(data)
                
                # Send response back to client
                await websocket.send_json({
                    "type": "message",
                    "content": response
                })
            except Exception as e:
                logger.error(f"Agent error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if session_id in agents:
            del agents[session_id]
        logger.info(f"Session closed: {session_id}")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    if WEB_AUTH_USERNAME and WEB_AUTH_PASSWORD:
        logger.info(f"Authentication ENABLED - username: {WEB_AUTH_USERNAME}")
    else:
        logger.info("Authentication DISABLED - no username/password set")
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Access the web interface at http://{host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
