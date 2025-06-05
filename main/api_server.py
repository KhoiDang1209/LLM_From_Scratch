from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyngrok import ngrok
import uvicorn
import os
import nest_asyncio
from google.colab import userdata
from rag_chatbot import RAGChatbot

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize FastAPI app
app = FastAPI(title="HCMIU RAG Chatbot API")

# Initialize RAG chatbot
chatbot = RAGChatbot(
    mongodb_uri=userdata.get('mongodb'),
    openai_api_key=userdata.get('OpenAI')
)

class Query(BaseModel):
    text: str

@app.get("/")
async def read_root():
    return {"message": "HCMIU RAG Chatbot API is running!"}

@app.post("/chat")
async def chat(query: Query):
    try:
        response = chatbot.chat(query.text)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    # Set up ngrok authtoken
    NGROK_AUTH_TOKEN = userdata.get('ngrok_auth_token')
    if NGROK_AUTH_TOKEN:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        print("ngrok authtoken set.")
    else:
        print("NGROK_AUTH_TOKEN not found in Colab secrets. Please add it to use ngrok.")

    try:
        # Kill any existing ngrok tunnels
        ngrok.kill()
        print("Existing ngrok tunnels killed.")

        # Start a new tunnel
        public_url = ngrok.connect(addr="8000", proto="http")
        print(f"FastAPI Public URL: {public_url}")
        
        # Start FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_server() 