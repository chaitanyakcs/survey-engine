from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql://chaitanya@localhost:5432/survey_engine_db"
    redis_url: str = "redis://localhost:6379"
    replicate_api_token: str = ""
    
    # Model configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    generation_model: str = "openai/gpt-5"
    golden_similarity_threshold: float = 0.75
    max_golden_examples: int = 3
    
    # Validation configuration
    methodology_validation_strict: bool = True
    enable_edit_tracking: bool = True
    edit_granularity_level: int = 2
    quality_gate_threshold: int = 50
    
    # Training configuration
    min_edits_for_sft_prep: int = 100
    min_golden_pairs_for_similarity: int = 10
    edit_collection_priority: str = "question_text,question_type,additions,deletions"
    
    # Application configuration
    debug: bool = False
    log_level: str = "INFO"
    
    # Additional environment variables that might be present
    skip_migrations: str = "false"  # Handle as string to avoid validation issues
    database_host: str = "localhost"
    database_port: str = "5432"
    database_user: str = "chaitanya"
    database_password: str = ""
    database_name: str = "survey_engine_db"
    openai_api_key: str = "your_openai_api_key_here"
    service: str = "backend"
    port: str = "8000"
    
    @property
    def edit_collection_priority_list(self) -> List[str]:
        return [item.strip() for item in self.edit_collection_priority.split(",")]
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",  # Ignore extra fields from environment
        validate_assignment=False,  # Don't validate on assignment
        arbitrary_types_allowed=True  # Allow arbitrary types
    )


# Only instantiate settings if not in test mode
import sys
if "pytest" not in sys.modules:
    settings = Settings()
else:
    # In test mode, create a mock settings object
    settings = Settings(
        database_url="postgresql://test@localhost:5432/test_db",
        redis_url="redis://localhost:6379",
        replicate_api_token="test_token"
    )