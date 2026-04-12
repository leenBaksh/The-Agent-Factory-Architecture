"""
PostgreSQL MCP Server for Digital FTEs

Provides tool access for:
- Querying databases
- Schema inspection
- Data validation
- Safe read-only operations (no writes without approval)
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "postgresql-server",
    description="PostgreSQL database integration for data queries and analysis",
    dependencies=["asyncpg"],
)

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def get_db_connection():
    """Get database connection from pool."""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
    async with db_pool.acquire() as conn:
        yield conn


@mcp.tool()
async def execute_query(
    query: str,
    params: Optional[dict] = None,
    limit: int = 100,
) -> dict:
    """
    Execute a read-only SQL query and return results.

    Args:
        query: SQL query to execute (SELECT only)
        params: Query parameters (dict)
        limit: Maximum rows to return (default: 100, max: 1000)

    Returns:
        dict with columns, rows, and row count
    """
    # Enforce read-only
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return {
            "success": False,
            "error": "Only SELECT queries are allowed",
            "rows": [],
        }

    # Enforce limit
    limit = min(limit, 1000)
    if "LIMIT" not in query_upper:
        query = f"{query.rstrip(';')} LIMIT {limit}"

    async with get_db_connection() as conn:
        try:
            rows = await conn.fetch(query, *(params.values() if params else []))
            if not rows:
                return {"columns": [], "rows": [], "count": 0}

            columns = list(rows[0].keys())
            result_rows = [dict(row) for row in rows]

            return {
                "success": True,
                "columns": columns,
                "rows": result_rows,
                "count": len(result_rows),
            }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"success": False, "error": str(e), "rows": []}


@mcp.tool()
async def get_schema(
    table_name: Optional[str] = None,
    schema: str = "public",
) -> dict:
    """
    Get database schema information.

    Args:
        table_name: Optional specific table name
        schema: Schema name (default: public)

    Returns:
        dict with table(s) and column definitions
    """
    async with get_db_connection() as conn:
        try:
            if table_name:
                # Get specific table schema
                columns = await conn.fetch(
                    """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """,
                    schema,
                    table_name,
                )
                
                constraints = await conn.fetch(
                    """
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = $1 AND tc.table_name = $2
                    """,
                    schema,
                    table_name,
                )

                return {
                    "success": True,
                    "table": table_name,
                    "columns": [dict(col) for col in columns],
                    "constraints": [dict(con) for con in constraints],
                }
            else:
                # List all tables
                tables = await conn.fetch(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = $1
                    ORDER BY table_name
                    """,
                    schema,
                )
                return {
                    "success": True,
                    "schema": schema,
                    "tables": [row["table_name"] for row in tables],
                }
        except Exception as e:
            logger.error(f"Schema query failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def get_table_stats(
    table_name: str,
    schema: str = "public",
) -> dict:
    """
    Get statistics for a specific table.

    Args:
        table_name: Table name
        schema: Schema name (default: public)

    Returns:
        dict with row count, size, and other stats
    """
    async with get_db_connection() as conn:
        try:
            # Get row count
            row = await conn.fetchval(
                f"SELECT COUNT(*) FROM {schema}.{table_name}"
            )
            
            # Get table size
            size = await conn.fetchval(
                """
                SELECT pg_size_pretty(pg_total_relation_size($1))
                """,
                f"{schema}.{table_name}",
            )

            return {
                "success": True,
                "table": table_name,
                "row_count": row,
                "total_size": size,
            }
        except Exception as e:
            logger.error(f"Table stats query failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def run_explain(
    query: str,
    analyze: bool = False,
) -> dict:
    """
    Run EXPLAIN on a query to analyze execution plan.

    Args:
        query: SQL query to analyze
        analyze: Whether to actually execute the query (default: False)

    Returns:
        dict with query plan details
    """
    async with get_db_connection() as conn:
        try:
            explain_keyword = "EXPLAIN ANALYZE" if analyze else "EXPLAIN"
            rows = await conn.fetch(f"{explain_keyword} {query}")
            return {
                "success": True,
                "plan": "\n".join([row["QUERY PLAN"] for row in rows]),
            }
        except Exception as e:
            logger.error(f"EXPLAIN failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def validate_data(
    table_name: str,
    conditions: dict,
) -> dict:
    """
    Validate data exists and matches expected conditions.

    Args:
        table_name: Table to check
        conditions: Key-value conditions to match

    Returns:
        dict with validation result
    """
    where_clauses = []
    params = []
    
    for key, value in conditions.items():
        where_clauses.append(f"{key} = ${len(params) + 1}")
        params.append(value)

    query = f"SELECT COUNT(*) FROM {table_name} WHERE {' AND '.join(where_clauses)}"

    async with get_db_connection() as conn:
        try:
            count = await conn.fetchval(query, *params)
            return {
                "success": True,
                "valid": count > 0,
                "matching_rows": count,
                "table": table_name,
            }
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
