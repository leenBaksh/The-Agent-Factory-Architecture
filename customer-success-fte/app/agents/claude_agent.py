"""
Claude Agent SDK Integration for Hybrid Orchestration

This module provides integration with Anthropic's Claude API for tasks that require:
- Complex bash operations
- MCP (Model Context Protocol) tool access
- Advanced agentic reasoning

The hybrid orchestration pattern:
1. OpenAI Agents SDK handles: orchestration, guardrails, handoffs, sessions, tracing
2. Claude API handles: bash, MCP, complex skills
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Try to import anthropic, but make it optional
try:
    from anthropic import Anthropic
    from anthropic.types import ToolResultBlockParam
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available. Claude features disabled.")


@dataclass
class ClaudeAgentConfig:
    """Configuration for Claude Agent"""

    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 60.0

    # Bash settings
    enable_bash: bool = True
    allowed_commands: list[str] = field(default_factory=lambda: [
        "ls", "cat", "grep", "find", "head", "tail", "wc",
        "pwd", "whoami", "date", "echo", "cd"
    ])

    # MCP settings
    enable_mcp: bool = False
    mcp_servers: list[str] = field(default_factory=list)


class ClaudeAgent:
    """
    Claude Agent for hybrid orchestration.

    Use this agent when tasks require:
    - Complex shell commands
    - MCP server interactions
    - Advanced reasoning beyond OpenAI's capabilities
    """
    
    def __init__(self, config: ClaudeAgentConfig | None = None):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("Anthropic SDK not installed. Run: pip install anthropic")
        
        self.config = config or ClaudeAgentConfig()
        
        if not self.config.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = Anthropic(api_key=self.config.api_key)
        self.conversation_history: list[dict[str, Any]] = []
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Claude agent"""
        
        prompt = """You are an AI assistant integrated into a Customer Success Digital FTE system.

Your role is to:
1. Help resolve complex customer issues that require advanced reasoning
2. Execute bash commands when needed for system operations
3. Interact with MCP servers for additional capabilities (if enabled)

Guidelines:
- Be concise and professional in customer-facing responses
- Always validate commands before execution
- Report errors clearly and suggest alternatives
- Respect security boundaries and allowed commands
- Log all actions for audit purposes
"""

        if self.config.enable_bash:
            prompt += f"""
Bash Capabilities:
- You can execute shell commands for system operations
- Allowed commands: {', '.join(self.config.allowed_commands)}
- Always use non-interactive flags (-y, -f) for commands
- Never execute commands that modify system state without confirmation
"""
        
        return prompt
    
    def _get_tools(self) -> list[dict[str, Any]]:
        """Get the tools available to the Claude agent"""
        
        tools = []
        
        if self.config.enable_bash:
            tools.append({
                "name": "bash",
                "description": "Execute a bash command. Use for system operations, file manipulation, and running scripts.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            })
        
        if self.config.enable_computer_use:
            tools.append({
                "name": "computer_use",
                "description": "Interact with a computer GUI using mouse and keyboard",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["click", "double_click", "type", "press_key", "screenshot"],
                            "description": "The action to perform"
                        },
                        "x": {
                            "type": "integer",
                            "description": "X coordinate for mouse actions"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate for mouse actions"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type for 'type' action"
                        },
                        "key": {
                            "type": "string",
                            "description": "Key to press for 'press_key' action"
                        }
                    },
                    "required": ["action"]
                }
            })
        
        return tools
    
    async def execute_bash(self, command: str) -> dict[str, Any]:
        """
        Execute a bash command safely.
        
        Args:
            command: The bash command to execute
            
        Returns:
            Dictionary with stdout, stderr, and return_code
        """
        
        # Validate command
        base_command = command.split()[0] if command.split() else ""
        if base_command not in self.config.allowed_commands:
            return {
                "success": False,
                "error": f"Command '{base_command}' is not in the allowed list",
                "allowed_commands": self.config.allowed_commands
            }
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {self.config.timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(
        self,
        message: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to Claude and get a response.
        
        Args:
            message: The user message
            system_prompt: Optional override for system prompt
            max_tokens: Optional override for max tokens
            
        Returns:
            Dictionary with response text and tool calls
        """
        
        if not ANTHROPIC_AVAILABLE:
            return {
                "success": False,
                "error": "Anthropic SDK not available"
            }
        
        try:
            # Add message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                system=system_prompt or self._get_system_prompt(),
                messages=self.conversation_history,
                tools=self._get_tools() if self._get_tools() else None,
            )
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Extract text content
            text_content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            return {
                "success": True,
                "text": text_content,
                "tool_calls": tool_calls,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_tool_call(
        self,
        tool_call: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a tool call from Claude.
        
        Args:
            tool_call: The tool call from Claude's response
            
        Returns:
            Tool execution result
        """

        tool_name = tool_call.get("name")
        tool_input = tool_call.get("input", {})

        if tool_name == "bash":
            return await self.execute_bash(tool_input.get("command", ""))

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    
    async def chat_with_tool_execution(
        self,
        message: str,
        max_iterations: int = 5
    ) -> dict[str, Any]:
        """
        Chat with Claude and automatically execute tool calls.
        
        Args:
            message: The user message
            max_iterations: Maximum tool execution iterations
            
        Returns:
            Final response after tool execution
        """
        
        current_message = message
        
        for iteration in range(max_iterations):
            response = await self.chat(current_message)
            
            if not response.get("success"):
                return response
            
            tool_calls = response.get("tool_calls", [])
            
            if not tool_calls:
                # No tool calls, return the text response
                return response
            
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = await self.execute_tool_call(tool_call)
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "result": result
                })
            
            # Format tool results for Claude
            tool_result_text = "Tool execution results:\n"
            for tr in tool_results:
                tool_result_text += f"- {tr['tool_call_id']}: {tr['result']}\n"
            
            current_message = tool_result_text
        
        return {
            "success": False,
            "error": "Max iterations reached"
        }
    
    def reset_conversation(self) -> None:
        """Reset the conversation history"""
        self.conversation_history = []


class HybridOrchestrator:
    """
    Hybrid Orchestrator that coordinates between OpenAI and Claude agents.
    
    Usage pattern:
    1. OpenAI Agents SDK handles initial orchestration
    2. For complex tasks, delegate to Claude Agent
    3. Return results to OpenAI for final response
    """
    
    def __init__(self, claude_config: ClaudeAgentConfig | None = None):
        self.claude_agent = ClaudeAgent(config=claude_config) if ANTHROPIC_AVAILABLE else None
        self.openai_available = True  # Assume OpenAI is available
        
        # Task routing rules
        self.claude_tasks = [
            "computer_use",
            "bash",
            "complex_reasoning",
            "mcp_interaction",
            "gui_automation"
        ]
    
    def should_delegate_to_claude(self, task_type: str) -> bool:
        """
        Determine if a task should be delegated to Claude.
        
        Args:
            task_type: The type of task to evaluate
            
        Returns:
            True if the task should be delegated to Claude
        """
        
        if self.claude_agent is None:
            return False
        
        return task_type in self.claude_tasks
    
    async def delegate_to_claude(
        self,
        task: str,
        task_type: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Delegate a task to Claude Agent.
        
        Args:
            task: The task description
            task_type: The type of task
            context: Additional context for the task
            
        Returns:
            Task execution result
        """
        
        if self.claude_agent is None:
            return {
                "success": False,
                "error": "Claude Agent not available"
            }
        
        # Build the prompt with context
        prompt = f"Task type: {task_type}\n\n"
        
        if context:
            prompt += "Context:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        prompt += f"Task: {task}\n\nPlease complete this task and provide a detailed response."
        
        # Execute with tool support
        result = await self.claude_agent.chat_with_tool_execution(prompt)
        
        logger.info(f"Claude delegation completed for task type: {task_type}")
        
        return result
    
    async def execute_hybrid_workflow(
        self,
        customer_message: str,
        openai_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a hybrid workflow using both OpenAI and Claude.
        
        Args:
            customer_message: Original customer message
            openai_response: Response from OpenAI agent
            context: Additional context
            
        Returns:
            Combined response
        """
        
        # Check if OpenAI identified a task for Claude
        needs_claude = openai_response.get("delegate_to_claude", False)
        
        if not needs_claude:
            return openai_response
        
        # Delegate to Claude
        task_type = openai_response.get("task_type", "general")
        task_description = openai_response.get("task_description", customer_message)
        
        claude_result = await self.delegate_to_claude(
            task=task_description,
            task_type=task_type,
            context={"customer_message": customer_message}
        )
        
        # Combine results
        return {
            **openai_response,
            "claude_result": claude_result,
            "hybrid_execution": True
        }


# Singleton instance
_hybrid_orchestrator: HybridOrchestrator | None = None


def get_hybrid_orchestrator() -> HybridOrchestrator:
    """Get or create the hybrid orchestrator singleton"""
    global _hybrid_orchestrator
    if _hybrid_orchestrator is None:
        _hybrid_orchestrator = HybridOrchestrator()
    return _hybrid_orchestrator
