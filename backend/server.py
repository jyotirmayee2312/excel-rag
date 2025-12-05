from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import os
import uuid
from typing import Dict
import tempfile

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions with their dataframes and agents
sessions: Dict[str, dict] = {}

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDtJqgeBzluEIZ77Y94Zv-R980HHMnlQNA")

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and create a new session with LangChain agent"""
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Load CSV into pandas DataFrame
        df = pd.read_csv(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Setup LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        
        # Create LangChain pandas agent
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            allow_dangerous_code=True
        )
        
        # Create new session
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "dataframe": df,
            "agent": agent,
            "filename": file.filename
        }
        
        return {
            "session_id": session_id,
            "message": f"Successfully loaded {file.filename} with {len(df)} rows and {len(df.columns)} columns",
            "rows": len(df),
            "columns": len(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """Send a message to the LangChain agent for the given session"""
    try:
        # Check if session exists
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a CSV file first.")
        
        session = sessions[request.session_id]
        agent = session["agent"]
        
        # Invoke the agent with the user's question
        response = agent.invoke(request.message)
        
        # Extract the output from the response
        answer = response.get('output', str(response))
        
        return {"response": answer}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "active_sessions": len(sessions)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
