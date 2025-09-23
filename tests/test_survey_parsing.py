#!/usr/bin/env python3
"""
Test script to debug survey JSON parsing issues
"""

import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.survey_utils import extract_all_questions, get_questions_count

def test_survey_parsing():
    """Test the survey parsing with the provided JSON"""

    # Your survey JSON
    survey_json = {
        "title": "Market Research Study: Pricing, Features, and Brand Positioning",
        "description": "A comprehensive survey to understand consumer preferences, price sensitivity, feature priorities, and brand perception for a new product. Includes Van Westendorp, Conjoint indicators, and MaxDiff tasks.",
        "sections": [
            {
                "id": 1,
                "title": "Screener & Demographics",
                "description": "Initial screening questions and demographic information",
                "questions": [
                    {
                        "id": "q1",
                        "text": "Which of the following best describes your age group?",
                        "type": "multiple_choice",
                        "options": [
                            "Under 18 (terminate)",
                            "18-24",
                            "25-34",
                            "35-44",
                            "45-54",
                            "55-64",
                            "65 or older"
                        ],
                        "required": True,
                        "methodology": "screening",
                        "validation": "single_select:required; terminate_if:option=='Under 18 (terminate)'",
                        "order": 1
                    },
                    {
                        "id": "q2",
                        "text": "In which country do you currently reside?",
                        "type": "text",
                        "options": [],
                        "required": True,
                        "methodology": "screening",
                        "validation": "open_text:country; required",
                        "order": 2
                    },
                    {
                        "id": "q3",
                        "text": "Which of the following best describes your primary role in household purchasing for this type of product?",
                        "type": "multiple_choice",
                        "options": [
                            "I am the primary decision-maker",
                            "I share decision-making equally",
                            "I influence but do not decide",
                            "I am not involved (terminate)"
                        ],
                        "required": True,
                        "methodology": "screening",
                        "validation": "single_select:required; terminate_if:option=='I am not involved (terminate)'",
                        "order": 3
                    },
                    {
                        "id": "q4",
                        "text": "What is your current employment status?",
                        "type": "multiple_choice",
                        "options": [
                            "Employed full-time",
                            "Employed part-time",
                            "Self-employed",
                            "Student",
                            "Homemaker",
                            "Retired",
                            "Unemployed and looking for work",
                            "Prefer not to say"
                        ],
                        "required": True,
                        "methodology": "demographic",
                        "validation": "single_select:required",
                        "order": 4
                    },
                    {
                        "id": "q5",
                        "text": "What is your approximate annual household income (before taxes)?",
                        "type": "multiple_choice",
                        "options": [
                            "Less than $25,000",
                            "$25,000 - $49,999",
                            "$50,000 - $74,999",
                            "$75,000 - $99,999",
                            "$100,000 - $149,999",
                            "$150,000 or more",
                            "Prefer not to say"
                        ],
                        "required": True,
                        "methodology": "demographic",
                        "validation": "single_select:required",
                        "order": 5
                    },
                    {
                        "id": "q6",
                        "text": "Please select your gender.",
                        "type": "multiple_choice",
                        "options": [
                            "Woman",
                            "Man",
                            "Non-binary",
                            "Another gender identity",
                            "Prefer not to say"
                        ],
                        "required": False,
                        "methodology": "demographic",
                        "validation": "single_select",
                        "order": 6
                    },
                    {
                        "id": "q7",
                        "text": "Which of the following best describes your household?",
                        "type": "multiple_choice",
                        "options": [
                            "Single-person household",
                            "Couple without children",
                            "Family with children under 18",
                            "Family with adult children",
                            "Multi-generational household",
                            "Other"
                        ],
                        "required": False,
                        "methodology": "demographic",
                        "validation": "single_select",
                        "order": 7
                    }
                ]
            },
            {
                "id": 2,
                "title": "Consumer Details",
                "description": "Detailed consumer information and behavior patterns",
                "questions": [
                    {
                        "id": "q8",
                        "text": "How often do you purchase products in this category?",
                        "type": "multiple_choice",
                        "options": [
                            "Weekly or more often",
                            "2-3 times per month",
                            "Monthly",
                            "Every 2-3 months",
                            "Less than every 3 months",
                            "Never (screen out from usage-based questions)"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "single_select:required",
                        "order": 1
                    },
                    {
                        "id": "q9",
                        "text": "Where do you typically shop for this type of product? Select all that apply.",
                        "type": "multiple_choice",
                        "options": [
                            "Online marketplaces (e.g., Amazon)",
                            "Brand website",
                            "Big-box retailers",
                            "Specialty stores",
                            "Local/independent stores",
                            "Social media shops",
                            "Other"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "multi_select:min=1",
                        "order": 2
                    },
                    {
                        "id": "q10",
                        "text": "Which of the following best describes your decision-making style for this product category?",
                        "type": "multiple_choice",
                        "options": [
                            "Price-first: I choose the lowest price that meets my needs",
                            "Value-balanced: I weigh features and price equally",
                            "Quality-first: I pay more for higher quality",
                            "Brand-first: I prefer specific brands",
                            "Impulse: I decide quickly without much research"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "single_select:required",
                        "order": 3
                    },
                    {
                        "id": "q11",
                        "text": "On a scale of 0-10, how confident are you in evaluating product features and quality in this category?",
                        "type": "scale",
                        "options": [
                            "0",
                            "10"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "scale:min=0;max=10;required",
                        "order": 4
                    },
                    {
                        "id": "q12",
                        "text": "What are your top 3 information sources when researching this type of product?",
                        "type": "multiple_choice",
                        "options": [
                            "Search engines",
                            "Retailer reviews",
                            "Independent expert reviews",
                            "Friends/family",
                            "Social media influencers",
                            "Brand website",
                            "In-store staff",
                            "Forums/communities",
                            "Price comparison sites"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "multi_select:min=1;max=3;required",
                        "order": 5
                    }
                ]
            },
            {
                "id": 3,
                "title": "Consumer product awareness, usage and preference",
                "description": "Understanding consumer awareness, usage patterns and preferences",
                "questions": [
                    {
                        "id": "q13",
                        "text": "Which brands are you aware of in this category? Select all that apply.",
                        "type": "multiple_choice",
                        "options": [
                            "Brand A",
                            "Brand B",
                            "Brand C",
                            "Brand D",
                            "Other (please specify)"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "multi_select:min=1; allow_other_text",
                        "order": 1
                    },
                    {
                        "id": "q14",
                        "text": "Which brand do you currently use most often?",
                        "type": "multiple_choice",
                        "options": [
                            "Brand A",
                            "Brand B",
                            "Brand C",
                            "Brand D",
                            "I do not currently use any brand in this category"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "single_select:required",
                        "order": 2
                    },
                    {
                        "id": "q15",
                        "text": "How satisfied are you with your current primary brand?",
                        "type": "scale",
                        "options": [
                            "1 Very dissatisfied",
                            "5 Neutral",
                            "10 Very satisfied"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "scale:min=1;max=10;required; show_labels=true",
                        "order": 3
                    },
                    {
                        "id": "q16",
                        "text": "Please rank the following product features in order of importance when choosing a product in this category.",
                        "type": "ranking",
                        "options": [
                            "Performance/quality",
                            "Price",
                            "Ease of use",
                            "Design/style",
                            "Durability",
                            "Warranty/support",
                            "Brand reputation",
                            "Sustainability"
                        ],
                        "required": True,
                        "methodology": "MaxDiff_setup",
                        "validation": "ranking:rank_all; required",
                        "order": 4
                    },
                    {
                        "id": "q17",
                        "text": "Thinking about feature trade-offs, which features are MOST and LEAST important to you? (MaxDiff block 1)",
                        "type": "multiple_choice",
                        "options": [
                            "Block 1: MOST from [Performance, Price, Ease of use, Design]",
                            "Block 1: LEAST from [Performance, Price, Ease of use, Design]"
                        ],
                        "required": True,
                        "methodology": "MaxDiff",
                        "validation": "paired_maxdiff:most_one;least_one; required",
                        "order": 5
                    },
                    {
                        "id": "q18",
                        "text": "How likely are you to consider switching brands in the next 6 months?",
                        "type": "scale",
                        "options": [
                            "1 Not at all likely",
                            "5 Neutral",
                            "10 Extremely likely"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "scale:min=1;max=10;required; show_labels=true",
                        "order": 6
                    }
                ]
            },
            {
                "id": 4,
                "title": "Product introduction and Concept reaction",
                "description": "Introduction of new concepts and gathering reactions",
                "questions": [
                    {
                        "id": "q19",
                        "text": "Please read the following concept for our new product: 'A high-quality, durable product with advanced features, intuitive setup, and eco-friendly materials. Backed by a 2-year warranty and 24/7 support.' Based on this concept, how appealing is the product to you?",
                        "type": "scale",
                        "options": [
                            "1 Not at all appealing",
                            "5 Neutral",
                            "10 Extremely appealing"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "scale:min=1;max=10;required; show_labels=true",
                        "order": 1
                    },
                    {
                        "id": "q20",
                        "text": "Purchase intent: How likely are you to purchase this product within the next 3 months if it were available?",
                        "type": "scale",
                        "options": [
                            "1 Definitely would not buy",
                            "5 Might or might not buy",
                            "10 Definitely would buy"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "scale:min=1;max=10;required; show_labels=true",
                        "order": 2
                    },
                    {
                        "id": "q21",
                        "text": "Which elements of the concept are most appealing? Select up to 3.",
                        "type": "multiple_choice",
                        "options": [
                            "Advanced features",
                            "Ease of setup",
                            "Durability",
                            "Eco-friendly materials",
                            "Warranty",
                            "24/7 support",
                            "Design/style",
                            "Brand reputation"
                        ],
                        "required": True,
                        "methodology": "core",
                        "validation": "multi_select:min=1;max=3;required",
                        "order": 3
                    },
                    {
                        "id": "q22",
                        "text": "Which elements of the concept are least appealing or unclear?",
                        "type": "text",
                        "options": [],
                        "required": False,
                        "methodology": "qual",
                        "validation": "open_text:max_chars=300",
                        "order": 4
                    },
                    {
                        "id": "q23",
                        "text": "Van Westendorp Price Sensitivity Meter: At what price would you consider the product to be so expensive that you would not consider buying it?",
                        "type": "text",
                        "options": [],
                        "required": True,
                        "methodology": "VanWestendorp",
                        "validation": "currency:required; min=0",
                        "order": 5
                    },
                    {
                        "id": "q24",
                        "text": "Van Westendorp: At what price would you consider the product to be expensive, but you would still consider buying it?",
                        "type": "text",
                        "options": [],
                        "required": True,
                        "methodology": "VanWestendorp",
                        "validation": "currency:required; min=0; greater_than:q25",
                        "order": 6
                    },
                    {
                        "id": "q25",
                        "text": "Van Westendorp: At what price would you consider the product to be a bargain—a great buy for the money?",
                        "type": "text",
                        "options": [],
                        "required": True,
                        "methodology": "VanWestendorp",
                        "validation": "currency:required; min=0; less_than:q24",
                        "order": 7
                    },
                    {
                        "id": "q26",
                        "text": "Van Westendorp: At what price would you consider the product to be so inexpensive that you would question its quality?",
                        "type": "text",
                        "options": [],
                        "required": True,
                        "methodology": "VanWestendorp",
                        "validation": "currency:required; min=0; less_than:q25",
                        "order": 8
                    },
                    {
                        "id": "q27",
                        "text": "Conjoint indicator: When choosing among similar products, which single attribute influences you most?",
                        "type": "multiple_choice",
                        "options": [
                            "Price",
                            "Brand",
                            "Feature set",
                            "Warranty length",
                            "Design/style",
                            "Sustainability credentials"
                        ],
                        "required": True,
                        "methodology": "Conjoint_setup",
                        "validation": "single_select:required",
                        "order": 9
                    },
                    {
                        "id": "q28",
                        "text": "If this product were priced at your 'expensive but would still consider' price (from earlier), how likely would you be to purchase?",
                        "type": "scale",
                        "options": [
                            "1 Very unlikely",
                            "5 Neutral",
                            "10 Very likely"
                        ],
                        "required": True,
                        "methodology": "pricing_research",
                        "validation": "scale:min=1;max=10;required; show_labels=true",
                        "order": 10
                    }
                ]
            },
            {
                "id": 5,
                "title": "Methodology",
                "description": "Methodology-specific questions and validation",
                "questions": [
                    {
                        "id": "q29",
                        "text": "Attention check: Please select 'Strongly agree' for this question.",
                        "type": "multiple_choice",
                        "options": [
                            "Strongly disagree",
                            "Disagree",
                            "Neither agree nor disagree",
                            "Agree",
                            "Strongly agree"
                        ],
                        "required": True,
                        "methodology": "data_quality",
                        "validation": "single_select:required; correct_option='Strongly agree'",
                        "order": 1
                    },
                    {
                        "id": "q30",
                        "text": "How clear and easy to understand was this survey?",
                        "type": "scale",
                        "options": [
                            "1 Not clear at all",
                            "5 Neutral",
                            "10 Extremely clear"
                        ],
                        "required": False,
                        "methodology": "survey_feedback",
                        "validation": "scale:min=1;max=10",
                        "order": 2
                    },
                    {
                        "id": "q31",
                        "text": "Did any question feel confusing, repetitive, or irrelevant? Please describe.",
                        "type": "text",
                        "options": [],
                        "required": False,
                        "methodology": "survey_feedback",
                        "validation": "open_text:max_chars=300",
                        "order": 3
                    },
                    {
                        "id": "q32",
                        "text": "Device used to complete this survey",
                        "type": "multiple_choice",
                        "options": [
                            "Smartphone",
                            "Tablet",
                            "Laptop",
                            "Desktop"
                        ],
                        "required": True,
                        "methodology": "metadata",
                        "validation": "single_select:required",
                        "order": 4
                    },
                    {
                        "id": "q33",
                        "text": "Approximate time spent on this survey (minutes)",
                        "type": "multiple_choice",
                        "options": [
                            "Under 5",
                            "5-7",
                            "8-10",
                            "11-15",
                            "More than 15"
                        ],
                        "required": True,
                        "methodology": "metadata",
                        "validation": "single_select:required",
                        "order": 5
                    }
                ]
            }
        ],
        "metadata": {
            "estimated_time": 12,
            "methodology_tags": [
                "pricing_research",
                "VanWestendorp",
                "Conjoint_setup",
                "MaxDiff",
                "brand_perception",
                "feature_prioritization",
                "data_quality"
            ],
            "target_responses": 400,
            "quality_score": 0.92,
            "sections_count": 5
        }
    }

    print("🧪 Testing Survey Parsing Functions")
    print("=" * 50)

    # Test extract_all_questions
    all_questions = extract_all_questions(survey_json)
    question_count = get_questions_count(survey_json)

    print(f"📊 Extract All Questions Result:")
    print(f"   - Total questions found: {len(all_questions)}")
    print(f"   - Question count function: {question_count}")
    print(f"   - Expected: 33 questions")
    print()

    # Analyze by section
    print(f"📋 Section-by-Section Analysis:")
    for i, section in enumerate(survey_json.get("sections", []), 1):
        section_questions = section.get("questions", [])
        print(f"   Section {i}: {section.get('title', 'Unknown')} - {len(section_questions)} questions")
        for q in section_questions:
            print(f"      - {q.get('id', 'No ID')}: {q.get('text', 'No text')[:60]}...")
    print()

    # Check for common parsing issues
    print(f"🔍 Detailed Question Analysis:")
    print(f"   - Questions with IDs: {len([q for q in all_questions if q.get('id')])}")
    print(f"   - Questions with text: {len([q for q in all_questions if q.get('text')])}")
    print(f"   - Questions with type: {len([q for q in all_questions if q.get('type')])}")
    print(f"   - Questions with options: {len([q for q in all_questions if q.get('options')])}")
    print()

    # Show question types distribution
    question_types = {}
    for q in all_questions:
        qtype = q.get('type', 'unknown')
        question_types[qtype] = question_types.get(qtype, 0) + 1

    print(f"📈 Question Types Distribution:")
    for qtype, count in question_types.items():
        print(f"   - {qtype}: {count} questions")
    print()

    # Check methodology distribution
    methodologies = {}
    for q in all_questions:
        methodology = q.get('methodology', 'none')
        methodologies[methodology] = methodologies.get(methodology, 0) + 1

    print(f"🔬 Methodology Distribution:")
    for methodology, count in methodologies.items():
        print(f"   - {methodology}: {count} questions")
    print()

    # Test edge cases
    print(f"⚠️  Edge Case Tests:")

    # Test with empty survey
    empty_questions = extract_all_questions({})
    print(f"   - Empty survey: {len(empty_questions)} questions")

    # Test with legacy format
    legacy_survey = {
        "questions": all_questions[:5]  # First 5 questions
    }
    legacy_questions = extract_all_questions(legacy_survey)
    print(f"   - Legacy format (5 questions): {len(legacy_questions)} questions")

    # Test with mixed/malformed data
    malformed_survey = {
        "sections": [
            {"questions": all_questions[:2]},  # Section with questions
            {"title": "No questions section"},  # Section without questions
            {"questions": []},  # Section with empty questions
            {"questions": all_questions[2:4]}  # Another section with questions
        ]
    }
    malformed_questions = extract_all_questions(malformed_survey)
    print(f"   - Malformed sections: {len(malformed_questions)} questions")
    print()

    # Summary
    print(f"✅ Summary:")
    if len(all_questions) == 33:
        print(f"   ✅ PASS: Found all 33 questions correctly")
        print(f"   🎯 The parsing function is working correctly!")
        print(f"   💡 Issue is likely in downstream processing, not in extract_all_questions()")
    else:
        print(f"   ❌ FAIL: Expected 33, got {len(all_questions)}")
        print(f"   🔍 The parsing function has issues")

    return all_questions

if __name__ == "__main__":
    test_survey_parsing()