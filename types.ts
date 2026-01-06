
export enum Priority {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  URGENT = 'Urgent'
}

export interface JiraTicket {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  status: 'To Do' | 'In Progress' | 'Done';
}

export interface SlackMessage {
  id: string;
  channel: string;
  user: string;
  text: string;
  timestamp: string;
}

export interface Document {
  id: string;
  title: string;
  content: string;
  tags: string[];
}

export interface SQLMetric {
  timestamp: string;
  api_latency_ms: number;
  error_rate_pct: number;
  request_count: number;
}

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

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolCalls?: ToolCall[];
  sources?: Source[];
  tokens?: number;
  cost?: number;
  latency?: number;
  id: string;
}

export interface AppState {
  tickets: JiraTicket[];
  messages: SlackMessage[];
  documents: Document[];
  metrics: SQLMetric[];
}
