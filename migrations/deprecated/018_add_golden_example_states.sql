-- Add golden example states table for state persistence
CREATE TABLE IF NOT EXISTS golden_example_states (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_golden_example_states_session_id ON golden_example_states(session_id);
CREATE INDEX IF NOT EXISTS idx_golden_example_states_created_at ON golden_example_states(created_at);

