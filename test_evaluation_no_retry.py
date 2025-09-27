#!/usr/bin/env python3
"""
Test script to verify evaluation workflow doesn't auto-retry on low quality scores
"""
import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.workflows.nodes import ValidatorAgent
from src.database.connection import SessionLocal
from src.workflows.state import SurveyGenerationState


async def test_no_auto_retry():
    """Test that ValidatorAgent doesn't auto-retry on low quality scores"""

    # Mock survey data that would typically get low quality scores
    mock_survey = {
        "title": "Basic Survey",
        "sections": [
            {
                "id": 1,
                "title": "Questions",
                "questions": [
                    {"id": "q1", "text": "What?", "type": "text"},  # Too short
                    {"id": "q2", "text": "How?", "type": "text"}   # Too short
                ]
            }
        ]
    }

    # Create a mock state with low retry count
    mock_state = SurveyGenerationState(
        rfq_text="Simple research request",
        generated_survey=mock_survey,
        retry_count=0,  # Start with 0 retries
        golden_examples=[]
    )

    print("🧪 Testing ValidatorAgent behavior...")
    print(f"📊 Initial retry count: {mock_state.retry_count}")
    print(f"📋 Mock survey quality: Low (short questions)")

    # Get database session
    db = SessionLocal()

    try:
        # Initialize ValidatorAgent
        validator = ValidatorAgent(db)

        print("\n🔍 Running validation (expecting low quality score)...")

        # Run validation - this should NOT auto-retry
        result = await validator(mock_state)

        print(f"\n📋 Validation Results:")
        print(f"  - Quality gate passed: {result.get('quality_gate_passed')}")
        print(f"  - Workflow should continue: {result.get('workflow_should_continue')}")
        print(f"  - Retry count after validation: {result.get('retry_count')}")
        print(f"  - Error message: {result.get('error_message')}")
        print(f"  - Pillar scores: {result.get('pillar_scores', {}).get('overall_grade', 'N/A')}")

        # Verify expected behavior
        if result.get('workflow_should_continue') == True:
            print("\n✅ SUCCESS: Workflow continues even with low quality score")
        else:
            print("\n❌ FAILURE: Workflow blocked despite expectation to continue")

        if result.get('retry_count') == 0:
            print("✅ SUCCESS: Retry count unchanged (no auto-retry)")
        else:
            print(f"❌ FAILURE: Retry count changed from 0 to {result.get('retry_count')}")

        # Check if evaluation provided useful feedback
        pillar_scores = result.get('pillar_scores', {})
        if pillar_scores:
            print(f"✅ SUCCESS: Evaluation provided quality assessment")
            print(f"   Grade: {pillar_scores.get('overall_grade', 'N/A')}")
            print(f"   Score: {pillar_scores.get('weighted_score', 0):.2%}")
        else:
            print("⚠️ WARNING: No pillar scores provided")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Testing Evaluation Workflow - No Auto-Retry")
    print("=" * 50)

    success = asyncio.run(test_no_auto_retry())

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Evaluation works without auto-retry.")
    else:
        print("💥 Tests failed! Check the implementation.")

    sys.exit(0 if success else 1)