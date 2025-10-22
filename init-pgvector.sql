-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create a test to verify pgvector is working
DO $$
BEGIN
    -- Test vector operations
    CREATE TEMP TABLE test_vectors (
        id SERIAL PRIMARY KEY,
        embedding VECTOR(3)
    );
    
    INSERT INTO test_vectors (embedding) VALUES 
        ('[1,2,3]'::vector),
        ('[4,5,6]'::vector);
    
    -- Test similarity search
    SELECT id, embedding <-> '[1,2,3]'::vector as distance 
    FROM test_vectors 
    ORDER BY embedding <-> '[1,2,3]'::vector;
    
    DROP TABLE test_vectors;
    
    RAISE NOTICE 'pgvector extension is working correctly!';
END $$;
