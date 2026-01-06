
import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, ChevronRight, CheckCircle2, Terminal as TerminalIcon, FileText, DollarSign, Clock } from 'lucide-react';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-white/50 backdrop-blur-md sticky top-0 z-10">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Operational Console</h2>
          <p className="text-xs text-slate-500">Connected to internal infrastructure</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-full text-[10px] font-bold text-slate-600 uppercase tracking-wider">
          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
          Live Agent
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 px-12">
            <div className="p-4 bg-indigo-50 rounded-full text-indigo-600">
              <Bot className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-800">Welcome to ContextOS</h3>
              <p className="text-slate-500 text-sm mt-1 max-w-sm">
                I'm your AI operations assistant. I can help you summarize issues, create tickets, and query metrics.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-2 w-full max-w-md mt-6">
              {[
                "Summarize customer issues from last week",
                "Why did API latency increase yesterday?",
                "Create a Jira ticket for login failures"
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(suggestion)}
                  className="text-left px-4 py-3 bg-slate-50 hover:bg-slate-100 rounded-xl text-sm text-slate-700 transition-colors border border-slate-100 flex items-center justify-between group"
                >
                  {suggestion}
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 group-hover:translate-x-1 transition-all" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-10 h-10 rounded-2xl flex-shrink-0 flex items-center justify-center ${
              msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>
            
            <div className={`flex flex-col space-y-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : ''}`}>
              <div className={`p-4 rounded-3xl text-sm leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-200' 
                  : 'bg-slate-50 text-slate-800 rounded-tl-none border border-slate-100'
              }`}>
                {msg.content}
              </div>

              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="space-y-2">
                  {msg.toolCalls.map((call, idx) => (
                    <div key={idx} className="flex flex-col gap-1 px-3 py-2 bg-emerald-50 border border-emerald-100 text-emerald-700 rounded-xl text-xs">
                      <div className="flex items-center gap-2 font-medium">
                        <TerminalIcon className="w-3.5 h-3.5" />
                        <span>Executed: <span className="font-mono">{call.name}</span></span>
                        <CheckCircle2 className="w-3.5 h-3.5 ml-auto" />
                      </div>
                      {Object.keys(call.args).length > 0 && (
                        <div className="text-[10px] text-emerald-600 pl-6">
                          {Object.entries(call.args).map(([key, value]) => (
                            <div key={key}>
                              <span className="font-mono">{key}:</span> {String(value).substring(0, 50)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {msg.sources && msg.sources.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Sources:</div>
                  {msg.sources.slice(0, 3).map((source, idx) => (
                    <div key={idx} className="flex items-start gap-2 px-3 py-2 bg-blue-50 border border-blue-100 text-blue-700 rounded-xl text-xs">
                      <FileText className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{source.title}</div>
                        <div className="text-[10px] text-blue-600 line-clamp-2">{source.content}</div>
                        <div className="text-[9px] text-blue-500 mt-1">Score: {source.score.toFixed(3)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {(msg.tokens || msg.cost || msg.latency) && (
                <div className="flex items-center gap-3 text-[10px] text-slate-400">
                  {msg.tokens && (
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {msg.tokens} tokens
                    </span>
                  )}
                  {msg.cost && (
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      ${msg.cost.toFixed(4)}
                    </span>
                  )}
                  {msg.latency && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {msg.latency.toFixed(0)}ms
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 text-slate-400 text-sm italic">
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing internal state...
            </div>
          </div>
        )}
      </div>

      <div className="p-6 bg-slate-50 border-t border-slate-100">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask anything about docs, tickets, or metrics..."
            className="w-full bg-white border border-slate-200 rounded-2xl py-4 pl-6 pr-14 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none shadow-sm transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl transition-all shadow-lg shadow-indigo-200"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <p className="mt-3 text-[10px] text-slate-400 text-center uppercase tracking-widest font-bold">
          ContextOS V1.2.0 • Proactive Decision Engine
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
