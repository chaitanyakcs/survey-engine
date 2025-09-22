import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import { DocumentUpload } from './DocumentUpload';

// Animated sprinkle component
const AnimatedSprinkle: React.FC<{ className?: string }> = ({ className = "" }) => (
  <span 
    className={`inline-block text-yellow-600 text-xs animate-pulse hover:animate-bounce ${className}`} 
    title="Auto-filled from document"
  >
    ✨
  </span>
);

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
        {isAutoFilled && <AnimatedSprinkle />}
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
    fieldMappings,
    addToast,
    // State persistence
    restoreEnhancedRfqState,
    clearEnhancedRfqState
  } = useAppStore();

  // Helper function to check if a field was actually auto-filled from document
  const isFieldAutoFilled = (fieldPath: string): boolean => {
    return fieldMappings.some(mapping => 
      mapping.field === fieldPath && 
      mapping.user_action === 'accepted'
    );
  };

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
            required_sections: ['Screener', 'Demographics', 'Awareness', 'Usage', 'Concept Testing', 'Pricing', 'Satisfaction'],
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

        <div className="w-full">
          {/* Main Content */}
          <div className="w-full">
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
                          <AnimatedSprinkle className="text-lg" />
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
                        isAutoFilled={isFieldAutoFilled('title')}
                      />

                      <FormField
                        label="Project Description"
                        value={enhancedRfq.description}
                        onChange={(value) => setEnhancedRfq({ ...enhancedRfq, description: value })}
                        placeholder="Brief overview of the research project..."
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('description')}
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
                      isAutoFilled={isFieldAutoFilled('business_context.company_product_background')}
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
                        isAutoFilled={isFieldAutoFilled('business_context.business_problem')}
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
                        isAutoFilled={isFieldAutoFilled('business_context.business_objective')}
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

                    <div className="grid grid-cols-1 gap-6">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FormField
                          label="Research Audience"
                          value={enhancedRfq.research_objectives?.research_audience || ''}
                          onChange={(value) => setEnhancedRfq({
                            ...enhancedRfq,
                            research_objectives: {
                              ...enhancedRfq.research_objectives,
                              research_audience: value,
                              success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                              key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                            }
                          })}
                          placeholder="Describe respondent type, demographics, targeted segments..."
                          type="textarea"
                          rows={4}
                          isAutoFilled={isFieldAutoFilled('research_objectives.research_audience')}
                        />

                        <FormField
                          label="Success Criteria"
                        value={enhancedRfq.research_objectives?.success_criteria || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          research_objectives: {
                            ...enhancedRfq.research_objectives,
                            research_audience: enhancedRfq.research_objectives?.research_audience || '',
                            success_criteria: value,
                            key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                          }
                        })}
                        placeholder="What defines success for this research? What decisions will flow from this?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('research_objectives.success_criteria')}
                        />
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

                    <FormField
                      label="Stimuli Details"
                      value={enhancedRfq.methodology?.stimuli_details || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        methodology: {
                          ...enhancedRfq.methodology,
                          primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                          stimuli_details: value
                        }
                      })}
                      placeholder="Describe concepts, price ranges, features to test, or other stimuli details..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('methodology.stimuli_details')}
                    />

                    <FormField
                      label="Methodology Requirements"
                      value={enhancedRfq.methodology?.methodology_requirements || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        methodology: {
                          ...enhancedRfq.methodology,
                          primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                          methodology_requirements: value
                        }
                      })}
                      placeholder="Any specific methodology requirements, constraints, or considerations..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('methodology.methodology_requirements')}
                    />
                  </div>
                )}

                {/* Survey Requirements Section */}
                {currentSection === 'survey_requirements' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">📋</span>
                      Survey Requirements
                    </h2>

                    <FormField
                      label="Sample Plan"
                      value={enhancedRfq.survey_requirements?.sample_plan || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: value,
                          required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                          must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || []
                        }
                      })}
                      placeholder="Include sample structure, LOI, recruiting criteria, target sample size..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.sample_plan')}
                    />

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

                    <FormField
                      label="Must-Have Questions"
                      value={(enhancedRfq.survey_requirements?.must_have_questions || []).join('\n')}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                          required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                          must_have_questions: value.split('\n').filter(q => q.trim())
                        }
                      })}
                      placeholder="List must-have questions (one per line)..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.must_have_questions')}
                    />

                    <FormField
                      label="Screener Requirements"
                      value={enhancedRfq.survey_requirements?.screener_requirements || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                          required_sections: enhancedRfq.survey_requirements?.required_sections || [],
                          must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                          screener_requirements: value
                        }
                      })}
                      placeholder="Screener and respondent tagging rules, piping logic..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.screener_requirements')}
                    />

                    <FormField
                      label="Rules & Definitions"
                      value={enhancedRfq.rules_and_definitions || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        rules_and_definitions: value
                      })}
                      placeholder="Rules, definitions, jargon feed, special terms..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('rules_and_definitions')}
                    />
                  </div>
                )}

                {/* Navigation Section */}
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    {/* Left side - Navigation buttons */}
                    <div className="flex items-center space-x-3">
                      {/* Previous Button */}
                      {sections.findIndex(s => s.id === currentSection) > 0 && (
                        <button
                          onClick={() => {
                            const currentIndex = sections.findIndex(s => s.id === currentSection);
                            setCurrentSection(sections[currentIndex - 1].id);
                          }}
                          className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                          </svg>
                          <span>Previous</span>
                        </button>
                      )}

                      {/* Next Button */}
                      {sections.findIndex(s => s.id === currentSection) < sections.length - 1 && (
                        <button
                          onClick={() => {
                            const currentIndex = sections.findIndex(s => s.id === currentSection);
                            setCurrentSection(sections[currentIndex + 1].id);
                          }}
                          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
                        >
                          <span>Next</span>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Right side - Refresh icon and Preview & Generate */}
                    <div className="flex items-center space-x-3">
                      {/* Refresh/Clear Button - only show if not on last section */}
                      {sections.findIndex(s => s.id === currentSection) < sections.length - 1 && (
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
                          className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Clear form and start over"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                      )}

                      {/* Preview & Generate - only show on last section */}
                      {sections.findIndex(s => s.id === currentSection) === sections.length - 1 && (
                        <>
                          <div className="text-right mr-4">
                            <h3 className="text-lg font-semibold text-gray-900">Ready to Generate Your Survey?</h3>
                            <p className="text-gray-600 text-sm">
                              Review your requirements and generate a professional survey
                            </p>
                          </div>
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
                        </>
                      )}
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