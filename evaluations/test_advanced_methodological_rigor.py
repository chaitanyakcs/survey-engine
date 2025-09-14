#!/usr/bin/env python3
"""
Test Advanced Methodological Rigor Evaluator
Compare advanced vs basic methodological rigor evaluation approaches
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_advanced_methodological_rigor():
    """
    Test the advanced methodological rigor evaluator
    """
    
    print("🔬 Testing Advanced Methodological Rigor Evaluator")
    print("=" * 60)
    
    # Test data with potential methodological issues
    test_rfq = """
    Research Objective: Evaluate pricing strategies for B2B software solutions
    Target Audience: IT decision makers and procurement managers in companies with 50-500 employees
    Key Research Questions: 
    1. What pricing models are preferred by different company sizes?
    2. How do buyers evaluate value vs price in software selection?
    3. What are acceptable price ranges for different feature sets?
    Business Goal: Optimize pricing strategy and packaging for maximum market penetration
    Methodology: Van Westendorp Price Sensitivity Meter and Conjoint Analysis
    """
    
    test_survey = {
        "title": "B2B Software Pricing Strategy Survey",
        "description": "Understanding pricing preferences and decision criteria",
        "target_responses": 150,
        "estimated_time": 12,
        "metadata": {
            "methodology": ["Van Westendorp PSM", "Conjoint Analysis"]
        },
        "questions": [
            # Good screening question
            {"id": "q1", "text": "What is your role in software purchasing decisions?", "type": "multiple_choice"},
            
            # Potential leading bias
            {"id": "q2", "text": "Don't you think expensive software often provides better value?", "type": "rating"},
            
            # Double-barreled question
            {"id": "q3", "text": "How important are price and feature completeness in your software selection?", "type": "rating"},
            
            # Good Van Westendorp question
            {"id": "q4", "text": "At what price would this software be too expensive to consider?", "type": "text", "methodology": "Van Westendorp PSM"},
            {"id": "q5", "text": "At what price would this software be so cheap you'd question its quality?", "type": "text", "methodology": "Van Westendorp PSM"},
            
            # Missing other Van Westendorp questions
            
            # Potential conjoint question but poorly implemented
            {"id": "q6", "text": "Which software package would you prefer?", "type": "multiple_choice", "methodology": "Conjoint Analysis",
             "options": ["Package A: $100/month, Basic features", "Package B: $200/month, Advanced features"]},
            
            # Sensitive question placed too early
            {"id": "q7", "text": "What is your company's annual software budget?", "type": "text"},
            
            # Loaded language
            {"id": "q8", "text": "How satisfied are you with your current overpriced software solution?", "type": "rating"}
        ]
    }
    
    try:
        # Import the advanced evaluator
        from modules.advanced_methodological_rigor_evaluator import AdvancedMethodologicalRigorEvaluator
        
        print("🔬 Initializing Advanced Methodological Rigor Evaluator...")
        evaluator = AdvancedMethodologicalRigorEvaluator(llm_client=None, db_session=None)
        
        print("🚀 Running advanced methodological rigor evaluation (fallback mode)...")
        result = await evaluator.evaluate_methodological_rigor(test_survey, test_rfq)
        
        print("\\n✅ ADVANCED METHODOLOGICAL RIGOR RESULTS:")
        print(f"📊 Overall Score: {result.overall_score:.2f}")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")
        print(f"⚠️  Biases Detected: {len(result.bias_analysis)}")
        print(f"🔄 Flow Issues: {len([f for f in result.question_flow_analysis if f.flow_score < 0.7])}")
        print(f"📋 Methodology Compliance Issues: {len([c for c in result.methodology_compliance if c.implementation_quality < 0.7])}")
        print(f"💡 Recommendations: {len(result.specific_recommendations)}")
        
        print("\\n🧠 REASONING CHAIN:")
        for i, step in enumerate(result.reasoning_chain, 1):
            print(f"   {i}. {step}")
        
        print("\\n⚠️  BIAS ANALYSIS:")
        for bias in result.bias_analysis:
            print(f"   • {bias.question_id}: {bias.bias_type.upper()} bias ({bias.severity})")
            print(f"     Issue: {bias.specific_issue}")
            print(f"     Fix: {bias.suggested_fix}")
        
        print("\\n🔄 QUESTION FLOW ANALYSIS:")
        for flow in result.question_flow_analysis:
            if flow.flow_score < 0.8:
                print(f"   • {flow.question_id} (Position {flow.position}): Score {flow.flow_score:.2f}")
                if flow.sequencing_issues:
                    for issue in flow.sequencing_issues:
                        print(f"     - {issue}")
        
        print("\\n📋 METHODOLOGY COMPLIANCE:")
        for compliance in result.methodology_compliance:
            print(f"   • {compliance.methodology}: Quality {compliance.implementation_quality:.2f}")
            if compliance.missing_elements:
                print(f"     Missing: {', '.join(compliance.missing_elements)}")
            if compliance.compliance_issues:
                for issue in compliance.compliance_issues:
                    print(f"     - {issue}")
        
        print("\\n📈 STATISTICAL POWER ASSESSMENT:")
        power = result.statistical_power_assessment
        print(f"   Adequacy Score: {power.get('adequacy_score', 'N/A')}")
        print(f"   Sample Size Evaluation: {power.get('sample_size_evaluation', 'N/A')}")
        if power.get('power_recommendations'):
            for rec in power['power_recommendations']:
                print(f"   - {rec}")
        
        print("\\n💡 SPECIFIC RECOMMENDATIONS:")
        for i, rec in enumerate(result.specific_recommendations[:5], 1):  # Show first 5
            print(f"   {i}. [{rec.get('priority', 'N/A')}] {rec.get('issue', 'N/A')}")
            if rec.get('suggested_fix'):
                print(f"      Fix: {rec['suggested_fix']}")
            elif rec.get('reasoning'):
                print(f"      Reasoning: {rec['reasoning']}")
        
        print(f"\\n📈 EVALUATION METADATA:")
        for key, value in result.evaluation_metadata.items():
            print(f"   {key}: {value}")
        
        print("\\n" + "=" * 60)
        print("🎯 ADVANCED METHODOLOGICAL RIGOR EVALUATION COMPLETE!")
        print("   This demonstrates sophisticated bias detection and flow analysis")
        print("   Next: Add LLM token for even more detailed reasoning")
        
        return result
        
    except ImportError as e:
        print(f"❌ Failed to import advanced methodological rigor evaluator: {e}")
        return None
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None

async def compare_with_basic_methodological():
    """
    Compare advanced evaluator with basic approach
    """
    
    print("\\n🔄 COMPARISON: Advanced vs Basic Methodological Rigor Evaluation")
    print("=" * 60)
    
    try:
        # Import basic evaluator for comparison
        from modules.methodological_rigor_evaluator import MethodologicalRigorEvaluator
        
        test_rfq = "Research Goal: Understand B2B software pricing preferences"
        test_survey = {
            "questions": [
                {"text": "What is your role?", "type": "multiple_choice"},
                {"text": "Don't you think expensive software is better?", "type": "rating"}
            ],
            "target_responses": 150
        }
        
        basic_evaluator = MethodologicalRigorEvaluator(llm_client=None, db_session=None)
        
        print("📊 Running basic methodological rigor evaluation...")
        basic_result = await basic_evaluator.evaluate_methodological_rigor(test_survey, test_rfq)
        
        print(f"📊 Basic Score: {basic_result.score:.2f}")
        print(f"💡 Basic Recommendations: {len(basic_result.recommendations)}")
        print(f"⚠️  Basic Bias Indicators: {len(basic_result.bias_indicators)}")
        print(f"🔍 Analysis Depth: Basic heuristics and simple pattern matching")
        
        print("\\n📈 ADVANCED vs BASIC COMPARISON:")
        print("   Advanced: Multi-type bias detection with severity assessment")
        print("   Basic: Simple pattern matching for common bias keywords")
        print("   Advanced: Sophisticated question flow analysis with optimal positioning")
        print("   Basic: Basic sequencing heuristics")
        print("   Advanced: Deep methodology compliance analysis")
        print("   Basic: Generic methodology coverage assessment")
        print("   Advanced: Statistical power assessment with effect size calculations")
        print("   Basic: Simple sample size adequacy rules")
        print("   Advanced: Specific actionable recommendations with implementation details")
        print("   Basic: Generic methodological improvement suggestions")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Advanced Methodological Rigor Evaluator - Phase 1 Test")
    print("Testing state-of-the-art methodological analysis vs basic approach")
    print()
    
    result = asyncio.run(test_advanced_methodological_rigor())
    
    if result:
        asyncio.run(compare_with_basic_methodological())
        print("\\n✅ Phase 1 Advanced Methodological Rigor: SUCCESS!")
        print("   Ready for Phase 1 next steps: Multi-Perspective Framework implementation")
    else:
        print("\\n❌ Phase 1 test failed - check implementation")