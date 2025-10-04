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

        <div className="max-w-6xl mx-auto">

          {/* Main Preview Panel */}
          <div className="space-y-6">

            {/* Project Overview */}
            <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="text-3xl mr-3">📋</span>
                Project Overview
              </h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Project Title</h3>
                  <p className="text-gray-600">{rfq.title || 'Untitled Research Project'}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Description</h3>
                  <p className="text-gray-600 leading-relaxed">{rfq.description}</p>
                </div>
              </div>
            </div>

            {/* Business Context */}
            {rfq.business_context && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🏢</span>
                  Business Context
                </h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {rfq.business_context.company_product_background && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Company & Product Background</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.company_product_background}</p>
                    </div>
                  )}

                  {rfq.business_context.business_problem && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Business Problem</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.business_problem}</p>
                    </div>
                  )}

                  {rfq.business_context.business_objective && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Business Objective</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.business_objective}</p>
                    </div>
                  )}

                  {rfq.business_context.stakeholder_requirements && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Stakeholder Requirements</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.stakeholder_requirements}</p>
                    </div>
                  )}

                  {rfq.business_context.decision_criteria && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Decision Criteria</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.decision_criteria}</p>
                    </div>
                  )}

                  {(rfq.business_context.budget_range || rfq.business_context.timeline_constraints) && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-3">Project Constraints</h3>
                      <div className="flex flex-wrap gap-4">
                        {rfq.business_context.budget_range && (
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium text-gray-700">Budget:</span>
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                              {rfq.business_context.budget_range.replace('_', ' - ').toUpperCase()}
                            </span>
                          </div>
                        )}
                        {rfq.business_context.timeline_constraints && (
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium text-gray-700">Timeline:</span>
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium capitalize">
                              {rfq.business_context.timeline_constraints}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Research Objectives */}
            {rfq.research_objectives && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🎯</span>
                  Research Objectives
                </h2>

                <div className="space-y-6">
                  {rfq.research_objectives.research_audience && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Target Audience</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.research_objectives.research_audience}</p>
                    </div>
                  )}

                  {rfq.research_objectives.success_criteria && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Success Criteria</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.research_objectives.success_criteria}</p>
                    </div>
                  )}

                  {rfq.research_objectives.key_research_questions && rfq.research_objectives.key_research_questions.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Key Research Questions ({rfq.research_objectives.key_research_questions.length})</h3>
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

                  {(rfq.research_objectives.success_metrics || rfq.research_objectives.validation_requirements || rfq.research_objectives.measurement_approach) && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      {rfq.research_objectives.success_metrics && (
                        <div className="p-4 bg-blue-50 rounded-xl">
                          <h4 className="font-semibold text-blue-800 mb-2">Success Metrics</h4>
                          <p className="text-blue-700 text-sm">{rfq.research_objectives.success_metrics}</p>
                        </div>
                      )}
                      {rfq.research_objectives.validation_requirements && (
                        <div className="p-4 bg-green-50 rounded-xl">
                          <h4 className="font-semibold text-green-800 mb-2">Validation Requirements</h4>
                          <p className="text-green-700 text-sm">{rfq.research_objectives.validation_requirements}</p>
                        </div>
                      )}
                      {rfq.research_objectives.measurement_approach && (
                        <div className="p-4 bg-purple-50 rounded-xl">
                          <h4 className="font-semibold text-purple-800 mb-2">Measurement Approach</h4>
                          <p className="text-purple-700 text-sm capitalize">
                            {rfq.research_objectives.measurement_approach.replace('_', ' ')}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Methodology */}
            {rfq.methodology && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🔬</span>
                  Methodology
                </h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {rfq.methodology.primary_method && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Primary Method</h3>
                      <div className="flex flex-wrap gap-2">
                        <span className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-xl text-sm font-medium">
                          {rfq.methodology.primary_method.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  )}

                  {rfq.methodology.sample_size_target && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Sample Size Target</h3>
                      <p className="text-gray-600">{rfq.methodology.sample_size_target}</p>
                    </div>
                  )}

                  {rfq.methodology.complexity_level && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Complexity Level</h3>
                      <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-lg text-sm font-medium capitalize">
                        {rfq.methodology.complexity_level}
                      </span>
                    </div>
                  )}

                  {rfq.methodology.stimuli_details && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-2">Stimuli Details</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.methodology.stimuli_details}</p>
                    </div>
                  )}

                  {rfq.methodology.methodology_requirements && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-2">Methodology Requirements</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.methodology.methodology_requirements}</p>
                    </div>
                  )}

                  {rfq.methodology.required_methodologies && rfq.methodology.required_methodologies.length > 0 && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-3">Required Methodologies</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.methodology.required_methodologies.map((method, index) => (
                          <span key={index} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                            {method.replace('_', ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Survey Requirements */}
            {rfq.survey_requirements && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">📝</span>
                  Survey Requirements
                </h2>

                <div className="space-y-6">
                  {rfq.survey_requirements.sample_plan && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Sample Plan</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.survey_requirements.sample_plan}</p>
                    </div>
                  )}

                  {rfq.survey_requirements.must_have_questions && rfq.survey_requirements.must_have_questions.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Must-Have Questions ({rfq.survey_requirements.must_have_questions.length})</h3>
                      <div className="space-y-2">
                        {rfq.survey_requirements.must_have_questions.map((question, index) => (
                          <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded-xl">
                            <div className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white bg-green-500">
                              {index + 1}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-gray-900 text-sm">{question}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {(rfq.survey_requirements.completion_time_target || rfq.survey_requirements.device_compatibility || rfq.survey_requirements.accessibility_requirements || rfq.survey_requirements.data_quality_requirements) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {rfq.survey_requirements.completion_time_target && (
                        <div className="p-4 bg-blue-50 rounded-xl">
                          <h4 className="font-semibold text-blue-800 mb-1">Completion Time</h4>
                          <p className="text-blue-700 text-sm">
                            {rfq.survey_requirements.completion_time_target.replace('_', ' - ').toUpperCase()}
                          </p>
                        </div>
                      )}
                      {rfq.survey_requirements.device_compatibility && (
                        <div className="p-4 bg-green-50 rounded-xl">
                          <h4 className="font-semibold text-green-800 mb-1">Device Compatibility</h4>
                          <p className="text-green-700 text-sm capitalize">
                            {rfq.survey_requirements.device_compatibility.replace('_', ' ')}
                          </p>
                        </div>
                      )}
                      {rfq.survey_requirements.accessibility_requirements && (
                        <div className="p-4 bg-purple-50 rounded-xl">
                          <h4 className="font-semibold text-purple-800 mb-1">Accessibility</h4>
                          <p className="text-purple-700 text-sm capitalize">
                            {rfq.survey_requirements.accessibility_requirements}
                          </p>
                        </div>
                      )}
                      {rfq.survey_requirements.data_quality_requirements && (
                        <div className="p-4 bg-orange-50 rounded-xl">
                          <h4 className="font-semibold text-orange-800 mb-1">Data Quality</h4>
                          <p className="text-orange-700 text-sm capitalize">
                            {rfq.survey_requirements.data_quality_requirements}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {rfq.survey_requirements.screener_requirements && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Screener Requirements</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.survey_requirements.screener_requirements}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Advanced Classification */}
            {rfq.advanced_classification && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🏷️</span>
                  Advanced Classification
                </h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {rfq.advanced_classification.industry_classification && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Industry Classification</h3>
                      <p className="text-gray-600">{rfq.advanced_classification.industry_classification}</p>
                    </div>
                  )}

                  {rfq.advanced_classification.respondent_classification && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Respondent Classification</h3>
                      <p className="text-gray-600">{rfq.advanced_classification.respondent_classification}</p>
                    </div>
                  )}

                  {rfq.advanced_classification.methodology_tags && rfq.advanced_classification.methodology_tags.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Methodology Tags</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.advanced_classification.methodology_tags.map((tag, index) => (
                          <span key={index} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {rfq.advanced_classification.compliance_requirements && rfq.advanced_classification.compliance_requirements.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Compliance Requirements</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.advanced_classification.compliance_requirements.map((req, index) => (
                          <span key={index} className="px-3 py-1 bg-red-100 text-red-700 rounded-lg text-sm font-medium">
                            {req}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {rfq.advanced_classification.target_countries && rfq.advanced_classification.target_countries.length > 0 && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-3">Target Countries</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.advanced_classification.target_countries.map((country, index) => (
                          <span key={index} className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                            {country}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {rfq.advanced_classification.healthcare_specifics && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-3">Healthcare Specifics</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {rfq.advanced_classification.healthcare_specifics.medical_conditions_general !== undefined && (
                          <div className="p-3 bg-blue-50 rounded-lg">
                            <span className="text-sm font-medium text-blue-800">Medical Conditions (General): </span>
                            <span className="text-blue-700">{rfq.advanced_classification.healthcare_specifics.medical_conditions_general ? 'Yes' : 'No'}</span>
                          </div>
                        )}
                        {rfq.advanced_classification.healthcare_specifics.medical_conditions_study !== undefined && (
                          <div className="p-3 bg-green-50 rounded-lg">
                            <span className="text-sm font-medium text-green-800">Medical Conditions (Study): </span>
                            <span className="text-green-700">{rfq.advanced_classification.healthcare_specifics.medical_conditions_study ? 'Yes' : 'No'}</span>
                          </div>
                        )}
                        {rfq.advanced_classification.healthcare_specifics.patient_requirements && (
                          <div className="p-3 bg-purple-50 rounded-lg">
                            <span className="text-sm font-medium text-purple-800">Patient Requirements: </span>
                            <span className="text-purple-700">{rfq.advanced_classification.healthcare_specifics.patient_requirements}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Survey Structure */}
            {rfq.survey_structure && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">📊</span>
                  Survey Structure
                </h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {rfq.survey_structure.qnr_sections && rfq.survey_structure.qnr_sections.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">QNR Sections ({rfq.survey_structure.qnr_sections.length})</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.survey_structure.qnr_sections.map((section, index) => (
                          <span key={index} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                            {section.replace('_', ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {rfq.survey_structure.text_requirements && rfq.survey_structure.text_requirements.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Text Requirements ({rfq.survey_structure.text_requirements.length})</h3>
                      <div className="flex flex-wrap gap-2">
                        {rfq.survey_structure.text_requirements.map((req, index) => (
                          <span key={index} className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                            {req.replace('_', ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Survey Logic Requirements */}
            {rfq.survey_logic && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">⚙️</span>
                  Survey Logic Requirements
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {rfq.survey_logic.requires_piping_logic !== undefined && (
                    <div className="p-4 bg-blue-50 rounded-xl">
                      <h4 className="font-semibold text-blue-800 mb-1">Piping Logic</h4>
                      <p className="text-blue-700 text-sm">{rfq.survey_logic.requires_piping_logic ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.survey_logic.requires_sampling_logic !== undefined && (
                    <div className="p-4 bg-green-50 rounded-xl">
                      <h4 className="font-semibold text-green-800 mb-1">Sampling Logic</h4>
                      <p className="text-green-700 text-sm">{rfq.survey_logic.requires_sampling_logic ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.survey_logic.requires_screener_logic !== undefined && (
                    <div className="p-4 bg-purple-50 rounded-xl">
                      <h4 className="font-semibold text-purple-800 mb-1">Screener Logic</h4>
                      <p className="text-purple-700 text-sm">{rfq.survey_logic.requires_screener_logic ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.survey_logic.custom_logic_requirements && (
                    <div className="p-4 bg-orange-50 rounded-xl">
                      <h4 className="font-semibold text-orange-800 mb-1">Custom Logic</h4>
                      <p className="text-orange-700 text-sm">{rfq.survey_logic.custom_logic_requirements}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Brand Usage Requirements */}
            {rfq.brand_usage_requirements && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🏷️</span>
                  Brand Usage Requirements
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {rfq.brand_usage_requirements.brand_recall_required !== undefined && (
                    <div className="p-4 bg-blue-50 rounded-xl">
                      <h4 className="font-semibold text-blue-800 mb-1">Brand Recall</h4>
                      <p className="text-blue-700 text-sm">{rfq.brand_usage_requirements.brand_recall_required ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.brand_usage_requirements.brand_awareness_funnel !== undefined && (
                    <div className="p-4 bg-green-50 rounded-xl">
                      <h4 className="font-semibold text-green-800 mb-1">Awareness Funnel</h4>
                      <p className="text-green-700 text-sm">{rfq.brand_usage_requirements.brand_awareness_funnel ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.brand_usage_requirements.brand_product_satisfaction !== undefined && (
                    <div className="p-4 bg-purple-50 rounded-xl">
                      <h4 className="font-semibold text-purple-800 mb-1">Product Satisfaction</h4>
                      <p className="text-purple-700 text-sm">{rfq.brand_usage_requirements.brand_product_satisfaction ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                  {rfq.brand_usage_requirements.usage_frequency_tracking !== undefined && (
                    <div className="p-4 bg-orange-50 rounded-xl">
                      <h4 className="font-semibold text-orange-800 mb-1">Usage Frequency</h4>
                      <p className="text-orange-700 text-sm">{rfq.brand_usage_requirements.usage_frequency_tracking ? 'Required' : 'Not Required'}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Rules and Definitions */}
            {rfq.rules_and_definitions && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">📚</span>
                  Rules and Definitions
                </h2>

                <div>
                  <p className="text-gray-600 leading-relaxed">{rfq.rules_and_definitions}</p>
                </div>
              </div>
            )}

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