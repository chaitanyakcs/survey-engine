#!/usr/bin/env python3
"""
Simple Pillar Scoring Test
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from database import get_db
from database.models import SurveyRule

def test_pillar_rules():
    """Test if pillar rules are properly loaded"""
    
    print("🧪 Testing Pillar Rules Loading")
    print("=" * 50)
    
    # Create database session
    db = next(get_db())
    
    try:
        # Check pillar rules count
        pillar_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == 'pillar',
            SurveyRule.is_active == True
        ).all()
        
        print(f"📊 Total pillar rules found: {len(pillar_rules)}")
        
        # Group by category
        by_category = {}
        for rule in pillar_rules:
            if rule.category not in by_category:
                by_category[rule.category] = []
            by_category[rule.category].append(rule)
        
        print(f"\n📋 Rules by category:")
        for category, rules in by_category.items():
            print(f"   {category}: {len(rules)} rules")
            
            # Check for duplicates
            descriptions = [rule.rule_description for rule in rules]
            unique_descriptions = set(descriptions)
            if len(descriptions) != len(unique_descriptions):
                print(f"     ⚠️  DUPLICATES FOUND: {len(descriptions) - len(unique_descriptions)} duplicates")
                
                # Show duplicates
                from collections import Counter
                desc_counts = Counter(descriptions)
                for desc, count in desc_counts.items():
                    if count > 1:
                        print(f"       - '{desc[:50]}...' appears {count} times")
            else:
                print(f"     ✅ No duplicates")
        
        # Test pillar scoring service initialization
        print(f"\n🏛️ Testing Pillar Scoring Service...")
        try:
            from services.pillar_scoring_service import PillarScoringService
            pillar_service = PillarScoringService(db)
            print("✅ PillarScoringService initialized successfully")
            
            # Test getting rules for each pillar
            pillar_weights = {
                'content_validity': 0.20,
                'methodological_rigor': 0.25,
                'clarity_comprehensibility': 0.25,
                'structural_coherence': 0.20,
                'deployment_readiness': 0.10
            }
            
            for pillar_name in pillar_weights.keys():
                rules = pillar_service._get_pillar_rules(pillar_name)
                print(f"   {pillar_name}: {len(rules)} rules loaded")
                
        except Exception as e:
            print(f"❌ Error initializing PillarScoringService: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing pillar rules: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_pillar_rules()
    if success:
        print("\n🎉 Pillar rules test completed!")
    else:
        print("\n❌ Pillar rules test failed!")
        sys.exit(1)
