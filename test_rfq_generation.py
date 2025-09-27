#!/usr/bin/env python3
"""
Test script for RFQ auto-generation functionality
"""
import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.golden_service import GoldenService
from src.database.connection import SessionLocal


async def test_rfq_generation():
    """Test the RFQ generation functionality with a sample survey"""

    # Sample survey JSON (Van Westendorp pricing methodology)
    sample_survey = {
        "title": "Premium Coffee Machine Pricing Research",
        "description": "Van Westendorp Price Sensitivity Analysis for premium coffee machines",
        "methodology": "Van Westendorp PSM",
        "questions": [
            {
                "id": "psm_1",
                "text": "At what price would this coffee machine be so expensive that you would not consider buying it?",
                "type": "number",
                "required": True
            },
            {
                "id": "psm_2",
                "text": "At what price would you consider this coffee machine to be priced so low that you would feel the quality couldn't be very good?",
                "type": "number",
                "required": True
            },
            {
                "id": "psm_3",
                "text": "At what price would you consider this coffee machine starting to get expensive?",
                "type": "number",
                "required": True
            },
            {
                "id": "psm_4",
                "text": "At what price would you consider this coffee machine to be a bargain—a great buy for the money?",
                "type": "number",
                "required": True
            }
        ]
    }

    # Test RFQ generation
    print("🧪 Testing RFQ generation from survey...")
    print(f"📊 Sample survey: {sample_survey['title']}")
    print(f"🔍 Questions: {len(sample_survey['questions'])}")

    # Get database session
    db = SessionLocal()

    try:
        # Initialize GoldenService
        golden_service = GoldenService(db)

        # Test RFQ generation
        print("\n🤖 Generating RFQ from survey...")
        generated_rfq = await golden_service.generate_rfq_from_survey(
            survey_json=sample_survey,
            methodology_tags=["van_westendorp", "pricing"],
            industry_category="consumer_appliances",
            research_goal="pricing_optimization"
        )

        print(f"\n✅ RFQ Generated Successfully!")
        print(f"📝 Generated RFQ ({len(generated_rfq)} characters):")
        print("-" * 60)
        print(generated_rfq)
        print("-" * 60)

        # Test complete golden pair creation (without actually saving)
        print("\n🏆 Testing complete golden pair creation workflow...")

        # This would normally save to database, but we're just testing the flow
        print("📋 Would create golden pair with:")
        print(f"  - RFQ: {len(generated_rfq)} characters")
        print(f"  - Survey: {len(sample_survey['questions'])} questions")
        print(f"  - Methodology: {['van_westendorp', 'pricing']}")
        print(f"  - Industry: consumer_appliances")
        print(f"  - Research Goal: pricing_optimization")

        print("\n🎉 RFQ generation test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_rfq_generation())
    sys.exit(0 if success else 1)