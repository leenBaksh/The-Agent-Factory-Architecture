-- ============================================================
-- PostgreSQL extensions required by the Customer Success FTE schema.
-- This file is executed automatically by the postgres container on
-- first boot (docker-entrypoint-initdb.d), before 01_schema.sql.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector similarity search
