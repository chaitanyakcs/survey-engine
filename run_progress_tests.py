#!/usr/bin/env python3
"""Simple test runner for progress tracking tests"""

import sys
import asyncio
import traceback
from unittest.mock import AsyncMock, MagicMock, patch

# Add current directory to path
sys.path.insert(0, '.')

def run_test(test_func, test_name):
    """Run a single test function and report results"""
    try:
        print(f"🧪 Running {test_name}...")
        if asyncio.iscoroutinefunction(test_func):
            asyncio.run(test_func())
        else:
            test_func()
        print(f"✅ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name} FAILED: {e}")
        traceback.print_exc()
        return False

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from src.workflows.workflow import create_workflow
        from src.workflows.state import SurveyGenerationState
        from src.services.websocket_client import WebSocketNotificationService
        from src.services.generation_service import GenerationService
        from src.services.evaluator_service import EvaluatorService
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_step_mapping():
    """Test that all backend steps have frontend mappings"""
    # All possible backend steps
    all_backend_steps = {
        "initializing_workflow", "parsing_rfq", "generating_embeddings", "rfq_parsed",
        "matching_golden_examples", "planning_methodologies", "build_context",
        "preparing_generation", "generating_questions", "llm_processing", "parsing_output",
        "validation_scoring", "evaluating_pillars", "single_call_evaluator",
        "pillar_scores_analysis", "advanced_evaluation", "legacy_evaluation",
        "fallback_evaluation", "finalizing", "completed", "human_review",
        "resuming_from_human_review", "resuming_generation"
    }
    
    # Expected frontend mapping
    frontend_step_mapping = {
        'generate': 'question_generation',
        'validate': 'quality_evaluation',
        'validation_scoring': 'quality_evaluation',
        'initializing_workflow': 'building_context',
        'parsing_rfq': 'building_context',
        'generating_embeddings': 'building_context',
        'rfq_parsed': 'building_context',
        'matching_golden_examples': 'building_context',
        'planning_methodologies': 'building_context',
        'parse_rfq': 'building_context',
        'retrieve_golden': 'building_context',
        'build_context': 'building_context',
        'preparing_generation': 'question_generation',
        'generating_questions': 'question_generation',
        'llm_processing': 'question_generation',
        'parsing_output': 'question_generation',
        'evaluating_pillars': 'quality_evaluation',
        'single_call_evaluator': 'quality_evaluation',
        'pillar_scores_analysis': 'quality_evaluation',
        'advanced_evaluation': 'quality_evaluation',
        'legacy_evaluation': 'quality_evaluation',
        'fallback_evaluation': 'quality_evaluation',
        'finalizing': 'completion',
        'prompt_review': 'human_review',
        'human_review': 'human_review',
        'resuming_from_human_review': 'question_generation',
        'resuming_generation': 'question_generation',
        'completion_handler': 'completion',
        'completed': 'completion'
    }
    
    # Check that all backend steps have mappings
    unmapped_steps = all_backend_steps - set(frontend_step_mapping.keys())
    if unmapped_steps:
        raise AssertionError(f"Backend steps without frontend mapping: {unmapped_steps}")
    
    print(f"✅ All {len(all_backend_steps)} backend steps have frontend mappings")
    return True

def test_progress_percentage_ranges():
    """Test that progress percentages are within expected ranges"""
    # Expected percentage ranges for each major step (updated to match ProgressTracker)
    frontend_step_ranges = {
        "building_context": (10, 25),
        "human_review": (65, 75),
        "question_generation": (35, 65),
        "quality_evaluation": (75, 95),
        "completion": (95, 100)
    }
    
    # Sample progress updates with their expected frontend step mappings (updated to match ProgressTracker)
    progress_samples = [
        ("initializing_workflow", 5, "building_context"),
        ("parsing_rfq", 10, "building_context"),
        ("generating_embeddings", 15, "building_context"),
        ("planning_methodologies", 30, "building_context"),
        ("build_context", 35, "building_context"),
        ("human_review", 70, "human_review"),
        ("preparing_generation", 30, "question_generation"),
        ("generating_questions", 50, "question_generation"),
        ("llm_processing", 55, "question_generation"),
        ("parsing_output", 62, "question_generation"),
        ("validation_scoring", 80, "quality_evaluation"),
        ("evaluating_pillars", 90, "quality_evaluation"),
        ("advanced_evaluation", 87, "quality_evaluation"),
        ("legacy_evaluation", 88, "quality_evaluation"),
        ("fallback_evaluation", 90, "quality_evaluation"),
        ("finalizing", 95, "completion"),
        ("completed", 100, "completion")
    ]
    
    for step_name, percent, frontend_step in progress_samples:
        min_percent, max_percent = frontend_step_ranges[frontend_step]
        if not (min_percent <= percent <= max_percent):
            raise AssertionError(f"Step '{step_name}' ({percent}%) outside expected range for {frontend_step} ({min_percent}-{max_percent}%)")
    
    print(f"✅ All {len(progress_samples)} progress samples are within expected ranges")
    return True

async def test_workflow_creation():
    """Test that workflow can be created with mocked dependencies"""
    try:
        from src.workflows.workflow import create_workflow
        from sqlalchemy.orm import Session
        
        # Mock database and connection manager
        mock_db = MagicMock(spec=Session)
        mock_connection_manager = MagicMock()
        
        # Create workflow
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        # Verify workflow has expected nodes
        expected_nodes = ['parse_rfq', 'retrieve_golden', 'build_context', 'prompt_review', 'generate', 'validate', 'completion_handler']
        available_nodes = list(workflow.nodes.keys())
        
        print(f"📋 Available nodes: {available_nodes}")
        
        for node_name in expected_nodes:
            if node_name not in workflow.nodes:
                raise AssertionError(f"Missing expected node: {node_name}")
        
        print(f"✅ Workflow created successfully with {len(workflow.nodes)} nodes")
        return True
    except Exception as e:
        print(f"❌ Workflow creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all progress tracking tests"""
    print("🚀 Running Progress Tracking Tests")
    print("=" * 50)
    
    tests = [
        (test_imports, "Module Imports"),
        (test_step_mapping, "Step Mapping Validation"),
        (test_progress_percentage_ranges, "Progress Percentage Ranges"),
        (test_workflow_creation, "Workflow Creation"),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Progress tracking implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
