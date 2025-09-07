#!/usr/bin/env python3
"""
Survey Engine Evaluation Runner
Run test cases and store results for performance tracking
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


class EvaluationRunner:
    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
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
            
            # Analyze the result
            analysis = self.analyze_result(result, test_case)
            
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
                "analysis": analysis
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
        
        summary = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "failed_tests": len(results) - len(successful_results),
            "average_processing_time": sum(r.get("processing_time_seconds", 0) for r in successful_results) / len(successful_results),
            "ai_generation_rate": sum(1 for r in successful_results if r.get("used_ai_generation")) / len(successful_results) * 100,
            "average_questions_per_survey": sum(r.get("analysis", {}).get("questions_count", 0) for r in successful_results) / len(successful_results),
            "methodology_coverage_avg": sum(r.get("analysis", {}).get("methodology_match", {}).get("coverage_percentage", 0) for r in successful_results) / len(successful_results),
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
        print(f"💾 Summary saved to: {summary_file}")


async def main():
    runner = EvaluationRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())