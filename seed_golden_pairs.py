#!/usr/bin/env python3
"""
Seed script for golden RFQ-survey pairs
"""
import asyncio
import json
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import GoldenRFQSurveyPair
from src.services.embedding_service import EmbeddingService
from datetime import datetime


# Sample golden pairs data
GOLDEN_PAIRS = [
    {
        "rfq_text": """
        We're launching a new smartphone in the premium segment and need to understand optimal pricing strategy. 
        Target market is tech-savvy consumers aged 25-45 with household income $75k+. 
        Key features include 5G, 108MP camera, 8GB RAM, 256GB storage. 
        Main competitors are iPhone 14 Pro ($999) and Samsung Galaxy S23+ ($999). 
        We want to identify the price point that maximizes revenue while maintaining perceived quality.
        """.strip(),
        "survey_json": {
            "title": "Premium Smartphone Pricing Research",
            "description": "Van Westendorp Price Sensitivity Analysis for new smartphone",
            "methodology": "Van Westendorp PSM",
            "questions": [
                {
                    "id": "psm_1",
                    "text": "At what price would this smartphone be so expensive that you would not consider buying it? (Too Expensive)",
                    "type": "number",
                    "required": True
                },
                {
                    "id": "psm_2", 
                    "text": "At what price would you consider this smartphone to be priced so low that you would feel the quality couldn't be very good? (Too Cheap)",
                    "type": "number",
                    "required": True
                },
                {
                    "id": "psm_3",
                    "text": "At what price would you consider this smartphone starting to get expensive, so that it is not out of the question, but you would have to give some thought to buying it? (Getting Expensive)",
                    "type": "number", 
                    "required": True
                },
                {
                    "id": "psm_4",
                    "text": "At what price would you consider this smartphone to be a bargain—a great buy for the money? (Good Deal)",
                    "type": "number",
                    "required": True
                },
                {
                    "id": "demo_1",
                    "text": "What is your age?",
                    "type": "single_choice",
                    "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
                    "required": True
                },
                {
                    "id": "demo_2", 
                    "text": "What is your annual household income?",
                    "type": "single_choice",
                    "options": ["Under $50k", "$50k-$75k", "$75k-$100k", "$100k-$150k", "$150k+"],
                    "required": True
                }
            ]
        },
        "methodology_tags": ["vw", "van_westendorp", "pricing"],
        "industry_category": "consumer_electronics", 
        "research_goal": "pricing optimization",
        "quality_score": 0.95
    },
    {
        "rfq_text": """
        We're developing a new subscription-based fitness app with AI personal trainer features. 
        Need to understand which features are most important to potential users and optimal feature combinations.
        Target audience: fitness enthusiasts, gym-goers, and home workout users aged 22-50.
        Considering features like: AI coaching, workout plans, nutrition tracking, social features, 
        live classes, equipment-free workouts, progress analytics, and music integration.
        Budget constraints mean we can only include 4-5 key features in the initial version.
        """.strip(),
        "survey_json": {
            "title": "Fitness App Feature Prioritization Study",
            "description": "MaxDiff analysis to identify most valuable features for fitness app",
            "methodology": "MaxDiff",
            "questions": [
                {
                    "id": "maxdiff_1",
                    "text": "From the features below, which would be MOST important to you in a fitness app and which would be LEAST important?",
                    "type": "maxdiff",
                    "features": ["AI Personal Coaching", "Custom Workout Plans", "Nutrition Tracking", "Social Community"],
                    "required": True
                },
                {
                    "id": "maxdiff_2", 
                    "text": "From the features below, which would be MOST important to you in a fitness app and which would be LEAST important?",
                    "type": "maxdiff",
                    "features": ["Live Classes", "Equipment-Free Workouts", "Progress Analytics", "Music Integration"],
                    "required": True
                },
                {
                    "id": "maxdiff_3",
                    "text": "From the features below, which would be MOST important to you in a fitness app and which would be LEAST important?", 
                    "type": "maxdiff",
                    "features": ["AI Personal Coaching", "Live Classes", "Equipment-Free Workouts", "Social Community"],
                    "required": True
                },
                {
                    "id": "demo_1",
                    "text": "How often do you currently exercise?",
                    "type": "single_choice",
                    "options": ["Daily", "4-6 times/week", "2-3 times/week", "Once a week", "Rarely/Never"],
                    "required": True
                },
                {
                    "id": "demo_2",
                    "text": "Where do you primarily work out?",
                    "type": "single_choice", 
                    "options": ["Home", "Gym/Fitness Center", "Outdoors", "Mix of locations"],
                    "required": True
                }
            ]
        },
        "methodology_tags": ["maxdiff", "feature_prioritization"],
        "industry_category": "fitness_technology",
        "research_goal": "feature optimization", 
        "quality_score": 0.88
    },
    {
        "rfq_text": """
        Our restaurant chain wants to test different price points for a new plant-based burger option.
        We're targeting health-conscious consumers who are willing to pay premium prices for quality alternatives.
        The burger costs $4.50 to make and current menu prices range from $8.99 (basic burger) to $16.99 (premium).
        We want to test price points between $11.99-$15.99 to find optimal demand curve.
        Key markets: Urban areas, college towns, health-conscious suburban areas.
        """.strip(),
        "survey_json": {
            "title": "Plant-Based Burger Pricing Study", 
            "description": "Gabor-Granger price testing for new menu item",
            "methodology": "Gabor-Granger",
            "questions": [
                {
                    "id": "gg_1",
                    "text": "Would you purchase this plant-based burger at $15.99?",
                    "type": "yes_no",
                    "price_point": 15.99,
                    "required": True
                },
                {
                    "id": "gg_2",
                    "text": "Would you purchase this plant-based burger at $14.99?", 
                    "type": "yes_no",
                    "price_point": 14.99,
                    "required": True
                },
                {
                    "id": "gg_3",
                    "text": "Would you purchase this plant-based burger at $13.99?",
                    "type": "yes_no", 
                    "price_point": 13.99,
                    "required": True
                },
                {
                    "id": "gg_4",
                    "text": "Would you purchase this plant-based burger at $12.99?",
                    "type": "yes_no",
                    "price_point": 12.99, 
                    "required": True
                },
                {
                    "id": "gg_5",
                    "text": "Would you purchase this plant-based burger at $11.99?",
                    "type": "yes_no",
                    "price_point": 11.99,
                    "required": True
                },
                {
                    "id": "demo_1",
                    "text": "How often do you eat plant-based meals?",
                    "type": "single_choice",
                    "options": ["Daily", "Several times a week", "Once a week", "Occasionally", "Never"],
                    "required": True
                },
                {
                    "id": "demo_2",
                    "text": "What is your primary motivation for eating plant-based foods?",
                    "type": "single_choice",
                    "options": ["Health benefits", "Environmental concerns", "Animal welfare", "Taste preference", "Not interested"],
                    "required": False
                }
            ]
        },
        "methodology_tags": ["gg", "gabor_granger", "pricing"],
        "industry_category": "food_service",
        "research_goal": "demand forecasting",
        "quality_score": 0.92
    },
    {
        "rfq_text": """
        We're launching a new cloud storage service for small businesses and need to understand 
        which service attributes drive purchase decisions and optimal service configurations.
        Key attributes to test: Storage capacity (100GB, 500GB, 1TB, 5TB), 
        Price ($9.99, $19.99, $39.99, $99.99/month), Security level (Standard, Enhanced, Enterprise), 
        Support (Email, Chat, Phone), and Backup frequency (Daily, Real-time).
        Target: Small business owners, IT managers, freelancers who need reliable cloud storage.
        """.strip(),
        "survey_json": {
            "title": "Cloud Storage Service Optimization",
            "description": "Choice-based conjoint analysis for cloud storage service attributes", 
            "methodology": "Choice-Based Conjoint",
            "questions": [
                {
                    "id": "cbc_1",
                    "text": "Which cloud storage service would you choose?",
                    "type": "choice",
                    "options": [
                        {
                            "id": "option_a",
                            "attributes": {
                                "storage": "500GB",
                                "price": "$19.99/month",
                                "security": "Enhanced", 
                                "support": "Chat",
                                "backup": "Daily"
                            }
                        },
                        {
                            "id": "option_b", 
                            "attributes": {
                                "storage": "1TB",
                                "price": "$39.99/month",
                                "security": "Standard",
                                "support": "Phone",
                                "backup": "Real-time"
                            }
                        },
                        {
                            "id": "none",
                            "text": "None of these"
                        }
                    ],
                    "required": True
                },
                {
                    "id": "cbc_2",
                    "text": "Which cloud storage service would you choose?",
                    "type": "choice",
                    "options": [
                        {
                            "id": "option_a",
                            "attributes": {
                                "storage": "100GB", 
                                "price": "$9.99/month",
                                "security": "Enterprise",
                                "support": "Email",
                                "backup": "Real-time"
                            }
                        },
                        {
                            "id": "option_b",
                            "attributes": {
                                "storage": "5TB",
                                "price": "$99.99/month", 
                                "security": "Enhanced",
                                "support": "Phone",
                                "backup": "Daily"
                            }
                        },
                        {
                            "id": "none",
                            "text": "None of these"
                        }
                    ],
                    "required": True
                }
            ]
        },
        "methodology_tags": ["conjoint", "cbc", "choice_modeling"],
        "industry_category": "cloud_services",
        "research_goal": "product optimization",
        "quality_score": 0.90
    }
]


async def create_golden_pair(session: Session, embedding_service: EmbeddingService, pair_data: dict):
    """Create a single golden pair with embedding"""
    print(f"Creating golden pair for: {pair_data['industry_category']}")
    
    # Generate embedding for RFQ text
    embedding = await embedding_service.get_embedding(pair_data["rfq_text"])
    
    # Create the golden pair
    golden_pair = GoldenRFQSurveyPair(
        rfq_text=pair_data["rfq_text"],
        rfq_embedding=embedding,
        survey_json=pair_data["survey_json"],
        methodology_tags=pair_data["methodology_tags"],
        industry_category=pair_data["industry_category"],
        research_goal=pair_data["research_goal"],
        quality_score=pair_data["quality_score"],
        usage_count=0,
        created_at=datetime.utcnow()
    )
    
    session.add(golden_pair)
    return golden_pair


async def seed_golden_pairs():
    """Seed the database with golden RFQ-survey pairs"""
    print("Starting to seed golden RFQ-survey pairs...")
    
    # Initialize services
    embedding_service = EmbeddingService()
    session = SessionLocal()
    
    try:
        # Check if we already have golden pairs
        existing_count = session.query(GoldenRFQSurveyPair).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing golden pairs. Clearing them first...")
            session.query(GoldenRFQSurveyPair).delete()
            session.commit()
        
        # Create new golden pairs
        created_pairs = []
        for i, pair_data in enumerate(GOLDEN_PAIRS):
            print(f"Processing pair {i+1}/{len(GOLDEN_PAIRS)}...")
            pair = await create_golden_pair(session, embedding_service, pair_data)
            created_pairs.append(pair)
        
        # Commit all pairs
        session.commit()
        print(f"Successfully created {len(created_pairs)} golden pairs!")
        
        # Verify creation
        total_pairs = session.query(GoldenRFQSurveyPair).count()
        print(f"Total golden pairs in database: {total_pairs}")
        
        # Display sample data
        sample_pair = session.query(GoldenRFQSurveyPair).first()
        if sample_pair:
            print(f"\nSample pair:")
            print(f"- Industry: {sample_pair.industry_category}")
            print(f"- Methodology: {sample_pair.methodology_tags}")
            print(f"- Quality Score: {sample_pair.quality_score}")
            print(f"- Embedding dimension: {len(sample_pair.rfq_embedding) if sample_pair.rfq_embedding else 'None'}")
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(seed_golden_pairs())