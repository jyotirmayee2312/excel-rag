import React, { useState } from 'react';
import ConnectForm from './components/ConnectForm';
import ChatInterface from './components/ChatInterface';
import { DatabaseConfig, ChatMessage, MessageRole } from './types';
import { generateSqlFromQuestion, verifyDatabaseConnection } from './services/geminiService';
import { Database, LogOut } from 'lucide-react';

const App: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [dbConfig, setDbConfig] = useState<DatabaseConfig | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleConnect = async (config: DatabaseConfig) => {
    setIsLoading(true);
    try {
      // Real connection check against Python Backend
      await verifyDatabaseConnection(config);
      
      setDbConfig(config);
      setIsConnected(true);
      
      const initialMsg: ChatMessage = {
        id: 'init-1',
        role: MessageRole.ASSISTANT,
        content: `Connected to ${config.database}. I am a SQL expert. I can help you query your database.`,
        timestamp: Date.now()
      };
      setMessages([initialMsg]);

    } catch (error: any) {
      alert(`Connection Failed: ${error.message}\n\nMake sure backend.py is running!`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    setDbConfig(null);
    setMessages([]);
  };

  const handleSendMessage = async (text: string) => {
    if (!dbConfig) return;

    // 1. Add User Message
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: MessageRole.USER,
      content: text,
      timestamp: Date.now()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    // 2. Call Backend Service
    const history = messages.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`);
    const response = await generateSqlFromQuestion(text, dbConfig, history);

    // 3. Add AI Response
    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: MessageRole.ASSISTANT,
      content: response.text,
      sql: response.sql || undefined,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, aiMsg]);
    setIsLoading(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {!isConnected ? (
        <ConnectForm onConnect={handleConnect} isLoading={isLoading} />
      ) : (
        <>
          {/* Header */}
          <header className="h-14 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between px-4 shrink-0 z-10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
                <Database className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-sm text-slate-100 leading-tight">SQL GenAI Agent</h1>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                  <span className="text-[10px] text-slate-400 font-mono">{dbConfig?.user}@{dbConfig?.host}</span>
                </div>
              </div>
            </div>
            <button 
              onClick={handleDisconnect}
              className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-red-500/10 hover:text-red-400 text-slate-400 text-xs font-medium transition-colors flex items-center gap-2"
            >
              <LogOut className="w-3 h-3" />
              Disconnect
            </button>
          </header>

          {/* Main Layout */}
          <main className="flex-1 flex overflow-hidden relative">
             <div className="flex-1 flex flex-col min-w-0">
               <ChatInterface 
                 messages={messages} 
                 onSendMessage={handleSendMessage}
                 isLoading={isLoading}
               />
             </div>
          </main>
        </>
      )}
    </div>
  );
};

export default App;
