
import React from 'react';
import { 
  Terminal, 
  FileText, 
  Trello, 
  Hash, 
  Database, 
  Activity,
  Zap
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  backendStatus: 'online' | 'offline' | 'checking';
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, backendStatus }) => {
  const navItems = [
    { id: 'chat', label: 'Agent Console', icon: Terminal },
    { id: 'metrics', label: 'Dashboard', icon: Activity },
  ];

  return (
    <div className="w-64 bg-slate-900 text-slate-300 flex flex-col h-full border-r border-slate-800">
      <div className="p-6 flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-lg">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <h1 className="font-bold text-white text-lg tracking-tight">ContextOS</h1>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeTab === item.id 
                ? 'bg-indigo-600/10 text-indigo-400 font-medium' 
                : 'hover:bg-slate-800 hover:text-white'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 mt-auto">
        <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${
              backendStatus === 'online' ? 'bg-emerald-500 animate-pulse' :
              backendStatus === 'offline' ? 'bg-rose-500' :
              'bg-amber-500 animate-pulse'
            }`} />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Backend</span>
          </div>
          <div className="text-sm text-slate-300">
            {backendStatus === 'online' ? 'Connected' :
             backendStatus === 'offline' ? 'Offline' :
             'Checking...'}
          </div>
          <div className="mt-2 text-[10px] text-slate-500 font-mono">
            {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
