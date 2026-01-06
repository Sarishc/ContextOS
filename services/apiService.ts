// Service to connect to FastAPI backend

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Source {
  document_id: string;
  title: string;
  content: string;
  chunk_id: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface ToolCall {
  name: string;
  args: Record<string, any>;
  result: any;
}

export interface AgentResponse {
  response: string;
  sources?: Source[];
  tool_calls?: ToolCall[];
  tokens_used?: number;
  cost?: number;
  latency_ms?: number;
}

export interface MetricsResponse {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  requests_by_endpoint: Record<string, number>;
}

export interface UsageResponse {
  timestamp: string;
  endpoint: string;
  tokens_used: number;
  cost: number;
  latency_ms: number;
  user_id?: string;
}

class APIService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_URL;
  }

  async query(message: string): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/agent/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: message }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getMetrics(): Promise<MetricsResponse> {
    const response = await fetch(`${this.baseURL}/metrics`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getUsage(limit: number = 100): Promise<UsageResponse[]> {
    const response = await fetch(`${this.baseURL}/usage?limit=${limit}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.usage || [];
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new APIService();

