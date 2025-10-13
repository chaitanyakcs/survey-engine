-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create vector index function for optimal performance
CREATE OR REPLACE FUNCTION create_vector_indexes() RETURNS void AS $$
BEGIN
    -- Create indexes after tables are created by SQL migrations
    -- This will be run after initial migration
END;
$$ LANGUAGE plpgsql;

-- Set up database for vector operations
ALTER DATABASE survey_engine_db SET maintenance_work_mem = '512MB';