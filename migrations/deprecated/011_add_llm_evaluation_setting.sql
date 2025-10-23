-- Add enable_llm_evaluation setting to existing evaluation_settings
-- This migration updates existing settings to include the new LLM evaluation toggle

UPDATE settings 
SET setting_value = setting_value || '{"enable_llm_evaluation": true}'::jsonb
WHERE setting_key = 'evaluation_settings' 
AND NOT (setting_value ? 'enable_llm_evaluation');
