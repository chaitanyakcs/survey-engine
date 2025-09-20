#!/usr/bin/env python3
"""
LLM Client for Evaluation System
Provides unified interface for LLM-powered survey evaluation
"""

import os
import json
import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import Replicate client (same as demo_server)
try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False

# Import audit components
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from utils.llm_audit_decorator import LLMAuditContext
    from services.llm_audit_service import LLMAuditService
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

@dataclass
class LLMResponse:
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EvaluationLLMClient:
    """
    LLM client specifically designed for survey evaluation tasks
    Uses the same Replicate setup as the main survey generation
    """
    
    def __init__(self, db_session: Optional[Any] = None):
        self.replicate_available = REPLICATE_AVAILABLE
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.db_session = db_session
        self.audit_available = AUDIT_AVAILABLE
        
        # Read evaluation model from main app settings if available
        try:
            from src.config.settings import settings as app_settings
            self.model = getattr(app_settings, 'evaluation_model', getattr(app_settings, 'generation_model', 'openai/gpt-4o-mini'))
        except Exception:
            self.model = 'openai/gpt-4o-mini'
        
        if self.replicate_available and self.replicate_token:
            replicate.api_token = self.replicate_token
            print("🤖 LLM client initialized with Replicate API")
        else:
            print("⚠️  LLM client in fallback mode (no Replicate token)")
    
    async def analyze(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """
        Analyze content using LLM (alias for generate_evaluation)
        
        Args:
            prompt: Analysis prompt
            max_tokens: Maximum response tokens
            
        Returns:
            LLMResponse with analysis content
        """
        return await self.generate_evaluation(prompt, max_tokens)
    
    async def generate_evaluation(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """
        Generate evaluation using LLM
        
        Args:
            prompt: Evaluation prompt
            max_tokens: Maximum response tokens
            
        Returns:
            LLMResponse with evaluation content
        """
        
        if not self.replicate_available or not self.replicate_token:
            return self._fallback_evaluation(prompt)
        
        try:
            # Create audit context for this LLM interaction
            interaction_id = f"evaluation_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if (self.audit_available and self.db_session) else None
            
            if audit_service:
                async with LLMAuditContext(
                    audit_service=audit_service,
                    interaction_id=interaction_id,
                    model_name=self.model,
                    model_provider="replicate",
                    purpose="evaluation",
                    input_prompt=prompt,
                    sub_purpose="survey_evaluation",
                    context_type="survey_data",
                    hyperparameters={
                        "max_tokens": max_tokens,
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    },
                    metadata={
                        "prompt_length": len(prompt),
                        "max_tokens": max_tokens
                    },
                    tags=["evaluation", "survey_analysis"]
                ) as audit_context:
                    start_time = time.time()
                    # Use the same model as survey generation for consistency
                    response = await asyncio.to_thread(
                        replicate.run,
                        self.model,
                        input={
                            "prompt": prompt,
                            "max_tokens": max_tokens,
                            "temperature": 0.3,  # Lower temperature for more consistent evaluation
                            "top_p": 0.9,
                            "frequency_penalty": 0.0,
                            "presence_penalty": 0.0
                        }
                    )
                    
                    # Extract content from response
                    if isinstance(response, list):
                        content = ''.join(response)
                    else:
                        content = str(response)
                    
                    # Process the output and set audit context
                    response_time_ms = int((time.time() - start_time) * 1000)
                    audit_context.set_output(
                        output_content=content,
                        response_time_ms=response_time_ms
                    )
                    
                    return LLMResponse(
                        content=content.strip(),
                        success=True,
                        metadata={"model": self.model, "tokens": max_tokens}
                    )
            else:
                # Fallback without auditing
                # Use the same model as survey generation for consistency
                response = await asyncio.to_thread(
                    replicate.run,
                    self.model,
                    input={
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.3,  # Lower temperature for more consistent evaluation
                        "top_p": 0.9,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                )
                
                # Extract content from response
                if isinstance(response, list):
                    content = ''.join(response)
                else:
                    content = str(response)
                
                return LLMResponse(
                    content=content.strip(),
                    success=True,
                    metadata={"model": self.model, "tokens": max_tokens}
                )
            
        except Exception as e:
            print(f"🔴 LLM evaluation failed: {e}")
            return self._fallback_evaluation(prompt, error=str(e))
    
    def _fallback_evaluation(self, prompt: str, error: Optional[str] = None) -> LLMResponse:
        """
        Provide fallback evaluation when LLM unavailable
        """
        # Basic heuristic analysis based on prompt keywords
        fallback_content = self._generate_heuristic_evaluation(prompt)
        
        return LLMResponse(
            content=fallback_content,
            success=False,
            error=error or "LLM unavailable, using heuristic fallback",
            metadata={"fallback": True}
        )
    
    def _generate_heuristic_evaluation(self, prompt: str) -> str:
        """
        Generate basic heuristic evaluation when LLM unavailable
        """
        # Extract key evaluation aspects from prompt
        if "content validity" in prompt.lower():
            return self._content_validity_heuristic(prompt)
        elif "methodological rigor" in prompt.lower():
            return self._methodological_rigor_heuristic(prompt)
        elif "clarity" in prompt.lower() or "comprehensibility" in prompt.lower():
            return self._clarity_heuristic(prompt)
        elif "structural coherence" in prompt.lower():
            return self._structural_heuristic(prompt)
        elif "deployment readiness" in prompt.lower():
            return self._deployment_heuristic(prompt)
        else:
            return self._general_heuristic(prompt)
    
    def _content_validity_heuristic(self, prompt: str) -> str:
        """Heuristic evaluation for content validity"""
        return json.dumps({
            "score": 0.7,
            "analysis": "Heuristic analysis: Survey appears to cover main research objectives based on question variety and topic coverage.",
            "strengths": ["Diverse question types", "Clear research focus"],
            "improvements": ["Consider adding more specific objective-mapping questions"],
            "confidence": "medium_heuristic"
        })
    
    def _methodological_rigor_heuristic(self, prompt: str) -> str:
        """Heuristic evaluation for methodological rigor"""
        return json.dumps({
            "score": 0.65,
            "analysis": "Heuristic analysis: Survey demonstrates basic methodological structure with screening and core questions.",
            "strengths": ["Question sequencing present", "Multiple question types"],
            "improvements": ["Review for potential bias", "Validate question order"],
            "confidence": "medium_heuristic"
        })
    
    def _clarity_heuristic(self, prompt: str) -> str:
        """Heuristic evaluation for clarity & comprehensibility"""
        return json.dumps({
            "score": 0.75,
            "analysis": "Heuristic analysis: Questions appear to use clear language appropriate for target audience.",
            "strengths": ["Simple sentence structure", "Avoid technical jargon"],
            "improvements": ["Review for ambiguous wording", "Test comprehension levels"],
            "confidence": "medium_heuristic"
        })
    
    def _structural_heuristic(self, prompt: str) -> str:
        """Heuristic evaluation for structural coherence"""
        return json.dumps({
            "score": 0.68,
            "analysis": "Heuristic analysis: Survey demonstrates logical flow from general to specific topics.",
            "strengths": ["Logical progression", "Grouped related questions"],
            "improvements": ["Optimize question transitions", "Review section organization"],
            "confidence": "medium_heuristic"
        })
    
    def _deployment_heuristic(self, prompt: str) -> str:
        """Heuristic evaluation for deployment readiness"""
        return json.dumps({
            "score": 0.72,
            "analysis": "Heuristic analysis: Survey length and complexity appear suitable for deployment.",
            "strengths": ["Reasonable length", "Feasible implementation"],
            "improvements": ["Validate technical requirements", "Test completion rates"],
            "confidence": "medium_heuristic"
        })
    
    def _general_heuristic(self, prompt: str) -> str:
        """General heuristic evaluation"""
        return json.dumps({
            "score": 0.7,
            "analysis": "Heuristic analysis: Survey meets basic quality standards based on structure and content review.",
            "strengths": ["Well-structured", "Comprehensive coverage"],
            "improvements": ["Consider LLM-powered analysis for detailed insights"],
            "confidence": "low_heuristic"
        })

def create_evaluation_llm_client(db_session: Optional[Any] = None) -> EvaluationLLMClient:
    """Factory function to create evaluation LLM client"""
    return EvaluationLLMClient(db_session=db_session)

# Test function
async def test_llm_client():
    """Test the LLM client"""
    client = create_evaluation_llm_client()
    
    test_prompt = """
    Evaluate this survey for content validity:
    
    Survey: Customer Satisfaction Survey
    Questions: 5 questions about product quality and service
    
    Provide a score from 0.0 to 1.0 and detailed analysis.
    """
    
    response = await client.generate_evaluation(test_prompt)
    print(f"✅ LLM Client Test:")
    print(f"   Success: {response.success}")
    print(f"   Content length: {len(response.content)} chars")
    if response.error:
        print(f"   Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_llm_client())