-- Migration: Add retrieval configuration tables
-- Description: Add configurable retrieval weights and methodology compatibility matrix

-- Configurable retrieval weights table
CREATE TABLE IF NOT EXISTS retrieval_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    weight_name VARCHAR(100) NOT NULL UNIQUE,
    context_type VARCHAR(50) NOT NULL DEFAULT 'global',
    context_value VARCHAR(100) NOT NULL DEFAULT 'default',
    semantic_weight DECIMAL(3,2) DEFAULT 0.40,
    methodology_weight DECIMAL(3,2) DEFAULT 0.25,
    industry_weight DECIMAL(3,2) DEFAULT 0.15,
    quality_weight DECIMAL(3,2) DEFAULT 0.10,
    annotation_weight DECIMAL(3,2) DEFAULT 0.10,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure weights sum to 1.0
    CONSTRAINT weights_sum_to_one CHECK (
        semantic_weight + methodology_weight + industry_weight + quality_weight + annotation_weight = 1.0
    ),
    
    -- Ensure weights are between 0 and 1
    CONSTRAINT weights_valid_range CHECK (
        semantic_weight >= 0 AND semantic_weight <= 1 AND
        methodology_weight >= 0 AND methodology_weight <= 1 AND
        industry_weight >= 0 AND industry_weight <= 1 AND
        quality_weight >= 0 AND quality_weight <= 1 AND
        annotation_weight >= 0 AND annotation_weight <= 1
    )
);

-- Methodology compatibility matrix table
CREATE TABLE IF NOT EXISTS methodology_compatibility (
    methodology_a VARCHAR(50) NOT NULL,
    methodology_b VARCHAR(50) NOT NULL,
    compatibility_score DECIMAL(3,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (methodology_a, methodology_b),
    
    -- Ensure compatibility score is between 0 and 1
    CONSTRAINT compatibility_score_valid CHECK (
        compatibility_score >= 0 AND compatibility_score <= 1
    ),
    
    -- Ensure methodologies are different
    CONSTRAINT different_methodologies CHECK (
        methodology_a != methodology_b
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_retrieval_weights_context 
    ON retrieval_weights(context_type, context_value);
CREATE INDEX IF NOT EXISTS idx_retrieval_weights_enabled 
    ON retrieval_weights(enabled) WHERE enabled = true;

CREATE INDEX IF NOT EXISTS idx_methodology_compatibility_a 
    ON methodology_compatibility(methodology_a);
CREATE INDEX IF NOT EXISTS idx_methodology_compatibility_b 
    ON methodology_compatibility(methodology_b);

-- Insert default global weights
INSERT INTO retrieval_weights (weight_name, context_type, context_value, semantic_weight, methodology_weight, industry_weight, quality_weight, annotation_weight)
VALUES ('global_default', 'global', 'default', 0.40, 0.25, 0.15, 0.10, 0.10)
ON CONFLICT (weight_name) DO NOTHING;

-- Insert methodology-specific weights
INSERT INTO retrieval_weights (weight_name, context_type, context_value, semantic_weight, methodology_weight, industry_weight, quality_weight, annotation_weight)
VALUES 
    ('methodology_van_westendorp', 'methodology', 'van_westendorp', 0.35, 0.40, 0.10, 0.10, 0.05),
    ('methodology_gabor_granger', 'methodology', 'gabor_granger', 0.35, 0.40, 0.10, 0.10, 0.05),
    ('methodology_conjoint', 'methodology', 'conjoint', 0.30, 0.35, 0.15, 0.15, 0.05),
    ('methodology_maxdiff', 'methodology', 'maxdiff', 0.30, 0.35, 0.15, 0.15, 0.05),
    ('methodology_nps', 'methodology', 'nps', 0.40, 0.20, 0.20, 0.15, 0.05),
    ('methodology_csat', 'methodology', 'csat', 0.40, 0.20, 0.20, 0.15, 0.05)
ON CONFLICT (weight_name) DO NOTHING;

-- Insert industry-specific weights
INSERT INTO retrieval_weights (weight_name, context_type, context_value, semantic_weight, methodology_weight, industry_weight, quality_weight, annotation_weight)
VALUES 
    ('industry_healthcare', 'industry', 'healthcare', 0.30, 0.20, 0.30, 0.15, 0.05),
    ('industry_technology', 'industry', 'technology', 0.35, 0.25, 0.25, 0.10, 0.05),
    ('industry_finance', 'industry', 'finance', 0.30, 0.25, 0.25, 0.15, 0.05),
    ('industry_retail', 'industry', 'retail', 0.40, 0.20, 0.20, 0.15, 0.05)
ON CONFLICT (weight_name) DO NOTHING;

-- Insert methodology compatibility data
INSERT INTO methodology_compatibility (methodology_a, methodology_b, compatibility_score, notes)
VALUES 
    ('van_westendorp', 'gabor_granger', 0.70, 'Both pricing methodologies'),
    ('gabor_granger', 'van_westendorp', 0.70, 'Both pricing methodologies'),
    ('conjoint', 'maxdiff', 0.60, 'Both feature ranking methodologies'),
    ('maxdiff', 'conjoint', 0.60, 'Both feature ranking methodologies'),
    ('nps', 'csat', 0.80, 'Both satisfaction measurement'),
    ('csat', 'nps', 0.80, 'Both satisfaction measurement'),
    ('brand_tracking', 'brand_awareness', 0.85, 'Both brand studies'),
    ('brand_awareness', 'brand_tracking', 0.85, 'Both brand studies'),
    ('van_westendorp', 'conjoint', 0.30, 'Different research objectives'),
    ('conjoint', 'van_westendorp', 0.30, 'Different research objectives'),
    ('maxdiff', 'nps', 0.25, 'Different research objectives'),
    ('nps', 'maxdiff', 0.25, 'Different research objectives')
ON CONFLICT (methodology_a, methodology_b) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE retrieval_weights IS 'Configurable weights for multi-factor golden example retrieval scoring';
COMMENT ON TABLE methodology_compatibility IS 'Compatibility matrix for methodology-based retrieval scoring';

COMMENT ON COLUMN retrieval_weights.context_type IS 'Type of context: global, methodology, or industry';
COMMENT ON COLUMN retrieval_weights.context_value IS 'Specific context value (e.g., van_westendorp, healthcare)';
COMMENT ON COLUMN retrieval_weights.semantic_weight IS 'Weight for semantic similarity (cosine distance)';
COMMENT ON COLUMN retrieval_weights.methodology_weight IS 'Weight for methodology match scoring';
COMMENT ON COLUMN retrieval_weights.industry_weight IS 'Weight for industry relevance scoring';
COMMENT ON COLUMN retrieval_weights.quality_weight IS 'Weight for golden example quality score';
COMMENT ON COLUMN retrieval_weights.annotation_weight IS 'Weight for annotation-based scoring';

COMMENT ON COLUMN methodology_compatibility.methodology_a IS 'First methodology in compatibility pair';
COMMENT ON COLUMN methodology_compatibility.methodology_b IS 'Second methodology in compatibility pair';
COMMENT ON COLUMN methodology_compatibility.compatibility_score IS 'Compatibility score between 0.0 and 1.0';
COMMENT ON COLUMN methodology_compatibility.notes IS 'Human-readable explanation of compatibility';
