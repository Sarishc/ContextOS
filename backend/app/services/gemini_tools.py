"""Tool registration for Gemini agent."""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gemini_agent import gemini_agent
from app.services.mock_services import jira_service, slack_service
from app.services.safe_sql import sql_executor
from app.services.search_service import search_service
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


# Tool implementations

async def search_knowledge_base(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search the knowledge base using RAG.
    
    Args:
        query: Search query
        top_k: Number of results
        
    Returns:
        Search results
    """
    async with AsyncSessionLocal() as db:
        try:
            results, execution_time = await search_service.search(
                db=db,
                query=query,
                top_k=top_k
            )
            
            return {
                "success": True,
                "results": [
                    {
                        "title": r.document_title,
                        "content": r.chunk_content,
                        "source": r.document_source,
                        "score": r.similarity_score
                    }
                    for r in results
                ],
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


async def get_jira_ticket(ticket_id: str) -> Dict[str, Any]:
    """
    Get Jira ticket by ID.
    
    Args:
        ticket_id: Ticket ID (e.g., "PROJ-101")
        
    Returns:
        Ticket information
    """
    ticket = await jira_service.get_ticket(ticket_id)
    if ticket:
        return {"success": True, "ticket": ticket}
    return {"success": False, "error": "Ticket not found"}


async def search_jira_tickets(
    query: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search Jira tickets.
    
    Args:
        query: Search text
        status: Filter by status
        priority: Filter by priority
        
    Returns:
        Matching tickets
    """
    tickets = await jira_service.search_tickets(query, status, priority)
    return {
        "success": True,
        "tickets": tickets,
        "count": len(tickets)
    }


async def create_jira_ticket(
    title: str,
    description: str,
    priority: str = "Medium"
) -> Dict[str, Any]:
    """
    Create a new Jira ticket.
    
    Args:
        title: Ticket title
        description: Ticket description
        priority: Priority level
        
    Returns:
        Created ticket
    """
    ticket = await jira_service.create_ticket(title, description, priority)
    return {"success": True, "ticket": ticket}


async def search_slack_messages(
    query: str,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search Slack messages.
    
    Args:
        query: Search query
        channel: Optional channel filter
        
    Returns:
        Matching messages
    """
    messages = await slack_service.search_messages(query, channel)
    return {
        "success": True,
        "messages": messages,
        "count": len(messages)
    }


async def get_slack_channel_messages(
    channel: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get recent messages from a Slack channel.
    
    Args:
        channel: Channel name
        limit: Number of messages
        
    Returns:
        Channel messages
    """
    messages = await slack_service.get_channel_messages(channel, limit)
    return {
        "success": True,
        "channel": channel,
        "messages": messages,
        "count": len(messages)
    }


async def post_slack_message(
    channel: str,
    text: str
) -> Dict[str, Any]:
    """
    Post a message to Slack.
    
    Args:
        channel: Channel name
        text: Message text
        
    Returns:
        Posted message info
    """
    try:
        message = await slack_service.post_message(channel, text)
        return {"success": True, "message": message}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def execute_safe_sql(query: str) -> Dict[str, Any]:
    """
    Execute a safe SQL query (SELECT only).
    
    Args:
        query: SQL query
        
    Returns:
        Query results
    """
    async with AsyncSessionLocal() as db:
        try:
            results = await sql_executor.execute_query(db, query)
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


async def get_database_tables() -> Dict[str, Any]:
    """
    Get list of available database tables.
    
    Returns:
        List of tables
    """
    async with AsyncSessionLocal() as db:
        tables = await sql_executor.get_available_tables(db)
        return {"success": True, "tables": tables, "count": len(tables)}


def register_all_tools() -> None:
    """Register all tools with the Gemini agent."""
    logger.info("Registering tools with Gemini agent...")
    
    # Search knowledge base
    gemini_agent.register_tool(
        name="search_knowledge_base",
        function=search_knowledge_base,
        description="Search the knowledge base for information. Use this when you need to find documents or information.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)"
                }
            },
            "required": ["query"]
        }
    )
    
    # Jira tools
    gemini_agent.register_tool(
        name="get_jira_ticket",
        function=get_jira_ticket,
        description="Get a Jira ticket by ID. Use when user asks about a specific ticket.",
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket ID (e.g., 'PROJ-101')"
                }
            },
            "required": ["ticket_id"]
        }
    )
    
    gemini_agent.register_tool(
        name="search_jira_tickets",
        function=search_jira_tickets,
        description="Search Jira tickets by text, status, or priority.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search text"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (e.g., 'Open', 'In Progress')"
                },
                "priority": {
                    "type": "string",
                    "description": "Filter by priority (e.g., 'High', 'Medium')"
                }
            }
        }
    )
    
    gemini_agent.register_tool(
        name="create_jira_ticket",
        function=create_jira_ticket,
        description="Create a new Jira ticket. Use when user wants to report an issue or create a task.",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Ticket title"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level (Low, Medium, High, Critical)"
                }
            },
            "required": ["title", "description"]
        }
    )
    
    # Slack tools
    gemini_agent.register_tool(
        name="search_slack_messages",
        function=search_slack_messages,
        description="Search Slack messages across channels. Use to find past conversations.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "channel": {
                    "type": "string",
                    "description": "Optional channel to search in"
                }
            },
            "required": ["query"]
        }
    )
    
    gemini_agent.register_tool(
        name="get_slack_channel_messages",
        function=get_slack_channel_messages,
        description="Get recent messages from a Slack channel.",
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel name (e.g., 'general', 'engineering')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages (default: 10)"
                }
            },
            "required": ["channel"]
        }
    )
    
    gemini_agent.register_tool(
        name="post_slack_message",
        function=post_slack_message,
        description="Post a message to a Slack channel. Use when user wants to send a message.",
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel name"
                },
                "text": {
                    "type": "string",
                    "description": "Message text"
                }
            },
            "required": ["channel", "text"]
        }
    )
    
    # SQL tools
    gemini_agent.register_tool(
        name="execute_safe_sql",
        function=execute_safe_sql,
        description="Execute a safe SQL query (SELECT only). Use to query the database directly.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query (SELECT statements only)"
                }
            },
            "required": ["query"]
        }
    )
    
    gemini_agent.register_tool(
        name="get_database_tables",
        function=get_database_tables,
        description="Get list of available database tables. Use before writing SQL queries.",
        parameters={
            "type": "object",
            "properties": {}
        }
    )
    
    logger.info(f"Registered {len(gemini_agent.dispatcher.tools)} tools")


# Register tools on module import
register_all_tools()

