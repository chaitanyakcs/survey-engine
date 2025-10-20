-- Add human_verified field to golden_rfq_survey_pairs table
-- This field indicates whether the golden pair was manually created by a human (True) 
-- or automatically migrated from existing surveys (False)

ALTER TABLE golden_rfq_survey_pairs 
ADD COLUMN human_verified BOOLEAN DEFAULT FALSE;

-- Update existing golden pairs to be human-verified (they were manually created)
UPDATE golden_rfq_survey_pairs 
SET human_verified = TRUE 
WHERE title NOT LIKE 'Migrated Survey%';

-- Create index for efficient querying by human verification status
CREATE INDEX idx_golden_pairs_human_verified 
ON golden_rfq_survey_pairs(human_verified);

-- Add comment for documentation
COMMENT ON COLUMN golden_rfq_survey_pairs.human_verified IS 'Indicates if this golden pair was manually created by a human (True) or auto-migrated from existing surveys (False). Human-verified examples get priority in retrieval.';
