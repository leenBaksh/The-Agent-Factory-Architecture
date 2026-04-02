-- ============================================================
-- Customer Success Digital FTE — CRM Schema
-- PostgreSQL 16+  |  pgvector extension required
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE channel_type AS ENUM ('web', 'gmail', 'whatsapp');
CREATE TYPE ticket_status AS ENUM ('open', 'in_progress', 'waiting_customer', 'resolved', 'closed', 'escalated');
CREATE TYPE ticket_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE message_status AS ENUM ('received', 'processing', 'replied', 'failed');

-- ============================================================
-- TABLE: customers
-- Core customer identity record.
-- ============================================================

CREATE TABLE customers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name        TEXT NOT NULL,
    email               TEXT UNIQUE,
    phone               TEXT UNIQUE,
    company             TEXT,
    plan                TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_email   ON customers (email);
CREATE INDEX idx_customers_phone   ON customers (phone);
CREATE INDEX idx_customers_company ON customers (company);
CREATE INDEX idx_customers_metadata ON customers USING GIN (metadata);

-- ============================================================
-- TABLE: customer_identifiers
-- Maps channel-specific IDs back to a customer record.
-- One customer can have identifiers across web, gmail, whatsapp.
-- ============================================================

CREATE TABLE customer_identifiers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    channel         channel_type NOT NULL,
    external_id     TEXT NOT NULL,          -- e.g. WhatsApp number, Gmail address, session token
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (channel, external_id)
);

CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers (customer_id);
CREATE INDEX idx_customer_identifiers_lookup   ON customer_identifiers (channel, external_id);

-- ============================================================
-- TABLE: conversations
-- A conversation groups all messages on one topic/session.
-- A customer can have multiple conversations across channels.
-- ============================================================

CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    channel         channel_type NOT NULL,
    subject         TEXT,
    status          ticket_status NOT NULL DEFAULT 'open',
    context         JSONB NOT NULL DEFAULT '{}',   -- channel-specific session data
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_customer      ON conversations (customer_id);
CREATE INDEX idx_conversations_channel       ON conversations (channel);
CREATE INDEX idx_conversations_status        ON conversations (status);
CREATE INDEX idx_conversations_last_message  ON conversations (last_message_at DESC);

-- ============================================================
-- TABLE: messages
-- Every individual message in a conversation, inbound or outbound.
-- ============================================================

CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    customer_id         UUID NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    direction           message_direction NOT NULL,
    channel             channel_type NOT NULL,
    status              message_status NOT NULL DEFAULT 'received',
    content             TEXT NOT NULL,
    raw_payload         JSONB NOT NULL DEFAULT '{}',  -- original webhook payload
    agent_response      TEXT,
    processing_metadata JSONB NOT NULL DEFAULT '{}',  -- tokens used, model, latency
    error_details       JSONB,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    replied_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages (conversation_id);
CREATE INDEX idx_messages_customer     ON messages (customer_id);
CREATE INDEX idx_messages_status       ON messages (status);
CREATE INDEX idx_messages_channel      ON messages (channel);
CREATE INDEX idx_messages_received_at  ON messages (received_at DESC);

-- ============================================================
-- TABLE: tickets
-- A ticket tracks a customer issue through its full lifecycle.
-- Linked to a conversation; may be escalated to a human agent.
-- ============================================================

CREATE TABLE tickets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    customer_id         UUID NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    subject             TEXT NOT NULL,
    description         TEXT,
    category            TEXT,
    status              ticket_status NOT NULL DEFAULT 'open',
    priority            ticket_priority NOT NULL DEFAULT 'medium',
    assigned_to         TEXT,                         -- human agent email or 'ai'
    resolution          TEXT,
    tags                TEXT[] NOT NULL DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    escalated_at        TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,
    closed_at           TIMESTAMPTZ,
    due_at              TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_conversation ON tickets (conversation_id);
CREATE INDEX idx_tickets_customer     ON tickets (customer_id);
CREATE INDEX idx_tickets_status       ON tickets (status);
CREATE INDEX idx_tickets_priority     ON tickets (priority);
CREATE INDEX idx_tickets_assigned_to  ON tickets (assigned_to);
CREATE INDEX idx_tickets_tags         ON tickets USING GIN (tags);
CREATE INDEX idx_tickets_metadata     ON tickets USING GIN (metadata);

-- ============================================================
-- TABLE: knowledge_base
-- Articles and FAQ entries used by the AI agent for answers.
-- Embeddings stored as vectors for semantic similarity search.
-- ============================================================

CREATE TABLE knowledge_base (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    category    TEXT,
    tags        TEXT[] NOT NULL DEFAULT '{}',
    embedding   VECTOR(1536),                -- OpenAI text-embedding-3-small dimensions
    metadata    JSONB NOT NULL DEFAULT '{}',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_knowledge_base_category  ON knowledge_base (category);
CREATE INDEX idx_knowledge_base_tags      ON knowledge_base USING GIN (tags);
CREATE INDEX idx_knowledge_base_active    ON knowledge_base (is_active);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- TABLE: channel_configs
-- Per-channel configuration: credentials, webhooks, toggles.
-- Stored encrypted via JSONB; never logged in plaintext.
-- ============================================================

CREATE TABLE channel_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel         channel_type NOT NULL UNIQUE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    config          JSONB NOT NULL DEFAULT '{}',   -- webhook URLs, API keys refs (not values)
    rate_limit      INTEGER NOT NULL DEFAULT 100,  -- max messages per minute
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_channel_configs_channel ON channel_configs (channel);
CREATE INDEX idx_channel_configs_active  ON channel_configs (is_active);

-- ============================================================
-- TABLE: agent_metrics
-- One row per message processed by the AI agent.
-- Used for observability, cost tracking, and eval regressions.
-- ============================================================

CREATE TABLE agent_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          UUID NOT NULL REFERENCES messages (id) ON DELETE CASCADE,
    ticket_id           UUID REFERENCES tickets (id) ON DELETE SET NULL,
    model               TEXT NOT NULL,
    prompt_tokens       INTEGER NOT NULL DEFAULT 0,
    completion_tokens   INTEGER NOT NULL DEFAULT 0,
    total_tokens        INTEGER NOT NULL DEFAULT 0,
    latency_ms          INTEGER NOT NULL DEFAULT 0,
    tools_called        TEXT[] NOT NULL DEFAULT '{}',
    confidence_score    NUMERIC(4, 3),              -- 0.000 – 1.000
    was_escalated       BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_reason   TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_metrics_message   ON agent_metrics (message_id);
CREATE INDEX idx_agent_metrics_ticket    ON agent_metrics (ticket_id);
CREATE INDEX idx_agent_metrics_model     ON agent_metrics (model);
CREATE INDEX idx_agent_metrics_escalated ON agent_metrics (was_escalated);
CREATE INDEX idx_agent_metrics_created   ON agent_metrics (created_at DESC);

-- ============================================================
-- UPDATED_AT TRIGGER (applied to all mutable tables)
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_channel_configs_updated_at
    BEFORE UPDATE ON channel_configs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
