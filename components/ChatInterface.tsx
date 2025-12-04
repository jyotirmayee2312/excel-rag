import React, { useRef, useEffect } from 'react';
import { ChatMessage, MessageRole } from '../types';
import { Send, User, Bot, Terminal, Copy, Check } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

const CodeBlock: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-3 mb-2 rounded-lg overflow-hidden border border-slate-700 bg-slate-950">
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono text-slate-400">Generated SQL</span>
        </div>
        <button 
          onClick={handleCopy}
          className="text-slate-500 hover:text-white transition-colors"
        >
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
        </button>
      </div>
      <div className="p-4 overflow-x-auto">
        <pre className="font-mono text-sm text-emerald-300 whitespace-pre-wrap">
          {code}
        </pre>
      </div>
    </div>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = React.useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex gap-4 ${msg.role === MessageRole.USER ? 'flex-row-reverse' : 'flex-row'}`}
          >
            {/* Avatar */}
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center shrink-0
              ${msg.role === MessageRole.USER ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'}
            `}>
              {msg.role === MessageRole.USER ? <User className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
            </div>

            {/* Content */}
            <div className={`
              flex flex-col max-w-[80%] 
              ${msg.role === MessageRole.USER ? 'items-end' : 'items-start'}
            `}>
              <div className={`
                px-4 py-3 rounded-2xl text-sm leading-relaxed
                ${msg.role === MessageRole.USER 
                  ? 'bg-blue-600 text-white rounded-tr-sm' 
                  : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-sm'}
              `}>
                <p>{msg.content}</p>
                {msg.sql && <CodeBlock code={msg.sql} />}
              </div>
              <span className="text-xs text-slate-500 mt-1 px-1">
                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-4">
             <div className="w-10 h-10 rounded-full bg-emerald-600/20 text-emerald-500 flex items-center justify-center shrink-0">
               <LoaderIcon />
             </div>
             <div className="flex items-center">
               <span className="text-slate-400 text-sm animate-pulse">Thinking about schema...</span>
             </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your data (e.g., 'Show top 5 users by order count')..."
            className="w-full bg-slate-950 text-white border border-slate-700 rounded-xl pl-4 pr-12 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 placeholder-slate-500 shadow-lg"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:bg-slate-700 text-white rounded-lg px-3 transition-colors flex items-center justify-center"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <div className="text-center mt-2">
            <p className="text-[10px] text-slate-600">AI generated SQL. Review before executing.</p>
        </div>
      </div>
    </div>
  );
};

const LoaderIcon = () => (
  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

export default ChatInterface;