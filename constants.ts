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

export const SYSTEM_INSTRUCTION = `You are an AI agent embedded inside a FastAPI application (ContextOS).
Your role is to act as an internal operations assistant for a startup.

You can:
- Read retrieved context from documentation, engineering tickets, and Slack messages.
- Decide whether to answer a question directly or take an action using tools.
- Call tools when required to fulfill user requests.

Rules:
- If user intent implies an action (e.g., "create a ticket", "post a summary", "check metrics"), you MUST call the appropriate tool.
- Never fabricate tool outputs, metrics, or data. If a tool returns no data, report it accurately.
- Always prefer existing context provided in the conversation history or tool outputs.
- If information is missing to perform an action (e.g., no priority for a ticket), ask a clarifying question.
- RETURN ONLY valid JSON when calling tools (no conversational filler before the JSON block).
- Be concise, accurate, and source-aware. Cite Slack channels or document titles where relevant.

Available Tools:
- search_documents(query): Search company wiki/Notion docs.
- create_jira_ticket(title, description, priority): Create engineering issues.
- run_sql_query(query): Query metrics database (latency, errors).
- post_slack_summary(channel, message): Send updates to Slack.`;