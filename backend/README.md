# Backend Server

This is a FastAPI backend that integrates LangChain with Google's Gemini AI to analyze CSV files using natural language queries.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your Google API key is set in `.env.local` at the project root

## Running the Server

From the backend directory:
```bash
python run.py
```

Or directly:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The server will start on http://localhost:8000

## API Endpoints

- `POST /upload` - Upload a CSV file and create a new session
- `POST /chat` - Send a query to analyze the uploaded CSV
- `GET /health` - Health check endpoint

## Environment Variables

- `GOOGLE_API_KEY` - Your Google Gemini API key (loaded from .env.local)
