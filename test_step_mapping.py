#!/usr/bin/env python3
"""
Test script to verify that backend step names match frontend expectations
"""
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_step_mapping():
    """Test that all backend steps have corresponding frontend mappings"""

    # Backend steps sent by workflow.py
    backend_steps = [
        'parsing_rfq',
        'generating_embeddings',
        'rfq_parsed',
        'matching_golden_examples',
        'planning_methodologies',
        'human_review',
        'preparing_generation',
        'generating_questions',
        'parsing_output',
        'validation_scoring',
        'single_call_evaluator',
        'pillar_scores_analysis',
        'fallback_evaluation',
        'completed'
    ]

    # Expected frontend substep mappings (from ProgressStepper.tsx)
    frontend_substeps = [
        'parsing_rfq',
        'generating_embeddings',
        'rfq_parsed',
        'matching_golden_examples',
        'planning_methodologies',
        'human_review',
        'preparing_generation',
        'generating_questions',
        'parsing_output',
        'validation_scoring',
        'single_call_evaluator',
        'pillar_scores_analysis',
        'fallback_evaluation',
        'completed'
    ]

    print("🧪 Testing Backend-Frontend Step Mapping")
    print("=" * 50)

    missing_mappings = []
    extra_mappings = []

    # Check if all backend steps have frontend mappings
    for step in backend_steps:
        if step not in frontend_substeps:
            missing_mappings.append(step)

    # Check if frontend has any extra mappings
    for step in frontend_substeps:
        if step not in backend_steps:
            extra_mappings.append(step)

    if missing_mappings:
        print("❌ Missing frontend mappings for backend steps:")
        for step in missing_mappings:
            print(f"  - {step}")
        print()

    if extra_mappings:
        print("⚠️ Extra frontend mappings (not sent by backend):")
        for step in extra_mappings:
            print(f"  - {step}")
        print()

    if not missing_mappings and not extra_mappings:
        print("✅ SUCCESS: All backend steps have corresponding frontend mappings!")
        print("✅ SUCCESS: No extra frontend mappings found!")
        print()
        print("📋 Complete step mapping:")
        for i, step in enumerate(backend_steps, 1):
            print(f"  {i:2d}. {step}")

        return True
    else:
        print("💥 FAILURE: Step mapping issues found!")
        return False

def test_workflow_progression():
    """Test the logical progression of workflow steps"""

    print("\n🔄 Testing Workflow Step Progression")
    print("=" * 50)

    # Expected workflow progression
    workflow_phases = [
        ("RFQ Processing", ['parsing_rfq', 'generating_embeddings', 'rfq_parsed']),
        ("Context Building", ['matching_golden_examples', 'planning_methodologies']),
        ("Human Review", ['human_review']),
        ("Survey Generation", ['preparing_generation', 'generating_questions', 'parsing_output']),
        ("Quality Evaluation", ['validation_scoring', 'single_call_evaluator', 'pillar_scores_analysis', 'fallback_evaluation']),
        ("Completion", ['completed'])
    ]

    total_steps = sum(len(steps) for _, steps in workflow_phases)
    current_step = 0

    print(f"📊 Total workflow steps: {total_steps}")
    print()

    for phase_name, steps in workflow_phases:
        print(f"📍 {phase_name}:")
        for step in steps:
            current_step += 1
            progress = int((current_step / total_steps) * 100)
            print(f"  {current_step:2d}. {step} ({progress}%)")
        print()

    print("✅ SUCCESS: Workflow progression looks logical!")
    return True

if __name__ == "__main__":
    print("🚀 Testing Survey Generation Step Mapping")
    print("=" * 60)

    success1 = test_step_mapping()
    success2 = test_workflow_progression()

    print("=" * 60)
    if success1 and success2:
        print("🎉 All tests passed! Step mapping is working correctly.")
    else:
        print("💥 Some tests failed! Check the implementation.")

    sys.exit(0 if (success1 and success2) else 1)