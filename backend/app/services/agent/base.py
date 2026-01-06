"""Base classes for AI agent system."""
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class ActionType(str, Enum):
    """Type of action the agent can take."""
    
    ANSWER = "answer"
    CALL_TOOL = "call_tool"
    SEARCH = "search"
    CLARIFY = "clarify"


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class Tool(BaseModel):
    """Tool definition for agent."""
    
    name: str
    description: str
    parameters: List[ToolParameter]
    function: Optional[Callable] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert tool to JSON schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description
                    }
                    for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }


class AgentDecision(BaseModel):
    """Agent's decision on how to respond."""
    
    action: ActionType
    reasoning: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    requires_context: bool = False
    context_query: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent's final response."""
    
    response: str
    action_taken: ActionType
    reasoning: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    context_used: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Context provided to the agent."""
    
    user_query: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for AI agents."""
    
    def __init__(self, name: str, tools: Optional[List[Tool]] = None) -> None:
        """Initialize agent."""
        self.name = name
        self.tools = {tool.name: tool for tool in (tools or [])}
    
    @abstractmethod
    async def decide(self, context: AgentContext) -> AgentDecision:
        """
        Decide what action to take based on context.
        
        Args:
            context: Agent context with query and available information
            
        Returns:
            Decision on what action to take
        """
        pass
    
    @abstractmethod
    async def execute(self, decision: AgentDecision, context: AgentContext) -> AgentResponse:
        """
        Execute the decided action.
        
        Args:
            decision: The decision made by the agent
            context: Agent context
            
        Returns:
            Final response
        """
        pass
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user query end-to-end.
        
        Args:
            context: Agent context
            
        Returns:
            Agent response
        """
        # Make decision
        decision = await self.decide(context)
        
        # Execute decision
        response = await self.execute(decision, context)
        
        return response
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools as JSON schemas."""
        return [tool.to_json_schema() for tool in self.tools.values()]

