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
import uuid
from typing import Dict
from starlette.middleware.sessions import SessionMiddleware

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Define FastAPI app
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=str(uuid.uuid4()),
    session_cookie="session_id",
    max_age=3600,  # Session expires after 1 hour
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins in production
    allow_credentials=True,  # Allow cookies to be sent
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store session-specific agents and clients
session_storage: Dict[str, Dict] = {}

# Define a request model
class UserMessage(BaseModel):
    message: str

# Dependency to get or create session-specific agent and client
async def get_session_agent(request: Request):
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        logger.info(f"New session created: {session_id}")

    if session_id not in session_storage:
        # Configuration for MCPClient
        config = {"mcpServers": {"http": {"url": "https://mcpai.gleeze.com/sse"}}}
        client = MCPClient.from_dict(config)
        logger.info(f"MCP Client initialized for session {session_id}")

        # Initialize LLM
        llm = ChatGroq(model="deepseek-r1-distill-llama-70b")

        # Get current date and time
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.strftime("%B %d, %Y")

        try:
            # Read system prompt from file
            with open("system_prompt.txt", "r") as file:
                system_prompt = file.read()

            # Update system prompt with date/time
            system_prompt_formatted = system_prompt.format(
                current_date=current_date
            )
        except Exception as e:
            logger.error(f"Error reading system prompt: {str(e)}")
            # Fallback to minimal prompt
            system_prompt_formatted = (
                "You are a helpful assistant for a healthcare provider. "
                f"Current date: {current_date}"
            )

        # Create MCPAgent for this session
        agent = MCPAgent(
            llm=llm,
            client=client,
            memory_enabled=True,
            system_prompt=system_prompt_formatted,
        )
        logger.info(f"MCP Agent initialized for session {session_id}")

        # Store client and agent in session storage
        session_storage[session_id] = {"client": client, "agent": agent}

    return session_storage[session_id]["agent"], session_storage[session_id]["client"]

@app.on_event("startup")
async def startup_event():
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown_event():
    # Close all MCP client sessions
    for session_id, session_data in session_storage.items():
        client = session_data.get("client")
        if client and client.sessions:
            await client.close_all_sessions()
            logger.info(f"Closed MCP client sessions for session {session_id}")
    session_storage.clear()
    logger.info("All sessions cleared")

@app.post("/chat")
async def chat(
    user_message: UserMessage,
    request: Request,
    session_data=Depends(get_session_agent),
):
    agent, client = session_data

    try:
        user_input = user_message.message.strip()

        if user_input.lower() in ["clear"]:
            agent.clear_conversation_history()
            return {"response": "Conversation history cleared."}

        logger.info(f"Processing user message: {user_input[:50]}...")
        response = await agent.run(user_input)

        # Handle if the agent needs additional input from the user
        if isinstance(response, dict) and "needs_input" in response:
            return {
                "needs_input": response["needs_input"],
                "message": response["message"],
            }

        logger.info("Response generated successfully")
        return {"response": response}

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clear_session")
async def clear_session(request: Request):
    session_id = request.session.get("session_id")
    if session_id and session_id in session_storage:
        client = session_storage[session_id].get("client")
        if client and client.sessions:
            await client.close_all_sessions()
            logger.info(f"Closed MCP client sessions for session {session_id}")
        del session_storage[session_id]
        logger.info(f"Cleared session {session_id}")
    request.session.clear()
    return {"response": "Session cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)