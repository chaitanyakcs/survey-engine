"""
Settings Service - Handle database operations for application settings
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Settings
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        try:
            setting = self.db.query(Settings).filter(
                Settings.setting_key == key,
                Settings.is_active == True
            ).first()
            
            if setting and setting.setting_value:
                return setting.setting_value
            return default
        except SQLAlchemyError as e:
            logger.error(f"❌ [SettingsService] Failed to get setting {key}: {e}")
            return default

    def set_setting(self, key: str, value: Any, description: str = None) -> bool:
        """Set a setting value by key"""
        try:
            # Check if setting exists
            existing_setting = self.db.query(Settings).filter(
                Settings.setting_key == key
            ).first()
            
            if existing_setting:
                # Update existing setting
                existing_setting.setting_value = value
                if description:
                    existing_setting.description = description
                existing_setting.is_active = True
            else:
                # Create new setting
                new_setting = Settings(
                    setting_key=key,
                    setting_value=value,
                    description=description,
                    is_active=True
                )
                self.db.add(new_setting)
            
            self.db.commit()
            logger.info(f"✅ [SettingsService] Setting {key} updated successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ [SettingsService] Failed to set setting {key}: {e}")
            self.db.rollback()
            return False

    def get_evaluation_settings(self) -> Dict[str, Any]:
        """Get evaluation settings"""
        default_settings = {
            "evaluation_mode": "single_call",
            "enable_cost_tracking": True,
            "enable_parallel_processing": False,
            "enable_ab_testing": False,
            "cost_threshold_daily": 50.0,
            "cost_threshold_monthly": 1000.0,
            "fallback_mode": "basic",
            "enable_prompt_review": False,
            "prompt_review_mode": "disabled",
            "require_approval_for_generation": False,
            "auto_approve_trusted_prompts": False,
            "prompt_review_timeout_hours": 24
        }
        
        try:
            settings = self.get_setting("evaluation_settings", default_settings)
            # Ensure all required keys are present
            for key, default_value in default_settings.items():
                if key not in settings:
                    settings[key] = default_value
            return settings
        except Exception as e:
            logger.error(f"❌ [SettingsService] Failed to get evaluation settings: {e}")
            return default_settings

    def update_evaluation_settings(self, settings: Dict[str, Any]) -> bool:
        """Update evaluation settings"""
        try:
            # Validate required settings
            required_keys = [
                "evaluation_mode", "enable_cost_tracking", "enable_parallel_processing",
                "enable_ab_testing", "cost_threshold_daily", "cost_threshold_monthly",
                "fallback_mode", "enable_prompt_review", "prompt_review_mode",
                "require_approval_for_generation", "auto_approve_trusted_prompts",
                "prompt_review_timeout_hours"
            ]
            
            for key in required_keys:
                if key not in settings:
                    logger.error(f"❌ [SettingsService] Missing required setting: {key}")
                    return False
            
            # Validate specific values
            if settings["evaluation_mode"] not in ["single_call", "multiple_calls", "hybrid"]:
                logger.error(f"❌ [SettingsService] Invalid evaluation_mode: {settings['evaluation_mode']}")
                return False
                
            if settings["prompt_review_mode"] not in ["disabled", "blocking", "parallel"]:
                logger.error(f"❌ [SettingsService] Invalid prompt_review_mode: {settings['prompt_review_mode']}")
                return False
            
            # Update the setting
            success = self.set_setting(
                "evaluation_settings", 
                settings, 
                "Evaluation and prompt review settings"
            )
            
            if success:
                logger.info("✅ [SettingsService] Evaluation settings updated successfully")
            return success
            
        except Exception as e:
            logger.error(f"❌ [SettingsService] Failed to update evaluation settings: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            default_settings = {
                "evaluation_mode": "single_call",
                "enable_cost_tracking": True,
                "enable_parallel_processing": False,
                "enable_ab_testing": False,
                "cost_threshold_daily": 50.0,
                "cost_threshold_monthly": 1000.0,
                "fallback_mode": "basic",
                "enable_prompt_review": False,
                "prompt_review_mode": "disabled",
                "require_approval_for_generation": False,
                "auto_approve_trusted_prompts": False,
                "prompt_review_timeout_hours": 24
            }
            
            success = self.set_setting(
                "evaluation_settings", 
                default_settings, 
                "Default evaluation and prompt review settings"
            )
            
            if success:
                logger.info("✅ [SettingsService] Settings reset to defaults successfully")
            return success
            
        except Exception as e:
            logger.error(f"❌ [SettingsService] Failed to reset settings: {e}")
            return False
