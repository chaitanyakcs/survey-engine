-- Add settings table for storing application configuration
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_settings_key ON settings(setting_key);
CREATE INDEX idx_settings_active ON settings(is_active);

-- Insert default evaluation settings
INSERT INTO settings (setting_key, setting_value, description, is_active) VALUES 
('evaluation_settings', '{
    "evaluation_mode": "single_call",
    "enable_cost_tracking": true,
    "enable_parallel_processing": false,
    "enable_ab_testing": false,
    "cost_threshold_daily": 50.0,
    "cost_threshold_monthly": 1000.0,
    "fallback_mode": "basic",
    "enable_prompt_review": false,
    "prompt_review_mode": "disabled",
    "require_approval_for_generation": false,
    "auto_approve_trusted_prompts": false,
    "prompt_review_timeout_hours": 24
}', 'Default evaluation and prompt review settings', true);
