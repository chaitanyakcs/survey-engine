-- Migration 012: Add document upload tracking tables
-- This migration adds tables to track document uploads and analysis for RFQ generation

-- Document uploads tracking table
CREATE TABLE document_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    analysis_result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document to RFQ mapping table for tracking usage
CREATE TABLE document_rfq_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES document_uploads(id) ON DELETE CASCADE,
    rfq_id UUID REFERENCES rfqs(id) ON DELETE CASCADE,
    mapping_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    fields_mapped JSONB, -- Track which fields were mapped and with what confidence
    user_corrections JSONB, -- Track user corrections to improve future mappings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure each document can only be mapped to an RFQ once
    UNIQUE(document_id, rfq_id)
);

-- Add document_upload_id to RFQs table for optional reference
ALTER TABLE rfqs ADD COLUMN document_upload_id UUID REFERENCES document_uploads(id) ON DELETE SET NULL;

-- Indexes for performance
CREATE INDEX idx_document_uploads_status ON document_uploads(processing_status);
CREATE INDEX idx_document_uploads_timestamp ON document_uploads(upload_timestamp);
CREATE INDEX idx_document_uploads_filename ON document_uploads(original_filename);

CREATE INDEX idx_document_rfq_mappings_document_id ON document_rfq_mappings(document_id);
CREATE INDEX idx_document_rfq_mappings_rfq_id ON document_rfq_mappings(rfq_id);
CREATE INDEX idx_document_rfq_mappings_confidence ON document_rfq_mappings(confidence_score);

CREATE INDEX idx_rfqs_document_upload_id ON rfqs(document_upload_id);

-- Add comments for documentation
COMMENT ON TABLE document_uploads IS 'Tracks uploaded documents (DOCX files) for RFQ data extraction';
COMMENT ON TABLE document_rfq_mappings IS 'Maps analyzed documents to created RFQs with confidence scores and user corrections';

COMMENT ON COLUMN document_uploads.processing_status IS 'Status of document processing: pending, processing, completed, failed';
COMMENT ON COLUMN document_uploads.analysis_result IS 'JSON result from document analysis including extracted RFQ data';
COMMENT ON COLUMN document_rfq_mappings.mapping_data IS 'Detailed mapping of document fields to RFQ fields';
COMMENT ON COLUMN document_rfq_mappings.user_corrections IS 'Track user corrections to improve AI mapping accuracy';
COMMENT ON COLUMN rfqs.document_upload_id IS 'Optional reference to the document that was used to create this RFQ';