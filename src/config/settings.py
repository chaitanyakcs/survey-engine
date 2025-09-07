from pydantic_settings import BaseSettings
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
    
    @property
    def edit_collection_priority_list(self) -> List[str]:
        return [item.strip() for item in self.edit_collection_priority.split(",")]
    
    class Config:
        env_file = ".env"


settings = Settings()