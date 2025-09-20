import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import {
  EnhancedRFQRequest,
  DocumentAnalysisResponse
} from '../types';
import { DocumentUpload } from './DocumentUpload';
import { DocumentAnalysisPreview } from './DocumentAnalysisPreview';

// Helper component for form fields with auto-fill indicators
const FormField: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: 'text' | 'textarea';
  rows?: number;
  isAutoFilled?: boolean;
}> = ({ label, value, onChange, placeholder, type = 'text', rows = 4, isAutoFilled = false }) => {
  const inputClasses = `w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 ${
    isAutoFilled ? 'bg-yellow-50 border-yellow-200' : ''
  } ${type === 'textarea' ? 'resize-none' : ''}`;

  return (
    <div>
      <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center space-x-2">
        <span>{label}</span>
        {isAutoFilled && (
          <span className="text-yellow-600 text-xs" title="Auto-filled from document">
            ✨
          </span>
        )}
      </label>
      <div className="relative">
        {type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={rows}
            className={inputClasses}
          />
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className={inputClasses}
          />
        )}
      </div>
    </div>
  );
};

interface EnhancedRFQEditorProps {
  onPreview?: () => void;
  mode?: 'create' | 'edit';
}

export const EnhancedRFQEditor: React.FC<EnhancedRFQEditorProps> = ({
  onPreview,
  mode = 'create'
}) => {
  const {
    enhancedRfq,
    setEnhancedRfq,
    workflow,
    // Document upload state and actions
    documentContent,
    documentAnalysis,
    fieldMappings,
    isDocumentProcessing,
    documentUploadError,
    uploadDocument,
    analyzeText,
    acceptFieldMapping,
    rejectFieldMapping,
    editFieldMapping,
    clearDocumentData,
    applyDocumentMappings,
    addToast,
    // State persistence
    restoreEnhancedRfqState,
    clearEnhancedRfqState
  } = useAppStore();

  const [currentSection, setCurrentSection] = useState<string>('document');

  // Initialize enhanced RFQ with defaults
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      
      // Try to restore state from localStorage first
      const wasRestored = restoreEnhancedRfqState();
      
      // If no state was restored, initialize with defaults
      if (!wasRestored && !enhancedRfq.title && !enhancedRfq.description) {
        setEnhancedRfq({
          title: '',
          description: '',
          business_context: {
            company_product_background: '',
            business_problem: '',
            business_objective: ''
          },
          research_objectives: {
            research_audience: '',
            success_criteria: '',
            key_research_questions: []
          },
          methodology: {
            primary_method: 'basic_survey'
          },
          survey_requirements: {
            sample_plan: '',
            required_sections: [],
            must_have_questions: []
          }
        });
      }
    }
  }, [enhancedRfq.title, enhancedRfq.description, setEnhancedRfq, restoreEnhancedRfqState]);

  const sections = [
    { id: 'document', title: 'Document Upload', icon: '📄', description: 'Upload RFQ document for auto-extraction' },
    { id: 'business_context', title: 'Business Context', icon: '🏢', description: 'Company background, business problem & objective' },
    { id: 'research_objectives', title: 'Research Objectives', icon: '🎯', description: 'Research audience, success criteria & key questions' },
    { id: 'methodology', title: 'Methodology', icon: '🔬', description: 'Van Westendorp, Conjoint, Gabor Granger or other approach' },
    { id: 'survey_requirements', title: 'Survey Requirements', icon: '📋', description: 'Sample plan, sections, must-have questions' }
  ];

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  const addResearchQuestion = () => {
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: [...(enhancedRfq.research_objectives?.key_research_questions || []), '']
      }
    });
  };

  const updateResearchQuestion = (index: number, value: string) => {
    const questions = [...(enhancedRfq.research_objectives?.key_research_questions || [])];
    questions[index] = value;
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: questions
      }
    });
  };

  const removeResearchQuestion = (index: number) => {
    const questions = [...(enhancedRfq.research_objectives?.key_research_questions || [])];
    questions.splice(index, 1);
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: questions
      }
    });
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced RFQ Builder</h1>
              <p className="text-gray-600">Create comprehensive research requirements with AI assistance</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="bg-gray-100 rounded-2xl p-4 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-800">Progress</span>
              <span className="text-sm text-gray-600">
                {sections.findIndex(s => s.id === currentSection) + 1} of {sections.length}
              </span>
            </div>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div
                className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((sections.findIndex(s => s.id === currentSection) + 1) / sections.length) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-2">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => setCurrentSection(section.id)}
                  className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-all duration-200 ${
                    currentSection === section.id
                      ? 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-lg">{section.icon}</span>
                  <span className="text-xs font-medium">{section.title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="xl:col-span-3">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">

                {/* Document Upload Section */}
                {currentSection === 'document' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">📄</span>
                      Document Upload
                    </h2>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                      <div className="flex items-start space-x-3">
                        <div className="text-yellow-600 text-2xl">💡</div>
                        <div>
                          <h3 className="font-semibold text-yellow-900 mb-2">Smart Auto-fill</h3>
                          <p className="text-yellow-800 text-sm">
                            Upload your RFQ document to automatically extract business context, research objectives,
                            methodology requirements, and survey specifications using AI-powered analysis.
                          </p>
                        </div>
                      </div>
                    </div>

                    <DocumentUpload
                      onDocumentAnalyzed={(result) => {
                        console.log('Document upload successful:', result);
                        addToast({
                          type: 'success',
                          title: 'Document Uploaded',
                          message: 'Document processed successfully. Check the sections below for auto-filled content.',
                          duration: 5000
                        });
                        
                        // Automatically advance to Business Context section to show auto-filled content
                        setTimeout(() => {
                          setCurrentSection('business_context');
                        }, 1000); // Small delay to let user see the success message
                      }}
                    />

                  </div>
                )}

                {/* Business Context Section */}
                {currentSection === 'business_context' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                        <span className="text-3xl mr-3">🏢</span>
                        Business Context
                      </h2>
                      {enhancedRfq.document_source && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 flex items-center space-x-2">
                          <span className="text-yellow-600">📄</span>
                          <span className="text-sm text-yellow-800 font-medium">Auto-filled from document</span>
                        </div>
                      )}
                    </div>

                    {enhancedRfq.document_source && (
                      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                        <div className="flex items-start space-x-3">
                          <div className="text-blue-600 text-xl">💡</div>
                          <div>
                            <h3 className="font-semibold text-blue-900 mb-1">Document Analysis Complete</h3>
                            <p className="text-blue-800 text-sm">
                              Your document has been analyzed and relevant information has been auto-filled below. 
                              Review and edit the content as needed, then continue through the remaining sections.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Project Title"
                        value={enhancedRfq.title || ''}
                        onChange={(value) => setEnhancedRfq({ ...enhancedRfq, title: value })}
                        placeholder="Enter your research project title"
                        type="text"
                        isAutoFilled={!!(enhancedRfq.document_source && enhancedRfq.title)}
                      />

                      <FormField
                        label="Project Description"
                        value={enhancedRfq.description}
                        onChange={(value) => setEnhancedRfq({ ...enhancedRfq, description: value })}
                        placeholder="Brief overview of the research project..."
                        type="textarea"
                        rows={4}
                        isAutoFilled={!!(enhancedRfq.document_source && enhancedRfq.description)}
                      />
                    </div>

                    <FormField
                      label="Company & Product Background"
                      value={enhancedRfq.business_context?.company_product_background || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        business_context: {
                          ...enhancedRfq.business_context,
                          company_product_background: value,
                          business_problem: enhancedRfq.business_context?.business_problem || '',
                          business_objective: enhancedRfq.business_context?.business_objective || ''
                        }
                      })}
                      placeholder="Provide background on your company, product, and any relevant research history that influences this study design..."
                      type="textarea"
                      rows={6}
                      isAutoFilled={!!(enhancedRfq.document_source && enhancedRfq.business_context?.company_product_background)}
                    />

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Business Problem"
                        value={enhancedRfq.business_context?.business_problem || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: value,
                            business_objective: enhancedRfq.business_context?.business_objective || ''
                          }
                        })}
                        placeholder="What business challenge or question needs to be addressed?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={!!(enhancedRfq.document_source && enhancedRfq.business_context?.business_problem)}
                      />

                      <FormField
                        label="Business Objective"
                        value={enhancedRfq.business_context?.business_objective || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: value
                          }
                        })}
                        placeholder="What does the business want to achieve from this research?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={!!(enhancedRfq.document_source && enhancedRfq.business_context?.business_objective)}
                      />
                    </div>
                  </div>
                )}

                {/* Research Objectives Section */}
                {currentSection === 'research_objectives' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🎯</span>
                      Research Objectives
                    </h2>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-800 mb-3">
                          Research Audience
                        </label>
                        <div className="relative">
                          <textarea
                            value={enhancedRfq.research_objectives?.research_audience || ''}
                            onChange={(e) => setEnhancedRfq({
                              ...enhancedRfq,
                              research_objectives: {
                                ...enhancedRfq.research_objectives,
                                research_audience: e.target.value,
                                success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                                key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                              }
                            })}
                            placeholder="Describe respondent type, demographics, targeted segments..."
                            rows={4}
                            className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                              enhancedRfq.document_source && enhancedRfq.research_objectives?.research_audience ? 'bg-yellow-50 border-yellow-200' : ''
                            }`}
                          />
                          {enhancedRfq.document_source && enhancedRfq.research_objectives?.research_audience && (
                            <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                              <span>📄</span>
                              <span className="text-xs text-yellow-700">Auto-filled</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-800 mb-3">
                          Success Criteria
                        </label>
                        <div className="relative">
                          <textarea
                            value={enhancedRfq.research_objectives?.success_criteria || ''}
                            onChange={(e) => setEnhancedRfq({
                              ...enhancedRfq,
                              research_objectives: {
                                ...enhancedRfq.research_objectives,
                                research_audience: enhancedRfq.research_objectives?.research_audience || '',
                                success_criteria: e.target.value,
                                key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                              }
                            })}
                            placeholder="What defines success for this research? What decisions will flow from this?"
                            rows={4}
                            className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                              enhancedRfq.document_source && enhancedRfq.research_objectives?.success_criteria ? 'bg-yellow-50 border-yellow-200' : ''
                            }`}
                          />
                          {enhancedRfq.document_source && enhancedRfq.research_objectives?.success_criteria && (
                            <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                              <span>📄</span>
                              <span className="text-xs text-yellow-700">Auto-filled</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <label className="block text-sm font-semibold text-gray-800">
                          Key Research Questions
                        </label>
                        <button
                          onClick={addResearchQuestion}
                          className="px-3 py-1 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
                        >
                          + Add Question
                        </button>
                      </div>
                      <div className="space-y-3">
                        {(enhancedRfq.research_objectives?.key_research_questions || []).map((question, index) => (
                          <div key={index} className="flex items-center space-x-3">
                            <div className="flex-1">
                              <input
                                type="text"
                                value={question}
                                onChange={(e) => updateResearchQuestion(index, e.target.value)}
                                placeholder={`Research question ${index + 1}...`}
                                className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300"
                              />
                            </div>
                            <button
                              onClick={() => removeResearchQuestion(index)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                        {(enhancedRfq.research_objectives?.key_research_questions || []).length === 0 && (
                          <div className="text-center py-8 text-gray-500">
                            <p>No research questions added yet.</p>
                            <p className="text-sm">Click "Add Question" to get started.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Methodology Section */}
                {currentSection === 'methodology' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🔬</span>
                      Research Methodology
                    </h2>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Primary Methodology
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        {(['basic_survey', 'van_westendorp', 'gabor_granger', 'conjoint'] as const).map((method) => (
                          <button
                            key={method}
                            onClick={() => setEnhancedRfq({
                              ...enhancedRfq,
                              methodology: {
                                ...enhancedRfq.methodology,
                                primary_method: method
                              }
                            })}
                            className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                              enhancedRfq.methodology?.primary_method === method
                                ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                                : 'border-gray-200 hover:border-gray-300 text-gray-700'
                            }`}
                          >
                            <div className="font-medium capitalize">
                              {method.replace('_', ' ')}
                            </div>
                            <div className="text-xs mt-1 text-gray-500">
                              {method === 'basic_survey' && 'Standard survey'}
                              {method === 'van_westendorp' && 'Price sensitivity'}
                              {method === 'gabor_granger' && 'Price acceptance'}
                              {method === 'conjoint' && 'Trade-off analysis'}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Stimuli Details
                      </label>
                      <div className="relative">
                        <textarea
                          value={enhancedRfq.methodology?.stimuli_details || ''}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            methodology: {
                              ...enhancedRfq.methodology,
                              primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                              stimuli_details: e.target.value
                            }
                          })}
                          placeholder="Describe concepts, price ranges, features to test, or other stimuli details..."
                          rows={4}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.methodology?.stimuli_details ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.methodology?.stimuli_details && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Methodology Requirements
                      </label>
                      <div className="relative">
                        <textarea
                          value={enhancedRfq.methodology?.methodology_requirements || ''}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            methodology: {
                              ...enhancedRfq.methodology,
                              primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                              methodology_requirements: e.target.value
                            }
                          })}
                          placeholder="Any specific methodology requirements, constraints, or considerations..."
                          rows={3}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.methodology?.methodology_requirements ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.methodology?.methodology_requirements && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Survey Requirements Section */}
                {currentSection === 'survey_requirements' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">📋</span>
                      Survey Requirements
                    </h2>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Sample Plan
                      </label>
                      <div className="relative">
                        <textarea
                          value={enhancedRfq.survey_requirements?.sample_plan || ''}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            survey_requirements: {
                              ...enhancedRfq.survey_requirements,
                              sample_plan: e.target.value,
                              required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                              must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || []
                            }
                          })}
                          placeholder="Include sample structure, LOI, recruiting criteria, target sample size..."
                          rows={4}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.survey_requirements?.sample_plan ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.survey_requirements?.sample_plan && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Required Survey Sections
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {['Screener', 'Demographics', 'Awareness', 'Usage', 'Concept Testing', 'Pricing', 'Satisfaction'].map((section) => (
                          <label key={section} className="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={(enhancedRfq.survey_requirements?.required_sections || []).includes(section)}
                              onChange={(e) => {
                                const sections = [...(enhancedRfq.survey_requirements?.required_sections || [])];
                                if (e.target.checked) {
                                  sections.push(section);
                                } else {
                                  const index = sections.indexOf(section);
                                  if (index > -1) sections.splice(index, 1);
                                }
                                setEnhancedRfq({
                                  ...enhancedRfq,
                                  survey_requirements: {
                                    ...enhancedRfq.survey_requirements,
                                    sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                                    required_sections: sections,
                                    must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || []
                                  }
                                });
                              }}
                              className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                            />
                            <span className="text-sm">{section}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Must-Have Questions
                      </label>
                      <div className="relative">
                        <textarea
                          value={(enhancedRfq.survey_requirements?.must_have_questions || []).join('\n')}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            survey_requirements: {
                              ...enhancedRfq.survey_requirements,
                              sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                              required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                              must_have_questions: e.target.value.split('\n').filter(q => q.trim())
                            }
                          })}
                          placeholder="List must-have questions (one per line)..."
                          rows={4}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.survey_requirements?.must_have_questions?.length ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.survey_requirements?.must_have_questions?.length && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Screener Requirements
                      </label>
                      <div className="relative">
                        <textarea
                          value={enhancedRfq.survey_requirements?.screener_requirements || ''}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            survey_requirements: {
                              ...enhancedRfq.survey_requirements,
                              sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                              required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                              must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                              screener_requirements: e.target.value
                            }
                          })}
                          placeholder="Screener and respondent tagging rules, piping logic..."
                          rows={3}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.survey_requirements?.screener_requirements ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.survey_requirements?.screener_requirements && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Rules & Definitions
                      </label>
                      <div className="relative">
                        <textarea
                          value={enhancedRfq.rules_and_definitions || ''}
                          onChange={(e) => setEnhancedRfq({
                            ...enhancedRfq,
                            rules_and_definitions: e.target.value
                          })}
                          placeholder="Rules, definitions, jargon feed, special terms..."
                          rows={3}
                          className={`w-full px-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 resize-none ${
                            enhancedRfq.document_source && enhancedRfq.rules_and_definitions ? 'bg-yellow-50 border-yellow-200' : ''
                          }`}
                        />
                        {enhancedRfq.document_source && enhancedRfq.rules_and_definitions && (
                          <div className="absolute right-4 top-4 text-yellow-600 text-sm flex items-center space-x-1">
                            <span>📄</span>
                            <span className="text-xs text-yellow-700">Auto-filled</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Preview & Generate Section */}
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Ready to Generate Your Survey?</h3>
                      <p className="text-gray-600 text-sm mt-1">
                        Review your requirements and generate a professional survey
                      </p>
                    </div>
                    <div className="flex space-x-4">
                     <button
                       onClick={() => setCurrentSection('document')}
                       className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium"
                     >
                       Back to Start
                     </button>
                     <button
                       onClick={() => {
                         if (window.confirm('Are you sure you want to clear all form data? This action cannot be undone.')) {
                           clearEnhancedRfqState();
                           setCurrentSection('document');
                           addToast({
                             type: 'info',
                             title: 'Form Cleared',
                             message: 'All form data has been cleared. You can start fresh.',
                             duration: 4000
                           });
                         }
                       }}
                       className="px-6 py-3 bg-red-100 text-red-700 rounded-xl hover:bg-red-200 transition-colors font-medium"
                     >
                       Clear Form
                     </button>
                      <button
                        onClick={onPreview}
                        disabled={isLoading}
                        className="px-8 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl hover:from-yellow-600 hover:to-orange-600 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>Generating...</span>
                          </>
                        ) : (
                          <>
                            <span>Preview & Generate</span>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                            </svg>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
      </div>
    </div>
  );
};