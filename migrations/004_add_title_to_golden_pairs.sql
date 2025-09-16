-- Add title column to golden_rfq_survey_pairs table
ALTER TABLE golden_rfq_survey_pairs 
ADD COLUMN IF NOT EXISTS title TEXT;

-- Add index for title searches
CREATE INDEX IF NOT EXISTS idx_golden_pairs_title ON golden_rfq_survey_pairs(title);

-- Update existing records to have a default title based on survey_json
UPDATE golden_rfq_survey_pairs 
SET title = COALESCE(
    survey_json->>'title',
    'Untitled Golden Example'
)
WHERE title IS NULL;










