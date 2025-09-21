#!/usr/bin/env python3
"""
Test full survey workflow to identify where questions get lost in the pipeline
"""

import json
import sys
sys.path.append('.')

from src.utils.survey_utils import extract_all_questions, get_questions_count
from src.services.survey_service import SurveyService
from src.database.models import Survey
from src.database import get_db
from sqlalchemy.orm import Session

def load_test_survey():
    """Load the test survey JSON from our test file"""
    with open('/Users/chaitanya/Work/repositories/survey-engine/test_survey_parsing.py', 'r') as f:
        content = f.read()

    # Extract the survey_json from the test file
    start = content.find('survey_json = {')
    if start == -1:
        raise ValueError("Could not find survey_json in test file")

    # Find the end of the survey_json dict
    brace_count = 0
    i = start + len('survey_json = ')
    while i < len(content):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        i += 1

    survey_str = content[start + len('survey_json = '):i + 1]
    return eval(survey_str)

def test_database_roundtrip():
    """Test storing and retrieving survey from database"""
    print("🔍 Testing Database Roundtrip")
    print("=" * 50)

    survey_json = load_test_survey()

    # Test parsing before DB
    print(f"📊 Questions before DB: {get_questions_count(survey_json)}")

    # Create a mock database session
    try:
        db = next(get_db())

        # Create a survey record (simulate what workflow service does)
        survey = Survey(
            rfq_id=None,  # We'll skip RFQ for this test
            status="draft",
            raw_output=survey_json,  # Store as raw_output first
            final_output=survey_json  # Store as final_output
        )

        db.add(survey)
        db.commit()

        # Retrieve it back
        retrieved_survey = db.query(Survey).filter(Survey.id == survey.id).first()

        print(f"📊 Questions in raw_output: {get_questions_count(retrieved_survey.raw_output)}")
        print(f"📊 Questions in final_output: {get_questions_count(retrieved_survey.final_output)}")

        # Test with SurveyService
        survey_service = SurveyService(db)
        fetched_survey = survey_service.get_survey(survey.id)

        if fetched_survey:
            print(f"📊 Questions via SurveyService: {get_questions_count(fetched_survey.final_output)}")

            # Test the actual response structure
            raw_questions = extract_all_questions(fetched_survey.final_output)
            print(f"📊 Raw extracted questions: {len(raw_questions)}")

            # Check if there's any corruption in the JSON
            if fetched_survey.final_output != survey_json:
                print("⚠️  JSON corruption detected during DB roundtrip!")

                # Find differences
                original_sections = survey_json.get('sections', [])
                fetched_sections = fetched_survey.final_output.get('sections', [])

                print(f"Original sections: {len(original_sections)}")
                print(f"Fetched sections: {len(fetched_sections)}")

                for i, (orig, fetch) in enumerate(zip(original_sections, fetched_sections)):
                    orig_q = len(orig.get('questions', []))
                    fetch_q = len(fetch.get('questions', []))
                    if orig_q != fetch_q:
                        print(f"  Section {i}: {orig_q} -> {fetch_q} questions")
            else:
                print("✅ JSON integrity maintained through DB roundtrip")

        # Cleanup
        db.delete(survey)
        db.commit()

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_response_format():
    """Test the API response transformation"""
    print("\n🔍 Testing API Response Format")
    print("=" * 50)

    survey_json = load_test_survey()

    # Simulate the API response structure (from survey.py)
    mock_survey_response = {
        "id": "test-id",
        "status": "draft",
        "raw_output": survey_json,
        "final_output": survey_json,
        "golden_similarity_score": None,
        "validation_results": {},
        "edit_suggestions": {},
        "pillar_scores": None
    }

    # Test the API transformation (from services/api.ts)
    transformed_survey = {
        "survey_id": mock_survey_response["id"],
        "title": mock_survey_response["final_output"].get("title", "Untitled Survey"),
        "description": mock_survey_response["final_output"].get("description", "No description available"),
        "estimated_time": mock_survey_response["final_output"].get("estimated_time", 10),
        "confidence_score": 0.8,  # Mock value
        "methodologies": mock_survey_response["final_output"].get("methodologies", []),
        "golden_examples": mock_survey_response["final_output"].get("golden_examples", []),
        "questions": mock_survey_response["final_output"].get("questions", []),
        "sections": mock_survey_response["final_output"].get("sections", []),
        "metadata": {
            "target_responses": mock_survey_response["final_output"].get("target_responses", 100),
            "methodology": mock_survey_response["final_output"].get("methodologies", []),
        }
    }

    print(f"📊 Original questions: {get_questions_count(survey_json)}")
    print(f"📊 Transformed questions: {get_questions_count(transformed_survey)}")

    # Check if transformation preserves question count
    if get_questions_count(survey_json) == get_questions_count(transformed_survey):
        print("✅ API transformation preserves question count")
    else:
        print("❌ API transformation loses questions!")
        print(f"   Original sections: {len(survey_json.get('sections', []))}")
        print(f"   Transformed sections: {len(transformed_survey.get('sections', []))}")
        print(f"   Original questions field: {len(survey_json.get('questions', []))}")
        print(f"   Transformed questions field: {len(transformed_survey.get('questions', []))}")

def test_frontend_processing():
    """Test how frontend processes the survey data"""
    print("\n🔍 Testing Frontend Processing")
    print("=" * 50)

    survey_json = load_test_survey()

    # Simulate what happens in frontend (from getQuestionCount function)
    def frontend_get_question_count(survey):
        # Check if we have sections (new format)
        if survey.get("sections") and len(survey["sections"]) > 0:
            return sum(len(section.get("questions", [])) for section in survey["sections"])
        # Fallback to legacy format
        return len(survey.get("questions", []))

    frontend_count = frontend_get_question_count(survey_json)
    utils_count = get_questions_count(survey_json)

    print(f"📊 Frontend count: {frontend_count}")
    print(f"📊 Utils count: {utils_count}")

    if frontend_count == utils_count:
        print("✅ Frontend and backend question counting match")
    else:
        print("❌ Frontend and backend question counting mismatch!")

def main():
    print("🧪 Testing Full Survey Workflow")
    print("=" * 80)

    try:
        test_database_roundtrip()
        test_api_response_format()
        test_frontend_processing()

        print("\n📋 Summary:")
        print("=" * 50)
        print("This test checks if questions get lost during:")
        print("1. Database storage/retrieval")
        print("2. API response transformation")
        print("3. Frontend processing")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()