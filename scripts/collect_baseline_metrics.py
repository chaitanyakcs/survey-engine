#!/usr/bin/env python3
"""
Baseline metrics collection script for golden retrieval enhancement
Collects metrics for 10 test RFQs to establish baseline before improvements
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.retrieval_service import RetrievalService
from src.services.embedding_service import EmbeddingService
from src.services.evaluator_service import EvaluatorService
from src.services.generation_service import GenerationService
from src.services.prompt_service import PromptService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test RFQs for baseline collection
TEST_RFQS = [
    {
        "title": "Smartphone Pricing Research",
        "text": "We're launching a new smartphone in the premium segment and need to understand optimal pricing strategy. Target market is tech-savvy consumers aged 25-45 with household income $75k+. Key features include 5G, 108MP camera, 8GB RAM, 256GB storage. Main competitors are iPhone 14 Pro ($999) and Samsung Galaxy S23+ ($999). We want to identify the price point that maximizes revenue while maintaining perceived quality.",
        "category": "consumer_electronics",
        "segment": "premium_tech",
        "goal": "pricing_optimization",
        "expected_methodology": "van_westendorp"
    },
    {
        "title": "Fitness App Feature Study",
        "text": "We're developing a new subscription-based fitness app with AI personal trainer features. Need to understand which features are most important to potential users and optimal feature combinations. Target audience: fitness enthusiasts, gym-goers, and home workout users aged 22-50. Considering features like: AI coaching, workout plans, nutrition tracking, social features, live classes, equipment-free workouts, progress analytics, and music integration.",
        "category": "fitness_technology",
        "segment": "fitness_enthusiasts",
        "goal": "feature_optimization",
        "expected_methodology": "maxdiff"
    },
    {
        "title": "Restaurant Menu Pricing",
        "text": "Our restaurant chain wants to test different price points for a new plant-based burger option. We're targeting health-conscious consumers who are willing to pay premium prices for quality alternatives. The burger costs $4.50 to make and current menu prices range from $8.99 (basic burger) to $16.99 (premium). We want to test price points between $11.99-$15.99 to find optimal demand curve.",
        "category": "food_service",
        "segment": "health_conscious",
        "goal": "demand_forecasting",
        "expected_methodology": "gabor_granger"
    },
    {
        "title": "Cloud Storage Service",
        "text": "We're launching a new cloud storage service for small businesses and need to understand which service attributes drive purchase decisions and optimal service configurations. Key attributes to test: Storage capacity (100GB, 500GB, 1TB, 5TB), Price ($9.99, $19.99, $39.99, $99.99/month), Security level (Standard, Enhanced, Enterprise), Support (Email, Chat, Phone), and Backup frequency (Daily, Real-time).",
        "category": "cloud_services",
        "segment": "small_business",
        "goal": "product_optimization",
        "expected_methodology": "conjoint"
    },
    {
        "title": "Customer Satisfaction Survey",
        "text": "We need to measure customer satisfaction and loyalty for our e-commerce platform. Target customers are online shoppers who have made at least one purchase in the last 6 months. We want to understand satisfaction levels, likelihood to recommend, and key drivers of satisfaction. Also need to identify areas for improvement and measure Net Promoter Score.",
        "category": "e_commerce",
        "segment": "online_shoppers",
        "goal": "satisfaction_research",
        "expected_methodology": "nps"
    },
    {
        "title": "Healthcare App Usability",
        "text": "We're developing a telemedicine app for chronic disease management and need to understand user experience and feature preferences. Target users are patients with diabetes, hypertension, or heart disease aged 40-70. Key features include medication reminders, symptom tracking, doctor consultations, health data integration, and family caregiver access.",
        "category": "healthcare",
        "segment": "chronic_patients",
        "goal": "user_experience",
        "expected_methodology": "usability_testing"
    },
    {
        "title": "Automotive Brand Study",
        "text": "We're conducting brand awareness and perception research for our electric vehicle brand. Target audience is environmentally conscious consumers aged 25-55 with household income $60k+. We want to measure brand awareness, consideration, purchase intent, and key brand attributes. Also need to understand how we compare to Tesla, BMW, and other EV brands.",
        "category": "automotive",
        "segment": "eco_conscious",
        "goal": "brand_research",
        "expected_methodology": "brand_tracking"
    },
    {
        "title": "Financial Services Product",
        "text": "We're launching a new robo-advisor investment platform and need to understand customer preferences and optimal service configurations. Target customers are millennials and Gen X with investable assets $25k-$500k. Key attributes include: Investment minimums, Management fees, Portfolio options, Human advisor access, Mobile app features, and Educational resources.",
        "category": "financial_services",
        "segment": "millennial_investors",
        "goal": "product_optimization",
        "expected_methodology": "conjoint"
    },
    {
        "title": "Education Technology",
        "text": "We're developing an online learning platform for professional development and need to understand course preferences and pricing sensitivity. Target learners are working professionals aged 25-50 seeking to upskill in technology, business, or creative fields. Key factors include course duration, certification value, instructor quality, interactive features, and pricing models.",
        "category": "education",
        "segment": "working_professionals",
        "goal": "product_development",
        "expected_methodology": "conjoint"
    },
    {
        "title": "Retail Customer Experience",
        "text": "We're improving our omnichannel retail experience and need to understand customer journey preferences and pain points. Target customers are omnichannel shoppers who use both online and in-store channels. We want to measure satisfaction across touchpoints, identify friction points, and understand preferences for different service options.",
        "category": "retail",
        "segment": "omnichannel_shoppers",
        "goal": "customer_experience",
        "expected_methodology": "csat"
    }
]


class BaselineMetricsCollector:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService(db_session)
        self.evaluator_service = EvaluatorService(db_session)
        self.generation_service = GenerationService(db_session)
        self.prompt_service = PromptService(db_session)
        
        # Initialize tokenizer for prompt analysis
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.tokenizer = None
            logger.warning("tiktoken not available, token counting will be approximate")
        except Exception:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, token counting will be approximate")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters
            return len(text) // 4

    async def collect_rfq_metrics(self, rfq_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics for a single RFQ"""
        logger.info(f"Collecting metrics for: {rfq_data['title']}")
        
        metrics = {
            "rfq_title": rfq_data["title"],
            "rfq_category": rfq_data["category"],
            "rfq_segment": rfq_data["segment"],
            "rfq_goal": rfq_data["goal"],
            "expected_methodology": rfq_data["expected_methodology"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Generate embedding
            embedding = await self.embedding_service.get_embedding(rfq_data["text"])
            metrics["embedding_generated"] = True
            metrics["embedding_dimension"] = len(embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            metrics["embedding_generated"] = False
            metrics["embedding_error"] = str(e)
            return metrics
        
        try:
            # Test golden pair retrieval
            golden_examples = await self.retrieval_service.retrieve_golden_pairs(
                embedding=embedding,
                methodology_tags=None,
                limit=3
            )
            
            metrics["golden_examples_retrieved"] = len(golden_examples)
            metrics["golden_similarity_scores"] = [ex.get("similarity", 0) for ex in golden_examples]
            metrics["avg_golden_similarity"] = sum(metrics["golden_similarity_scores"]) / len(metrics["golden_similarity_scores"]) if golden_examples else 0
            
            # Check methodology match
            retrieved_methodologies = set()
            for ex in golden_examples:
                if ex.get("methodology_tags"):
                    retrieved_methodologies.update(ex["methodology_tags"])
            
            expected_methodology = rfq_data["expected_methodology"]
            methodology_match = any(expected_methodology in meth.lower() for meth in retrieved_methodologies)
            metrics["methodology_match"] = methodology_match
            metrics["retrieved_methodologies"] = list(retrieved_methodologies)
            
        except Exception as e:
            logger.error(f"Failed to retrieve golden examples: {e}")
            metrics["golden_retrieval_error"] = str(e)
            metrics["golden_examples_retrieved"] = 0
            metrics["methodology_match"] = False
        
        try:
            # Test prompt generation
            context = {
                "rfq_details": {
                    "text": rfq_data["text"],
                    "title": rfq_data["title"],
                    "category": rfq_data["category"],
                    "segment": rfq_data["segment"],
                    "goal": rfq_data["goal"]
                },
                "golden_examples": golden_examples if 'golden_examples' in locals() else [],
                "methodology_guidance": [],
                "template_fallbacks": []
            }
            
            prompt = await self.prompt_service.build_golden_enhanced_prompt(
                context=context,
                golden_examples=golden_examples if 'golden_examples' in locals() else [],
                methodology_blocks=[],
                custom_rules={"rules": []}
            )
            
            metrics["prompt_generated"] = True
            metrics["prompt_length"] = len(prompt)
            metrics["prompt_tokens"] = self.count_tokens(prompt)
            
        except Exception as e:
            logger.error(f"Failed to generate prompt: {e}")
            metrics["prompt_generated"] = False
            metrics["prompt_error"] = str(e)
        
        # Note: We don't run full generation in baseline collection to avoid API costs
        # This will be done in a separate test after improvements
        
        return metrics

    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect metrics for all test RFQs"""
        logger.info("Starting baseline metrics collection...")
        
        all_metrics = {
            "collection_timestamp": datetime.utcnow().isoformat(),
            "total_rfqs": len(TEST_RFQS),
            "rfq_metrics": []
        }
        
        for i, rfq_data in enumerate(TEST_RFQS):
            logger.info(f"Processing RFQ {i+1}/{len(TEST_RFQS)}: {rfq_data['title']}")
            metrics = await self.collect_rfq_metrics(rfq_data)
            all_metrics["rfq_metrics"].append(metrics)
        
        # Calculate summary statistics
        successful_embeddings = sum(1 for m in all_metrics["rfq_metrics"] if m.get("embedding_generated", False))
        successful_retrievals = sum(1 for m in all_metrics["rfq_metrics"] if m.get("golden_examples_retrieved", 0) > 0)
        methodology_matches = sum(1 for m in all_metrics["rfq_metrics"] if m.get("methodology_match", False))
        successful_prompts = sum(1 for m in all_metrics["rfq_metrics"] if m.get("prompt_generated", False))
        
        avg_similarity_scores = [m.get("avg_golden_similarity", 0) for m in all_metrics["rfq_metrics"] if m.get("avg_golden_similarity", 0) > 0]
        avg_similarity = sum(avg_similarity_scores) / len(avg_similarity_scores) if avg_similarity_scores else 0
        
        prompt_lengths = [m.get("prompt_length", 0) for m in all_metrics["rfq_metrics"] if m.get("prompt_length", 0) > 0]
        avg_prompt_length = sum(prompt_lengths) / len(prompt_lengths) if prompt_lengths else 0
        
        all_metrics["summary"] = {
            "successful_embeddings": successful_embeddings,
            "embedding_success_rate": successful_embeddings / len(TEST_RFQS),
            "successful_retrievals": successful_retrievals,
            "retrieval_success_rate": successful_retrievals / len(TEST_RFQS),
            "methodology_matches": methodology_matches,
            "methodology_match_rate": methodology_matches / len(TEST_RFQS),
            "successful_prompts": successful_prompts,
            "prompt_success_rate": successful_prompts / len(TEST_RFQS),
            "avg_golden_similarity": avg_similarity,
            "avg_prompt_length": avg_prompt_length,
            "avg_prompt_tokens": sum(m.get("prompt_tokens", 0) for m in all_metrics["rfq_metrics"]) / len(TEST_RFQS)
        }
        
        return all_metrics


async def main():
    """Main function to collect baseline metrics"""
    logger.info("Starting baseline metrics collection...")
    
    # Initialize database session
    db_session = SessionLocal()
    
    try:
        collector = BaselineMetricsCollector(db_session)
        metrics = await collector.collect_all_metrics()
        
        # Save metrics to file
        output_file = "baseline_metrics.json"
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Baseline metrics collected and saved to {output_file}")
        logger.info(f"Summary:")
        logger.info(f"  - Embedding success rate: {metrics['summary']['embedding_success_rate']:.1%}")
        logger.info(f"  - Retrieval success rate: {metrics['summary']['retrieval_success_rate']:.1%}")
        logger.info(f"  - Methodology match rate: {metrics['summary']['methodology_match_rate']:.1%}")
        logger.info(f"  - Prompt success rate: {metrics['summary']['prompt_success_rate']:.1%}")
        logger.info(f"  - Average golden similarity: {metrics['summary']['avg_golden_similarity']:.3f}")
        logger.info(f"  - Average prompt length: {metrics['summary']['avg_prompt_length']:.0f} chars")
        logger.info(f"  - Average prompt tokens: {metrics['summary']['avg_prompt_tokens']:.0f}")
        
    except Exception as e:
        logger.error(f"Failed to collect baseline metrics: {e}")
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    asyncio.run(main())
