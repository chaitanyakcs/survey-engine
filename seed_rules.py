#!/usr/bin/env python3
"""
Script to seed the database with initial rules and methodologies
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database import get_db, SurveyRule
from sqlalchemy.orm import Session
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_seed_rules():
    """Get all the rules to seed"""
    return [
        # Methodology Rules
        {
            "rule_type": "methodology",
            "category": "van_westendorp",
            "rule_name": "Van Westendorp Price Sensitivity Meter",
            "rule_description": "Measures price sensitivity through four key questions",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "conjoint",
            "rule_name": "Conjoint Analysis / Choice Modeling",
            "rule_description": "Measures preferences for product attributes",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "maxdiff",
            "rule_name": "MaxDiff (Maximum Difference Scaling)",
            "rule_description": "Ranks items by importance",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "nps",
            "rule_name": "Net Promoter Score",
            "rule_description": "Measures customer loyalty and satisfaction",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "csat",
            "rule_name": "Customer Satisfaction",
            "rule_description": "Measures satisfaction with products/services",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "brand_tracking",
            "rule_name": "Brand Tracking",
            "rule_description": "Measures brand awareness, perception, and equity",
            "rule_content": {
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
            "priority": 10
        },
        {
            "rule_type": "methodology",
            "category": "pricing_research",
            "rule_name": "Pricing Research",
            "rule_description": "Determines optimal pricing strategies",
            "rule_content": {
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
            },
            "priority": 10
        },
        
        # Quality Rules
        {
            "rule_type": "quality",
            "category": "question_quality",
            "rule_name": "Question Quality Standards",
            "rule_description": "Ensures high-quality question design",
            "rule_content": {
                "rules": [
                    "Questions must be clear, concise, and unambiguous",
                    "Avoid leading, loaded, or double-barreled questions",
                    "Use appropriate question types for the data needed",
                    "Include proper validation and skip logic where needed",
                    "Avoid jargon and technical terms unless necessary",
                    "Use consistent terminology throughout the survey",
                    "Ensure questions are culturally appropriate and inclusive"
                ]
            },
            "priority": 8
        },
        {
            "rule_type": "quality",
            "category": "survey_structure",
            "rule_name": "Survey Structure Guidelines",
            "rule_description": "Ensures proper survey organization and flow",
            "rule_content": {
                "rules": [
                    "Start with screening questions to qualify respondents",
                    "Group related questions logically",
                    "Place sensitive questions near the end",
                    "Include demographic questions for segmentation",
                    "Use progress indicators for long surveys",
                    "Include clear instructions and context",
                    "End with thank you message and next steps"
                ]
            },
            "priority": 8
        },
        {
            "rule_type": "quality",
            "category": "methodology_compliance",
            "rule_name": "Methodology Compliance",
            "rule_description": "Ensures adherence to research methodology standards",
            "rule_content": {
                "rules": [
                    "Follow established research methodology standards",
                    "Include appropriate sample size considerations",
                    "Ensure statistical validity of question design",
                    "Add proper metadata for analysis",
                    "Use validated scales when available",
                    "Include appropriate control questions",
                    "Ensure randomization where needed"
                ]
            },
            "priority": 9
        },
        {
            "rule_type": "quality",
            "category": "respondent_experience",
            "rule_name": "Respondent Experience",
            "rule_description": "Optimizes survey experience for respondents",
            "rule_content": {
                "rules": [
                    "Keep survey length appropriate (5-15 minutes)",
                    "Use clear instructions and progress indicators",
                    "Avoid repetitive or redundant questions",
                    "Ensure mobile-friendly question formats",
                    "Use engaging and conversational language",
                    "Include appropriate incentives information",
                    "Provide clear privacy and data usage information"
                ]
            },
            "priority": 7
        },
        {
            "rule_type": "quality",
            "category": "data_quality",
            "rule_name": "Data Quality Assurance",
            "rule_description": "Ensures high-quality data collection",
            "rule_content": {
                "rules": [
                    "Include attention check questions",
                    "Use appropriate question scales and ranges",
                    "Include 'Don't know' or 'Prefer not to answer' options",
                    "Ensure logical flow and skip patterns",
                    "Include validation for open-ended responses",
                    "Use consistent response formats",
                    "Include quality control measures"
                ]
            },
            "priority": 8
        },
        {
            "rule_type": "quality",
            "category": "accessibility",
            "rule_name": "Accessibility Standards",
            "rule_description": "Ensures surveys are accessible to all users",
            "rule_content": {
                "rules": [
                    "Use clear, readable fonts and colors",
                    "Ensure keyboard navigation compatibility",
                    "Include alt text for images",
                    "Use sufficient color contrast",
                    "Provide text alternatives for audio/video",
                    "Ensure screen reader compatibility",
                    "Test with assistive technologies"
                ]
            },
            "priority": 6
        },
        
        # Industry Rules
        {
            "rule_type": "industry",
            "category": "healthcare",
            "rule_name": "Healthcare Research Standards",
            "rule_description": "Specialized rules for healthcare research",
            "rule_content": {
                "rules": [
                    "Include HIPAA compliance considerations",
                    "Use appropriate medical terminology",
                    "Include consent and privacy statements",
                    "Consider patient confidentiality",
                    "Use validated health assessment tools",
                    "Include appropriate demographic questions",
                    "Ensure cultural sensitivity in health questions"
                ]
            },
            "priority": 7
        },
        {
            "rule_type": "industry",
            "category": "financial_services",
            "rule_name": "Financial Services Research",
            "rule_description": "Specialized rules for financial services research",
            "rule_content": {
                "rules": [
                    "Include appropriate disclaimers",
                    "Use clear financial terminology",
                    "Include risk assessment questions",
                    "Ensure regulatory compliance",
                    "Include appropriate demographic questions",
                    "Use validated financial scales",
                    "Consider privacy and security requirements"
                ]
            },
            "priority": 7
        },
        {
            "rule_type": "industry",
            "category": "technology",
            "rule_name": "Technology Research Standards",
            "rule_description": "Specialized rules for technology research",
            "rule_content": {
                "rules": [
                    "Use current technology terminology",
                    "Include appropriate technical questions",
                    "Consider user experience factors",
                    "Include adoption and usage questions",
                    "Use appropriate demographic questions",
                    "Consider privacy and security concerns",
                    "Include innovation and future trends questions"
                ]
            },
            "priority": 7
        },
        {
            "rule_type": "industry",
            "category": "retail",
            "rule_name": "Retail Research Standards",
            "rule_description": "Specialized rules for retail research",
            "rule_content": {
                "rules": [
                    "Include shopping behavior questions",
                    "Use appropriate product categories",
                    "Include brand and price sensitivity questions",
                    "Consider seasonal factors",
                    "Include customer service questions",
                    "Use appropriate demographic questions",
                    "Include purchase intent and behavior questions"
                ]
            },
            "priority": 7
        }
    ]


async def seed_rules_to_database():
    """Seed all rules to the database"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get existing rules to avoid duplicates
        existing_rules = db.query(SurveyRule).all()
        existing_combinations = {(rule.rule_type, rule.category) for rule in existing_rules}
        
        rules_to_seed = get_seed_rules()
        new_rules_count = 0
        updated_rules_count = 0
        
        for rule_data in rules_to_seed:
            rule_type = rule_data["rule_type"]
            category = rule_data["category"]
            
            # Check if rule already exists
            existing_rule = db.query(SurveyRule).filter(
                SurveyRule.rule_type == rule_type,
                SurveyRule.category == category
            ).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.rule_name = rule_data["rule_name"]
                existing_rule.rule_description = rule_data["rule_description"]
                existing_rule.rule_content = rule_data["rule_content"]
                existing_rule.priority = rule_data["priority"]
                existing_rule.is_active = True
                updated_rules_count += 1
                logger.info(f"Updated rule: {rule_type}/{category}")
            else:
                # Create new rule
                new_rule = SurveyRule(
                    rule_type=rule_type,
                    category=category,
                    rule_name=rule_data["rule_name"],
                    rule_description=rule_data["rule_description"],
                    rule_content=rule_data["rule_content"],
                    priority=rule_data["priority"],
                    is_active=True,
                    created_by="system"
                )
                db.add(new_rule)
                new_rules_count += 1
                logger.info(f"Created new rule: {rule_type}/{category}")
        
        # Commit all changes
        db.commit()
        
        logger.info("✅ All rules seeded successfully!")
        
        # Print summary
        print("\n📊 Rules Seeding Summary:")
        print(f"  • New rules created: {new_rules_count}")
        print(f"  • Existing rules updated: {updated_rules_count}")
        print(f"  • Total rules processed: {len(rules_to_seed)}")
        
        # Show some examples
        print("\n🔍 Example Methodology Rules:")
        methodology_rules = db.query(SurveyRule).filter(SurveyRule.rule_type == "methodology").limit(3).all()
        for rule in methodology_rules:
            print(f"  • {rule.category}: {rule.rule_name}")
            print(f"    - Priority: {rule.priority}")
            print(f"    - Active: {rule.is_active}")
        
        print("\n🔍 Example Quality Rules:")
        quality_rules = db.query(SurveyRule).filter(SurveyRule.rule_type == "quality").limit(3).all()
        for rule in quality_rules:
            print(f"  • {rule.category}: {rule.rule_name}")
            print(f"    - Priority: {rule.priority}")
        
        print("\n🔍 Example Industry Rules:")
        industry_rules = db.query(SurveyRule).filter(SurveyRule.rule_type == "industry").limit(2).all()
        for rule in industry_rules:
            print(f"  • {rule.category}: {rule.rule_name}")
            print(f"    - Priority: {rule.priority}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed rules: {str(e)}")
        if 'db' in locals():
            db.rollback()
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







