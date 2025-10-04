-- Database Schema Fix Script
-- This script adds the missing session_id column and related changes to document_uploads table
-- Run this script against your Railway database to fix the migration issue

-- Check if session_id column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_uploads' AND column_name = 'session_id'
    ) THEN
        ALTER TABLE document_uploads ADD COLUMN session_id VARCHAR(100);
        RAISE NOTICE 'Added session_id column to document_uploads table';
    ELSE
        RAISE NOTICE 'session_id column already exists in document_uploads table';
    END IF;
END $$;

-- Check if uploaded_by column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_uploads' AND column_name = 'uploaded_by'
    ) THEN
        ALTER TABLE document_uploads ADD COLUMN uploaded_by VARCHAR(255);
        RAISE NOTICE 'Added uploaded_by column to document_uploads table';
    ELSE
        RAISE NOTICE 'uploaded_by column already exists in document_uploads table';
    END IF;
END $$;

-- Make original_filename nullable if it isn't already
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_uploads' 
        AND column_name = 'original_filename' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE document_uploads ALTER COLUMN original_filename DROP NOT NULL;
        RAISE NOTICE 'Made original_filename nullable in document_uploads table';
    ELSE
        RAISE NOTICE 'original_filename is already nullable in document_uploads table';
    END IF;
END $$;

-- Make file_size nullable if it isn't already
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_uploads' 
        AND column_name = 'file_size' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE document_uploads ALTER COLUMN file_size DROP NOT NULL;
        RAISE NOTICE 'Made file_size nullable in document_uploads table';
    ELSE
        RAISE NOTICE 'file_size is already nullable in document_uploads table';
    END IF;
END $$;

-- Create index on session_id if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_document_uploads_session_id'
    ) THEN
        CREATE INDEX idx_document_uploads_session_id ON document_uploads (session_id);
        RAISE NOTICE 'Created index idx_document_uploads_session_id on document_uploads table';
    ELSE
        RAISE NOTICE 'Index idx_document_uploads_session_id already exists on document_uploads table';
    END IF;
END $$;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'document_uploads' 
AND column_name IN ('session_id', 'uploaded_by', 'original_filename', 'file_size')
ORDER BY column_name;

-- Show indexes on document_uploads table
SELECT 
    indexname, 
    indexdef
FROM pg_indexes 
WHERE tablename = 'document_uploads' 
AND indexname LIKE '%session_id%';
