#!/usr/bin/env python3
"""
Diagnostic script for survey generation issues
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
sys.path.append('/Users/chaitanya/Work/repositories/survey-engine')

from src.config import settings
from src.database.models import LLMAudit

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def diagnose_generation_issues():
    """Diagnose survey generation issues by checking recent LLM audit records"""

    print("🔍 Survey Generation Diagnostic Tool")
    print("=" * 50)

    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   Replicate API Token: {'✅ Present' if settings.replicate_api_token else '❌ Missing'}")
    print(f"   Generation Model: {settings.generation_model}")
    print(f"   Database URL: {settings.database_url[:50]}...")

    # Connect to database
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        print("\n📊 Recent LLM Audit Records (last 24 hours):")

        # Get recent survey generation records
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        recent_records = db.query(LLMAudit).filter(
            LLMAudit.purpose == 'survey_generation',
            LLMAudit.created_at >= cutoff_time
        ).order_by(LLMAudit.created_at.desc()).limit(5).all()

        if not recent_records:
            print("   ❌ No recent survey generation records found")
            return

        for i, record in enumerate(recent_records, 1):
            print(f"\n   Record {i}:")
            print(f"   ├─ ID: {record.interaction_id}")
            print(f"   ├─ Created: {record.created_at}")
            print(f"   ├─ Model: {record.model_name}")
            print(f"   ├─ Success: {'✅' if record.success else '❌'}")
            print(f"   ├─ Input Length: {len(record.input_prompt) if record.input_prompt else 0} chars")
            print(f"   ├─ Output Length: {len(record.output_content) if record.output_content else 0} chars")
            print(f"   ├─ Response Time: {record.response_time_ms}ms")

            if record.error_message:
                print(f"   ├─ Error: {record.error_message}")

            # Analyze output content
            if record.output_content:
                content = record.output_content

                # Check if it's JSON
                try:
                    import json
                    parsed = json.loads(content)
                    print(f"   ├─ JSON Valid: ✅")
                    print(f"   ├─ JSON Keys: {list(parsed.keys())}")

                    # Check for survey structure
                    if 'sections' in parsed:
                        sections = parsed['sections']
                        total_questions = sum(len(section.get('questions', [])) for section in sections)
                        print(f"   ├─ Sections: {len(sections)}")
                        print(f"   └─ Questions: {total_questions}")
                    else:
                        print(f"   └─ Structure: Missing sections (minimal survey)")

                except json.JSONDecodeError as e:
                    print(f"   ├─ JSON Valid: ❌ ({e})")
                    print(f"   └─ Content Preview: {content[:200]}...")
            else:
                print(f"   └─ Output: None/Empty")

        # Check for pattern
        success_rates = [r.success for r in recent_records]
        output_lengths = [len(r.output_content) if r.output_content else 0 for r in recent_records]

        print(f"\n📈 Analysis:")
        print(f"   Success Rate: {sum(success_rates)}/{len(success_rates)} ({sum(success_rates)/len(success_rates)*100:.1f}%)")
        print(f"   Avg Output Length: {sum(output_lengths)/len(output_lengths):.0f} chars")
        print(f"   Min/Max Output: {min(output_lengths)}/{max(output_lengths)} chars")

        # Recommendations
        print(f"\n💡 Recommendations:")

        if not all(success_rates):
            print("   🔧 Some generations failed - check API configuration")

        if min(output_lengths) < 1000:
            print("   🔧 Short responses detected - may indicate:")
            print("      - JSON parsing failures (falling back to minimal survey)")
            print("      - API token limits")
            print("      - Model configuration issues")
            print("      - Prompt formatting problems")

        if max(output_lengths) - min(output_lengths) > 5000:
            print("   🔧 Inconsistent response lengths - check for:")
            print("      - Different input contexts")
            print("      - API rate limiting")
            print("      - Model temperature settings")

        db.close()

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_generation_issues())