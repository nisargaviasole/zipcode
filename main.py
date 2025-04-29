import asyncio
import os
from fastapi import FastAPI, HTTPException, Response
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

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Define FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In production, specify the exact URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize variables
agent = None
client = None

# Define a request model
class UserMessage(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    global agent, client

    # Configuration
    config = {"mcpServers": {"http": {"url": "https://mcpai.gleeze.com/sse"}}}
    client = MCPClient.from_dict(config)
    logger.info("MCP Client initialized")
    
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
        
        # Create MCPAgent
        agent = MCPAgent(
            llm=llm,
            client=client,
            memory_enabled=True,
            system_prompt=system_prompt_formatted,
        )
        logger.info("MCP Agent initialized with system prompt")
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        # Fallback to a minimal system prompt if file loading fails
        minimal_prompt = "You are a helpful assistant for a healthcare provider. Current date: {current_date}".format(
            current_date=current_date
        )
        agent = MCPAgent(
            llm=llm,
            client=client,
            memory_enabled=True,
            system_prompt=minimal_prompt,
        )
        logger.info("MCP Agent initialized with minimal prompt due to error")

@app.on_event("shutdown")
async def shutdown_event():
    if client and client.sessions:
        await client.close_all_sessions()
        logger.info("All MCP client sessions closed")

@app.post("/chat")
async def chat(user_message: UserMessage):
    global agent

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
                "message": response["message"]
            }

        logger.info("Response generated successfully")
        return {"response": response}

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)