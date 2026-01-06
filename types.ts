
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

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolCalls?: any[];
  id: string;
}

export interface AppState {
  tickets: JiraTicket[];
  messages: SlackMessage[];
  documents: Document[];
  metrics: SQLMetric[];
}
