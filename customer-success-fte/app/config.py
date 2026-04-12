"""
Application configuration via Pydantic Settings.
All values are read from environment variables or a .env file.
"""

from functools import lru_cache
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "Customer Success Digital FTE"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="SQLAlchemy async DSN — must use asyncpg driver. Required, no default.",
    )
    db_pool_size: int = Field(default=10, ge=1, le=50)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5, le=120)      # seconds
    db_pool_recycle: int = Field(default=1800, ge=60)            # seconds
    db_echo: bool = False                                         # SQL query logging

    # ── Kafka ─────────────────────────────────────────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_inbound: str = "cs-fte.messages.inbound"
    kafka_topic_outbound: str = "cs-fte.messages.outbound"
    kafka_topic_escalations: str = "cs-fte.tickets.escalations"
    kafka_consumer_group: str = "cs-fte-worker"
    kafka_topic_dlq: str = "cs-fte.messages.dlq"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: str = Field(..., description="OpenAI API key — required")
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536
    
    # OpenAI pricing per 1K tokens (USD) — update as pricing changes
    # Default values reflect GPT-4o pricing as of 2025
    openai_input_cost_per_1k: dict[str, float] = Field(
        default={
            "gpt-4o": 0.0025,
            "gpt-4o-mini": 0.00015,
            "gpt-4-turbo": 0.010,
            "gpt-3.5-turbo": 0.0005,
        },
        description="Input token cost per 1K tokens by model",
    )
    openai_output_cost_per_1k: dict[str, float] = Field(
        default={
            "gpt-4o": 0.010,
            "gpt-4o-mini": 0.0006,
            "gpt-4-turbo": 0.030,
            "gpt-3.5-turbo": 0.0015,
        },
        description="Output token cost per 1K tokens by model",
    )

    # ── Anthropic (Claude) ────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    claude_model: str = "claude-3-5-sonnet-20241022"

    # ── Channels ──────────────────────────────────────────────────────────────
    # Gmail
    gmail_credentials_file: str = "credentials/gmail_credentials.json"
    gmail_token_file: str = "credentials/gmail_token.json"
    gmail_poll_interval_seconds: int = 60

    # WhatsApp (Meta Cloud API)
    whatsapp_api_url: str = "https://graph.facebook.com/v19.0"
    whatsapp_phone_number_id: str = Field(default="", description="Meta phone number ID")
    whatsapp_access_token: str = Field(default="", description="Meta access token")
    whatsapp_verify_token: str = Field(default="", description="Webhook verify token")
    whatsapp_app_secret: str = Field(default="", description="Meta app secret for X-Hub-Signature-256 verification")

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str = Field(..., description="App secret key for signing — required")
    api_key_header: str = "X-API-Key"
    internal_api_key: str = Field(..., description="Internal service-to-service key — required")
    
    # ── A2A Protocol ──────────────────────────────────────────────────────────
    fte_id: str = Field(default="cs-fte-001", description="Unique FTE identifier")
    a2a_api_key: str = Field(default="", description="A2A protocol API key for inter-FTE auth")
    a2a_enabled: bool = Field(default=True, description="Enable A2A protocol endpoints")

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins — override per environment",
    )

    # ── SMTP (email reply delivery) ───────────────────────────────────────────
    smtp_host: str = Field(default="", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port (587=STARTTLS, 465=SSL)")
    smtp_user: str = Field(default="", description="SMTP username / sender address")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(default="", description="From address for outbound emails")
    smtp_use_tls: bool = True

    # ── Ticket thresholds ─────────────────────────────────────────────────────
    auto_escalation_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_ai_retries_before_escalation: int = Field(default=3, ge=1, le=10)

    # ── Notifications & escalation ────────────────────────────────────────────
    slack_webhook_url: str = Field(default="", description="Slack incoming webhook URL for team alerts")
    support_team_email: str = Field(default="", description="Support team inbox for escalation/SLA emails")
    app_base_url: str = Field(default="http://localhost:8000", description="Public base URL used in survey links")
    escalation_sla_hours: int = Field(default=4, ge=1, le=168, description="Hours before an open ticket triggers SLA breach")
    sla_monitor_interval_minutes: int = Field(default=15, ge=1, le=1440, description="How often the SLA monitor runs")
    survey_response_window_hours: int = Field(default=48, ge=1, le=720, description="Hours customer has to submit satisfaction survey")

    # ── Dapr (distributed application runtime) ────────────────────────────────
    dapr_grpc_endpoint: str = Field(default="localhost:50001", description="Dapr gRPC endpoint")
    dapr_http_endpoint: str = Field(default="http://localhost:3500", description="Dapr HTTP endpoint")
    dapr_pubsub_name: str = Field(default="cs-pubsub", description="Dapr pubsub component name")
    dapr_state_store: str = Field(default="cs-state", description="Dapr state store component name")
    dapr_workflow_runtime: str = Field(default="workflow-runtime", description="Dapr workflow runtime ID")

    # ── MCP (Model Context Protocol) ──────────────────────────────────────────
    mcp_enabled: bool = Field(default=False, description="Enable MCP server integrations")
    mcp_server_ids: str = Field(
        default="",
        description="Comma-separated list of MCP server IDs to load (e.g., filesystem,postgres,github,slack,jira)",
    )
    mcp_filesystem_path: str = Field(default="", description="Path to expose via filesystem MCP")
    mcp_postgres_connection_string: str = Field(default="", description="PostgreSQL connection string for MCP")
    mcp_github_token: str = Field(default="", description="GitHub token for GitHub MCP")
    mcp_slack_bot_token: str = Field(default="", description="Slack bot token for Slack MCP")

    # ── Jira Integration ──────────────────────────────────────────────────────
    jira_url: str = Field(default="", description="Jira instance URL (e.g., https://company.atlassian.net)")
    jira_email: str = Field(default="", description="Atlassian account email")
    jira_api_token: str = Field(default="", description="Jira API token")
    jira_project_key: str = Field(default="", description="Jira project key (e.g., CS, SCRUM)")
    jira_default_assignee: str = Field(default="", description="Default assignee for Jira tickets")
    jira_enabled: bool = Field(default=False, description="Enable Jira integration")

    @field_validator("mcp_server_ids")
    @classmethod
    def parse_server_ids(cls, v: str) -> str:
        """Validate and normalize server IDs list"""
        if v:
            # Strip whitespace and filter empty strings
            ids = [sid.strip() for sid in v.split(",") if sid.strip()]
            return ",".join(ids)
        return v

    @property
    def mcp_server_ids_list(self) -> list[str]:
        """Get server IDs as a list"""
        if not self.mcp_server_ids:
            return []
        return [sid.strip() for sid in self.mcp_server_ids.split(",") if sid.strip()]

    @field_validator("database_url")
    @classmethod
    def validate_asyncpg_driver(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must use the asyncpg driver: postgresql+asyncpg://...")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance. Import and call this wherever settings are needed.
    The cache ensures the .env file is read exactly once.
    """
    return Settings()
