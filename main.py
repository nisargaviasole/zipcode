import asyncio
import os
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
from fastapi.middleware.cors import CORSMiddleware
import logging
import datetime
import uvicorn
from groq import AsyncGroq
from uuid import uuid4
from typing import Dict, List

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

session_agents: Dict[str, MCPAgent] = {}
# Define FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Explicitly list allowed methods
    allow_headers=["*"],  # Allow all headers
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure multiple MCP servers
# config = {
#     "mcpServers": {
#         "primary": {
#             "url": "https://mcpai.gleeze.com/sse"
#         },
#         "secondary": {
#             "url": "https://mcptool.gleeze.com/sse"
#         }
#     }
# }

config = {"mcpServers": {"https": {"url": "https://mcptool.gleeze.com/sse"}}}

# Create MCP client with multiple servers
client = MCPClient.from_dict(config)

# Initialize LLM
llm = ChatGroq(model="deepseek-r1-distill-llama-70b")

# Get current date and time
current_datetime = datetime.datetime.now()
current_date = current_datetime.strftime("%B %d, %Y")

# Load system prompt
with open("system_prompt.txt", "r") as file:
    system_prompt = file.read()

# Update system prompt with date/time
system_prompt_formatted = system_prompt.format(
    current_date=current_date
)


# Define request models
class UserMessage(BaseModel):
    message: str
    session_id: str  # Unique per browser
    server_preference: str = "primary"  # Optional parameter to choose server


@app.post("/chat")
async def chat(user_message: UserMessage, request: Request):
    try:
        session_id = user_message.session_id.strip()
        user_input = user_message.message.strip()

        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required.")

        print("session_agents",session_agents)
        print("sessionid",session_id)
        print("condition",session_id not in session_agents)
        # Get or create agent for session
        if session_id not in session_agents:
            session_agents[session_id] = MCPAgent(
                llm=llm,
                client=client,
                memory_enabled=True,
                system_prompt=system_prompt_formatted,
            )

        agent = session_agents[session_id]

        if user_input.lower() == "clear":
            agent.clear_conversation_history()
            return {"response": "Conversation history cleared."}

        logger.info(f"Processing user message for session {session_id}: {user_input[:50]}...")
        response = await agent.run(user_input)

        if isinstance(response, dict) and "needs_input" in response:
            return {
                "needs_input": response["needs_input"],
                "message": response["message"],
            }

        return {"response": response}

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
# Route to get available servers
@app.get("/servers")
async def get_servers():
    return {"servers": list(config["mcpServers"].keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)