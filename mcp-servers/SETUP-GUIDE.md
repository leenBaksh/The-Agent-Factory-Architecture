# MCP Servers - Setup Guide

## Overview

MCP (Model Context Protocol) servers connect Digital FTEs to external systems like Slack, databases, and web search.

## Quick Start

### Option 1: Use Pre-Built MCP Servers (Recommended)

Many production-ready MCP servers are already available:

| Server | Repository | Status |
|--------|-----------|--------|
| **Slack** | https://github.com/modelcontextprotocol/servers/tree/main/src/slack | ✅ Ready to use |
| **PostgreSQL** | https://github.com/modelcontextprotocol/servers/tree/main/src/postgres | ✅ Ready to use |
| **Web Search** | https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search | ✅ Ready to use |
| **GitHub** | https://github.com/modelcontextprotocol/servers/tree/main/src/github | ✅ Ready to use |
| **Google Drive** | https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive | ✅ Ready to use |
| **Filesystem** | https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem | ✅ Ready to use |

### Option 2: Use Custom MCP Servers (This Directory)

Custom implementations are provided in `mcp-servers/` for specific use cases.

#### Setup Steps

**1. Create Virtual Environment**

```bash
cd "D:\The Agent Factory Architecture\The Agent Factory Architecture"
python -m venv mcp-venv
mcp-venv\Scripts\activate
pip install -r mcp-servers\requirements-mcp.txt
```

**2. Set Environment Variables**

```bash
# For Slack MCP Server
set SLACK_BOT_TOKEN=xoxb-your-bot-token

# For PostgreSQL MCP Server
set DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# For Web Search MCP Server
set SEARCH_API_KEY=your-google-api-key
set SEARCH_ENGINE_ID=your-custom-search-engine-id
set NEWS_API_KEY=your-news-api-key
```

**3. Start MCP Server**

```bash
# Slack Server
mcp-venv\Scripts\python mcp-servers\slack_mcp.py

# PostgreSQL Server
mcp-venv\Scripts\python mcp-servers\postgresql_mcp.py

# Web Search Server
mcp-venv\Scripts\python mcp-servers\web_search_mcp.py
```

---

## Integration with Digital FTEs

Once MCP servers are running, Digital FTEs connect via the MCP protocol:

### Example: FTE Configuration

```yaml
# In your FTE spec (e.g., specs/customer-success-fte.md)

MCP Servers:
  slack:
    url: http://localhost:8001/mcp/slack
    tools:
      - send_message
      - post_alert
      - get_channel_messages

  postgresql:
    url: http://localhost:8001/mcp/postgres
    tools:
      - execute_query
      - get_schema
      - validate_data

  web-search:
    url: http://localhost:8001/mcp/search
    tools:
      - web_search
      - search_news
      - search_wikipedia
```

---

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use read-only database credentials** for PostgreSQL MCP
3. **Limit Slack bot permissions** to necessary scopes only
4. **Rate limit** all MCP endpoints to prevent abuse
5. **Audit logging** - all tool invocations are logged to Kafka

---

## Testing MCP Servers

### Test Slack MCP

```bash
curl -X POST http://localhost:PORT/tools/send_message \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#test",
    "message": "Hello from MCP!"
  }'
```

### Test PostgreSQL MCP

```bash
curl -X POST http://localhost:PORT/tools/execute_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT COUNT(*) FROM users",
    "limit": 100
  }'
```

### Test Web Search MCP

```bash
curl -X POST http://localhost:PORT/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI news",
    "num_results": 5
  }'
```

---

## Production Deployment

For production, MCP servers should be deployed as:

1. **Docker containers** (see `infrastructure/docker/`)
2. **Kubernetes Deployments** with proper secrets management
3. **Behind API Gateway** with authentication and rate limiting
4. **With mTLS** for secure communication between FTEs and MCP servers

### Example Docker Run

```bash
docker run -d \
  --name slack-mcp \
  -e SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN} \
  -p 8001:8001 \
  agent-factory/slack-mcp:latest
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "SLACK_BOT_TOKEN not set" | Set environment variable before starting |
| "Database connection failed" | Check DATABASE_URL format and network access |
| "Search API error" | Verify API key has sufficient quota |
| "Tool not found" | Check tool name matches server implementation |

---

## Resources

- **MCP Specification**: https://modelcontextprotocol.io
- **Official MCP Servers**: https://github.com/modelcontextprotocol/servers
- **MCP Python SDK**: https://pypi.org/project/mcp/
