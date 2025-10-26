-- ============================================================================
-- QNR TAXONOMY TABLES
-- Survey Engine - QNR Label Management System
-- Version: 1.0.0
-- ============================================================================
-- This migration creates tables for managing QNR label taxonomy
-- These tables allow dynamic management of question labels via API/UI
-- ============================================================================

-- QNR Sections Table
CREATE TABLE IF NOT EXISTS qnr_sections (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL,
    mandatory BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QNR Labels Table
CREATE TABLE IF NOT EXISTS qnr_labels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    mandatory BOOLEAN DEFAULT FALSE,
    label_type VARCHAR(20) NOT NULL,
    applicable_labels TEXT[],
    detection_patterns TEXT[],
    section_id INTEGER NOT NULL REFERENCES qnr_sections(id),
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QNR Label History Table (Audit Trail)
CREATE TABLE IF NOT EXISTS qnr_label_history (
    id SERIAL PRIMARY KEY,
    label_id INTEGER REFERENCES qnr_labels(id),
    changed_by VARCHAR(255),
    change_type VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_qnr_labels_category ON qnr_labels(category);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_section_id ON qnr_labels(section_id);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_mandatory ON qnr_labels(mandatory);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_active ON qnr_labels(active);

-- Seed QNR Sections (idempotent)
INSERT INTO qnr_sections (id, name, description, display_order, mandatory) VALUES
(1, 'Sample Plan', 'Sample plan and quotas', 1, TRUE),
(2, 'Screener Recruitment', 'Screening and qualification questions', 2, TRUE),
(3, 'Brand/Product Awareness & Usage', 'Brand awareness and product usage', 3, TRUE),
(4, 'Concept Exposure', 'Concept testing and evaluation', 4, TRUE),
(5, 'Methodology', 'Pricing and methodology-specific questions', 5, TRUE),
(6, 'Additional Questions', 'Demographics and psychographics', 6, TRUE),
(7, 'Programmer Instructions', 'Programming notes and QC', 7, TRUE)
ON CONFLICT (id) DO NOTHING;

