-- Migration: Add human reviews table for persistent review state

CREATE TABLE IF NOT EXISTS human_reviews (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL UNIQUE,
    survey_id VARCHAR(255),
    review_status VARCHAR(50) DEFAULT 'pending',
    prompt_data TEXT NOT NULL,
    original_rfq TEXT NOT NULL,
    reviewer_id VARCHAR(255),
    review_deadline TIMESTAMP,
    reviewer_notes TEXT,
    approval_reason TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_human_reviews_workflow_id ON human_reviews (workflow_id);
CREATE INDEX IF NOT EXISTS idx_human_reviews_status ON human_reviews (review_status);
CREATE INDEX IF NOT EXISTS idx_human_reviews_reviewer ON human_reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS idx_human_reviews_created ON human_reviews (created_at);

-- Add trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_human_reviews_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_human_reviews_updated_at
    BEFORE UPDATE ON human_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_human_reviews_updated_at();

-- Add enum constraint for review_status
ALTER TABLE human_reviews 
ADD CONSTRAINT check_review_status 
CHECK (review_status IN ('pending', 'in_progress', 'approved', 'rejected', 'expired'));