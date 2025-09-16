-- Migration: Add 5-Pillar Evaluation Rules
-- Created: $(date)
-- Description: This migration is now empty - pillar rules are managed via API

-- Pillar rules are now managed through the API endpoints and should not be seeded via SQL migrations
-- This prevents duplicate pillar rules from being created during deployment

-- Add comment about pillar rules
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies - includes seeded methodology, quality, industry, and pillar-based evaluation rules';

