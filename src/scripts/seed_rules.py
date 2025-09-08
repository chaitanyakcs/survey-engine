#!/usr/bin/env python3
"""
Script to seed the database with initial rules and methodologies
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.database import get_db
from src.services.prompt_service import PromptService
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_methodology_rules():
    """Seed comprehensive methodology rules"""
    return {
        "van_westendorp": {
            "description": "Van Westendorp Price Sensitivity Meter - Measures price sensitivity through four key questions",
            "required_questions": 4,
            "question_flow": [
                "At what price would you consider this product to be so expensive that you would not consider buying it?",
                "At what price would you consider this product to be priced so low that you would feel the quality couldn't be very good?",
                "At what price would you consider this product starting to get expensive, so that it is not out of the question, but you would have to give some thought to buying it?",
                "At what price would you consider this product to be a bargain - a great buy for the money?"
            ],
            "validation_rules": [
                "Must have exactly 4 price questions",
                "Questions must follow the exact Van Westendorp format",
                "Price ranges should be logical and sequential",
                "Include open-ended follow-up for reasoning",
                "Use currency-appropriate formatting"
            ],
            "best_practices": [
                "Present questions in random order to avoid bias",
                "Include product description before price questions",
                "Use realistic price ranges based on market research",
                "Add demographic questions for segmentation"
            ]
        },
        "conjoint": {
            "description": "Conjoint Analysis / Choice Modeling - Measures preferences for product attributes",
            "required_attributes": 3,
            "max_attributes": 6,
            "question_flow": [
                "Screening questions for product familiarity",
                "Attribute importance ranking",
                "Choice sets with different combinations",
                "Demographic and behavioral questions"
            ],
            "validation_rules": [
                "Must have balanced choice sets",
                "Attributes must be orthogonal (independent)",
                "Include appropriate sample size calculations",
                "Use realistic attribute levels",
                "Include 'None of the above' option"
            ],
            "best_practices": [
                "Limit to 3-6 attributes to avoid cognitive overload",
                "Use 2-4 levels per attribute",
                "Include 8-12 choice tasks per respondent",
                "Randomize choice set presentation"
            ]
        },
        "maxdiff": {
            "description": "MaxDiff (Maximum Difference Scaling) - Ranks items by importance",
            "required_items": 8,
            "max_items": 20,
            "question_flow": [
                "Item familiarity screening",
                "Multiple choice sets showing 3-5 items",
                "Best/worst selection within each set",
                "Demographic questions"
            ],
            "validation_rules": [
                "Items must be balanced across choice sets",
                "Include appropriate number of choice tasks (typically 12-15)",
                "Ensure statistical power for analysis",
                "Use clear, distinct item descriptions"
            ],
            "best_practices": [
                "Keep items concise and mutually exclusive",
                "Use 3-5 items per choice set",
                "Include 12-15 choice tasks total",
                "Randomize item order within sets"
            ]
        },
        "nps": {
            "description": "Net Promoter Score - Measures customer loyalty and satisfaction",
            "required_questions": 2,
            "question_flow": [
                "How likely are you to recommend [product/service] to a friend or colleague? (0-10 scale)",
                "What is the primary reason for your score? (open text)"
            ],
            "validation_rules": [
                "Must use 0-10 scale",
                "Include follow-up question for reasoning",
                "Properly categorize promoters (9-10), passives (7-8), detractors (0-6)",
                "Use consistent wording across surveys"
            ],
            "best_practices": [
                "Ask NPS question early in survey",
                "Include context about the product/service",
                "Add behavioral questions for segmentation",
                "Use consistent timeframes (e.g., 'in the past 6 months')"
            ]
        },
        "csat": {
            "description": "Customer Satisfaction - Measures satisfaction with products/services",
            "required_questions": 3,
            "question_flow": [
                "Overall satisfaction rating (1-5 or 1-10 scale)",
                "Satisfaction with specific aspects",
                "Likelihood to continue using/recommend"
            ],
            "validation_rules": [
                "Use consistent scale (1-5 or 1-10)",
                "Include multiple satisfaction dimensions",
                "Add open-ended feedback question",
                "Include behavioral intent questions"
            ],
            "best_practices": [
                "Ask about recent experience (within 30 days)",
                "Include both overall and specific satisfaction",
                "Add demographic questions for analysis",
                "Use clear, specific question wording"
            ]
        },
        "brand_tracking": {
            "description": "Brand Tracking - Measures brand awareness, perception, and equity",
            "required_questions": 8,
            "question_flow": [
                "Unaided brand awareness (open text)",
                "Aided brand awareness (multiple choice)",
                "Brand perception attributes (rating scales)",
                "Purchase intent and preference",
                "Demographic and psychographic questions"
            ],
            "validation_rules": [
                "Include both unaided and aided awareness",
                "Use consistent attribute lists across waves",
                "Include competitive brands",
                "Add behavioral and demographic questions"
            ],
            "best_practices": [
                "Ask awareness questions first",
                "Use consistent attribute scales",
                "Include both functional and emotional attributes",
                "Add purchase behavior questions"
            ]
        },
        "pricing_research": {
            "description": "Pricing Research - Determines optimal pricing strategies",
            "required_questions": 6,
            "question_flow": [
                "Price sensitivity questions",
                "Willingness to pay at different price points",
                "Price vs. value perception",
                "Competitive pricing awareness",
                "Purchase behavior at different prices"
            ],
            "validation_rules": [
                "Include multiple price points",
                "Test different price presentations",
                "Include competitive context",
                "Add purchase behavior questions"
            ],
            "best_practices": [
                "Use realistic price ranges",
                "Test different price formats",
                "Include value proposition context",
                "Add demographic questions for segmentation"
            ]
        }
    }


def seed_quality_rules():
    """Seed comprehensive quality rules"""
    return {
        "question_quality": [
            "Questions must be clear, concise, and unambiguous",
            "Avoid leading, loaded, or double-barreled questions",
            "Use appropriate question types for the data needed",
            "Include proper validation and skip logic where needed",
            "Avoid jargon and technical terms unless necessary",
            "Use consistent terminology throughout the survey",
            "Ensure questions are culturally appropriate and inclusive"
        ],
        "survey_structure": [
            "Start with screening questions to qualify respondents",
            "Group related questions logically",
            "Place sensitive questions near the end",
            "Include demographic questions for segmentation",
            "Use progress indicators for long surveys",
            "Include clear instructions and context",
            "End with thank you message and next steps"
        ],
        "methodology_compliance": [
            "Follow established research methodology standards",
            "Include appropriate sample size considerations",
            "Ensure statistical validity of question design",
            "Add proper metadata for analysis",
            "Use validated scales when available",
            "Include appropriate control questions",
            "Ensure randomization where needed"
        ],
        "respondent_experience": [
            "Keep survey length appropriate (5-15 minutes)",
            "Use clear instructions and progress indicators",
            "Avoid repetitive or redundant questions",
            "Ensure mobile-friendly question formats",
            "Use engaging and conversational language",
            "Include appropriate incentives information",
            "Provide clear privacy and data usage information"
        ],
        "data_quality": [
            "Include attention check questions",
            "Use appropriate question scales and ranges",
            "Include 'Don't know' or 'Prefer not to answer' options",
            "Ensure logical flow and skip patterns",
            "Include validation for open-ended responses",
            "Use consistent response formats",
            "Include quality control measures"
        ],
        "accessibility": [
            "Use clear, readable fonts and colors",
            "Ensure keyboard navigation compatibility",
            "Include alt text for images",
            "Use sufficient color contrast",
            "Provide text alternatives for audio/video",
            "Ensure screen reader compatibility",
            "Test with assistive technologies"
        ]
    }


def seed_industry_rules():
    """Seed industry-specific rules"""
    return {
        "healthcare": [
            "Include HIPAA compliance considerations",
            "Use appropriate medical terminology",
            "Include consent and privacy statements",
            "Consider patient confidentiality",
            "Use validated health assessment tools",
            "Include appropriate demographic questions",
            "Ensure cultural sensitivity in health questions"
        ],
        "financial_services": [
            "Include appropriate disclaimers",
            "Use clear financial terminology",
            "Include risk assessment questions",
            "Ensure regulatory compliance",
            "Include appropriate demographic questions",
            "Use validated financial scales",
            "Consider privacy and security requirements"
        ],
        "technology": [
            "Use current technology terminology",
            "Include appropriate technical questions",
            "Consider user experience factors",
            "Include adoption and usage questions",
            "Use appropriate demographic questions",
            "Consider privacy and security concerns",
            "Include innovation and future trends questions"
        ],
        "retail": [
            "Include shopping behavior questions",
            "Use appropriate product categories",
            "Include brand and price sensitivity questions",
            "Consider seasonal factors",
            "Include customer service questions",
            "Use appropriate demographic questions",
            "Include purchase intent and behavior questions"
        ]
    }


async def seed_rules_to_database():
    """Seed all rules to the database"""
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize prompt service
        prompt_service = PromptService()
        
        # Seed methodology rules
        methodology_rules = seed_methodology_rules()
        logger.info(f"Seeding {len(methodology_rules)} methodology rules...")
        
        # Update the prompt service with seeded rules
        prompt_service.methodology_rules.update(methodology_rules)
        
        # Seed quality rules
        quality_rules = seed_quality_rules()
        logger.info(f"Seeding {len(quality_rules)} quality rule categories...")
        
        # Update the prompt service with seeded rules
        prompt_service.quality_rules.update(quality_rules)
        
        # Seed industry rules
        industry_rules = seed_industry_rules()
        logger.info(f"Seeding {len(industry_rules)} industry-specific rule categories...")
        
        # Add industry rules to quality rules
        prompt_service.quality_rules.update(industry_rules)
        
        logger.info("✅ All rules seeded successfully!")
        
        # Print summary
        print("\n📊 Rules Summary:")
        print(f"  • Methodologies: {len(methodology_rules)}")
        print(f"  • Quality Categories: {len(quality_rules)}")
        print(f"  • Industry Categories: {len(industry_rules)}")
        print(f"  • Total Rule Categories: {len(methodology_rules) + len(quality_rules) + len(industry_rules)}")
        
        # Show some examples
        print("\n🔍 Example Methodology Rules:")
        for method, rules in list(methodology_rules.items())[:3]:
            print(f"  • {method}: {rules['description']}")
            print(f"    - Required Questions: {rules['required_questions']}")
            print(f"    - Validation Rules: {len(rules['validation_rules'])}")
        
        print("\n🔍 Example Quality Rules:")
        for category, rules in list(quality_rules.items())[:3]:
            print(f"  • {category}: {len(rules)} rules")
        
        print("\n🔍 Example Industry Rules:")
        for industry, rules in list(industry_rules.items())[:2]:
            print(f"  • {industry}: {len(rules)} rules")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed rules: {str(e)}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def main():
    """Main function to run the seeding script"""
    print("🌱 Starting rules seeding process...")
    
    success = asyncio.run(seed_rules_to_database())
    
    if success:
        print("\n🎉 Rules seeding completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Deploy the updated application")
        print("  2. Access the Rules Manager in the frontend")
        print("  3. View and customize rules as needed")
        print("  4. Test survey generation with new rules")
    else:
        print("\n❌ Rules seeding failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
