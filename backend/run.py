import os
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('../.env.local')

# Import and run the server
if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting server with API key: {os.getenv('GOOGLE_API_KEY', 'NOT SET')[:20]}...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
