import React, { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { DataPreview } from './components/DataPreview';
import { ChatInterface } from './components/ChatInterface';
import { CsvData, Message, LoadingState } from './types';
import { parseCsv } from './utils/csv';
import { uploadCsvFile, sendChatMessage } from './services/gemini';
import { LayoutDashboard, Database, MessageSquare, Trash2, Eye, EyeOff } from 'lucide-react';

const App: React.FC = () => {
  const [csvData, setCsvData] = useState<CsvData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loadingState, setLoadingState] = useState<LoadingState>(LoadingState.IDLE);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [showDataPreview, setShowDataPreview] = useState(true);

  const handleFileSelect = async (file: File) => {
    setLoadingState(LoadingState.PARSING);
    setFileName(file.name);
    
    // 1. Parse locally for UI Preview
    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      if (text) {
        const parsedData = parseCsv(text);
        setCsvData(parsedData);
      }
    };
    reader.readAsText(file);

    // 2. Upload to Python Backend
    try {
      await uploadCsvFile(file);
      setLoadingState(LoadingState.IDLE);
      setMessages([{
        role: 'model',
        text: `I've analyzed **${file.name}**. I'm ready to answer your questions about the data!`
      }]);
    } catch (error) {
      console.error(error);
      setLoadingState(LoadingState.IDLE);
      alert("Failed to upload file to the backend. Please ensure the Python server is running.");
      setCsvData(null); // Reset on failure
      setFileName(null);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = inputValue;
    setInputValue('');
    setIsSending(true);

    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);

    try {
      const responseText = await sendChatMessage(userMessage);
      setMessages(prev => [...prev, { role: 'model', text: responseText }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'model', 
        text: 'Sorry, I encountered an error communicating with the server. Please check the backend console.',
        isError: true 
      }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleReset = () => {
    setCsvData(null);
    setMessages([]);
    setFileName(null);
    setInputValue('');
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center gap-2 text-blue-600 font-bold text-xl">
            <LayoutDashboard className="w-6 h-6" />
            <span>DataAnalyst</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Powered by LangChain & Python</p>
        </div>
        
        <div className="flex-1 p-4">
          <div className="space-y-1">
            <button 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${!csvData ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
              onClick={handleReset}
            >
              <Database className="w-4 h-4" />
              Upload Data
            </button>
            <button 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${csvData ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
              disabled={!csvData}
            >
              <MessageSquare className="w-4 h-4" />
              Chat Analysis
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-slate-100">
          {fileName && (
            <div className="mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Active File</p>
              <p className="text-sm text-slate-700 truncate" title={fileName}>{fileName}</p>
            </div>
          )}
          {csvData && (
            <button 
              onClick={handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Reset Session
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {!csvData ? (
          <div className="flex-1 p-8 overflow-y-auto">
            <div className="max-w-3xl mx-auto mt-20">
              <div className="text-center mb-10">
                <h1 className="text-4xl font-bold text-slate-900 mb-4">AI Data Analysis Agent</h1>
                <p className="text-lg text-slate-600 max-w-xl mx-auto">
                  Upload your CSV file and ask questions in plain English. 
                  Our Python agent will write code to find the answers.
                </p>
              </div>
              <FileUpload 
                onFileSelect={handleFileSelect} 
                isParsing={loadingState === LoadingState.PARSING} 
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-full">
            <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 justify-between shrink-0">
              <h1 className="font-semibold text-slate-800 flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-600" />
                {fileName}
              </h1>
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => {
                    console.log('Toggle clicked, current state:', showDataPreview);
                    setShowDataPreview(!showDataPreview);
                  }} 
                  className="flex items-center gap-2 px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md transition-colors text-sm font-medium"
                  title={showDataPreview ? "Hide Data Preview" : "Show Data Preview"}
                >
                  {showDataPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span className="hidden sm:inline">{showDataPreview ? 'Hide' : 'Show'} Data</span>
                </button>
                <div className="md:hidden">
                   <button onClick={handleReset} className="text-red-500 hover:bg-red-50 p-2 rounded-md transition-colors">
                      <Trash2 className="w-5 h-5" />
                   </button>
                </div>
              </div>
            </header>
            
            <div className="flex-1 overflow-hidden flex">
                {showDataPreview && (
                  <div className="flex-1 p-4 overflow-hidden flex flex-col min-w-0">
                      <DataPreview data={csvData} />
                  </div>
                )}
                <div className={`${showDataPreview ? 'w-[400px] lg:w-[450px]' : 'flex-1'} border-l border-slate-200 bg-white h-full flex-shrink-0`}>
                    <ChatInterface 
                        messages={messages}
                        input={inputValue}
                        setInput={setInputValue}
                        onSend={handleSend}
                        isLoading={isSending}
                    />
                </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;