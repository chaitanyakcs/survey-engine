#!/usr/bin/env python3
"""
Seed initial reference examples into the database
"""
import asyncio
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, GoldenRFQSurveyPair
from src.config import settings

# Sample reference examples
REFERENCE_EXAMPLES = [
    {
        "rfq_text": "We need market research for premium coffee machines in the $500-2000 range. Key areas: brand preference, feature importance, price sensitivity using Van Westendorp methodology, and purchase drivers.",
        "survey_json": {
            "title": "Premium Coffee Machine Market Research",
            "description": "Understanding consumer preferences for high-end coffee machines",
            "estimated_time": 12,
            "questions": [
                {
                    "id": "q1",
                    "text": "Have you purchased a coffee machine in the past 2 years?",
                    "type": "multiple_choice",
                    "options": ["Yes", "No, but considering", "No, not interested"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q2",
                    "text": "Which coffee machine brands are you familiar with?",
                    "type": "multiple_choice",
                    "options": ["Breville", "De'Longhi", "Nespresso", "Keurig", "Jura", "Saeco"],
                    "required": True,
                    "category": "brand",
                    "multiple_select": True
                },
                {
                    "id": "q3",
                    "text": "At what price would you consider this coffee machine to be so inexpensive that you would feel the quality couldn't be very good?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "too_cheap"
                },
                {
                    "id": "q4",
                    "text": "At what price would you consider this coffee machine to be priced so low that you would feel it's a bargain—a great value for the money?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "bargain"
                },
                {
                    "id": "q5",
                    "text": "At what price would you begin to think this coffee machine is getting expensive, but you would still consider buying it?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "expensive"
                },
                {
                    "id": "q6",
                    "text": "At what price would you consider this coffee machine to be too expensive to consider buying?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "too_expensive"
                },
                {
                    "id": "q7",
                    "text": "What's most important in a coffee machine?",
                    "type": "multiple_choice",
                    "options": ["Brewing quality", "Ease of use", "Design", "Speed", "Durability"],
                    "required": True,
                    "category": "features"
                }
            ],
            "metadata": {
                "methodology": ["van_westendorp", "brand_tracking"],
                "target_responses": 300
            }
        },
        "methodology_tags": ["van_westendorp", "brand_research"],
        "industry_category": "appliances",
        "research_goal": "pricing_research",
        "quality_score": 0.92
    },
    {
        "rfq_text": "Consumer electronics survey for smartphone purchasing behavior. Focus on feature preferences, brand loyalty, and price sensitivity in the $200-1200 range.",
        "survey_json": {
            "title": "Smartphone Purchase Behavior Study",
            "description": "Understanding smartphone buying patterns and preferences",
            "estimated_time": 10,
            "questions": [
                {
                    "id": "q1",
                    "text": "How often do you upgrade your smartphone?",
                    "type": "multiple_choice",
                    "options": ["Every year", "Every 2-3 years", "Only when broken", "Rarely"],
                    "required": True,
                    "category": "behavior"
                },
                {
                    "id": "q2",
                    "text": "Which smartphone features are most important?",
                    "type": "multiple_choice",
                    "options": ["Camera quality", "Battery life", "Storage space", "Screen size", "Performance"],
                    "required": True,
                    "category": "features",
                    "multiple_select": True,
                    "max_selections": 3
                },
                {
                    "id": "q3",
                    "text": "What's your preferred smartphone budget range?",
                    "type": "multiple_choice",
                    "options": ["Under $300", "$300-600", "$600-900", "$900-1200", "Over $1200"],
                    "required": True,
                    "category": "pricing"
                },
                {
                    "id": "q4",
                    "text": "How loyal are you to your current smartphone brand?",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "scale_labels": {"1": "Not loyal", "5": "Very loyal"},
                    "required": True,
                    "category": "brand"
                }
            ],
            "metadata": {
                "methodology": ["feature_preference", "brand_loyalty"],
                "target_responses": 250
            }
        },
        "methodology_tags": ["feature_analysis", "brand_loyalty"],
        "industry_category": "electronics",
        "research_goal": "feature_research",
        "quality_score": 0.88
    },
    {
        "rfq_text": "Restaurant dining experience survey. We want to understand customer satisfaction, service quality perception, and likelihood to recommend.",
        "survey_json": {
            "title": "Restaurant Experience Survey",
            "description": "Measuring customer satisfaction and service quality",
            "estimated_time": 8,
            "questions": [
                {
                    "id": "q1",
                    "text": "How often do you dine at restaurants?",
                    "type": "multiple_choice",
                    "options": ["Daily", "2-3 times/week", "Weekly", "Monthly", "Rarely"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q2",
                    "text": "How satisfied were you with your recent dining experience?",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "scale_labels": {"1": "Very dissatisfied", "5": "Very satisfied"},
                    "required": True,
                    "category": "satisfaction"
                },
                {
                    "id": "q3",
                    "text": "How would you rate the service quality?",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "scale_labels": {"1": "Poor", "5": "Excellent"},
                    "required": True,
                    "category": "service"
                },
                {
                    "id": "q4",
                    "text": "How likely are you to recommend this restaurant?",
                    "type": "scale",
                    "options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    "scale_labels": {"0": "Not likely", "10": "Very likely"},
                    "required": True,
                    "category": "nps",
                    "methodology": "net_promoter_score"
                }
            ],
            "metadata": {
                "methodology": ["satisfaction", "nps"],
                "target_responses": 200
            }
        },
        "methodology_tags": ["satisfaction", "nps"],
        "industry_category": "hospitality",
        "research_goal": "satisfaction_research",
        "quality_score": 0.85
    },
    {
        "rfq_text": "Medical technology pricing research for a new patient care management platform targeting mid-sized hospitals. Need comprehensive price sensitivity analysis using Van Westendorp methodology combined with Gabor-Granger purchase intent. Include competitive analysis against existing EMR systems, feature importance assessment, and decision-maker influence mapping. Target hospital administrators, IT directors, and clinical staff.",
        "survey_json": {
            "title": "Patient Care Management Platform: Pricing & Value Assessment",
            "description": "Research to determine optimal pricing strategy for innovative patient care management technology",
            "estimated_time": 15,
            "questions": [
                {
                    "id": "q1",
                    "text": "What is your primary role in healthcare technology purchasing decisions?",
                    "type": "multiple_choice",
                    "options": ["Hospital Administrator/C-Suite", "IT Director/Manager", "Clinical Director", "Department Head", "Other"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q2",
                    "text": "How many beds does your hospital have?",
                    "type": "multiple_choice", 
                    "options": ["Under 100", "100-200", "200-400", "400-600", "Over 600"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q3",
                    "text": "At what monthly price per bed would you consider this patient care platform to be so inexpensive that you would question its quality?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "too_cheap"
                },
                {
                    "id": "q4", 
                    "text": "At what monthly price per bed would you consider this platform to be a bargain—excellent value for money?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "bargain"
                },
                {
                    "id": "q5",
                    "text": "At what monthly price per bed would you begin to think this platform is getting expensive, but still consider it?",
                    "type": "text", 
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "expensive"
                },
                {
                    "id": "q6",
                    "text": "At what monthly price per bed would this platform be too expensive to consider?",
                    "type": "text",
                    "required": True,
                    "category": "pricing", 
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "too_expensive"
                },
                {
                    "id": "q7",
                    "text": "At $50 per bed per month, how likely would you be to purchase this platform?",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "scale_labels": {"1": "Definitely would not buy", "5": "Definitely would buy"},
                    "required": True,
                    "category": "pricing",
                    "methodology": "gabor_granger",
                    "price_point": "$50"
                },
                {
                    "id": "q8",
                    "text": "At $100 per bed per month, how likely would you be to purchase this platform?", 
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "scale_labels": {"1": "Definitely would not buy", "5": "Definitely would buy"},
                    "required": True,
                    "category": "pricing",
                    "methodology": "gabor_granger",
                    "price_point": "$100"
                },
                {
                    "id": "q9",
                    "text": "Which features are most critical for patient care management? (Select up to 3)",
                    "type": "multiple_choice",
                    "options": ["Real-time patient monitoring", "Automated alerts", "Integration with existing EMR", "Mobile accessibility", "Analytics dashboard", "Compliance reporting"],
                    "required": True,
                    "category": "features",
                    "multiple_select": True,
                    "max_selections": 3
                },
                {
                    "id": "q10",
                    "text": "What current systems would this platform need to integrate with?",
                    "type": "multiple_choice",
                    "options": ["Epic", "Cerner", "Allscripts", "Meditech", "Custom EMR", "None currently"],
                    "required": True,
                    "category": "technical",
                    "multiple_select": True
                }
            ],
            "metadata": {
                "methodology": ["van_westendorp", "gabor_granger", "feature_importance"],
                "target_responses": 180,
                "price_testing": {
                    "currency": "USD",
                    "unit": "per bed per month",
                    "test_points": ["$50", "$100"]
                }
            }
        },
        "methodology_tags": ["van_westendorp", "gabor_granger", "b2b_pricing"],
        "industry_category": "healthcare_technology", 
        "research_goal": "pricing_research",
        "quality_score": 0.91
    },
    {
        "rfq_text": "B2B SaaS pricing optimization study for enterprise project management software. Combine Van Westendorp price sensitivity with choice-based conjoint analysis for feature bundles. Include competitive benchmarking against Asana, Monday.com, and Jira. Need to understand pricing sensitivity across different company sizes and user roles with Newton-Miller-Smith demand estimation.",
        "survey_json": {
            "title": "Enterprise Project Management Software: Pricing & Feature Optimization",
            "description": "Advanced pricing research combining multiple methodologies for SaaS platform optimization",
            "estimated_time": 18,
            "questions": [
                {
                    "id": "q1",
                    "text": "What is your company size?",
                    "type": "multiple_choice",
                    "options": ["50-200 employees", "200-500 employees", "500-1000 employees", "1000-2500 employees", "2500+ employees"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q2", 
                    "text": "What is your role in software purchasing decisions?",
                    "type": "multiple_choice",
                    "options": ["Final decision maker", "Influencer/recommender", "End user with input", "IT/Technical evaluator", "Budget approver"],
                    "required": True,
                    "category": "screening"
                },
                {
                    "id": "q3",
                    "text": "At what price per user per month would you consider project management software to be so cheap you'd question its capabilities?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "too_cheap"
                },
                {
                    "id": "q4",
                    "text": "At what price per user per month would you consider it a great value—an excellent deal?",
                    "type": "text", 
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "bargain"
                },
                {
                    "id": "q5",
                    "text": "At what price per user per month would you think it's getting expensive but still acceptable?",
                    "type": "text",
                    "required": True, 
                    "category": "pricing",
                    "methodology": "van_westendorp",
                    "van_westendorp_type": "expensive"
                },
                {
                    "id": "q6",
                    "text": "At what price per user per month would it be too expensive to consider?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp", 
                    "van_westendorp_type": "too_expensive"
                },
                {
                    "id": "q7",
                    "text": "Choose your preferred project management solution:",
                    "type": "multiple_choice",
                    "options": [
                        "Option A: Advanced analytics + API integration + Unlimited storage | $25/user/month",
                        "Option B: Basic analytics + Limited API + 10GB storage | $15/user/month", 
                        "Option C: Premium analytics + Full API + Unlimited storage + Priority support | $35/user/month",
                        "None of these"
                    ],
                    "required": True,
                    "category": "pricing",
                    "methodology": "choice_conjoint"
                },
                {
                    "id": "q8",
                    "text": "Choose your preferred project management solution:",
                    "type": "multiple_choice", 
                    "options": [
                        "Option A: Basic analytics + Full API + Unlimited storage | $20/user/month",
                        "Option B: Premium analytics + Limited API + 10GB storage | $30/user/month",
                        "Option C: Advanced analytics + No API + 50GB storage | $18/user/month",
                        "None of these" 
                    ],
                    "required": True,
                    "category": "pricing",
                    "methodology": "choice_conjoint"
                },
                {
                    "id": "q9",
                    "text": "How important are each of these features? (Rank from most to least important)",
                    "type": "ranking",
                    "options": ["Advanced analytics", "API integrations", "Storage capacity", "Customer support", "User interface", "Mobile app"],
                    "required": True,
                    "category": "features",
                    "methodology": "feature_ranking"
                },
                {
                    "id": "q10",
                    "text": "Which project management tools has your company used?",
                    "type": "multiple_choice",
                    "options": ["Asana", "Monday.com", "Jira", "Trello", "Microsoft Project", "Slack", "Custom solution", "None"],
                    "required": True,
                    "category": "competitive",
                    "multiple_select": True
                }
            ],
            "metadata": {
                "methodology": ["van_westendorp", "choice_conjoint", "feature_ranking", "competitive_analysis"],
                "target_responses": 250,
                "conjoint_attributes": {
                    "analytics": ["Basic", "Advanced", "Premium"],
                    "api": ["None", "Limited", "Full"],
                    "storage": ["10GB", "50GB", "Unlimited"],
                    "price": ["$15", "$18", "$20", "$25", "$30", "$35"]
                },
                "demand_estimation": "newton_miller_smith"
            }
        },
        "methodology_tags": ["van_westendorp", "choice_conjoint", "nms_demand", "b2b_saas"],
        "industry_category": "enterprise_software",
        "research_goal": "pricing_optimization", 
        "quality_score": 0.94
    }
]

def seed_reference_examples():
    """
    Add reference examples to the database
    """
    # Create engine and session
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🌱 Seeding reference examples...")
        
        for i, example in enumerate(REFERENCE_EXAMPLES, 1):
            # Check if example already exists
            existing = session.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.rfq_text == example["rfq_text"]
            ).first()
            
            if existing:
                print(f"   ⏭️  Reference example {i} already exists, skipping...")
                continue
            
            # Create new reference example
            reference_pair = GoldenRFQSurveyPair(
                rfq_text=example["rfq_text"],
                survey_json=example["survey_json"],
                methodology_tags=example["methodology_tags"],
                industry_category=example["industry_category"],
                research_goal=example["research_goal"],
                quality_score=example["quality_score"],
                usage_count=0
            )
            
            session.add(reference_pair)
            print(f"   ✅ Added reference example {i}: {example['industry_category']} - {example['research_goal']}")
        
        session.commit()
        print(f"🎉 Successfully seeded {len(REFERENCE_EXAMPLES)} reference examples!")
        
        # Show summary
        total_count = session.query(GoldenRFQSurveyPair).count()
        print(f"📊 Total reference examples in database: {total_count}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    
    finally:
        session.close()

if __name__ == "__main__":
    seed_reference_examples()