from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
from agent import AIAgent
import json
from typing import Dict
import uuid
from datetime import datetime
from pathlib import Path
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment. Please set it in .env file")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Server")

# Store active agents per session
agents: Dict[str, AIAgent] = {}

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    logger.info(f"New WebSocket connection: {session_id}")
    
    # Create agent with session-specific log file
    log_dir = Path.home() / "ai-agent-logs"
    log_file = log_dir / f"web_session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    agent = AIAgent(api_key=API_KEY, log_file=log_file)
    agents[session_id] = agent
    
    try:
        await websocket.send_json({
            "type": "system",
            "content": "Connected to AI Agent. How can I help you?"
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
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Access the web interface at http://{host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
