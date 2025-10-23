-- Migration 017: Drop alembic_version table
-- Remove Alembic version tracking table as we transition to SQL-only migrations
-- This migration is safe to run multiple times (idempotent)

DROP TABLE IF EXISTS alembic_version CASCADE;
