import asyncio
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
import os
from dotenv import load_dotenv

async def run_memory_chat():
    load_dotenv()
    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
    
    # config_file = "server/services.json"
    
    # client = MCPClient.from_config_file(config_file)
    
    config = {
        "mcpServers": {
            "http": {
                "url": "http://localhost:8000/sse"
            }
        }
    }

    client = MCPClient.from_dict(config)
    
    llm = ChatGroq(model="qwen-qwq-32b")
    
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=True
    )
    
    try:
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit","quit"]:
                print("Ending Conversation....")
                break
            
            if user_input.lower() in ["clear"]:
                agent.clear_conversation_history()
                print("Conversation History cleared")
                continue
            
            print("\nAssistant: ", end="",flush=True)
            
            try:
                response = await agent.run(user_input)
                while isinstance(response, dict) and "needs_input" in response:
                    needed = response["needs_input"]
                    print(response["message"])
                    user_fill = input(f"{needed.capitalize()}: ")

                    # 👇 Re-run agent with just the missing piece — it will use memory
                    response = await agent.run(user_fill)

                print(response)
            except Exception as e:
                print(f"\nError:{e}")
    finally:
        if client and client.sessions:
            await client.close_all_sessions()
            
if __name__ == "__main__":
    asyncio.run(run_memory_chat())