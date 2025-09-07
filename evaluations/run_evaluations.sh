#!/bin/bash
# Quick evaluation runner script
# Usage: ./run_evaluations.sh

echo "🚀 Running Survey Engine Evaluations..."
cd evaluations
REPLICATE_API_TOKEN=${REPLICATE_API_TOKEN} python3 evaluation_runner.py
echo "✅ Evaluation complete! Check evaluations/results/ for detailed reports."
