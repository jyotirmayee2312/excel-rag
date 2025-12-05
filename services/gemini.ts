// This service now communicates with the Python FastAPI backend
const API_URL = 'http://44.215.127.109:8000';

let currentSessionId: string | null = null;

export const uploadCsvFile = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${errorText}`);
    }

    const data = await response.json();
    currentSessionId = data.session_id;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const sendChatMessage = async (message: string): Promise<string> => {
  if (!currentSessionId) {
    throw new Error("No active session. Please upload a CSV file first.");
  }

  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: message,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat request failed: ${errorText}`);
    }

    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};
