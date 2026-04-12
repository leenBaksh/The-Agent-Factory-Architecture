# MCP Servers for Digital FTEs

This directory contains Model Context Protocol (MCP) servers that provide tool and data access for Digital FTEs.

## Available Servers

### 1. Slack MCP Server (`slack_mcp.py`)

**Purpose**: Team communication, alerts, and notifications

**Tools Provided**:
- `send_message`: Send messages to channels or threads
- `get_channel_messages`: Retrieve recent messages from channels
- `post_alert`: Post formatted alerts with severity levels
- `get_user_info`: Get user details by ID
- `list_channels`: List available Slack channels

**Environment Variables**:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
```

**Usage**:
```bash
python mcp-servers/slack_mcp.py
```

---

### 2. PostgreSQL MCP Server (`postgresql_mcp.py`)

**Purpose**: Database queries, schema inspection, data validation

**Tools Provided**:
- `execute_query`: Run read-only SQL queries (SELECT only)
- `get_schema`: Inspect database schema and tables
- `get_table_stats`: Get row counts and table sizes
- `run_explain`: Analyze query execution plans
- `validate_data`: Check data exists and matches conditions

**Environment Variables**:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

**Security**: 
- Only SELECT queries allowed (read-only)
- Query result limits enforced (max 1000 rows)
- No destructive operations (DELETE, DROP, UPDATE blocked)

**Usage**:
```bash
python mcp-servers/postgresql_mcp.py
```

---

### 3. Web Search MCP Server (`web_search_mcp.py`)

**Purpose**: Web research, fact-checking, news retrieval

**Tools Provided**:
- `web_search`: General web search
- `search_news`: Recent news articles
- `fetch_url_content`: Extract content from URLs
- `search_wikipedia`: Wikipedia article summaries

**Environment Variables**:
```bash
SEARCH_API_KEY=your-google-api-key
SEARCH_ENGINE_ID=your-custom-search-engine-id
NEWS_API_KEY=your-news-api-key
```

**Usage**:
```bash
python mcp-servers/web_search_mcp.py
```

---

## Adding New MCP Servers

To create a new MCP server:

1. Create `<name>_mcp.py` in this directory
2. Import `FastMCP` from `mcp.server.fastmcp`
3. Define tools using `@mcp.tool()` decorator
4. Document each tool with clear Args and Returns
5. Add environment variable requirements
6. Update this README

### Example Template

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "my-service-server",
    description="My service integration",
    dependencies=["required-package"],
)

@mcp.tool()
async def my_tool(param1: str, param2: int = 10) -> dict:
    """
    Description of what the tool does.
    
    Args:
        param1: Description
        param2: Description (default: 10)
    
    Returns:
        dict with result details
    """
    # Implementation
    return {"success": True, "data": "result"}

if __name__ == "__main__":
    mcp.run()
```

---

## Integration with Digital FTEs

Digital FTEs connect to MCP servers via the MCP client protocol. Configuration is specified in the FTE's spec:

```yaml
# In FTE spec.md
MCP Servers:
  - slack-mcp: For team communication
  - postgresql-mcp: For database queries
  - web-search-mcp: For research and fact-checking
```

The FTE's runtime loads these connections and makes tools available to the agent for task execution.

---

## Security Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Read-Only by Default**: Block write operations unless explicitly needed
3. **Rate Limiting**: Implement rate limits to prevent abuse
4. **Audit Logging**: Log all tool invocations
5. **Secrets Management**: Use environment variables, never hardcode credentials
6. **Input Validation**: Validate all inputs before execution
7. **Error Handling**: Return structured error responses
