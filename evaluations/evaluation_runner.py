#!/usr/bin/env python3
"""
Survey Engine Evaluation Runner - Enhanced with LLM-based 5-Pillar Assessment
Run test cases and store results for performance tracking with comprehensive evaluation
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from demo_server import generate_survey_with_gpt5, generate_fallback_survey, RFQSubmissionRequest
from test_cases import COMPLEX_RFQ_TEST_CASES

# Import the new LLM-based evaluation modules
try:
    from modules.pillar_based_evaluator import PillarBasedEvaluator
    PILLAR_EVALUATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Pillar evaluation modules not available: {e}")
    PILLAR_EVALUATION_AVAILABLE = False


class EvaluationRunner:
    def __init__(self, enable_pillar_evaluation=True):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize LLM-based pillar evaluator if available
        self.enable_pillar_evaluation = enable_pillar_evaluation and PILLAR_EVALUATION_AVAILABLE
        if self.enable_pillar_evaluation:
            self.pillar_evaluator = PillarBasedEvaluator(llm_client=None)  # TODO: Integrate with actual LLM client
            print("🔍 5-Pillar LLM-based evaluation enabled")
        else:
            self.pillar_evaluator = None
            print("⚠️  5-Pillar evaluation disabled - using basic analysis only")
        
    async def run_single_test(self, test_case):
        """Run a single test case and return results"""
        print(f"\n🧪 Testing: {test_case['description']}")
        print(f"📋 Category: {test_case['category']}")
        
        start_time = time.time()
        
        try:
            # Create RFQ request object
            rfq_request = RFQSubmissionRequest(
                description=test_case['rfq_text'],
                title=f"Evaluation Test: {test_case['id']}"
            )
            
            # Try GPT-5 generation first, fallback if needed
            try:
                survey_result = await generate_survey_with_gpt5(rfq_request)
                used_ai = True
                model_version = "gpt-5-via-replicate"
            except Exception as ai_error:
                print(f"🔄 AI generation failed ({ai_error}), using fallback template")
                survey_result = generate_fallback_survey(rfq_request)
                used_ai = False
                model_version = "fallback-template"
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Package result in expected format
            result = {
                "survey": survey_result,
                "used_ai_generation": used_ai,
                "model_version": model_version,
                "used_golden_examples": [],
                "golden_similarity_score": None
            }
            
            # Analyze the result with basic analysis
            analysis = self.analyze_result(result, test_case)
            
            # Perform LLM-based 5-pillar evaluation if enabled
            pillar_evaluation = None
            if self.enable_pillar_evaluation and result.get("survey"):
                try:
                    print("🔍 Running 5-pillar evaluation...")
                    pillar_start = time.time()
                    pillar_evaluation = await self.pillar_evaluator.evaluate_survey(
                        result["survey"], 
                        test_case["rfq_text"]
                    )
                    pillar_time = time.time() - pillar_start
                    print(f"✅ Pillar evaluation completed in {pillar_time:.1f}s")
                except Exception as e:
                    print(f"⚠️  Pillar evaluation failed: {e}")
                    pillar_evaluation = None
            
            # Store the full result
            full_result = {
                "test_case_id": test_case["id"],
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": round(processing_time, 2),
                "rfq_input": test_case["rfq_text"],
                "generated_survey": result.get("survey"),
                "model_used": result.get("model_version"),
                "used_ai_generation": result.get("used_ai_generation", False),
                "golden_examples_used": result.get("used_golden_examples", []),
                "similarity_score": result.get("golden_similarity_score"),
                "analysis": analysis,
                "pillar_evaluation": pillar_evaluation.__dict__ if pillar_evaluation else None
            }
            
            # Save individual result
            result_file = self.results_dir / f"{test_case['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_file, 'w') as f:
                json.dump(full_result, f, indent=2)
            
            # Print summary
            self.print_test_summary(full_result, analysis)
            
            return full_result
            
        except Exception as e:
            print(f"❌ Error processing test case: {e}")
            return {
                "test_case_id": test_case["id"],
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    def analyze_result(self, result, test_case):
        """Analyze the generated survey against expected criteria"""
        if not result.get("survey"):
            return {"error": "No survey generated"}
        
        survey = result["survey"]
        analysis = {
            "title_generated": bool(survey.get("title")),
            "description_generated": bool(survey.get("description")),
            "questions_count": len(survey.get("questions", [])),
            "estimated_time": survey.get("estimated_time"),
            "methodologies_detected": survey.get("metadata", {}).get("methodology", []),
            "meets_min_questions": len(survey.get("questions", [])) >= test_case.get("min_questions", 10),
            "has_advanced_methodologies": bool(survey.get("metadata", {}).get("methodology", [])),
            "quality_indicators": {
                "has_screening_questions": any(q.get("category") == "screening" for q in survey.get("questions", [])),
                "has_scale_questions": any(q.get("type") == "scale" for q in survey.get("questions", [])),
                "has_multiple_choice": any(q.get("type") == "multiple_choice" for q in survey.get("questions", [])),
                "has_methodology_tags": any(q.get("methodology") for q in survey.get("questions", [])),
                "has_categories": any(q.get("category") for q in survey.get("questions", []))
            }
        }
        
        # Check for expected methodologies
        expected_methods = set(test_case.get("expected_methodologies", []))
        detected_methods = set(analysis["methodologies_detected"])
        analysis["methodology_match"] = {
            "expected": list(expected_methods),
            "detected": list(detected_methods),
            "intersection": list(expected_methods & detected_methods),
            "coverage_percentage": len(expected_methods & detected_methods) / len(expected_methods) * 100 if expected_methods else 100
        }
        
        return analysis
    
    def print_test_summary(self, result, analysis):
        """Print a summary of the test results"""
        survey = result.get("generated_survey")
        if not survey:
            print("❌ No survey generated")
            return
        
        print(f"✅ Generated: \"{survey.get('title', 'N/A')}\"")
        print(f"📊 Questions: {analysis['questions_count']}")
        print(f"⏱️  Estimated time: {analysis['estimated_time']} minutes")
        print(f"🔬 Methodologies: {', '.join(analysis['methodologies_detected'])}")
        print(f"🎯 Methodology coverage: {analysis['methodology_match']['coverage_percentage']:.0f}%")
        print(f"⚡ Processing time: {result['processing_time_seconds']}s")
        print(f"🤖 Used AI: {result['used_ai_generation']}")
        
        if result.get("golden_examples_used"):
            print(f"📚 Golden examples used: {len(result['golden_examples_used'])}")
        
        # Display 5-pillar evaluation results if available
        pillar_eval = result.get("pillar_evaluation")
        if pillar_eval and self.enable_pillar_evaluation:
            print("\n🏛️  5-PILLAR EVALUATION RESULTS:")
            print(f"   Overall Score: {pillar_eval.get('overall_score', 0):.2f}/1.0")
            
            pillar_scores = pillar_eval.get('pillar_scores', {})
            print("   Individual Pillars:")
            print(f"   📖 Content Validity (20%):        {pillar_scores.get('content_validity', 0):.2f}")
            print(f"   🔬 Methodological Rigor (25%):    {pillar_scores.get('methodological_rigor', 0):.2f}")
            print(f"   📝 Clarity & Comprehensibility (25%): {pillar_scores.get('clarity_comprehensibility', 0):.2f}")
            print(f"   🏗️ Structural Coherence (20%):    {pillar_scores.get('structural_coherence', 0):.2f}")
            print(f"   🚀 Deployment Readiness (10%):    {pillar_scores.get('deployment_readiness', 0):.2f}")
            
            recommendations = pillar_eval.get('recommendations', [])
            if recommendations:
                print("\n💡 Top Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec}")
        elif self.enable_pillar_evaluation:
            print("\n⚠️  5-Pillar evaluation was enabled but failed to complete")
    
    async def run_all_tests(self):
        """Run all test cases and generate summary report"""
        print("🚀 Starting Survey Engine Evaluation Suite")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Running {len(COMPLEX_RFQ_TEST_CASES)} test cases\n")
        
        all_results = []
        
        for test_case in COMPLEX_RFQ_TEST_CASES:
            result = await self.run_single_test(test_case)
            all_results.append(result)
            print("-" * 80)
        
        # Generate summary report
        await self.generate_summary_report(all_results)
        
        return all_results
    
    async def generate_summary_report(self, results):
        """Generate a summary report of all test results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.results_dir / f"evaluation_summary_{timestamp}.json"
        
        successful_results = [r for r in results if not r.get("error")]
        
        if not successful_results:
            print("\n❌ No successful test cases")
            return
        
        # Calculate pillar evaluation statistics if available
        pillar_stats = None
        pillar_results = [r for r in successful_results if r.get("pillar_evaluation")]
        
        if pillar_results and self.enable_pillar_evaluation:
            pillar_overall_scores = [r["pillar_evaluation"]["overall_score"] for r in pillar_results]
            pillar_content_scores = [r["pillar_evaluation"]["pillar_scores"]["content_validity"] for r in pillar_results]
            pillar_method_scores = [r["pillar_evaluation"]["pillar_scores"]["methodological_rigor"] for r in pillar_results]
            pillar_clarity_scores = [r["pillar_evaluation"]["pillar_scores"]["clarity_comprehensibility"] for r in pillar_results]
            pillar_structural_scores = [r["pillar_evaluation"]["pillar_scores"]["structural_coherence"] for r in pillar_results]
            pillar_deployment_scores = [r["pillar_evaluation"]["pillar_scores"]["deployment_readiness"] for r in pillar_results]
            
            pillar_stats = {
                "pillar_evaluation_enabled": True,
                "surveys_with_pillar_evaluation": len(pillar_results),
                "average_overall_score": sum(pillar_overall_scores) / len(pillar_overall_scores),
                "average_pillar_scores": {
                    "content_validity": sum(pillar_content_scores) / len(pillar_content_scores),
                    "methodological_rigor": sum(pillar_method_scores) / len(pillar_method_scores),
                    "clarity_comprehensibility": sum(pillar_clarity_scores) / len(pillar_clarity_scores),
                    "structural_coherence": sum(pillar_structural_scores) / len(pillar_structural_scores),
                    "deployment_readiness": sum(pillar_deployment_scores) / len(pillar_deployment_scores)
                },
                "score_distribution": {
                    "excellent_surveys": len([s for s in pillar_overall_scores if s >= 0.8]),
                    "good_surveys": len([s for s in pillar_overall_scores if 0.6 <= s < 0.8]),
                    "needs_improvement": len([s for s in pillar_overall_scores if s < 0.6])
                }
            }
        else:
            pillar_stats = {"pillar_evaluation_enabled": False}

        summary = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "failed_tests": len(results) - len(successful_results),
            "average_processing_time": sum(r.get("processing_time_seconds", 0) for r in successful_results) / len(successful_results),
            "ai_generation_rate": sum(1 for r in successful_results if r.get("used_ai_generation")) / len(successful_results) * 100,
            "average_questions_per_survey": sum(r.get("analysis", {}).get("questions_count", 0) for r in successful_results) / len(successful_results),
            "methodology_coverage_avg": sum(r.get("analysis", {}).get("methodology_match", {}).get("coverage_percentage", 0) for r in successful_results) / len(successful_results),
            "pillar_evaluation_stats": pillar_stats,
            "detailed_results": results
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print(f"\n📊 EVALUATION SUMMARY")
        print(f"✅ Successful tests: {summary['successful_tests']}/{summary['total_tests']}")
        print(f"⚡ Average processing time: {summary['average_processing_time']:.1f}s")
        print(f"🤖 AI generation rate: {summary['ai_generation_rate']:.0f}%")
        print(f"📋 Average questions per survey: {summary['average_questions_per_survey']:.1f}")
        print(f"🎯 Average methodology coverage: {summary['methodology_coverage_avg']:.0f}%")
        
        # Print pillar evaluation summary if available
        pillar_stats = summary.get("pillar_evaluation_stats", {})
        if pillar_stats.get("pillar_evaluation_enabled"):
            print(f"\n🏛️  5-PILLAR EVALUATION SUMMARY")
            print(f"📊 Surveys evaluated: {pillar_stats['surveys_with_pillar_evaluation']}")
            print(f"🎯 Average overall score: {pillar_stats['average_overall_score']:.2f}/1.0")
            
            avg_scores = pillar_stats["average_pillar_scores"]
            print(f"📖 Content Validity: {avg_scores['content_validity']:.2f}")
            print(f"🔬 Methodological Rigor: {avg_scores['methodological_rigor']:.2f}")
            print(f"📝 Clarity & Comprehensibility: {avg_scores['clarity_comprehensibility']:.2f}")
            print(f"🏗️ Structural Coherence: {avg_scores['structural_coherence']:.2f}")
            print(f"🚀 Deployment Readiness: {avg_scores['deployment_readiness']:.2f}")
            
            distribution = pillar_stats["score_distribution"]
            print(f"\n📈 Quality Distribution:")
            print(f"   🌟 Excellent (≥0.8): {distribution['excellent_surveys']}")
            print(f"   ✅ Good (0.6-0.8): {distribution['good_surveys']}")
            print(f"   ⚠️  Needs work (<0.6): {distribution['needs_improvement']}")
        else:
            print(f"\n⚠️  5-Pillar evaluation was disabled or failed")
        
        print(f"\n💾 Summary saved to: {summary_file}")


async def main():
    runner = EvaluationRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())