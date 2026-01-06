import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import DataViewer from './components/DataViewer';
import { ChatMessage } from './types';
import { apiService } from './services/apiService';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Check backend health on mount
  useEffect(() => {
    apiService.healthCheck()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleSendMessage = async (text: string) => {
    const newUserMsg: ChatMessage = {
      role: 'user',
      content: text,
      id: Date.now().toString()
    };
    
    setChatMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      const response = await apiService.query(text);
      
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        toolCalls: response.tool_calls,
        sources: response.sources,
        tokens: response.tokens_used,
        cost: response.cost,
        latency: response.latency_ms
      };
      
      setChatMessages(prev => [...prev, assistantMsg]);

      // Switch to appropriate tab if actions were taken
      if (response.tool_calls) {
        response.tool_calls.forEach(call => {
          if (call.name === 'create_jira_ticket') {
            setActiveTab('jira');
          } else if (call.name === 'post_slack_summary') {
            setActiveTab('slack');
          }
        });
      }
    } catch (error: any) {
      console.error('Error in agent response:', error);

      const errorMsg: ChatMessage = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: `Error: ${error.message}. Please ensure the backend is running at ${import.meta.env.VITE_API_URL || 'http://localhost:8000'}`
      };
      setChatMessages(prev => [...prev, errorMsg]);
      setBackendStatus('offline');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-900 overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} backendStatus={backendStatus} />
      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 p-6 flex flex-col min-w-0 overflow-hidden">
          <ChatInterface 
            messages={chatMessages} 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading} 
          />
        </div>
        <DataViewer tab={activeTab} />
      </main>
    </div>
  );
};

export default App;