import { DatabaseConfig } from "../types";

const BACKEND_URL = "http://18.233.93.208:6001";

export const verifyDatabaseConnection = async (dbConfig: DatabaseConfig): Promise<boolean> => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dbConfig),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Connection failed');
    }

    const data = await response.json();
    return data.status === 'success';
  } catch (error) {
    console.error("Connection Error:", error);
    throw error;
  }
};

export const generateSqlFromQuestion = async (
  question: string,
  dbConfig: DatabaseConfig,
  history: string[]
): Promise<{ text: string; sql: string | null }> => {
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        db_config: dbConfig,
        history
      }),
    });

    if (!response.ok) {
       const errorText = await response.text();
       return {
         text: `Error from backend: ${errorText}`,
         sql: null
       }
    }

    const data = await response.json();
    
    // Handle LangChain agent output format: { input: "...", output: "..." }
    // We prioritize data.output if it exists.
    const responseText = data.output || data.text || JSON.stringify(data);
    
    // The default agent doesn't separate SQL unless configured to return intermediate steps.
    // If the backend sends 'sql' explicitly, we use it, otherwise null.
    const responseSql = data.sql || null;

    return {
      text: responseText,
      sql: responseSql
    };

  } catch (error) {
    console.error("API Error:", error);
    return {
      text: "Could not connect to the backend server. Please ensure `backend.py` is running on port 8000.",
      sql: null
    };
  }
};