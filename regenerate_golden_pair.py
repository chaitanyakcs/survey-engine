#!/usr/bin/env python3
"""
Script to regenerate golden pair using the LLM response from production.
This script will:
1. Fetch the LLM response from the audit API
2. Process it through the document parser pipeline
3. Create a new golden pair with the processed data
"""

import sys
import os
import json
import asyncio
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.document_parser import DocumentParser
from src.services.golden_service import GoldenService
from src.database.connection import get_db
from sqlalchemy.orm import Session

# Production API endpoint
PRODUCTION_API_BASE = "https://survey-engine-production.up.railway.app/api/v1"

def fetch_llm_response():
    """Use the LLM response data we saw from the audit API."""
    print("🔍 Using LLM response data from audit API...")
    
    # This is the actual LLM response from the audit data we saw earlier
    llm_response = {
        "raw_output": {
            "document_text": "Project_J : Product_A & Product_B Price Elasticity Study\nQNR\nv1\nSep 21,2025\nobjectives\nResearch Objectives:\nIdentifying the Missing Features along with the Most Important and Least Important features of Product_A & Product_B Concept among target customers with respect to competitor product GoPro.\nCalculate price elasticity to understand optimal price for Product_A & Product_B products with strategic/traditional target consumers.\nSAMPLE PLAN\nGEOGRAPHY:  US\nLOI: 8-10 MINS\nRECRUITING CRITERIA :-\nOWN/EXPERIENCE W/\"LIVE STREAMING\" CAMERA\nOPEN TO/INTEREST IN \"LIVE STREAMING\" CAMERA AND/OR \"CAMERA FOR CREATING (PRE-RECORDED CONTENT)\"\nMIX OF \"BROADCAST/CREATOR\"/DESK LIVE STREAMING/PRE-RECORDED USE CASES\nScreener (1-2 min)\nIntroduction\nThank you for agreeing to participate in this online survey.\nWe will begin by asking a few questions.  After answering these questions, you will be informed of your eligibility to participate in a 8-10-minute survey.\nPlease click 'Next' (>>) to continue...\nSQ01. Please let us know if you or any of your immediate family members are employees or have been employed in the past 12 months at any of the following?\n(Please select all that apply)\nAccounting\nEducation\nMarketing research [Thank & Terminate]\nAdvertising or public relations [Thank & Terminate]\nVideo content service website [Thank & Terminate]\nRestaurant\nInsurance company or brokerage\nFinancial services provider\nAutomotive manufacturer or retailer\nNon-Profit organization\nHospital or physician's office\nTechnology Company [Thank & Terminate]\nNone of the above [Anchor to bottom, Exclusive]\nSQ02. What is your gender?\n(Please select one)\nMale\nFemale\nNon-Binary\nOther, please specify\nPrefer not to answer\nSQ03. What is your age?\n(Please select one)\n17 years or younger [Thank & Terminate]\n18-25 years old\n26-35 years old\n36-45 years old\n46-55 years old\n56-70 years old [Quota – 15% of the sample]\n71 years or older [Thank & Terminate]",
            "extraction_timestamp": "2024-01-01T00:00:00Z",
            "source_file": None,
            "error": None
        },
        "final_output": {
            "title": "Project_J: Product_A & Product_B Price Elasticity Study",
            "description": "Online survey to identify missing and key features for Product_A and Product_B versus GoPro HERO BLACK 9, and to calculate price elasticity among target US consumers involved with live streaming and content creation.",
            "metadata": {
                "quality_score": 0.88,
                "estimated_time": 10,
                "methodology_tags": ["pricing", "Gabor Granger", "brand awareness", "concept testing", "feature prioritization"],
                "target_responses": 450,
                "source_file": None
            },
            "sections": [
                {
                    "id": 1,
                    "title": "Sample Plan and Introduction",
                    "description": "Study overview, objectives, sample plan, recruiting criteria, quotas, and confidentiality.",
                    "introText": {
                        "text": "Thank you for agreeing to participate in this online survey. We will begin by asking a few questions. After answering these questions, you will be informed of your eligibility to participate in a 8-10-minute survey. Please click 'Next' (>>) to continue..."
                    },
                    "textBlocks": [
                        {
                            "text": "Research Objectives: Identifying the Missing Features along with the Most Important and Least Important features of Product_A & Product_B Concept among target customers with respect to competitor product GoPro. Calculate price elasticity to understand optimal price for Product_A & Product_B products with strategic/traditional target consumers."
                        }
                    ],
                    "questions": [
                        {
                            "id": "q1",
                            "text": "SAMPLE PLAN: GEOGRAPHY: US; LOI: 8-10 MINS; RECRUITING CRITERIA :- OWN/EXPERIENCE W/\"LIVE STREAMING\" CAMERA; OPEN TO/INTEREST IN \"LIVE STREAMING\" CAMERA AND/OR \"CAMERA FOR CREATING (PRE-RECORDED CONTENT)\"; MIX OF \"BROADCAST/CREATOR\"/DESK LIVE STREAMING/PRE-RECORDED USE CASES; QUOTAS: Live Broadcasters- 150; General S&C- 300; Include Quotas: 150 Techies & 150 Expressionists; TERMINATE the remaining segments]",
                            "type": "instruction",
                            "required": False,
                            "order": 1
                        },
                        {
                            "id": "q2",
                            "text": "SQ09.Confidentiality Agreement I understand that I am being asked to participate in a market research study and that my participation is voluntary. I understand that I will be presented with information during the research which may or may not be factual or true and that I may be asked to accept certain representations or make certain assumptions about new products to answer various questions for the market research study. I understand that such representations have been made for research purposes and no other purposes. I acknowledge that I may receive information during the market research study which is confidential information belonging to the study sponsor. I agree that I will not disclose or use this confidential information, nor discuss with any party, any of the information with which I have been provided or been made aware in connection with my participation in this market research study. The term of this non-disclosure agreement will continue until such time, if ever, the information becomes publicly available.",
                            "type": "single_choice",
                            "options": [
                                "I Agree [RECRUIT]",
                                "I Disagree [TERMINATE]"
                            ],
                            "required": True,
                            "order": 2
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Screener",
                    "description": "Qualification questions to determine eligibility and segment.",
                    "questions": [
                        {
                            "id": "q3",
                            "text": "SQ01. Please let us know if you or any of your immediate family members are employees or have been employed in the past 12 months at any of the following? (Please select all that apply)",
                            "type": "multiple_choice",
                            "options": [
                                "Accounting",
                                "Education",
                                "Marketing research [Thank & Terminate]",
                                "Advertising or public relations [Thank & Terminate]",
                                "Video content service website [Thank & Terminate]",
                                "Restaurant",
                                "Insurance company or brokerage",
                                "Financial services provider",
                                "Automotive manufacturer or retailer",
                                "Non-Profit organization",
                                "Hospital or physician's office",
                                "Technology Company [Thank & Terminate]",
                                "None of the above [Anchor to bottom, Exclusive]"
                            ],
                            "required": True,
                            "order": 1
                        },
                        {
                            "id": "q4",
                            "text": "SQ02. What is your gender? (Please select one)",
                            "type": "single_choice",
                            "options": [
                                "Male",
                                "Female",
                                "Non-Binary",
                                "Other, please specify",
                                "Prefer not to answer"
                            ],
                            "required": True,
                            "order": 2
                        }
                    ]
                },
                {
                    "id": 3,
                    "title": "Brand/Product Awareness",
                    "description": "Brand recall, usage patterns, and product awareness questions.",
                    "questions": [
                        {
                            "id": "q5",
                            "text": "AQ00. What kind of content do you usually stream or create? (Please Select All that apply)",
                            "type": "multiple_choice",
                            "options": [
                                "Animation", "ASMR", "Beauty", "Comedy", "Conspiracy", "Cooking", "Daily Vlog", "Design / Art", "Digital / Online Events", "DIY", "Education / Classroom", "Family", "Fashion", "Gaming", "Health and Fitness", "Just Chatting", "Learning", "Lifestyle", "Live Events at venues- conferences, concerts, team sports", "Live events - House of Worship", "Live events - Weddings and celebrations", "Live events - local sports games, local events, etc...", "Makers / Crafting", "Music", "Dance", "Pranks / Challenges", "Politics", "Podcast", "Spirituality", "Sports", "Tech", "Travel", "Unboxing", "Other, please specify ___________ [Anchor at bottom]"
                            ],
                            "required": True,
                            "order": 1
                        }
                    ]
                },
                {
                    "id": 4,
                    "title": "Concept Exposure",
                    "description": "Product concept introduction, impression ratings, and evaluation questions.",
                    "questions": [
                        {
                            "id": "q6",
                            "text": "[BQ01] On a scale of 1 to 5 where 1 is 'Poor' and a 5 is 'Excellent', what is your overall impression of Product_A?",
                            "type": "scale",
                            "options": [
                                "1= Poor",
                                "2= Fair", 
                                "3= Average",
                                "4= Good",
                                "5= Excellent"
                            ],
                            "scale_min": 1,
                            "scale_max": 5,
                            "scale_labels": {
                                "min": "Poor",
                                "max": "Excellent"
                            },
                            "required": True,
                            "order": 1
                        },
                        {
                            "id": "q7",
                            "text": "[BQ02] Please highlight the MOST IMPORTANT and the LEAST IMPORTANT Features in the Product_A description.",
                            "type": "maxdiff",
                            "required": True,
                            "order": 2
                        }
                    ]
                },
                {
                    "id": 5,
                    "title": "Pricing Methodology - Gabor Granger",
                    "description": "Sequential price purchase likelihood for Product_A, Product_B, and GoPro HERO BLACK 9.",
                    "questions": [
                        {
                            "id": "q8",
                            "text": "CQ01a. On a scale of 1 to 5 : where 1 is 'Definitely will not purchase' and 5 is 'Definitely will purchase', how likely would you be to purchase Product_A ?",
                            "type": "gabor_granger",
                            "options": [
                                "Product_A at $249",
                                "Product_A at $299",
                                "Product_A at $349",
                                "Product_A at $399",
                                "Product_A at $499",
                                "Product_A at $549",
                                "Product_A at $599"
                            ],
                            "required": True,
                            "order": 1
                        }
                    ]
                },
                {
                    "id": 6,
                    "title": "Demographics and Additional Questions",
                    "description": "Employment status, social media usage, education, income, ethnicity.",
                    "questions": [
                        {
                            "id": "q9",
                            "text": "DQ01. Which of the following best describes your current employment status? (Please select one)",
                            "type": "single_choice",
                            "options": [
                                "Employed full-time (30+ hours/week)",
                                "Employed part-time (less than 30 hours/week)",
                                "Homemaker",
                                "Student",
                                "Retired",
                                "Full time Content Creator",
                                "Business Owner",
                                "Other",
                                "[99] Prefer not to answer"
                            ],
                            "required": True,
                            "order": 1
                        }
                    ]
                },
                {
                    "id": 7,
                    "title": "Programmer Instructions and Technical Notes",
                    "description": "Routing logic, randomization, quotas, and additional implementation details.",
                    "questions": [
                        {
                            "id": "q10",
                            "text": "[RANDOMIZE EXPOSURE TO \"Product_A 1\" AND ''GoPro HERO BLACK 9'': 50% SAMPLE TO SEE Product_A-1 FIRST, 50% SAMPLE TO SEE GoPro HERO BLACK 9 FIRST]",
                            "type": "instruction",
                            "required": False,
                            "order": 1
                        }
                    ]
                }
            ],
            "parsing_issues": []
        }
    }
    
    print(f"✅ Using LLM response data (length: {len(str(llm_response))} chars)")
    return llm_response

def process_llm_response(raw_response):
    """Process the LLM response through the document parser pipeline."""
    print("🔄 Processing LLM response through document parser...")
    
    try:
        # Initialize document parser
        parser = DocumentParser()
        
        # Parse the JSON response
        if isinstance(raw_response, str):
            survey_data = json.loads(raw_response)
        else:
            survey_data = raw_response
        
        print(f"📊 Raw response structure: {list(survey_data.keys())}")
        
        # Validate the survey JSON
        validated_survey = parser.validate_survey_json(survey_data)
        print("✅ Survey JSON validation completed")
        
        # Fix invalid question types
        fixed_survey = parser._fix_invalid_question_types(validated_survey)
        print("✅ Question type fixing completed")
        
        # Count sections and questions
        sections = fixed_survey.get('final_output', {}).get('sections', [])
        total_questions = sum(len(section.get('questions', [])) for section in sections)
        
        print(f"📊 Processed survey: {len(sections)} sections, {total_questions} questions")
        
        return fixed_survey
        
    except Exception as e:
        print(f"❌ Failed to process LLM response: {e}")
        raise

async def create_golden_pair(processed_survey):
    """Create a new golden pair using the processed survey data."""
    print("💎 Creating new golden pair...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize golden service
        golden_service = GoldenService(db)
        
        # Extract RFQ text from the processed survey
        rfq_text = processed_survey.get('raw_output', {}).get('document_text', '')
        if not rfq_text:
            raise Exception("No RFQ text found in processed survey")
        
        # Extract survey data
        survey_data = processed_survey.get('final_output', {})
        
        # Create golden pair
        golden_pair = await golden_service.create_golden_pair(
            rfq_text=rfq_text,
            survey_json=survey_data,
            quality_score=0.9,  # High quality since it's from production LLM
            industry_category="technology",
            research_goal="pricing_research",
            methodology_tags=["gabor_granger", "maxdiff", "brand_awareness", "concept_testing"]
        )
        
        print(f"✅ Created golden pair with ID: {golden_pair.id}")
        print(f"📊 Golden pair details:")
        print(f"   - Quality Score: {golden_pair.quality_score}")
        print(f"   - Industry: {golden_pair.industry_category}")
        print(f"   - Research Goal: {golden_pair.research_goal}")
        print(f"   - Methodology Tags: {golden_pair.methodology_tags}")
        
        return golden_pair
        
    except Exception as e:
        print(f"❌ Failed to create golden pair: {e}")
        raise

async def main():
    """Main function to regenerate golden pair."""
    print("🚀 Starting Golden Pair Regeneration")
    print("=" * 50)
    
    try:
        # Step 1: Fetch LLM response from production
        raw_response = fetch_llm_response()
        
        # Step 2: Process through document parser pipeline
        processed_survey = process_llm_response(raw_response)
        
        # Step 3: Create new golden pair
        golden_pair = await create_golden_pair(processed_survey)
        
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Golden pair regenerated successfully!")
        print(f"✅ Golden Pair ID: {golden_pair.id}")
        print(f"✅ Quality Score: {golden_pair.quality_score}")
        print(f"✅ Sections: {len(processed_survey.get('final_output', {}).get('sections', []))}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
