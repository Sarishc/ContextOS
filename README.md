# ContextOS AI Assistant

ContextOS is an advanced internal operations AI agent designed for high-growth startups. It integrates seamlessly with company documentation, engineering workflows (Jira), messaging (Slack), and real-time database metrics to provide a unified operational intelligence layer.

## 🚀 Repository
This project is maintained at: [https://github.com/Sarishc/ContextOS](https://github.com/Sarishc/ContextOS)

## ✨ Features

- **Agent Console**: A command-center style interface for interacting with the Gemini-powered reasoning engine.
- **Unified Knowledge Base**: Instant retrieval from internal docs with citation capabilities.
- **Automated Workflows**: Create Jira tickets and post Slack summaries directly through natural language.
- **Real-time Observability**: SQL-backed metrics visualization for system health (latency, error rates, throughput).
- **Tool-Augmented Reasoning**: Uses Gemini's latest function calling capabilities to interact with mock/real infrastructure.

## 🛠️ Tech Stack

- **Frontend**: React 19 (ESM), Tailwind CSS, Lucide Icons.
- **AI Core**: Google Gemini 3 Pro (`gemini-3-pro-preview`) via `@google/genai`.
- **Logic**: TypeScript with strict typing for operational data structures.

## 🏁 Getting Started

### 1. Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation
```bash
git clone https://github.com/Sarishc/ContextOS.git
cd ContextOS
npm install
```

### 3. Environment Configuration
The application expects an `API_KEY` environment variable. Ensure your execution environment has access to it.
```env
API_KEY=your_gemini_api_key_here
```

### 4. Development
```bash
npm run dev
```

## 🧠 Operational Tools (Function Calling)

ContextOS leverages specialized tools to bridge the gap between LLM reasoning and company data:
- `search_documents(query)`: Vector-like search over company knowledge.
- `create_jira_ticket(title, description, priority)`: Direct engineering task automation.
- `run_sql_query(query)`: Real-time system health interrogation.
- `post_slack_summary(channel, message)`: Cross-team communication automation.

## 📁 Project Map
- `App.tsx`: Main application entry and state coordinator.
- `services/geminiService.ts`: Agent reasoning logic and tool execution.
- `components/`: Modular UI units (Sidebar, Chat, DataViewer).
- `constants.ts`: Mock operational datasets and system prompts.
- `types.ts`: Domain-specific interface definitions.

## 🔗 Extension for Cursor
This codebase is ready for backend extension. To integrate real services:
1. Navigate to `services/geminiService.ts`.
2. Update the `executeTool` method to dispatch `fetch` requests to your Node/Python API endpoints.
3. Configure authentication headers for Jira/Slack OAuth integrations.
