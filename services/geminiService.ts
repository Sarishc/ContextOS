import { GoogleGenAI, Type, FunctionDeclaration, Content } from "@google/genai";
import { SYSTEM_INSTRUCTION } from "../constants";
import { AppState } from "../types";

const SEARCH_DOCUMENTS_DECLARATION: FunctionDeclaration = {
  name: 'search_documents',
  parameters: {
    type: Type.OBJECT,
    description: 'Search internal company documentation for keywords or topics.',
    properties: {
      query: {
        type: Type.STRING,
        description: 'The search query or keywords to find in documents.',
      },
    },
    required: ['query'],
  },
};

const CREATE_JIRA_TICKET_DECLARATION: FunctionDeclaration = {
  name: 'create_jira_ticket',
  parameters: {
    type: Type.OBJECT,
    description: 'Create a new engineering ticket in Jira.',
    properties: {
      title: {
        type: Type.STRING,
        description: 'A brief, descriptive title for the issue.',
      },
      description: {
        type: Type.STRING,
        description: 'Detailed explanation of the issue or requirement.',
      },
      priority: {
        type: Type.STRING,
        description: 'The priority level: Low, Medium, High, or Urgent.',
        enum: ['Low', 'Medium', 'High', 'Urgent']
      },
    },
    required: ['title', 'description', 'priority'],
  },
};

const RUN_SQL_QUERY_DECLARATION: FunctionDeclaration = {
  name: 'run_sql_query',
  parameters: {
    type: Type.OBJECT,
    description: 'Execute a SQL query against the internal metrics database to get system health data.',
    properties: {
      query: {
        type: Type.STRING,
        description: 'The SQL SELECT statement. Valid tables: metrics. Columns: timestamp, api_latency_ms, error_rate_pct, request_count.',
      },
    },
    required: ['query'],
  },
};

const POST_SLACK_SUMMARY_DECLARATION: FunctionDeclaration = {
  name: 'post_slack_summary',
  parameters: {
    type: Type.OBJECT,
    description: 'Post a message or summary to a specific Slack channel.',
    properties: {
      channel: {
        type: Type.STRING,
        description: 'The slack channel name starting with #.',
      },
      message: {
        type: Type.STRING,
        description: 'The message content to post.',
      },
    },
    required: ['channel', 'message'],
  },
};

export interface ToolResult {
  name: string;
  result: any;
  id: string;
  args: any;
}

export class AgentService {
  private state: AppState;

  constructor(initialState: AppState) {
    this.state = initialState;
  }

  updateState(newState: AppState) {
    this.state = newState;
  }

  async processMessage(userMessage: string, history: Content[] = []): Promise<{ 
    text?: string; 
    toolResults?: ToolResult[];
    finalResponse?: string;
  }> {
    // Creating a fresh instance to ensure correct API key usage
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const model = 'gemini-3-pro-preview';
    
    // 1. Initial Call: Decide whether to act or answer
    const response = await ai.models.generateContent({
      model,
      contents: [
        ...history,
        { role: 'user', parts: [{ text: userMessage }] }
      ],
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        thinkingConfig: { thinkingBudget: 32768 },
        tools: [{
          functionDeclarations: [
            SEARCH_DOCUMENTS_DECLARATION,
            CREATE_JIRA_TICKET_DECLARATION,
            RUN_SQL_QUERY_DECLARATION,
            POST_SLACK_SUMMARY_DECLARATION
          ]
        }],
      },
    });

    // 2. Handle Action (Tool Call)
    if (response.functionCalls && response.functionCalls.length > 0) {
      const toolResults: ToolResult[] = response.functionCalls.map(call => ({
        name: call.name,
        id: call.id,
        args: call.args,
        result: this.executeTool(call.name, call.args)
      }));

      // 3. Final Call: Integrate tool results into a human-readable response
      const finalResponse = await ai.models.generateContent({
        model,
        contents: [
          ...history,
          { role: 'user', parts: [{ text: userMessage }] },
          { 
            role: 'model', 
            parts: response.functionCalls.map(call => ({
              functionCall: { name: call.name, args: call.args, id: call.id }
            }))
          },
          {
            role: 'user',
            parts: toolResults.map(tr => ({
              functionResponse: { name: tr.name, id: tr.id, response: tr.result }
            }))
          }
        ],
        config: { 
          systemInstruction: SYSTEM_INSTRUCTION,
          thinkingConfig: { thinkingBudget: 32768 }
        }
      });

      return { 
        toolResults, 
        finalResponse: finalResponse.text 
      };
    }

    return { text: response.text };
  }

  /**
   * Mock tool execution logic. 
   * In a real FastAPI setup, these would be replaced by actual API calls.
   */
  private executeTool(name: string, args: any): any {
    switch (name) {
      case 'search_documents':
        const q = (args.query || '').toLowerCase();
        const results = this.state.documents.filter(d => 
          d.title.toLowerCase().includes(q) || d.content.toLowerCase().includes(q)
        ).map(d => ({ title: d.title, snippet: d.content.substring(0, 150) + '...' }));
        return results.length > 0 ? results : { message: "No documents matching that query were found." };

      case 'create_jira_ticket':
        const newId = `ENG-${Math.floor(Math.random() * 900) + 500}`;
        // Simulation of a successful database write
        return { success: true, ticketId: newId, status: "Created", timestamp: new Date().toISOString() };

      case 'run_sql_query':
        const query = (args.query || '').toLowerCase();
        if (query.includes('latency')) {
          return this.state.metrics.map(m => ({ 
            timestamp: m.timestamp, 
            latency_ms: m.api_latency_ms 
          }));
        }
        if (query.includes('error')) {
          return this.state.metrics.map(m => ({ 
            timestamp: m.timestamp, 
            error_rate: m.error_rate_pct 
          }));
        }
        return this.state.metrics.slice(-5);

      case 'post_slack_summary':
        return { success: true, message: `Successfully posted to ${args.channel}` };

      default:
        return { error: `Tool ${name} is not implemented yet.` };
    }
  }
}