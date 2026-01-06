
import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  DollarSign,
  Clock,
  Zap,
  TrendingUp,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { apiService, MetricsResponse, UsageResponse } from '../services/apiService';

interface DataViewerProps {
  tab: string;
}

const DataViewer: React.FC<DataViewerProps> = ({ tab }) => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [usage, setUsage] = useState<UsageResponse[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tab === 'metrics') {
      loadMetrics();
    }
  }, [tab]);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const [metricsData, usageData] = await Promise.all([
        apiService.getMetrics(),
        apiService.getUsage(20)
      ]);
      setMetrics(metricsData);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    switch (tab) {
      case 'metrics':
        if (loading) {
          return (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="w-8 h-8 text-slate-300 animate-spin" />
            </div>
          );
        }

        if (!metrics) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-4">
              <Activity className="w-12 h-12" />
              <p className="text-sm">No metrics available</p>
              <button
                onClick={loadMetrics}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm hover:bg-indigo-700"
              >
                Load Metrics
              </button>
            </div>
          );
        }

        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-800">System Metrics</h3>
              <button
                onClick={loadMetrics}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="w-3.5 h-3.5 text-indigo-600" />
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Total Requests</div>
                </div>
                <div className="text-xl font-bold text-slate-800">{metrics.total_requests}</div>
              </div>
              
              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="w-3.5 h-3.5 text-emerald-600" />
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Avg Latency</div>
                </div>
                <div className="text-xl font-bold text-slate-800">{metrics.avg_latency_ms.toFixed(0)}ms</div>
              </div>

              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Total Tokens</div>
                </div>
                <div className="text-xl font-bold text-slate-800">{metrics.total_tokens.toLocaleString()}</div>
              </div>

              <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="w-3.5 h-3.5 text-rose-600" />
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Total Cost</div>
                </div>
                <div className="text-xl font-bold text-slate-800">${metrics.total_cost.toFixed(4)}</div>
              </div>
            </div>

            {/* Endpoint Breakdown */}
            <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
              <h4 className="text-xs font-bold text-slate-800 mb-3 uppercase tracking-wider">Requests by Endpoint</h4>
              <div className="space-y-2">
                {Object.entries(metrics.requests_by_endpoint).map(([endpoint, count]) => (
                  <div key={endpoint} className="flex items-center justify-between">
                    <span className="text-xs text-slate-600 font-mono">{endpoint}</span>
                    <span className="text-xs font-bold text-slate-800">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Usage */}
            <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
              <h4 className="text-xs font-bold text-slate-800 mb-3 uppercase tracking-wider">Recent Queries</h4>
              <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {usage.map((item, idx) => (
                  <div key={idx} className="flex items-start justify-between gap-2 pb-2 border-b border-slate-50 last:border-0">
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] text-slate-400">{new Date(item.timestamp).toLocaleString()}</div>
                      <div className="text-xs font-mono text-slate-600 truncate">{item.endpoint}</div>
                    </div>
                    <div className="flex flex-col items-end text-[10px]">
                      <span className="text-slate-600">{item.tokens_used} tokens</span>
                      <span className="text-slate-500">${item.cost.toFixed(4)}</span>
                      <span className="text-slate-400">{item.latency_ms.toFixed(0)}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-4 opacity-50">
            <Activity className="w-12 h-12" />
            <p className="text-sm font-medium">Select a view</p>
          </div>
        );
    }
  };

  const getTitle = () => {
    switch(tab) {
      case 'metrics': return 'Performance Dashboard';
      default: return 'System View';
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
