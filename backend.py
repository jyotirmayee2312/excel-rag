from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env.local")

app = FastAPI(title="SQL GenAI Explorer API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class DatabaseConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str
    dbType: str = "mysql"

class ChatRequest(BaseModel):
    question: str
    db_config: DatabaseConfig
    history: Optional[List[str]] = []

class ChatResponse(BaseModel):
    output: str
    sql: Optional[str] = None

# Global variables to store agent and config
current_agent = None
current_db_config = None

# Security Prompt
SECURITY_PROMPT = """
You are a SQL expert. Given an input question, create a syntactically correct SQL query to run.
Unless the user specifies a specific number of examples, obtain the top 5 rows.

IMPORTANT:
If the user greets you (examples: "hi", "hello", "hey", "good morning", "good evening", "wassup"),
respond ONLY with:

Final Answer: Hello! I can help you with database questions. Please ask your SQL-related query.

Do NOT use Thought, Action, or Action Input for greetings.

SECURITY RULES:
1. You are authorized ONLY to read data (SELECT).
2. NEVER generate an INSERT, UPDATE, DELETE, ALTER, or DROP statement.
3. If user asks to modify data, respond with:
   Final Answer: I am not allowed to modify the database.
"""


def create_db_uri(config: DatabaseConfig) -> str:
    """Create database URI from config"""
    if config.dbType.lower() == "mysql":
        return f"mysql+pymysql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
    elif config.dbType.lower() == "postgresql":
        return f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
    else:
        raise ValueError(f"Unsupported database type: {config.dbType}")

def initialize_agent(db_config: DatabaseConfig):
    """Initialize the SQL agent with the given database configuration"""
    global current_agent, current_db_config
    
    # Create database URI
    db_uri = create_db_uri(db_config)
    
    # Connect to database
    db = SQLDatabase.from_uri(db_uri)
    
    # Setup LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    
    # Create agent
    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="zero-shot-react-description",
        verbose=True,
        prefix=SECURITY_PROMPT,
        allow_dangerous_code=True,
        handle_parsing_errors=True
    )
    
    current_agent = agent
    current_db_config = db_config
    
    return agent

def run_safe_query(question: str) -> str:
    """Run query with safety checks"""
    forbidden_words = ["delete", "drop", "truncate", "insert", "update", "alter"]
    
    # Simple check on user input
    if any(word in question.lower() for word in forbidden_words):
        return "I am sorry, I cannot authorize modification requests."
    
    # Run the agent
    if current_agent is None:
        raise HTTPException(status_code=400, detail="Database not connected. Please connect first.")
    
    result = current_agent.invoke(question)
    return result.get("output", str(result))

@app.get("/")
async def root():
    return {"message": "SQL GenAI Explorer API is running", "status": "ok"}

@app.post("/api/connect")
async def connect_database(config: DatabaseConfig):
    """Verify database connection and initialize agent"""
    try:
        # Initialize agent (this will test the connection)
        initialize_agent(config)
        
        return {
            "status": "success",
            "message": f"Successfully connected to {config.database}",
            "tables": current_agent.tools[0].db.get_usable_table_names() if current_agent else []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message and return SQL agent response"""
    try:
        # Check if we need to reinitialize agent (config changed)
        if current_db_config != request.db_config:
            initialize_agent(request.db_config)
        
        # Run the query
        print(request.question)
        response = run_safe_query(request.question)
        print(response)
        return ChatResponse(
            output=response,
            sql=None  # Could be enhanced to extract SQL from agent output
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

if __name__ == "__main__":
    print("Starting SQL GenAI Explorer Backend...")
    print("API will be available at: http://localhost:6001")
    print("API docs available at: http://localhost:6001/docs")
    uvicorn.run(app, host="0.0.0.0", port=6001)
