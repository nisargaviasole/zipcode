import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
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
    allow_origins=["*"],  # <-- for development, allow all. In production, specify the exact URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize variables
config = {"mcpServers": {"http": {"url": "http://127.0.0.1:8000/sse"}}}
client = MCPClient.from_dict(config)

llm = ChatGroq(model="deepseek-r1-distill-llama-70b")

system_prompt = (
    "If user ask normal questions genral question then answer them regarding that question."
    "You are not only healthcare agent u can give general information to user."
    "You are a warm, professional, and helpful call center agent working for a healthcare provider. "
    "When a user asks about getting a health insurance or healthcare plan, you politely guide them through the process of collecting all the necessary information, step by step. "
    "You must collect the following details before suggesting a plan: full name, age, gender, zip code, tobacco use (yes or no), pregnancy status (if applicable), household size, income,doctor,hospital,medication and whether they have any dependents."
    "ASk Doctor, Hospital and Medicine question seprately"
    "Dont add any previous response for example after giving age dont say user that your age is this and all."
    "Ask one question at a time and wait for the user's response before proceeding. "
    "Use polite phrases like 'May I ask', 'Can you please share', or 'Just to confirm' to keep the tone customer-friendly. "
    "Confirm each detail as the user provides it, and thank them for their response. "
    "Always maintain a helpful, empathetic, and conversational tone, just like a real call center representative."
    "After get all the values create json and send to my get_saving_info tool.Its giving a savings , healthcare plan name and premium of the plan so say that all to the user"
    "Dont add any emojis ** and dont bold and word or sentense"
    "If user wants to change previous data like after giving age user wants to change age then change that field and send update json and again continue the conversation"
)

agent = MCPAgent(
    llm=llm,
    client=client,
    max_steps=1500,
    memory_enabled=True,
    system_prompt=system_prompt,
)
# Define a request model
class UserMessage(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    global agent, client

    # Configuration

@app.on_event("shutdown")
async def shutdown_event():
    if client and client.sessions:
        await client.close_all_sessions()

@app.post("/chat")
async def chat(user_message: UserMessage):
    global agent

    try:
        user_input = user_message.message.strip()

        if user_input.lower() in ["clear"]:
            agent.clear_conversation_history()
            return {"response": "Conversation history cleared."}

        response = await agent.run(user_input)

        while isinstance(response, dict) and "needs_input" in response:
            needed = response["needs_input"]
            message = response["message"]
            return {
                "needs_input": needed,
                "message": message
            }

        return {"response": response}

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

