"""Safe SQL execution service."""
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.core.exceptions import ValidationException

logger = get_logger(__name__)


class SafeSQLExecutor:
    """Safe SQL query executor with validation."""
    
    # Allowed SQL keywords for read-only queries
    ALLOWED_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER",
        "ON", "AND", "OR", "GROUP", "BY", "ORDER", "LIMIT", "OFFSET",
        "AS", "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT"
    }
    
    # Disallowed patterns (dangerous operations)
    DISALLOWED_PATTERNS = [
        r"INSERT\s+INTO",
        r"UPDATE\s+",
        r"DELETE\s+FROM",
        r"DROP\s+",
        r"CREATE\s+",
        r"ALTER\s+",
        r"TRUNCATE\s+",
        r"EXEC",
        r"EXECUTE",
        r"xp_",
        r"sp_",
        r"--",  # SQL comments
        r";.*",  # Multiple statements
        r"UNION",  # Union attacks
    ]
    
    def __init__(self) -> None:
        """Initialize safe SQL executor."""
        logger.info("SafeSQLExecutor initialized")
    
    def validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        query_upper = query.upper().strip()
        
        # Check if query starts with SELECT
        if not query_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"
        
        # Check for disallowed patterns
        for pattern in self.DISALLOWED_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, f"Disallowed SQL pattern detected: {pattern}"
        
        # Check query length
        if len(query) > 2000:
            return False, "Query too long (max 2000 characters)"
        
        return True, None
    
    async def execute_query(
        self,
        db: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a safe SQL query.
        
        Args:
            db: Database session
            query: SQL query (SELECT only)
            params: Query parameters
            
        Returns:
            Query results as list of dictionaries
            
        Raises:
            ValidationException: If query is not safe
        """
        # Validate query
        is_valid, error = self.validate_query(query)
        if not is_valid:
            logger.warning(f"Unsafe SQL query rejected: {error}")
            raise ValidationException(f"Unsafe query: {error}")
        
        try:
            logger.info(f"Executing safe SQL query: {query[:100]}...")
            
            # Execute query with parameters
            stmt = text(query)
            result = await db.execute(stmt, params or {})
            
            # Fetch results
            rows = result.fetchall()
            
            # Convert to list of dictionaries
            if rows:
                columns = result.keys()
                results = [dict(zip(columns, row)) for row in rows]
            else:
                results = []
            
            logger.info(f"Query returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise ValidationException(f"Query execution failed: {str(e)}")
    
    async def get_table_info(
        self,
        db: AsyncSession,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            db: Database session
            table_name: Table name
            
        Returns:
            Table information
        """
        # Validate table name (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValidationException("Invalid table name")
        
        try:
            # Get column information (PostgreSQL specific)
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
            
            result = await db.execute(text(query), {"table_name": table_name})
            columns = result.fetchall()
            
            if not columns:
                return {"error": f"Table '{table_name}' not found"}
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES"
                    }
                    for col in columns
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    async def get_available_tables(
        self,
        db: AsyncSession
    ) -> List[str]:
        """
        Get list of available tables.
        
        Args:
            db: Database session
            
        Returns:
            List of table names
        """
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            
            result = await db.execute(text(query))
            tables = [row[0] for row in result.fetchall()]
            
            return tables
            
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []


# Global instance
sql_executor = SafeSQLExecutor()

