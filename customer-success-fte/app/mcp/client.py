"""
MCP (Model Context Protocol) Client Integration

This module provides MCP client functionality for connecting to MCP servers
and exposing additional tools/capabilities to the AI agents.

MCP enables:
- Dynamic tool discovery from MCP servers
- Access to external data sources (databases, APIs, file systems)
- Standardized protocol for agent-tool communication
- Secure, sandboxed tool execution
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


# ── MCP Constants ──────────────────────────────────────────────────────────────

MCP_PROTOCOL_VERSION = "2024-11-05"
DEFAULT_TIMEOUT_SECONDS = 30.0


class MCPCapability(Enum):
    """MCP server capabilities"""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    COMPLETION = "completion"


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass
class MCPPrompt:
    """MCP prompt definition"""
    name: str
    description: str
    arguments: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


@dataclass
class MCPConnectionConfig:
    """MCP server connection configuration"""
    server_id: str
    server_type: str  # "stdio", "sse", "streamable-http"
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    url: Optional[str] = None
    env: dict[str, str] = field(default_factory=dict)
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    headers: dict[str, str] = field(default_factory=dict)


# ── MCP Client ─────────────────────────────────────────────────────────────────

class MCPClient:
    """
    MCP client for connecting to MCP servers and invoking tools.
    
    Supports multiple transport types:
    - stdio: Spawn subprocess for local MCP servers
    - SSE: Server-Sent Events for remote servers
    - Streamable HTTP: HTTP streaming for remote servers
    """
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.connected = False
        self.tools: list[MCPTool] = []
        self.resources: list[MCPResource] = []
        self.prompts: list[MCPPrompt] = []
        self.capabilities: list[MCPCapability] = []
        
        self.http_client: Optional[httpx.AsyncClient] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        
        self._message_id = 0
    
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        
        if self.connected:
            return True
        
        try:
            if self.config.server_type == "stdio":
                await self._connect_stdio()
            elif self.config.server_type in ("sse", "streamable-http"):
                await self._connect_http()
            else:
                raise ValueError(f"Unsupported server type: {self.config.server_type}")
            
            # Initialize and discover capabilities
            await self._initialize()
            await self._discover_capabilities()
            
            self.connected = True
            logger.info(f"Connected to MCP server: {self.config.server_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def _connect_stdio(self):
        """Connect to MCP server via stdio (subprocess)"""
        
        if not self.config.command:
            raise ValueError("Command required for stdio transport")
        
        self.process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**self.config.env},
        )
        
        logger.info(f"Started MCP server process: {self.config.command}")
    
    async def _connect_http(self):
        """Connect to MCP server via HTTP"""
        
        if not self.config.url:
            raise ValueError("URL required for HTTP transport")
        
        self.http_client = httpx.AsyncClient(
            base_url=self.config.url,
            timeout=self.config.timeout,
            headers=self.config.headers,
        )
        
        logger.info(f"Connecting to MCP server at: {self.config.url}")
    
    async def _initialize(self):
        """Send initialize request to MCP server"""
        
        result = await self._send_request(
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "customer-success-fte",
                    "version": "1.0.0",
                },
            },
        )
        
        logger.info(f"MCP server initialized: {result}")
        
        # Send initialized notification
        await self._send_notification(
            method="notifications/initialized",
            params={},
        )
    
    async def _discover_capabilities(self):
        """Discover server capabilities"""
        
        # List tools
        try:
            tools_result = await self._send_request(
                method="tools/list",
                params={},
            )
            self.tools = [
                MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                )
                for t in tools_result.get("tools", [])
            ]
            if self.tools:
                self.capabilities.append(MCPCapability.TOOLS)
            logger.info(f"Discovered {len(self.tools)} MCP tools")
        except Exception as e:
            logger.warning(f"Failed to list tools: {e}")
        
        # List resources
        try:
            resources_result = await self._send_request(
                method="resources/list",
                params={},
            )
            self.resources = [
                MCPResource(
                    uri=r["uri"],
                    name=r.get("name", ""),
                    description=r.get("description", ""),
                    mime_type=r.get("mimeType"),
                )
                for r in resources_result.get("resources", [])
            ]
            if self.resources:
                self.capabilities.append(MCPCapability.RESOURCES)
            logger.info(f"Discovered {len(self.resources)} MCP resources")
        except Exception as e:
            logger.warning(f"Failed to list resources: {e}")
        
        # List prompts
        try:
            prompts_result = await self._send_request(
                method="prompts/list",
                params={},
            )
            self.prompts = [
                MCPPrompt(
                    name=p["name"],
                    description=p.get("description", ""),
                    arguments=p.get("arguments", []),
                )
                for p in prompts_result.get("prompts", [])
            ]
            if self.prompts:
                self.capabilities.append(MCPCapability.PROMPTS)
            logger.info(f"Discovered {len(self.prompts)} MCP prompts")
        except Exception as e:
            logger.warning(f"Failed to list prompts: {e}")
    
    async def _send_request(
        self,
        method: str,
        params: dict[str, Any],
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Send an MCP JSON-RPC request"""
        
        self._message_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self._message_id,
            "method": method,
            "params": params,
        }
        
        if self.http_client:
            # HTTP transport
            response = await self.http_client.post(
                "/",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=timeout or self.config.timeout,
            )
            response.raise_for_status()
            
            # Handle SSE or JSON response
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                # Parse SSE
                return self._parse_sse_response(response.text)
            else:
                return response.json()
        
        elif self.process:
            # stdio transport
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await self.process.stdout.readline()
            return json.loads(response_line.decode())
        
        else:
            raise RuntimeError("Not connected to MCP server")
    
    async def _send_notification(
        self,
        method: str,
        params: dict[str, Any],
    ) -> None:
        """Send an MCP notification (no response expected)"""
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        
        if self.http_client:
            await self.http_client.post(
                "/",
                json=notification,
                headers={"Content-Type": "application/json"},
            )
        elif self.process:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()
    
    def _parse_sse_response(self, sse_text: str) -> dict[str, Any]:
        """Parse SSE response into JSON"""
        
        # Simple SSE parser - extract data lines
        for line in sse_text.split("\n"):
            if line.startswith("data:"):
                data = line[5:].strip()
                if data:
                    return json.loads(data)
        
        raise ValueError("No valid SSE data found")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call an MCP tool"""
        
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self._send_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments,
            },
        )
        
        logger.info(f"Called MCP tool: {tool_name}")
        
        return result
    
    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read an MCP resource"""
        
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self._send_request(
            method="resources/read",
            params={"uri": uri},
        )
        
        logger.info(f"Read MCP resource: {uri}")
        
        return result
    
    async def get_prompt(
        self,
        prompt_name: str,
        arguments: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Get an MCP prompt"""
        
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self._send_request(
            method="prompts/get",
            params={
                "name": prompt_name,
                "arguments": arguments or {},
            },
        )
        
        logger.info(f"Got MCP prompt: {prompt_name}")
        
        return result
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        
        if not self.connected:
            return
        
        try:
            # Send shutdown notification
            await self._send_notification(
                method="notifications/cancelled",
                params={"reason": "client disconnecting"},
            )
        except Exception:
            pass
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except Exception:
                self.process.kill()
            self.process = None
        
        self.connected = False
        logger.info(f"Disconnected from MCP server: {self.config.server_id}")
    
    def get_tools_as_openai_functions(self) -> list[dict[str, Any]]:
        """Convert MCP tools to OpenAI function format"""
        
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self.tools
        ]
    
    def get_tools_as_claude_tools(self) -> list[dict[str, Any]]:
        """Convert MCP tools to Claude tool format"""
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools
        ]


# ── MCP Manager ────────────────────────────────────────────────────────────────

class MCPManager:
    """Manager for multiple MCP server connections"""
    
    def __init__(self):
        self.clients: dict[str, MCPClient] = {}
    
    def add_server(self, config: MCPConnectionConfig):
        """Add an MCP server configuration"""
        
        if config.server_id in self.clients:
            logger.warning(f"MCP server already exists: {config.server_id}")
            return
        
        client = MCPClient(config)
        self.clients[config.server_id] = client
        logger.info(f"Added MCP server config: {config.server_id}")
    
    def remove_server(self, server_id: str):
        """Remove an MCP server"""
        
        if server_id in self.clients:
            del self.clients[server_id]
            logger.info(f"Removed MCP server: {server_id}")
    
    async def connect_all(self) -> dict[str, bool]:
        """Connect to all configured MCP servers"""
        
        results = {}
        
        for server_id, client in self.clients.items():
            success = await client.connect()
            results[server_id] = success
            logger.info(f"MCP server {server_id} connection: {'success' if success else 'failed'}")
        
        return results
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        
        for client in self.clients.values():
            await client.disconnect()
        
        logger.info("Disconnected from all MCP servers")
    
    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all connected MCP servers"""
        
        all_tools = []
        for client in self.clients.values():
            if client.connected:
                all_tools.extend(client.tools)
        
        return all_tools
    
    def get_client(self, server_id: str) -> Optional[MCPClient]:
        """Get an MCP client by server ID"""
        
        return self.clients.get(server_id)


# ── Factory Functions ──────────────────────────────────────────────────────────

def create_mcp_client(config: MCPConnectionConfig) -> MCPClient:
    """Create an MCP client instance"""
    return MCPClient(config)


def create_mcp_manager() -> MCPManager:
    """Create an MCP manager instance"""
    return MCPManager()


# ── Pre-configured MCP Servers ────────────────────────────────────────────────

def create_filesystem_mcp(path: str) -> MCPConnectionConfig:
    """Create config for filesystem MCP server"""
    
    return MCPConnectionConfig(
        server_id="filesystem",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", path],
    )


def create_postgres_mcp(connection_string: str) -> MCPConnectionConfig:
    """Create config for PostgreSQL MCP server"""
    
    return MCPConnectionConfig(
        server_id="postgres",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres", connection_string],
    )


def create_github_mcp(token: str) -> MCPConnectionConfig:
    """Create config for GitHub MCP server"""
    
    return MCPConnectionConfig(
        server_id="github",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": token},
    )


def create_slack_mcp(token: str) -> MCPConnectionConfig:
    """Create config for Slack MCP server"""
    
    return MCPConnectionConfig(
        server_id="slack",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-slack"],
        env={"SLACK_BOT_TOKEN": token},
    )
