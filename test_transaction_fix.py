#!/usr/bin/env python3
"""
Test script to verify transaction fixes in annotation insights service
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.database.connection import SessionLocal
from src.services.annotation_insights_service import AnnotationInsightsService

async def test_annotation_insights():
    """Test annotation insights service with transaction fixes"""
    print("🧪 Testing Annotation Insights Service...")
    
    db = SessionLocal()
    try:
        service = AnnotationInsightsService(db)
        
        # Test quality pattern extraction
        print("📊 Testing quality pattern extraction...")
        patterns = await service.extract_quality_patterns()
        
        print(f"✅ Quality patterns extracted successfully!")
        print(f"   - High quality patterns: {len(patterns.get('high_quality_patterns', {}))}")
        print(f"   - Low quality patterns: {len(patterns.get('low_quality_patterns', {}))}")
        print(f"   - Common issues: {len(patterns.get('common_issues', []))}")
        
        # Test improvement trend calculation
        print("📈 Testing improvement trend calculation...")
        trend = await service.calculate_improvement_trend()
        
        print(f"✅ Improvement trend calculated successfully!")
        print(f"   - Status: {trend.get('status', 'unknown')}")
        print(f"   - Trend: {trend.get('improvement_trend', 0)}%")
        print(f"   - Message: {trend.get('message', 'No message')}")
        
        print("\n🎉 All tests passed! Transaction issues appear to be resolved.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_annotation_insights())
