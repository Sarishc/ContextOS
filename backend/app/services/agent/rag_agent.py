"""RAG-integrated AI agent."""
import json
from typing import Any, Dict, List, Optional
from app.services.agent.base import (
    BaseAgent,
    AgentContext,
    AgentDecision,
    AgentResponse,
    ActionType,
    Tool
)
from app.services.agent.tools import get_default_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGAgent(BaseAgent):
    """
    AI Agent that integrates with RAG pipeline.
    
    Rules:
    1. If user intent implies action, call tools
    2. Never fabricate tool outputs
    3. Always prefer existing context
    4. Return only valid JSON when calling tools
    """
    
    def __init__(
        self,
        name: str = "RAGAgent",
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None
    ) -> None:
        """Initialize RAG agent."""
        # Use default tools if none provided
        if tools is None:
            tools = get_default_tools()
        
        super().__init__(name, tools)
        
        self.system_prompt = system_prompt or self._get_default_prompt()
        logger.info(f"Initialized {name} with {len(self.tools)} tools")
    
    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are an AI agent embedded in a FastAPI application with access to a RAG knowledge base.

Rules:
1. If user intent implies an action (search, get info, create task), call the appropriate tool
2. NEVER fabricate tool outputs - only use actual returned data
3. ALWAYS prefer using retrieved context over general knowledge
4. Return ONLY valid JSON when calling tools
5. Be concise and accurate in responses
6. Cite sources when using retrieved information

Available capabilities:
- Search documents using semantic search
- Get information about available sources
- Create background tasks
- Get system statistics

When unsure, ask for clarification rather than guessing."""
    
    async def decide(self, context: AgentContext) -> AgentDecision:
        """
        Decide what action to take based on user query.
        
        Args:
            context: Agent context with query and available information
            
        Returns:
            Decision on what action to take
        """
        query = context.user_query.lower()
        
        # Check if context is already provided
        if context.retrieved_context:
            return AgentDecision(
                action=ActionType.ANSWER,
                reasoning="Context already provided, can answer directly",
                response=None,
                requires_context=False
            )
        
        # Check for action keywords
        action_keywords = {
            "search": ["search", "find", "look for", "show me", "what is", "how to", "tell me about"],
            "sources": ["sources", "available", "what data", "list documents", "what documents"],
            "stats": ["stats", "statistics", "how many", "count", "status", "health"],
            "task": ["create", "start", "run", "execute", "process"]
        }
        
        # Determine action
        for action, keywords in action_keywords.items():
            if any(keyword in query for keyword in keywords):
                if action == "search":
                    return AgentDecision(
                        action=ActionType.CALL_TOOL,
                        reasoning="User query requires searching the knowledge base",
                        tool_name="search_documents",
                        tool_arguments={"query": context.user_query, "top_k": 5}
                    )
                elif action == "sources":
                    return AgentDecision(
                        action=ActionType.CALL_TOOL,
                        reasoning="User wants to know about available sources",
                        tool_name="get_sources",
                        tool_arguments={}
                    )
                elif action == "stats":
                    return AgentDecision(
                        action=ActionType.CALL_TOOL,
                        reasoning="User wants system statistics",
                        tool_name="get_stats",
                        tool_arguments={}
                    )
                elif action == "task":
                    # For tasks, we might need more info
                    return AgentDecision(
                        action=ActionType.CLARIFY,
                        reasoning="Need more details about the task to create",
                        response="What type of task would you like me to create? Please provide details."
                    )
        
        # Default: search for relevant context
        return AgentDecision(
            action=ActionType.SEARCH,
            reasoning="Query requires context from knowledge base",
            requires_context=True,
            context_query=context.user_query
        )
    
    async def execute(self, decision: AgentDecision, context: AgentContext) -> AgentResponse:
        """
        Execute the decided action.
        
        Args:
            decision: The decision made by the agent
            context: Agent context
            
        Returns:
            Final response
        """
        tool_calls = []
        context_used = context.retrieved_context.copy()
        
        if decision.action == ActionType.CALL_TOOL:
            # Execute tool
            if not decision.tool_name or decision.tool_name not in self.tools:
                return AgentResponse(
                    response=f"Error: Tool '{decision.tool_name}' not found",
                    action_taken=ActionType.ANSWER,
                    reasoning="Tool not available",
                    metadata={"error": "tool_not_found"}
                )
            
            tool = self.tools[decision.tool_name]
            
            try:
                # Call tool function
                logger.info(f"Calling tool: {tool.name} with args: {decision.tool_arguments}")
                
                tool_result = await tool.function(**decision.tool_arguments)
                
                tool_calls.append({
                    "tool": tool.name,
                    "arguments": decision.tool_arguments,
                    "result": tool_result
                })
                
                # Format response based on tool result
                response = self._format_tool_response(tool.name, tool_result)
                
                return AgentResponse(
                    response=response,
                    action_taken=ActionType.CALL_TOOL,
                    reasoning=decision.reasoning,
                    tool_calls=tool_calls,
                    context_used=context_used,
                    metadata={"tool_used": tool.name}
                )
                
            except Exception as e:
                logger.error(f"Error executing tool {tool.name}: {e}")
                return AgentResponse(
                    response=f"Error executing tool: {str(e)}",
                    action_taken=ActionType.ANSWER,
                    reasoning="Tool execution failed",
                    tool_calls=tool_calls,
                    metadata={"error": str(e)}
                )
        
        elif decision.action == ActionType.SEARCH:
            # Perform search and then answer
            search_tool = self.tools.get("search_documents")
            if search_tool:
                try:
                    search_result = await search_tool.function(
                        query=decision.context_query or context.user_query,
                        top_k=5
                    )
                    
                    tool_calls.append({
                        "tool": "search_documents",
                        "arguments": {"query": decision.context_query or context.user_query},
                        "result": search_result
                    })
                    
                    # Add to context
                    context_used = search_result.get("results", [])
                    
                    # Generate response using context
                    response = self._generate_response_with_context(
                        context.user_query,
                        context_used
                    )
                    
                    return AgentResponse(
                        response=response,
                        action_taken=ActionType.SEARCH,
                        reasoning=decision.reasoning,
                        tool_calls=tool_calls,
                        context_used=context_used
                    )
                    
                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    return AgentResponse(
                        response=f"I encountered an error while searching: {str(e)}",
                        action_taken=ActionType.ANSWER,
                        reasoning="Search failed",
                        metadata={"error": str(e)}
                    )
        
        elif decision.action == ActionType.CLARIFY:
            return AgentResponse(
                response=decision.response or "Could you please provide more details?",
                action_taken=ActionType.CLARIFY,
                reasoning=decision.reasoning
            )
        
        elif decision.action == ActionType.ANSWER:
            # Direct answer using provided context
            if context_used:
                response = self._generate_response_with_context(
                    context.user_query,
                    context_used
                )
            else:
                response = "I don't have enough information to answer that question. Try searching the knowledge base first."
            
            return AgentResponse(
                response=response,
                action_taken=ActionType.ANSWER,
                reasoning=decision.reasoning,
                context_used=context_used
            )
        
        # Default response
        return AgentResponse(
            response="I'm not sure how to handle that request.",
            action_taken=ActionType.ANSWER,
            reasoning="Unknown action type"
        )
    
    def _format_tool_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool result into human-readable response."""
        if not result.get("success"):
            return f"Tool execution failed: {result.get('error', 'Unknown error')}"
        
        if tool_name == "search_documents":
            results = result.get("results", [])
            if not results:
                return "No results found for your query."
            
            response = f"Found {len(results)} relevant results:\n\n"
            for i, r in enumerate(results, 1):
                response += f"{i}. **{r['title']}** (Source: {r['source']}, Score: {r['score']:.2f})\n"
                response += f"   {r['content'][:200]}...\n\n"
            
            return response
        
        elif tool_name == "get_sources":
            sources = result.get("sources", [])
            total_docs = result.get("total_documents", 0)
            
            response = f"Available Sources ({total_docs} total documents):\n\n"
            for source in sources:
                response += f"- **{source['source']}** ({source['doc_type']}): "
                response += f"{source['document_count']} documents, {source['chunk_count']} chunks\n"
            
            return response
        
        elif tool_name == "get_stats":
            db_stats = result.get("database", {})
            vector_stats = result.get("vector_store", {})
            
            response = "System Statistics:\n\n"
            response += f"**Database:**\n"
            response += f"- Documents: {db_stats.get('total_documents', 0)}\n"
            response += f"- Chunks: {db_stats.get('total_chunks', 0)}\n"
            response += f"- Sources: {db_stats.get('total_sources', 0)}\n\n"
            response += f"**Vector Store:**\n"
            response += f"- Indexed Vectors: {vector_stats.get('total_vectors', 0)}\n"
            response += f"- Dimensions: {vector_stats.get('vector_dim', 0)}\n"
            
            return response
        
        # Default: return JSON
        return json.dumps(result, indent=2)
    
    def _generate_response_with_context(
        self,
        query: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Generate response using retrieved context."""
        if not context:
            return "I don't have enough context to answer your question."
        
        response = "Based on the available information:\n\n"
        
        for item in context[:3]:  # Use top 3 results
            content = item.get("content", "")
            source = item.get("source", "Unknown")
            title = item.get("title", "Untitled")
            
            response += f"From **{title}** ({source}):\n"
            response += f"{content[:300]}...\n\n"
        
        response += f"\n*Based on {len(context)} source(s)*"
        
        return response


# Global agent instance
rag_agent = RAGAgent()

