"""
LLM Provider Abstraction
Supports multiple LLM providers (Replicate, OpenAI) with unified interface
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import replicate
from openai import AsyncOpenAI
from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 16000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM
        
        Returns:
            Dict with 'output' (raw response) and 'metadata'
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name (replicate, openai, etc.)"""
        pass


class ReplicateProvider(LLMProvider):
    """Replicate API provider"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.replicate_api_token
        if not self.api_token:
            raise ValueError("Replicate API token is required")
        self.client = replicate.Client(api_token=self.api_token)
        logger.info("✅ [ReplicateProvider] Initialized")
    
    def get_provider_name(self) -> str:
        return "replicate"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 16000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate using Replicate API"""
        start_time = time.time()
        
        try:
            # Replicate API call with timeout
            output = await asyncio.wait_for(
                self.client.async_run(
                    model,
                    input={
                        "prompt": prompt,
                        "response_format": response_format or {"type": "json_object"},
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": 0.9,
                        "system_prompt": system_prompt
                    }
                ),
                timeout=900.0  # 15 minute timeout
            )
            
            # Convert output to string for unified parsing
            import json as json_module
            from collections.abc import Iterable
            
            # Handle iterables (including async generators, lists, etc.) - but not strings
            if isinstance(output, str):
                raw_response = output
            elif isinstance(output, Iterable) and not isinstance(output, (dict, bytes, str)):
                # For iterables (lists, generators, etc.), join directly without newlines
                # This handles streaming responses that come character-by-character
                raw_response = "".join(str(item) for item in output)
                logger.debug(f"🔍 [ReplicateProvider] Joined iterable output, length: {len(raw_response)}")
            elif isinstance(output, dict):
                # Replicate returns dict like {'response_id': '...', 'text': '{...JSON...}'}
                # Check if there's a 'text' field with the actual content
                if 'text' in output and isinstance(output['text'], str):
                    raw_response = output['text']
                    logger.debug(f"🔍 [ReplicateProvider] Extracted 'text' field from dict")
                else:
                    raw_response = json_module.dumps(output, ensure_ascii=False)
            else:
                raw_response = str(output)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "output": raw_response,
                "metadata": {
                    "provider": "replicate",
                    "model": model,
                    "response_time_ms": response_time_ms,
                    "raw_output_type": type(output).__name__
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("Replicate API call timed out after 15 minutes")
        except Exception as e:
            logger.error(f"❌ [ReplicateProvider] Generation failed: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI API provider with structured outputs support"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("✅ [OpenAIProvider] Initialized")
    
    def get_provider_name(self) -> str:
        return "openai"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 16000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate using OpenAI API with structured outputs"""
        start_time = time.time()
        
        try:
            # OpenAI structured outputs with JSON schema
            # Use gpt-4o-2024-08-06 or later for structured outputs
            # For now, we'll use response_format for JSON mode
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare response format
            # If structured outputs available, use json_schema
            # Otherwise, use json_object for basic JSON mode
            if response_format and "json_schema" in response_format:
                # Structured outputs (available in newer models)
                response_format_param = {
                    "type": "json_schema",
                    "json_schema": response_format["json_schema"]
                }
            else:
                # Basic JSON mode
                response_format_param = {"type": "json_object"}
            
            # OpenAI API call
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model or "gpt-4o",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format_param
                ),
                timeout=900.0  # 15 minute timeout
            )
            
            # Extract raw response
            raw_response = response.choices[0].message.content
            if not raw_response:
                raise Exception("OpenAI returned empty response")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "output": raw_response,
                "metadata": {
                    "provider": "openai",
                    "model": model or "gpt-4o",
                    "response_time_ms": response_time_ms,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                        "completion_tokens": response.usage.completion_tokens if response.usage else None,
                        "total_tokens": response.usage.total_tokens if response.usage else None
                    }
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("OpenAI API call timed out after 15 minutes")
        except Exception as e:
            logger.error(f"❌ [OpenAIProvider] Generation failed: {e}")
            raise


def create_llm_provider(
    provider: str = "replicate",
    model: Optional[str] = None,
    api_token: Optional[str] = None,
    api_key: Optional[str] = None
) -> LLMProvider:
    """
    Factory function to create appropriate LLM provider
    
    Args:
        provider: "replicate" or "openai"
        model: Model name (used to auto-detect provider if provider not specified)
        api_token: Replicate API token (optional, uses settings if not provided)
        api_key: OpenAI API key (optional, uses settings if not provided)
        
    Returns:
        LLMProvider instance
    """
    # Auto-detect provider from model name if not specified
    if not provider:
        if model and model.startswith("gpt-"):
            provider = "openai"
        else:
            provider = "replicate"
    
    if provider == "openai":
        return OpenAIProvider(api_key=api_key)
    elif provider == "replicate":
        return ReplicateProvider(api_token=api_token)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: 'replicate', 'openai'")

