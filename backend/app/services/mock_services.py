"""Mock services for Jira and Slack."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockJiraService:
    """Mock Jira service for testing."""
    
    def __init__(self) -> None:
        """Initialize mock Jira service."""
        self.tickets = {
            "PROJ-101": {
                "id": "PROJ-101",
                "title": "Password reset not working",
                "description": "Users report that password reset emails are not being received",
                "status": "Open",
                "priority": "High",
                "assignee": "john.doe@company.com",
                "reporter": "user@company.com",
                "created": "2024-01-05T10:00:00Z",
                "updated": "2024-01-06T09:30:00Z"
            },
            "PROJ-102": {
                "id": "PROJ-102",
                "title": "API authentication timeout",
                "description": "API requests are timing out during authentication",
                "status": "In Progress",
                "priority": "Critical",
                "assignee": "jane.smith@company.com",
                "reporter": "admin@company.com",
                "created": "2024-01-04T14:20:00Z",
                "updated": "2024-01-06T11:00:00Z"
            },
            "PROJ-103": {
                "id": "PROJ-103",
                "title": "Update documentation",
                "description": "Need to update API documentation with new endpoints",
                "status": "Todo",
                "priority": "Medium",
                "assignee": "doc.writer@company.com",
                "reporter": "manager@company.com",
                "created": "2024-01-03T09:00:00Z",
                "updated": "2024-01-03T09:00:00Z"
            }
        }
        logger.info("MockJiraService initialized")
    
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID (e.g., "PROJ-101")
            
        Returns:
            Ticket data or None if not found
        """
        logger.info(f"Getting Jira ticket: {ticket_id}")
        return self.tickets.get(ticket_id)
    
    async def search_tickets(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search tickets.
        
        Args:
            query: Text to search in title/description
            status: Filter by status
            priority: Filter by priority
            
        Returns:
            List of matching tickets
        """
        logger.info(f"Searching Jira tickets: query={query}, status={status}, priority={priority}")
        
        results = list(self.tickets.values())
        
        if query:
            query_lower = query.lower()
            results = [
                t for t in results
                if query_lower in t["title"].lower() or query_lower in t["description"].lower()
            ]
        
        if status:
            results = [t for t in results if t["status"].lower() == status.lower()]
        
        if priority:
            results = [t for t in results if t["priority"].lower() == priority.lower()]
        
        return results
    
    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """
        Create a new ticket.
        
        Args:
            title: Ticket title
            description: Ticket description
            priority: Priority level
            
        Returns:
            Created ticket data
        """
        ticket_id = f"PROJ-{len(self.tickets) + 101}"
        
        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "status": "Open",
            "priority": priority,
            "assignee": None,
            "reporter": "system@company.com",
            "created": datetime.utcnow().isoformat() + "Z",
            "updated": datetime.utcnow().isoformat() + "Z"
        }
        
        self.tickets[ticket_id] = ticket
        logger.info(f"Created Jira ticket: {ticket_id}")
        
        return ticket
    
    async def update_ticket(
        self,
        ticket_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a ticket.
        
        Args:
            ticket_id: Ticket ID
            status: New status
            priority: New priority
            assignee: New assignee
            
        Returns:
            Updated ticket or None if not found
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        
        if status:
            ticket["status"] = status
        if priority:
            ticket["priority"] = priority
        if assignee:
            ticket["assignee"] = assignee
        
        ticket["updated"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Updated Jira ticket: {ticket_id}")
        return ticket


class MockSlackService:
    """Mock Slack service for testing."""
    
    def __init__(self) -> None:
        """Initialize mock Slack service."""
        self.channels = {
            "general": {
                "id": "C001",
                "name": "general",
                "members": 50,
                "messages": [
                    {
                        "id": "M001",
                        "user": "alice",
                        "text": "Has anyone seen the new API documentation?",
                        "timestamp": "2024-01-06T10:00:00Z",
                        "thread_ts": None
                    },
                    {
                        "id": "M002",
                        "user": "bob",
                        "text": "Yes, it's available at docs.company.com",
                        "timestamp": "2024-01-06T10:05:00Z",
                        "thread_ts": "M001"
                    }
                ]
            },
            "engineering": {
                "id": "C002",
                "name": "engineering",
                "members": 25,
                "messages": [
                    {
                        "id": "M003",
                        "user": "charlie",
                        "text": "The password reset feature is broken. JIRA ticket PROJ-101 created.",
                        "timestamp": "2024-01-06T09:00:00Z",
                        "thread_ts": None
                    },
                    {
                        "id": "M004",
                        "user": "diana",
                        "text": "I'm looking into it. Seems like an email service issue.",
                        "timestamp": "2024-01-06T09:30:00Z",
                        "thread_ts": "M003"
                    }
                ]
            },
            "support": {
                "id": "C003",
                "name": "support",
                "members": 15,
                "messages": [
                    {
                        "id": "M005",
                        "user": "support_agent",
                        "text": "Customer asking about API rate limits",
                        "timestamp": "2024-01-06T11:00:00Z",
                        "thread_ts": None
                    }
                ]
            }
        }
        logger.info("MockSlackService initialized")
    
    async def get_channel_messages(
        self,
        channel: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a channel.
        
        Args:
            channel: Channel name
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        logger.info(f"Getting Slack messages from #{channel}")
        
        channel_data = self.channels.get(channel)
        if not channel_data:
            return []
        
        return channel_data["messages"][:limit]
    
    async def search_messages(
        self,
        query: str,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search messages.
        
        Args:
            query: Search query
            channel: Optional channel filter
            
        Returns:
            List of matching messages
        """
        logger.info(f"Searching Slack messages: query={query}, channel={channel}")
        
        query_lower = query.lower()
        results = []
        
        channels_to_search = [channel] if channel else self.channels.keys()
        
        for ch in channels_to_search:
            channel_data = self.channels.get(ch)
            if channel_data:
                for msg in channel_data["messages"]:
                    if query_lower in msg["text"].lower():
                        results.append({
                            **msg,
                            "channel": ch
                        })
        
        return results
    
    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a message to a channel.
        
        Args:
            channel: Channel name
            text: Message text
            thread_ts: Thread timestamp (for replies)
            
        Returns:
            Posted message data
        """
        channel_data = self.channels.get(channel)
        if not channel_data:
            raise ValueError(f"Channel #{channel} not found")
        
        message = {
            "id": f"M{len(channel_data['messages']) + 100}",
            "user": "bot",
            "text": text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "thread_ts": thread_ts
        }
        
        channel_data["messages"].append(message)
        logger.info(f"Posted message to Slack #{channel}")
        
        return message
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """
        List all channels.
        
        Returns:
            List of channels
        """
        return [
            {
                "id": data["id"],
                "name": data["name"],
                "members": data["members"],
                "message_count": len(data["messages"])
            }
            for data in self.channels.values()
        ]


# Global instances
jira_service = MockJiraService()
slack_service = MockSlackService()

