-- Migration: Add concept_files table for storing concept uploads (images and documents)
-- This migration is idempotent and safe to run multiple times

-- Create concept_files table
CREATE TABLE IF NOT EXISTS concept_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_data BYTEA NOT NULL,
    concept_stimulus_id VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_concept_files_rfq_id ON concept_files(rfq_id);
CREATE INDEX IF NOT EXISTS idx_concept_files_display_order ON concept_files(display_order);
CREATE INDEX IF NOT EXISTS idx_concept_files_concept_stimulus_id ON concept_files(concept_stimulus_id);
CREATE INDEX IF NOT EXISTS idx_concept_files_created_at ON concept_files(created_at);

-- Add comments for documentation
COMMENT ON TABLE concept_files IS 'Stores concept files (images and documents) uploaded for RFQ concept exposure';
COMMENT ON COLUMN concept_files.rfq_id IS 'Foreign key to the RFQ this concept file belongs to';
COMMENT ON COLUMN concept_files.file_data IS 'Binary file data stored in BYTEA format';
COMMENT ON COLUMN concept_files.concept_stimulus_id IS 'Optional link to concept_stimulus (stored as string ID in enhanced_rfq_data)';
COMMENT ON COLUMN concept_files.display_order IS 'Order in which files should be displayed';

