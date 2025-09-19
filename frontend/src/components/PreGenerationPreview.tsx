import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { EnhancedRFQRequest, RFQQualityAssessment } from '../types';

interface PreGenerationPreviewProps {
  rfq: EnhancedRFQRequest;
  onGenerate?: () => void;
  onEdit?: () => void;
}

interface ConfidenceIndicator {
  id: string;
  label: string;
  score: number;
  description: string;
  icon: string;
  recommendations?: string[];
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
  const { rfqAssessment, assessRfqQuality, submitEnhancedRFQ, workflow } = useAppStore();
  const [estimatedMetrics, setEstimatedMetrics] = useState<EstimatedMetrics | null>(null);
  const [confidenceIndicators, setConfidenceIndicators] = useState<ConfidenceIndicator[]>([]);
  const [showDetailedPreview, setShowDetailedPreview] = useState(false);

  useEffect(() => {
    calculateEstimates();
    generateConfidenceIndicators();
  }, [rfq, rfqAssessment]);

  const calculateEstimates = () => {
    // Simulate AI-powered estimation logic
    const objectiveCount = rfq.objectives?.length || 0;
    const hasComplexMethodologies = rfq.methodologies?.preferred?.some(m =>
      ['Choice Conjoint', 'Van Westendorp PSM', 'MaxDiff'].includes(m)
    ) || false;

    let questionEstimate = 15; // Base
    questionEstimate += objectiveCount * 8; // 8 questions per objective
    if (hasComplexMethodologies) questionEstimate += 20;
    if (rfq.generation_config?.complexity_level === 'advanced') questionEstimate += 15;
    if (rfq.generation_config?.include_validation_questions) questionEstimate += 10;

    const complexity: 'low' | 'medium' | 'high' =
      hasComplexMethodologies || objectiveCount > 3 ? 'high' :
      objectiveCount > 1 ? 'medium' : 'low';

    const duration = complexity === 'high' ? '25-35 min' :
                    complexity === 'medium' ? '15-25 min' : '10-15 min';

    const costMultiplier = complexity === 'high' ? 1.5 : complexity === 'medium' ? 1.2 : 1.0;
    const baseCost = rfq.target_audience?.size_estimate || 1000;
    const estimatedCost = Math.round(baseCost * costMultiplier * 0.75); // $0.75 per response

    const sampleSize = rfq.constraints?.find(c => c.type === 'sample_size')?.value ||
                      (complexity === 'high' ? '800-1200' : '400-800');

    setEstimatedMetrics({
      estimated_duration: duration,
      estimated_cost: `$${estimatedCost.toLocaleString()}`,
      sample_size_recommendation: typeof sampleSize === 'string' ? sampleSize : `${sampleSize}`,
      question_count_estimate: `${questionEstimate - 5}-${questionEstimate + 5}`,
      methodology_complexity: complexity,
      quality_score: rfqAssessment?.overall_score || 0.7
    });
  };

  const generateConfidenceIndicators = () => {
    const indicators: ConfidenceIndicator[] = [
      {
        id: 'objectives_clarity',
        label: 'Objectives Clarity',
        score: rfqAssessment?.confidence_indicators.objectives_clear ? 0.9 : 0.4,
        description: 'How well-defined and measurable your research objectives are',
        icon: '🎯',
        recommendations: !rfqAssessment?.confidence_indicators.objectives_clear ?
          ['Define specific, measurable objectives', 'Include success criteria for each objective'] : undefined
      },
      {
        id: 'target_definition',
        label: 'Target Audience',
        score: rfqAssessment?.confidence_indicators.target_defined ? 0.95 : 0.3,
        description: 'Specificity and reachability of your target audience',
        icon: '👥',
        recommendations: !rfqAssessment?.confidence_indicators.target_defined ?
          ['Specify demographic criteria', 'Define audience size and accessibility'] : undefined
      },
      {
        id: 'methodology_alignment',
        label: 'Methodology Fit',
        score: rfqAssessment?.confidence_indicators.methodology_appropriate ? 0.85 : 0.5,
        description: 'Alignment between chosen methodologies and research objectives',
        icon: '🔬',
        recommendations: !rfqAssessment?.confidence_indicators.methodology_appropriate ?
          ['Select methodologies that match your objectives', 'Consider proven approaches for your research goals'] : undefined
      },
      {
        id: 'project_feasibility',
        label: 'Project Feasibility',
        score: rfqAssessment?.confidence_indicators.constraints_realistic ? 0.8 : 0.6,
        description: 'Realistic timeline, budget, and resource constraints',
        icon: '⚖️',
        recommendations: !rfqAssessment?.confidence_indicators.constraints_realistic ?
          ['Set realistic timeline constraints', 'Define clear budget parameters'] : undefined
      },
      {
        id: 'content_completeness',
        label: 'Content Completeness',
        score: (rfqAssessment?.completeness_score || 0.5) * 1.0,
        description: 'Completeness of research requirements and context',
        icon: '📋',
        recommendations: (rfqAssessment?.completeness_score || 0) < 0.8 ?
          ['Provide more business context', 'Complete all required sections'] : undefined
      }
    ];

    setConfidenceIndicators(indicators);
  };

  const getOverallConfidence = () => {
    const avgScore = confidenceIndicators.reduce((sum, indicator) => sum + indicator.score, 0) / confidenceIndicators.length;
    return avgScore;
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'yellow';
    if (score >= 0.4) return 'orange';
    return 'red';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Good Confidence';
    if (score >= 0.4) return 'Fair Confidence';
    return 'Low Confidence';
  };

  const handleGenerate = async () => {
    if (onGenerate) {
      onGenerate();
    } else {
      await submitEnhancedRFQ(rfq);
    }
  };

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';
  const overallConfidence = getOverallConfidence();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto p-6">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Pre-Generation Preview</h1>
              <p className="text-gray-600">Review your research requirements and generation confidence</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-500">Overall Confidence</p>
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded-full bg-${getConfidenceColor(overallConfidence)}-400`}></div>
                  <span className="font-semibold">{Math.round(overallConfidence * 100)}%</span>
                  <span className="text-sm text-gray-500">{getConfidenceLabel(overallConfidence)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* Main Preview Panel */}
          <div className="xl:col-span-2 space-y-6">

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

                {rfq.objectives && rfq.objectives.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">Research Objectives ({rfq.objectives.length})</h3>
                    <div className="space-y-3">
                      {rfq.objectives.map((objective, index) => (
                        <div key={objective.id} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-xl">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                            objective.priority === 'high' ? 'bg-red-500' :
                            objective.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                          }`}>
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{objective.title}</p>
                            <p className="text-sm text-gray-600 mt-1">{objective.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {rfq.methodologies?.preferred && rfq.methodologies.preferred.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">Preferred Methodologies</h3>
                    <div className="flex flex-wrap gap-2">
                      {rfq.methodologies.preferred.map((method) => (
                        <span key={method} className="px-3 py-2 bg-purple-100 text-purple-700 rounded-xl text-sm font-medium">
                          {method}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {rfq.target_audience?.primary_segment && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-2">Target Audience</h3>
                    <p className="text-gray-600">{rfq.target_audience.primary_segment}</p>
                    {rfq.target_audience.size_estimate && (
                      <p className="text-sm text-gray-500 mt-1">Estimated size: {rfq.target_audience.size_estimate} participants</p>
                    )}
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
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-blue-700">Completion Time</span>
                      <span className="text-lg">⏱️</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-900">{estimatedMetrics.estimated_duration}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-green-700">Estimated Cost</span>
                      <span className="text-lg">💰</span>
                    </div>
                    <p className="text-2xl font-bold text-green-900">{estimatedMetrics.estimated_cost}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-purple-700">Question Count</span>
                      <span className="text-lg">❓</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-900">{estimatedMetrics.question_count_estimate}</p>
                  </div>

                  <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-orange-700">Sample Size</span>
                      <span className="text-lg">👥</span>
                    </div>
                    <p className="text-2xl font-bold text-orange-900">{estimatedMetrics.sample_size_recommendation}</p>
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
                    disabled={isLoading || overallConfidence < 0.3}
                    className={`px-8 py-3 rounded-xl font-semibold transition-all duration-300 ${
                      isLoading || overallConfidence < 0.3
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg transform hover:scale-105'
                    }`}
                  >
                    {isLoading ? 'Generating...' : 'Generate Survey'}
                  </button>
                </div>
              </div>

              {overallConfidence < 0.3 && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-sm text-red-700">
                    ⚠️ Confidence is too low for reliable survey generation. Please address the recommendations in the confidence panel.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Confidence Indicators Panel */}
          <div className="xl:col-span-1">
            <div className="bg-white/60 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 p-6 sticky top-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl mr-3 flex items-center justify-center">
                  <span className="text-white">📈</span>
                </div>
                Confidence Indicators
              </h3>

              <div className="space-y-4">
                {confidenceIndicators.map((indicator) => (
                  <div key={indicator.id} className="p-4 bg-gradient-to-r from-gray-50 to-white rounded-2xl border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{indicator.icon}</span>
                        <span className="font-semibold text-gray-800">{indicator.label}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full bg-${getConfidenceColor(indicator.score)}-400`}></div>
                        <span className="text-sm font-medium">{Math.round(indicator.score * 100)}%</span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-600 mb-3">{indicator.description}</p>

                    {/* Progress bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                      <div
                        className={`h-2 rounded-full bg-${getConfidenceColor(indicator.score)}-400`}
                        style={{ width: `${indicator.score * 100}%` }}
                      ></div>
                    </div>

                    {indicator.recommendations && indicator.recommendations.length > 0 && (
                      <div className="space-y-1">
                        {indicator.recommendations.map((rec, index) => (
                          <p key={index} className="text-xs text-orange-600 flex items-start">
                            <span className="mr-2">•</span>
                            <span>{rec}</span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Overall Score */}
              <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-100">
                <div className="text-center">
                  <p className="text-sm font-medium text-blue-700 mb-2">Overall Confidence</p>
                  <div className="flex items-center justify-center space-x-3">
                    <div className={`w-6 h-6 rounded-full bg-${getConfidenceColor(overallConfidence)}-400`}></div>
                    <span className="text-3xl font-bold text-blue-900">{Math.round(overallConfidence * 100)}%</span>
                  </div>
                  <p className="text-sm text-blue-600 mt-2">{getConfidenceLabel(overallConfidence)}</p>
                </div>
              </div>

              {/* AI Recommendations */}
              {rfqAssessment?.recommendations && rfqAssessment.recommendations.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">AI Recommendations</h4>
                  <div className="space-y-2">
                    {rfqAssessment.recommendations.map((rec, index) => (
                      <div key={index} className="p-3 bg-yellow-50 rounded-xl border border-yellow-100">
                        <p className="text-sm text-yellow-800 flex items-start">
                          <span className="mr-2">💡</span>
                          <span>{rec}</span>
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};