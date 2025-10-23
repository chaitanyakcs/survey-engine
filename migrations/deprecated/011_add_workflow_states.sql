-- Migration: Add workflow states table for state persistence

CREATE TABLE IF NOT EXISTS workflow_states (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL UNIQUE,
    survey_id VARCHAR(255),
    state_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_id ON workflow_states (workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_survey_id ON workflow_states (survey_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_created_at ON workflow_states (created_at);

-- Add trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_workflow_states_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflow_states_updated_at
    BEFORE UPDATE ON workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_states_updated_at();
