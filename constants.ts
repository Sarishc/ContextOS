
import { Priority, Document, JiraTicket, SlackMessage, SQLMetric } from './types';

export const MOCK_DOCUMENTS: Document[] = [
  {
    id: 'doc-1',
    title: 'Security Compliance 2024',
    content: 'Our infrastructure uses SOC2 Type II controls. All production data is encrypted at rest using AES-256.',
    tags: ['security', 'compliance']
  },
  {
    id: 'doc-2',
    title: 'Onboarding Guide - Engineering',
    content: 'New engineers should set up their local environment using the script in /scripts/init.sh. VPN is required for staging access.',
    tags: ['onboarding', 'engineering']
  },
  {
    id: 'doc-3',
    title: 'API Rate Limiting Policy',
    content: 'Standard tier users are limited to 1000 requests per minute. Enterprise tier has custom limits.',
    tags: ['api', 'policy']
  }
];

export const MOCK_TICKETS: JiraTicket[] = [
  {
    id: 'ENG-402',
    title: 'Intermittent timeout in payment gateway',
    description: 'Stripe webhooks are occasionally timing out under high load.',
    priority: Priority.HIGH,
    status: 'In Progress'
  },
  {
    id: 'ENG-410',
    title: 'Update OAuth documentation',
    description: 'The readme for the auth service is outdated regarding PKCE.',
    priority: Priority.LOW,
    status: 'To Do'
  }
];

export const MOCK_SLACK: SlackMessage[] = [
  {
    id: 'msg-1',
    channel: '#ops-alerts',
    user: 'CloudWatch-Bot',
    text: 'ALERT: Latency increased for /api/v1/user endpoint in us-east-1.',
    timestamp: '2024-05-20T10:00:00Z'
  },
  {
    id: 'msg-2',
    channel: '#engineering',
    user: 'Sarah',
    text: 'Is anyone else seeing weird login failures? Multiple reports in #support.',
    timestamp: '2024-05-20T10:05:00Z'
  },
  {
    id: 'msg-3',
    channel: '#engineering',
    user: 'David',
    text: 'Checking the logs now. Database seems to be hitting connection limits.',
    timestamp: '2024-05-20T10:10:00Z'
  }
];

export const MOCK_METRICS: SQLMetric[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: `2024-05-20T${i.toString().padStart(2, '0')}:00:00Z`,
  api_latency_ms: 120 + Math.random() * 50 + (i === 10 ? 300 : 0),
  error_rate_pct: 0.1 + Math.random() * 0.5 + (i === 10 ? 4.5 : 0),
  request_count: 5000 + Math.round(Math.random() * 2000)
}));

export const SYSTEM_INSTRUCTION = `You are ContextOS, an advanced AI internal operations assistant for a high-growth startup.
Your goal is to help employees navigate company data, manage engineering workflows, and monitor system health.

You have access to:
1. Internal Documentation (Notion-style)
2. Engineering Tickets (Jira-style)
3. Slack Messages
4. SQL Database Metrics (latency, errors, traffic)

Rules:
- Be concise, professional, and accurate.
- Always explain your reasoning before taking an action.
- If you find relevant information in the documents or slack, cite the source.
- Do not hallucinate metrics. If the run_sql_query tool doesn't return data, state that clearly.
- For Jira tickets, ensure you have a clear title, description, and priority level before calling create_jira_ticket.
- If a request is ambiguous, ask for clarification.

Output Format:
- Use Markdown for structured responses.
- If you call a tool, only provide the tool call JSON as per standard function calling protocols.`;
