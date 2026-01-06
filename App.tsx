import React, { useState, useMemo, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import DataViewer from './components/DataViewer';
import { 
  MOCK_DOCUMENTS, 
  MOCK_TICKETS, 
  MOCK_SLACK, 
  MOCK_METRICS 
} from './constants';
import { AppState, ChatMessage, Priority, JiraTicket, SlackMessage } from './types';
import { AgentService, ToolResult } from './services/geminiService';
import { Content } from '@google/genai';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [state, setState] = useState<AppState>(() => {
    const saved = localStorage.getItem('context-os-state');
    return saved ? JSON.parse(saved) : {
      documents: MOCK_DOCUMENTS,
      tickets: MOCK_TICKETS,
      messages: MOCK_SLACK,
      metrics: MOCK_METRICS
    };
  });
  
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Sync state to local storage to simulate persistence during development
  useEffect(() => {
    localStorage.setItem('context-os-state', JSON.stringify(state));
  }, [state]);

  const agent = useMemo(() => new AgentService(state), [state]);

  const handleSendMessage = async (text: string) => {
    const newUserMsg: ChatMessage = {
      role: 'user',
      content: text,
      id: Date.now().toString()
    };
    
    setChatMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      const history: Content[] = chatMessages.map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }]
      }));

      const response = await agent.processMessage(text, history);
      
      if (response.toolResults) {
        response.toolResults.forEach((tr: ToolResult) => {
          if (tr.name === 'create_jira_ticket' && tr.result.success) {
            const newTicket: JiraTicket = {
              id: tr.result.ticketId,
              title: tr.args.title || 'New Task',
              description: tr.args.description || 'Created via ContextOS Agent',
              priority: (tr.args.priority as Priority) || Priority.MEDIUM,
              status: 'To Do'
            };
            setState(prev => ({
              ...prev,
              tickets: [newTicket, ...prev.tickets]
            }));
            setActiveTab('jira');
          }
          if (tr.name === 'post_slack_summary' && tr.result.success) {
            const newMessage: SlackMessage = {
              id: `slack-${Date.now()}`,
              channel: tr.args.channel || '#general',
              user: 'ContextOS Bot',
              text: tr.args.message || '',
              timestamp: new Date().toISOString()
            };
            setState(prev => ({
              ...prev,
              messages: [newMessage, ...prev.messages]
            }));
            setActiveTab('slack');
          }
        });

        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.finalResponse || 'Action completed successfully.',
          toolCalls: response.toolResults
        };
        setChatMessages(prev => [...prev, assistantMsg]);
      } else {
        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.text || 'I have completed your request.'
        };
        setChatMessages(prev => [...prev, assistantMsg]);
      }
    } catch (error: any) {
      console.error('Error in agent response:', error);
      
      // Handle potential API key errors as per guidelines
      if (error?.message?.includes('Requested entity was not found')) {
        // In a real environment, we might call window.aistudio.openSelectKey() here
        // but for now we'll just log it.
        console.warn('Potential API key issue detected.');
      }

      const errorMsg: ChatMessage = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: 'I encountered an error processing your request. Please check your connectivity and try again.'
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-900 overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 p-6 flex flex-col min-w-0 overflow-hidden">
          <ChatInterface 
            messages={chatMessages} 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading} 
          />
        </div>
        <DataViewer tab={activeTab} state={state} />
      </main>
    </div>
  );
};

export default App;