## AI Agent Documentation

## Overview

The AI Agent is embedded in the FastAPI application and integrates with the RAG pipeline to provide intelligent responses based on your knowledge base.

## Architecture

```
User Query → Agent Decision → Tool Execution → Response
                ↓                  ↓
         RAG Context          JSON Output
```

## Core Principles

The agent follows strict rules:

1. **Action-Based**: If user intent implies action, call tools
2. **No Fabrication**: Never fabricate tool outputs
3. **Context First**: Always prefer existing context over general knowledge
4. **Valid JSON**: Return only valid JSON when calling tools
5. **Source Attribution**: Always cite sources when using retrieved information

## Components

### 1. Base Agent (`app/services/agent/base.py`)

Defines the agent architecture:

- **AgentContext**: Input context with query, history, and metadata
- **AgentDecision**: Decision on what action to take
- **AgentResponse**: Final response with reasoning and sources
- **Tool**: Tool definition with parameters and execution logic

### 2. RAG Agent (`app/services/agent/rag_agent.py`)

Main agent implementation:

- Integrates with RAG pipeline
- Makes intelligent decisions
- Executes tools safely
- Formats responses with sources

### 3. Tools (`app/services/agent/tools.py`)

Built-in tools:

- `search_documents`: Semantic search through knowledge base
- `get_sources`: List available document sources
- `get_stats`: System statistics
- `create_task`: Create background tasks

## API Endpoints

### Query Agent

**POST /api/v1/agent/query**

Ask the agent a question. It will decide whether to answer directly or call tools.

**Request:**
```json
{
  "query": "How do I reset my password?",
  "conversation_history": [],
  "metadata": {}
}
```

**Response:**
```json
{
  "response": "Based on the available information:\n\nFrom **Password Reset Guide** (docs/auth_guide.txt):\nTo reset your password, go to the login page...",
  "action_taken": "search",
  "reasoning": "Query requires context from knowledge base",
  "tool_calls": [
    {
      "tool": "search_documents",
      "arguments": {"query": "How do I reset my password?", "top_k": 5},
      "result": {...}
    }
  ],
  "context_used": [
    {
      "content": "To reset your password...",
      "source": "docs/auth_guide.txt",
      "title": "Password Reset Guide",
      "score": 0.92
    }
  ],
  "metadata": {}
}
```

### Chat with Agent

**POST /api/v1/agent/chat**

Conversational interface with conversation history.

**Request:**
```json
{
  "query": "Tell me more about that",
  "conversation_history": [
    {"role": "user", "content": "How do I reset my password?"},
    {"role": "assistant", "content": "To reset your password..."}
  ],
  "metadata": {}
}
```

### List Tools

**GET /api/v1/agent/tools**

Get list of available tools the agent can use.

**Response:**
```json
[
  {
    "name": "search_documents",
    "description": "Search through ingested documents using semantic search",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "The search query"},
        "top_k": {"type": "integer", "description": "Number of results"}
      },
      "required": ["query"]
    }
  }
]
```

### Get System Prompt

**GET /api/v1/agent/system-prompt**

View the agent's instructions and rules.

### Health Check

**GET /api/v1/agent/health**

Check agent status and capabilities.

## Decision Making

The agent analyzes queries and decides actions:

### 1. Search Action

Triggered by keywords: "search", "find", "what is", "how to", "tell me about"

```python
Query: "How do I authenticate with the API?"
→ Action: SEARCH
→ Tool: search_documents(query="How do I authenticate with the API?")
→ Response: Context-based answer with sources
```

### 2. Direct Answer

When context is already provided:

```python
Context: [...retrieved documents...]
Query: "What does this mean?"
→ Action: ANSWER
→ Response: Answer using provided context
```

### 3. Tool Call

For specific actions:

```python
Query: "What sources are available?"
→ Action: CALL_TOOL
→ Tool: get_sources()
→ Response: List of sources
```

### 4. Clarification

When more information is needed:

```python
Query: "Create a task"
→ Action: CLARIFY
→ Response: "What type of task would you like me to create?"
```

## Tool System

### Tool Structure

```python
Tool(
    name="tool_name",
    description="What the tool does",
    parameters=[
        ToolParameter(
            name="param_name",
            type="string",
            description="Parameter description",
            required=True
        )
    ],
    function=async_function
)
```

### Creating Custom Tools

```python
from app.services.agent.base import Tool, ToolParameter

async def my_custom_tool(param: str) -> Dict[str, Any]:
    """Custom tool implementation."""
    # Your logic here
    return {"success": True, "result": "..."}

custom_tool = Tool(
    name="my_tool",
    description="Does something useful",
    parameters=[
        ToolParameter(
            name="param",
            type="string",
            description="A parameter",
            required=True
        )
    ],
    function=my_custom_tool
)

# Register with agent
rag_agent.register_tool(custom_tool)
```

## Usage Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/agent"

# Simple query
response = requests.post(
    f"{BASE_URL}/query",
    json={"query": "How do I reset my password?"}
)

result = response.json()
print(f"Response: {result['response']}")
print(f"Action: {result['action_taken']}")
print(f"Sources: {len(result['context_used'])}")

# Conversational
history = []

def chat(message):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "query": message,
            "conversation_history": history
        }
    )
    
    result = response.json()
    
    # Update history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result['response']})
    
    return result['response']

# Chat
print(chat("What documents do we have?"))
print(chat("Search for password reset information"))
print(chat("Show me the statistics"))
```

### cURL Examples

```bash
# Query agent
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?"
  }'

# List tools
curl http://localhost:8000/api/v1/agent/tools

# Get system prompt
curl http://localhost:8000/api/v1/agent/system-prompt

# Health check
curl http://localhost:8000/api/v1/agent/health
```

## Response Format

Every agent response includes:

- **response**: Human-readable answer
- **action_taken**: What action was performed
- **reasoning**: Why that action was chosen
- **tool_calls**: List of tools executed (if any)
- **context_used**: Sources used in the response
- **metadata**: Additional information

## Best Practices

### 1. Query Formulation

Good queries are specific and clear:

✅ "How do I reset my password?"  
✅ "What are the available data sources?"  
✅ "Search for API authentication information"  

❌ "Help"  
❌ "Info"  
❌ "Stuff"  

### 2. Conversation History

Maintain context for better responses:

```python
history = [
    {"role": "user", "content": "What documents do we have?"},
    {"role": "assistant", "content": "We have 3 sources..."},
    {"role": "user", "content": "Tell me more about the first one"}  # Uses context
]
```

### 3. Metadata

Add context to queries:

```python
{
    "query": "Search for tickets",
    "metadata": {
        "user_id": "123",
        "department": "engineering",
        "priority": "high"
    }
}
```

## Error Handling

The agent handles errors gracefully:

```json
{
  "response": "Error executing tool: Connection timeout",
  "action_taken": "answer",
  "reasoning": "Tool execution failed",
  "metadata": {"error": "Connection timeout"}
}
```

## Extending the Agent

### Add New Tools

1. Create tool function
2. Define tool schema
3. Register with agent

```python
# 1. Create function
async def analyze_sentiment(text: str) -> Dict[str, Any]:
    # Sentiment analysis logic
    return {"sentiment": "positive", "score": 0.95}

# 2. Define tool
sentiment_tool = Tool(
    name="analyze_sentiment",
    description="Analyze sentiment of text",
    parameters=[
        ToolParameter(
            name="text",
            type="string",
            description="Text to analyze",
            required=True
        )
    ],
    function=analyze_sentiment
)

# 3. Register
rag_agent.register_tool(sentiment_tool)
```

### Custom Agent

Extend the base agent:

```python
from app.services.agent.base import BaseAgent, AgentContext, AgentDecision

class MyCustomAgent(BaseAgent):
    async def decide(self, context: AgentContext) -> AgentDecision:
        # Custom decision logic
        pass
    
    async def execute(self, decision: AgentDecision, context: AgentContext):
        # Custom execution logic
        pass
```

## Integration with RAG

The agent automatically uses RAG for:

1. **Semantic Search**: Finds relevant documents
2. **Source Attribution**: Cites sources in responses
3. **Context Building**: Gathers information before answering
4. **Relevance Filtering**: Uses similarity scores

## Performance

- **Decision Time**: <10ms
- **Tool Execution**: Varies by tool (search: ~100ms)
- **Response Generation**: <50ms
- **End-to-End**: Typically <200ms

## Monitoring

Check agent performance:

```bash
# Health check
curl http://localhost:8000/api/v1/agent/health

# View logs
docker-compose logs -f api | grep -i "agent"
```

## Security Considerations

- **Input Validation**: All inputs are validated
- **Tool Sandboxing**: Tools execute in controlled environment
- **Rate Limiting**: Consider adding rate limits for production
- **Authentication**: Add auth middleware for production use

## Troubleshooting

### Agent Not Responding

1. Check agent health: `GET /api/v1/agent/health`
2. Verify RAG pipeline is working: `GET /api/v1/rag/stats`
3. Check logs: `docker-compose logs -f api`

### Tool Execution Fails

1. Verify tool is registered: `GET /api/v1/agent/tools`
2. Check tool function implementation
3. Review error in response metadata

### Poor Responses

1. Verify documents are ingested: `GET /api/v1/rag/sources`
2. Test search directly: `POST /api/v1/rag/search`
3. Check embedding quality and index

## Future Enhancements

- [ ] Memory and conversation persistence
- [ ] Multi-agent collaboration
- [ ] Custom tool marketplace
- [ ] Advanced reasoning (chain-of-thought)
- [ ] Integration with external AI models (OpenAI, Anthropic)
- [ ] A/B testing for decision strategies
- [ ] Agent analytics and metrics

## Resources

- **API Documentation**: http://localhost:8000/docs#/agent
- **RAG Pipeline**: [RAG_PIPELINE.md](RAG_PIPELINE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Main README**: [README.md](README.md)

