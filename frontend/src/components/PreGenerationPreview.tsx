import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { EnhancedRFQRequest, ConceptFile } from '../types';
import { PromptPreview } from './PromptPreview';
import { PhotoIcon } from '@heroicons/react/24/outline';

interface PreGenerationPreviewProps {
  rfq: EnhancedRFQRequest;
  onGenerate?: (customPrompt?: string) => void;
  onEdit?: () => void;
  rfqId?: string; // Optional rfq_id for fetching concept files when workflow.rfq_id is not available
}

export const PreGenerationPreview: React.FC<PreGenerationPreviewProps> = ({
  rfq,
  onGenerate,
  onEdit,
  rfqId
}) => {
  const { submitEnhancedRFQ, workflow, fetchConceptFiles } = useAppStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'prompt'>('overview');
  const [customPrompt, setCustomPrompt] = useState<string | null>(null);
  const [conceptFiles, setConceptFiles] = useState<ConceptFile[]>([]);
  
  // Generation configuration state
  const [jsonExamplesMode, setJsonExamplesMode] = useState<'rag_reference' | 'consolidated'>(
    rfq.generation_config?.json_examples_mode || 'consolidated'
  );
  const [pillarRulesDetail, setPillarRulesDetail] = useState<'full' | 'digest' | 'none'>(
    rfq.generation_config?.pillar_rules_detail || 'digest'
  );

  const handlePromptEdited = (editedPrompt: string) => {
    setCustomPrompt(editedPrompt);
    console.log('✅ [PreGenerationPreview] Custom prompt saved:', editedPrompt.length, 'chars');
  };

  const handleGenerate = async () => {
    // Merge generation_config into rfq before submission
    const rfqWithConfig: EnhancedRFQRequest = {
      ...rfq,
      generation_config: {
        json_examples_mode: jsonExamplesMode,
        pillar_rules_detail: pillarRulesDetail
      }
    };
    
    if (onGenerate) {
      onGenerate(customPrompt || undefined);
    } else {
      await submitEnhancedRFQ(rfqWithConfig, customPrompt || undefined);
    }
  };

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  // Fetch concept files when preview is shown
  useEffect(() => {
    const loadConceptFiles = async () => {
      // Try multiple sources for rfq_id: prop > workflow > rfq metadata
      const effectiveRfqId = rfqId || workflow.rfq_id || (rfq as any).rfq_id;
      
      if (effectiveRfqId && fetchConceptFiles) {
        try {
          console.log('🔍 [PreGenerationPreview] Fetching concept files for rfq_id:', effectiveRfqId);
          console.log('🔍 [PreGenerationPreview] rfq_id sources:', {
            prop: rfqId,
            workflow: workflow.rfq_id,
            rfq_metadata: (rfq as any).rfq_id,
            effective: effectiveRfqId
          });
          const files = await fetchConceptFiles(effectiveRfqId);
          console.log('✅ [PreGenerationPreview] Loaded concept files:', files.length);
          setConceptFiles(files);
        } catch (error) {
          console.error('❌ [PreGenerationPreview] Failed to load concept files:', error);
          setConceptFiles([]);
        }
      } else {
        console.log('⚠️ [PreGenerationPreview] No rfq_id available for concept files. Sources:', {
          prop: rfqId,
          workflow: workflow.rfq_id,
          rfq_metadata: (rfq as any).rfq_id
        });
        setConceptFiles([]);
      }
    };
    loadConceptFiles();
  }, [rfqId, workflow.rfq_id, fetchConceptFiles, rfq]);

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-6xl mx-auto p-6">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {onGenerate || onEdit ? 'Pre-Generation Preview' : 'RFQ Preview'}
              </h1>
              <p className="text-gray-600">
                {onGenerate || onEdit ? 'Review your research requirements before generation' : 'Original request for quotation that generated this survey'}
              </p>
            </div>
          </div>

          {/* Tab Navigation with Action Buttons - Only show if onGenerate/onEdit are provided */}
          {(onGenerate || onEdit) && (
            <div className="border-b border-gray-200">
              <div className="flex items-center justify-between">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                      activeTab === 'overview'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <span className="text-xl mr-2">📋</span>
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('prompt')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                      activeTab === 'prompt'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <span className="text-xl mr-2">🤖</span>
                    AI Prompt Preview
                  </button>
                </nav>
                
                {/* Action Buttons */}
                <div className="flex items-center space-x-3">
                  <button
                    onClick={onEdit}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                  >
                    Edit RFQ
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={isLoading}
                    className={`px-6 py-2 rounded-lg font-semibold transition-all duration-300 text-sm ${
                      isLoading
                        ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                        : 'bg-gradient-to-r from-yellow-600 to-amber-600 text-white hover:shadow-lg transform hover:scale-105'
                    }`}
                  >
                    {isLoading ? 'Generating...' : customPrompt ? 'Generate with Custom Prompt' : 'Generate Survey'}
                  </button>
                  {customPrompt && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium flex items-center">
                      <span className="mr-1">✏️</span>
                      Custom Prompt Active
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Tab Content */}
          {(activeTab === 'overview' || (!onGenerate && !onEdit)) && (
            <div className="space-y-6">

            {/* Generation Configuration - Hidden (defaults work) */}
            {/* {(onGenerate || onEdit) && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">⚙️</span>
                  Generation Configuration
                </h2>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-lg font-semibold text-gray-800">
                        JSON Examples Mode
                      </label>
                      <button
                        onClick={() => setJsonExamplesMode(jsonExamplesMode === 'consolidated' ? 'rag_reference' : 'consolidated')}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          jsonExamplesMode === 'consolidated' ? 'bg-blue-600' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            jsonExamplesMode === 'consolidated' ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                    <div className="text-sm text-gray-600 space-y-2">
                      {jsonExamplesMode === 'consolidated' ? (
                        <>
                          <p className="font-medium text-blue-700">✓ Consolidated Examples (ON)</p>
                          <p>Full JSON schema example included for maximum clarity. ~195 lines.</p>
                        </>
                      ) : (
                        <>
                          <p className="font-medium text-purple-700">✓ RAG Reference (OFF)</p>
                          <p>Explicit guidance to use RAG context for JSON structure. ~75 lines (68% smaller).</p>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-lg font-semibold text-gray-800">
                      Pillar Rules Detail Level
                    </label>
                    <select
                      value={pillarRulesDetail}
                      onChange={(e) => setPillarRulesDetail(e.target.value as 'full' | 'digest' | 'none')}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    >
                      <option value="full">Full - All rules with details</option>
                      <option value="digest">Digest - Core rules only (Recommended)</option>
                      <option value="none">None - No pillar rules</option>
                    </select>
                    <div className="text-sm text-gray-600">
                      {pillarRulesDetail === 'full' && (
                        <p>All pillar rules with priority indicators and implementation notes.</p>
                      )}
                      {pillarRulesDetail === 'digest' && (
                        <p className="text-green-700 font-medium">✓ Recommended: Core rules only for balanced prompt size.</p>
                      )}
                      {pillarRulesDetail === 'none' && (
                        <p>No pillar rules included in prompt.</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <span className="font-medium">💡 Tip:</span> Use RAG Reference mode to reduce prompt size when you trust the quality of retrieved golden examples. 
                    Consolidated Examples mode provides maximum guidance for complex RFQs.
                  </p>
                </div>
              </div>
            )} */}

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

                  {rfq.business_context.business_problem_and_objective && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Business Problem & Objective</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.business_problem_and_objective}</p>
                    </div>
                  )}

                  {rfq.business_context.sample_requirements && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Sample Requirements</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.business_context.sample_requirements}</p>
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

                  {/* Enhanced Research Objectives Fields - REMOVED for simplification */}
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
                  {((rfq.methodology.selected_methodologies && rfq.methodology.selected_methodologies.length > 0) || rfq.methodology.primary_method) && (
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-3">Selected Methodologies</h3>
                      <div className="flex flex-wrap gap-2">
                        {(rfq.methodology.selected_methodologies || (rfq.methodology.primary_method ? [rfq.methodology.primary_method] : [])).map((method) => (
                          <span key={method} className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-xl text-sm font-medium">
                            {method.replace('_', ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {rfq.methodology.stimuli_details && (
                    <div className="lg:col-span-2">
                      <h3 className="font-semibold text-gray-800 mb-2">Stimuli Details</h3>
                      <p className="text-gray-600 leading-relaxed">{rfq.methodology.stimuli_details}</p>
                    </div>
                  )}

                  {/* Enhanced Methodology Fields - REMOVED for simplification */}
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

                  {/* Must-Have Questions - REMOVED for simplification */}

                  {(rfq.survey_requirements.completion_time_target || rfq.survey_requirements.device_compatibility) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

                  {/* Compliance Requirements - REMOVED for simplification */}

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

                {/* QNR Label Requirements Preview */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <span className="text-xl mr-2">🎯</span>
                    Quality Requirements Preview
                  </h3>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Essential Requirements - Always shown */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <span className="text-green-600 text-lg mr-2">✅</span>
                        <h4 className="font-semibold text-green-900">Essential Requirements</h4>
                      </div>
                      <div className="space-y-2">
                        {[
                          'Recent participation check',
                          'Conflict of interest screening', 
                          'Basic demographics',
                          'Category usage qualification'
                        ].map((req, index) => (
                          <div key={index} className="flex items-center text-sm text-green-800">
                            <span className="text-green-600 mr-2">•</span>
                            {req}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Conditional Requirements - Dynamic */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <span className="text-blue-600 text-lg mr-2">⚠️</span>
                        <h4 className="font-semibold text-blue-900">Smart Requirements</h4>
                        <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Auto-detected</span>
                      </div>
                      <div className="space-y-2">
                        {/* Brand Study Requirements */}
                        {(rfq.research_objectives?.key_research_questions?.some((obj: string) => 
                          obj.toLowerCase().includes('brand') || 
                          obj.toLowerCase().includes('awareness') ||
                          obj.toLowerCase().includes('recall')
                        ) || rfq.business_context?.company_product_background?.toLowerCase().includes('consumer')) && (
                          <>
                            <div className="text-xs font-medium text-blue-700 mb-1">Brand Study:</div>
                            <div className="text-sm text-blue-800">• Unaided brand recall • Awareness funnel • Product satisfaction</div>
                          </>
                        )}

                        {/* Concept Testing Requirements */}
                        {rfq.research_objectives?.key_research_questions?.some((obj: string) => 
                          obj.toLowerCase().includes('concept') || 
                          obj.toLowerCase().includes('testing') ||
                          obj.toLowerCase().includes('evaluation')
                        ) && (
                          <>
                            <div className="text-xs font-medium text-blue-700 mb-1">Concept Testing:</div>
                            <div className="text-sm text-blue-800">• Concept introduction • Overall impression • Purchase likelihood</div>
                          </>
                        )}

                        {/* Van Westendorp Requirements */}
                        {(rfq.methodology?.selected_methodologies?.includes('van_westendorp') || rfq.methodology?.primary_method === 'van_westendorp') && (
                          <>
                            <div className="text-xs font-medium text-orange-700 mb-1">Van Westendorp Pricing:</div>
                            <div className="text-sm text-orange-800">• 4 price sensitivity questions (critical)</div>
                          </>
                        )}

                        {/* Gabor Granger Requirements */}
                        {(rfq.methodology?.selected_methodologies?.includes('gabor_granger') || rfq.methodology?.primary_method === 'gabor_granger') && (
                          <>
                            <div className="text-xs font-medium text-purple-700 mb-1">Gabor Granger Pricing:</div>
                            <div className="text-sm text-purple-800">• Sequential price acceptance questions</div>
                          </>
                        )}

                        {/* Default message if no conditional requirements */}
                        {!rfq.research_objectives?.key_research_questions?.some((obj: string) => 
                          obj.toLowerCase().includes('brand') || 
                          obj.toLowerCase().includes('awareness') ||
                          obj.toLowerCase().includes('recall') ||
                          obj.toLowerCase().includes('concept') || 
                          obj.toLowerCase().includes('testing') ||
                          obj.toLowerCase().includes('evaluation')
                        ) && !rfq.business_context?.company_product_background?.toLowerCase().includes('consumer') &&
                        !rfq.methodology?.selected_methodologies?.includes('van_westendorp') &&
                        !rfq.methodology?.selected_methodologies?.includes('gabor_granger') &&
                        rfq.methodology?.primary_method !== 'van_westendorp' &&
                        rfq.methodology?.primary_method !== 'gabor_granger' && (
                          <div className="text-sm text-gray-600 italic">No additional requirements detected</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Quality Assurance Note */}
                  <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <div className="flex items-start space-x-2">
                      <div className="text-gray-500 text-sm">ℹ️</div>
                      <div className="text-sm text-gray-700">
                        <span className="font-medium">Quality Assurance:</span> Missing requirements will be flagged but won't block generation. 
                        Aim for 85%+ compliance for optimal survey quality.
                      </div>
                    </div>
                  </div>
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

            {/* Advanced Classification */}
            {rfq.advanced_classification && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🏭</span>
                  Advanced Classification
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {rfq.advanced_classification.industry_classification && (
                    <div className="p-4 bg-blue-50 rounded-xl">
                      <h4 className="font-semibold text-blue-800 mb-1">Industry</h4>
                      <p className="text-blue-700 text-sm">{rfq.advanced_classification.industry_classification.replace('_', ' ').toUpperCase()}</p>
                    </div>
                  )}
                  {rfq.advanced_classification.respondent_classification && (
                    <div className="p-4 bg-green-50 rounded-xl">
                      <h4 className="font-semibold text-green-800 mb-1">Respondent Type</h4>
                      <p className="text-green-700 text-sm">{rfq.advanced_classification.respondent_classification}</p>
                    </div>
                  )}
                  {rfq.advanced_classification.methodology_tags && rfq.advanced_classification.methodology_tags.length > 0 && (
                    <div className="p-4 bg-purple-50 rounded-xl">
                      <h4 className="font-semibold text-purple-800 mb-1">Methodology Tags</h4>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rfq.advanced_classification.methodology_tags.map((tag, index) => (
                          <span key={index} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                            {tag.replace('_', ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Compliance Requirements - REMOVED for simplification */}
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

            {/* Concept Files */}
            {conceptFiles.length > 0 && (
              <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <PhotoIcon className="w-8 h-8 mr-3 text-purple-600" />
                  Concept Files
                </h2>
                <p className="text-gray-600 mb-4">
                  These files will be included in Section 4 (Concept Exposure) of the generated survey.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {conceptFiles
                    .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
                    .map((file) => {
                      const isImage = file.content_type?.startsWith('image/');
                      return (
                        <div
                          key={file.id}
                          className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                        >
                          {isImage ? (
                            <img
                              src={file.file_url}
                              alt={file.original_filename || file.filename}
                              className="w-full h-32 object-cover"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/placeholder-image.png';
                              }}
                            />
                          ) : (
                            <div className="w-full h-32 bg-gray-100 flex items-center justify-center">
                              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                          )}
                          <div className="p-2">
                            <p className="text-xs font-medium text-gray-900 truncate" title={file.original_filename || file.filename}>
                              {file.original_filename || file.filename}
                            </p>
                            {file.content_type && (
                              <p className="text-xs text-gray-500 mt-1">{file.content_type}</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}

            </div>
          )}

          {activeTab === 'prompt' && (onGenerate || onEdit) && (
            <div className="space-y-6">
              <PromptPreview 
                key={`${jsonExamplesMode}-${pillarRulesDetail}`}
                rfq={{
                  ...rfq,
                  generation_config: {
                    json_examples_mode: jsonExamplesMode,
                    pillar_rules_detail: pillarRulesDetail
                  }
                }} 
                onPromptEdited={handlePromptEdited} 
              />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};