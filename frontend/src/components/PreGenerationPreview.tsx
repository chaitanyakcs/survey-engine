import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { EnhancedRFQRequest } from '../types';

interface PreGenerationPreviewProps {
  rfq: EnhancedRFQRequest;
  onGenerate?: () => void;
  onEdit?: () => void;
}


interface EstimatedMetrics {
  estimated_duration: string;
  estimated_cost: string;
  sample_size_recommendation: string;
  question_count_estimate: string;
  methodology_complexity: 'low' | 'medium' | 'high';
  quality_score: number;
}

export const PreGenerationPreview: React.FC<PreGenerationPreviewProps> = ({
  rfq,
  onGenerate,
  onEdit
}) => {
  const { submitEnhancedRFQ, workflow } = useAppStore();
  const [estimatedMetrics, setEstimatedMetrics] = useState<EstimatedMetrics | null>(null);

  useEffect(() => {
    calculateEstimates();
  }, [rfq]); // calculateEstimates doesn't need to be in deps as it only uses rfq

  const calculateEstimates = () => {
    // Simulate AI-powered estimation logic
    const objectiveCount = rfq.research_objectives?.key_research_questions?.length || 0;
    const hasComplexMethodologies = rfq.methodology?.primary_method && 
      ['conjoint', 'van_westendorp', 'gabor_granger'].includes(rfq.methodology.primary_method);

    let questionEstimate = 15; // Base
    questionEstimate += objectiveCount * 8; // 8 questions per objective
    if (hasComplexMethodologies) questionEstimate += 20;
    // Note: generation_config is not part of EnhancedRFQRequest interface
    // if (rfq.generation_config?.complexity_level === 'advanced') questionEstimate += 15;
    // if (rfq.generation_config?.include_validation_questions) questionEstimate += 10;

    const complexity: 'low' | 'medium' | 'high' =
      hasComplexMethodologies || objectiveCount > 3 ? 'high' :
      objectiveCount > 1 ? 'medium' : 'low';

    const duration = complexity === 'high' ? '25-35 min' :
                    complexity === 'medium' ? '15-25 min' : '10-15 min';

    const costMultiplier = complexity === 'high' ? 1.5 : complexity === 'medium' ? 1.2 : 1.0;
    const baseCost = 1000; // Default base cost
    const estimatedCost = Math.round(baseCost * costMultiplier * 0.75); // $0.75 per response

    const sampleSize = (complexity === 'high' ? '800-1200' : '400-800');

    setEstimatedMetrics({
      estimated_duration: duration,
      estimated_cost: `$${estimatedCost.toLocaleString()}`,
      sample_size_recommendation: typeof sampleSize === 'string' ? sampleSize : `${sampleSize}`,
      question_count_estimate: `${questionEstimate - 5}-${questionEstimate + 5}`,
      methodology_complexity: complexity,
      quality_score: 0.8 // Static reasonable default
    });
  };


  const handleGenerate = async () => {
    if (onGenerate) {
      onGenerate();
    } else {
      await submitEnhancedRFQ(rfq);
    }
  };

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-6xl mx-auto p-6">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Pre-Generation Preview</h1>
              <p className="text-gray-600">Review your research requirements before generation</p>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto">

          {/* Main Preview Panel */}
          <div className="space-y-6">

            {/* RFQ Summary */}
            <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="text-3xl mr-3">📋</span>
                Research Summary
              </h2>

              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Project Title</h3>
                  <p className="text-gray-600">{rfq.title || 'Untitled Research Project'}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Description</h3>
                  <p className="text-gray-600 leading-relaxed">{rfq.description}</p>
                </div>

                {rfq.research_objectives?.key_research_questions && rfq.research_objectives.key_research_questions.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">Research Objectives ({rfq.research_objectives.key_research_questions.length})</h3>
                    <div className="space-y-3">
                      {rfq.research_objectives.key_research_questions.map((objective, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-xl">
                          <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white bg-yellow-500">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{objective}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {rfq.methodology?.primary_method && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">Primary Methodology</h3>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-2 bg-yellow-100 text-yellow-700 rounded-xl text-sm font-medium">
                        {rfq.methodology.primary_method}
                      </span>
                    </div>
                  </div>
                )}

                {rfq.research_objectives?.research_audience && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-2">Target Audience</h3>
                    <p className="text-gray-600">{rfq.research_objectives.research_audience}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Estimated Metrics */}
            {estimatedMetrics && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">📊</span>
                  Estimated Survey Metrics
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-700">Completion Time</span>
                      <span className="text-lg">⏱️</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-900">{estimatedMetrics.estimated_duration}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-700">Estimated Cost</span>
                      <span className="text-lg">💰</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-900">{estimatedMetrics.estimated_cost}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-700">Question Count</span>
                      <span className="text-lg">❓</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-900">{estimatedMetrics.question_count_estimate}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-700">Sample Size</span>
                      <span className="text-lg">👥</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-900">{estimatedMetrics.sample_size_recommendation}</p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-gray-50 rounded-2xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Methodology Complexity</span>
                      <p className="text-lg font-bold text-gray-900 capitalize">{estimatedMetrics.methodology_complexity}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-gray-700">Predicted Quality Score</span>
                      <p className="text-lg font-bold text-gray-900">{Math.round(estimatedMetrics.quality_score * 100)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Generation Actions */}
            <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Ready to Generate?</h2>
                  <p className="text-gray-600">Your research requirements are ready for AI survey generation</p>
                </div>

                <div className="flex space-x-4">
                  <button
                    onClick={onEdit}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors"
                  >
                    Edit Requirements
                  </button>

                  <button
                    onClick={handleGenerate}
                    disabled={isLoading}
                    className={`px-8 py-3 rounded-xl font-semibold transition-all duration-300 ${
                      isLoading
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-yellow-600 to-amber-600 text-white hover:shadow-lg transform hover:scale-105'
                    }`}
                  >
                    {isLoading ? 'Generating...' : 'Generate Survey'}
                  </button>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
};