-- Migration: Add enhanced_rfq_data field to RFQ table
-- This field stores structured Enhanced RFQ data for analytics and future features
-- while maintaining the open-closed principle for the workflow

-- Add enhanced_rfq_data JSONB column to rfqs table
ALTER TABLE rfqs ADD COLUMN enhanced_rfq_data JSONB;

-- Add index on enhanced_rfq_data for efficient queries
CREATE INDEX IF NOT EXISTS idx_rfqs_enhanced_rfq_data ON rfqs USING GIN (enhanced_rfq_data);

-- Add comment explaining the purpose
COMMENT ON COLUMN rfqs.enhanced_rfq_data IS 'Structured Enhanced RFQ data (objectives, constraints, stakeholders) for analytics and future features';