
import React from 'react';
import { AppState, Priority } from '../types';
import { 
  FileText, 
  Trello, 
  Hash, 
  Activity, 
  Clock, 
  AlertCircle,
  ExternalLink,
  ChevronRight
} from 'lucide-react';

interface DataViewerProps {
  tab: string;
  state: AppState;
}

const DataViewer: React.FC<DataViewerProps> = ({ tab, state }) => {
  const renderContent = () => {
    switch (tab) {
      case 'docs':
        return (
          <div className="space-y-4">
            {state.documents.map(doc => (
              <div key={doc.id} className="p-4 bg-white rounded-2xl border border-slate-100 hover:border-indigo-200 transition-colors shadow-sm group">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span className="font-semibold text-slate-800 text-sm">{doc.title}</span>
                </div>
                <p className="text-xs text-slate-500 line-clamp-3 mb-3 leading-relaxed">{doc.content}</p>
                <div className="flex flex-wrap gap-1">
                  {doc.tags.map(tag => (
                    <span key={tag} className="px-2 py-0.5 bg-slate-100 rounded text-[10px] text-slate-600 font-medium">#{tag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        );

      case 'jira':
        return (
          <div className="space-y-4">
            {state.tickets.map(ticket => (
              <div key={ticket.id} className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">{ticket.id}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                    ticket.priority === Priority.URGENT ? 'bg-rose-50 text-rose-600' :
                    ticket.priority === Priority.HIGH ? 'bg-orange-50 text-orange-600' :
                    'bg-sky-50 text-sky-600'
                  }`}>
                    {ticket.priority}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-800 mb-1">{ticket.title}</h4>
                <p className="text-xs text-slate-500 mb-3">{ticket.description}</p>
                <div className="flex items-center gap-2 pt-3 border-t border-slate-50">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{ticket.status}</span>
                </div>
              </div>
            ))}
          </div>
        );

      case 'slack':
        return (
          <div className="space-y-3">
            {state.messages.map(msg => (
              <div key={msg.id} className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-600">{msg.channel}</span>
                  <span className="text-[10px] text-slate-400">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-5 h-5 bg-slate-200 rounded-full flex items-center justify-center text-[10px] font-bold text-slate-600">
                    {msg.user[0]}
                  </div>
                  <span className="text-[11px] font-bold text-slate-700">{msg.user}</span>
                </div>
                <p className="text-xs text-slate-600">{msg.text}</p>
              </div>
            ))}
          </div>
        );

      case 'metrics':
        const latest = state.metrics[state.metrics.length - 1];
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Avg Latency</div>
                <div className="text-xl font-bold text-slate-800">{Math.round(latest.api_latency_ms)}ms</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Error Rate</div>
                <div className={`text-xl font-bold ${latest.error_rate_pct > 1 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {latest.error_rate_pct.toFixed(2)}%
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-slate-900 rounded-2xl shadow-lg shadow-slate-200 overflow-hidden relative">
              <div className="flex items-center justify-between mb-4">
                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Historical Trend</div>
                <Activity className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex items-end gap-1 h-32">
                {state.metrics.slice(-15).map((m, idx) => (
                  <div 
                    key={idx} 
                    className={`flex-1 rounded-t-sm transition-all hover:bg-white ${
                      m.error_rate_pct > 2 ? 'bg-rose-500' : 'bg-emerald-500/60'
                    }`} 
                    style={{ height: `${Math.min(100, (m.api_latency_ms / 400) * 100)}%` }}
                  />
                ))}
              </div>
              <div className="mt-3 text-[10px] font-mono text-slate-500 text-center">API Latency (24h Window)</div>
            </div>

            <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
              <h4 className="text-xs font-bold text-slate-800 mb-3 uppercase tracking-wider">System Alerts</h4>
              <div className="space-y-2">
                <div className="flex items-start gap-3 p-2 rounded-lg bg-rose-50 border border-rose-100">
                  <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5" />
                  <div>
                    <div className="text-[11px] font-bold text-rose-900">High Connection Latency</div>
                    <div className="text-[10px] text-rose-700">Database cluster "db-prod-1" at 89% capacity</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-4 opacity-50">
            <Trello className="w-12 h-12" />
            <p className="text-sm font-medium">Select a system to inspect</p>
          </div>
        );
    }
  };

  const getTitle = () => {
    switch(tab) {
      case 'docs': return 'Internal Docs';
      case 'jira': return 'Engineering Flow';
      case 'slack': return 'Recent Comms';
      case 'metrics': return 'Core Metrics';
      default: return 'System Inspector';
    }
  }

  return (
    <div className="w-96 flex flex-col h-full bg-slate-50/50 p-6 border-l border-slate-100 overflow-y-auto custom-scrollbar">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-bold text-slate-900 flex items-center gap-2">
          {getTitle()}
        </h3>
        <button className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-indigo-600 transition-colors">
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
      {renderContent()}
    </div>
  );
};

export default DataViewer;
