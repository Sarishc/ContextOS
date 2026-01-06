"""Gemini-powered agent with tool calling."""
import json
from typing import Any, Dict, List, Optional, Callable
import google.generativeai as genai
from google.ai import generativelanguage as glm

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import AppException

logger = get_logger(__name__)


class TokenTracker:
    """Track token usage across requests."""
    
    def __init__(self) -> None:
        """Initialize token tracker."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
    
    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add token usage."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_requests": self.total_requests
        }
    
    def reset(self) -> None:
        """Reset counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0


class GeminiToolDispatcher:
    """Dispatcher for tool calls from Gemini."""
    
    def __init__(self) -> None:
        """Initialize tool dispatcher."""
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: List[Dict[str, Any]] = []
        logger.info("GeminiToolDispatcher initialized")
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Register a tool for the agent.
        
        Args:
            name: Tool name
            function: Tool function
            description: Tool description
            parameters: Tool parameters schema
        """
        self.tools[name] = function
        
        # Convert to Gemini function declaration format
        tool_schema = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        
        self.tool_schemas.append(tool_schema)
        logger.info(f"Registered tool: {name}")
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool call.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
        
        try:
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            
            # Execute tool function
            tool_function = self.tools[tool_name]
            result = await tool_function(**arguments)
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for Gemini."""
        return self.tool_schemas


class GeminiAgent:
    """Gemini-powered agent with RAG and tool calling."""
    
    def __init__(self) -> None:
        """Initialize Gemini agent."""
        # Validate API key configuration
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key":
            error_msg = (
                "GEMINI_API_KEY not configured! Set it in .env or environment variables. "
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
            logger.error(error_msg)
            raise AppException(error_msg)
        
        # Configure Gemini API
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            raise AppException(f"Failed to configure Gemini API: {str(e)}")
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": settings.GEMINI_TEMPERATURE,
                "max_output_tokens": settings.GEMINI_MAX_TOKENS,
            }
        )
        
        self.dispatcher = GeminiToolDispatcher()
        self.token_tracker = TokenTracker()
        
        logger.info(f"GeminiAgent initialized with model: {settings.GEMINI_MODEL}")
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Register a tool with the agent."""
        self.dispatcher.register_tool(name, function, description, parameters)
    
    def _build_context(
        self,
        query: str,
        rag_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build context for Gemini.
        
        Args:
            query: User query
            rag_context: Retrieved context from RAG
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # System instructions
        context_parts.append(
            "You are an AI assistant with access to tools and a knowledge base. "
            "Use the provided context to answer questions accurately. "
            "Call tools when needed to get information or perform actions. "
            "Always cite sources when using retrieved information."
        )
        
        # Add RAG context if available
        if rag_context:
            context_parts.append("\n\n=== Retrieved Context ===")
            for i, ctx in enumerate(rag_context[:5], 1):  # Top 5 results
                context_parts.append(f"\n[Source {i}] {ctx.get('title', 'Untitled')}")
                context_parts.append(f"From: {ctx.get('source', 'Unknown')}")
                context_parts.append(f"Content: {ctx.get('content', '')[:500]}...")
        
        # Add user query
        context_parts.append(f"\n\n=== User Query ===\n{query}")
        
        return "\n".join(context_parts)
    
    def _validate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a tool call before execution.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if tool exists
        if tool_name not in self.dispatcher.tools:
            return False, f"Unknown tool: {tool_name}"
        
        # Validate arguments are present
        if not isinstance(arguments, dict):
            return False, "Invalid arguments format"
        
        # Additional validation could be added here
        # (e.g., schema validation, permission checks)
        
        return True, None
    
    async def query(
        self,
        user_query: str,
        rag_context: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process user query with RAG context and tool calling.
        
        Args:
            user_query: User's question
            rag_context: Retrieved context from RAG pipeline
            conversation_history: Previous conversation messages
            
        Returns:
            Response with answer, tool calls, and token usage
        """
        try:
            # Build context
            context = self._build_context(user_query, rag_context)
            
            # Prepare chat with tool schemas
            if self.dispatcher.tool_schemas:
                # Create model with tools
                model_with_tools = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    generation_config={
                        "temperature": settings.GEMINI_TEMPERATURE,
                        "max_output_tokens": settings.GEMINI_MAX_TOKENS,
                    },
                    tools=self.dispatcher.tool_schemas
                )
                
                # Start chat
                chat = model_with_tools.start_chat()
                response = chat.send_message(context)
            else:
                # No tools, use standard model
                response = self.model.generate_content(context)
            
            # Track token usage
            if hasattr(response, 'usage_metadata'):
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                self.token_tracker.add_usage(input_tokens, output_tokens)
            
            # Process response
            tool_calls = []
            final_response = ""
            
            # Check for function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Handle text response
                    if hasattr(part, 'text') and part.text:
                        final_response += part.text
                    
                    # Handle function call
                    if hasattr(part, 'function_call'):
                        fc = part.function_call
                        tool_name = fc.name
                        arguments = dict(fc.args) if fc.args else {}
                        
                        # Validate tool call
                        is_valid, error = self._validate_tool_call(tool_name, arguments)
                        if not is_valid:
                            logger.warning(f"Invalid tool call: {error}")
                            tool_calls.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "error": error,
                                "success": False
                            })
                            continue
                        
                        # Execute tool
                        result = await self.dispatcher.execute_tool(tool_name, arguments)
                        
                        tool_calls.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result,
                            "success": result.get("success", True)
                        })
                        
                        # If we got tool results, send back to model for final response
                        if tool_calls and not final_response:
                            # Create function response
                            function_response = {
                                "name": tool_name,
                                "response": result
                            }
                            
                            # Send function response back to model
                            follow_up = chat.send_message(
                                [glm.Part(function_response=function_response)]
                            )
                            
                            # Get final text response
                            if follow_up.candidates and follow_up.candidates[0].content.parts:
                                for p in follow_up.candidates[0].content.parts:
                                    if hasattr(p, 'text'):
                                        final_response += p.text
            
            return {
                "response": final_response or "No response generated",
                "tool_calls": tool_calls,
                "rag_context_used": len(rag_context) if rag_context else 0,
                "token_usage": self.token_tracker.get_stats(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Gemini agent error: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "tool_calls": [],
                "rag_context_used": 0,
                "token_usage": self.token_tracker.get_stats(),
                "success": False,
                "error": str(e)
            }
    
    def get_token_stats(self) -> Dict[str, int]:
        """Get token usage statistics."""
        return self.token_tracker.get_stats()
    
    def reset_token_stats(self) -> None:
        """Reset token statistics."""
        self.token_tracker.reset()


# Global instance
gemini_agent = GeminiAgent()

