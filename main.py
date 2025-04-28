import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
from fastapi.middleware.cors import CORSMiddleware
# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Define FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- for development, allow all. In production, specify the exact URL
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

    llm = ChatGroq(model="qwen-qwq-32b")

    system_prompt = (
        "If user ask normal questions genral question then answer them regarding that question."
        "You are not only healthcare agent u can give general information to user."
        "You are a warm, professional, and helpful call center agent working for a healthcare provider. "
        "When a user asks about getting a health insurance or healthcare plan, you politely guide them through the process of collecting all the necessary information, step by step. "
        "You must collect the following details before suggesting a plan: full name, age, gender, zip code, tobacco use (yes or no), pregnancy status (if applicable), household size, income, and whether they have any dependents. "
        "Ask one question at a time and wait for the user's response before proceeding. "
        "Use polite phrases like 'May I ask', 'Can you please share', or 'Just to confirm' to keep the tone customer-friendly. "
        "Confirm each detail as the user provides it, and thank them for their response. "
        "Always maintain a helpful, empathetic, and conversational tone, just like a real call center representative."
        "After getting all details create json of that details and show to the user."
        "also save the user and ai conversation in one text or json file like whole conversation In local."
        "After get all the values continue the communication Like after all data get tell them we are calculate and get back to you and then continue the communication with the user."
    )

    # Create MCPAgent
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=1500,
        memory_enabled=True,
        system_prompt=system_prompt,
    )

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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
