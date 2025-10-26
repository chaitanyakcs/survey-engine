import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Survey } from '../types';
import { PreGenerationPreview } from '../components/PreGenerationPreview';
import { LLMAuditViewer } from '../components/LLMAuditViewer';
import SurveyInsights from '../components/SurveyInsights';
import { apiService } from '../services/api';
import { 
  DocumentTextIcon,
  StarIcon,
  QuestionMarkCircleIcon,
  RectangleStackIcon,
  ChartBarIcon,
  ClockIcon,
  TagIcon,
  ChartBarSquareIcon
} from '@heroicons/react/24/outline';

interface GoldenPair {
  id: string;
  title?: string;
  rfq_text: string;
  survey_json: any;
  methodology_tags?: string[];
  industry_category?: string;
  research_goal?: string;
  quality_score?: number;
  usage_count: number;
}

interface GoldenQuestion {
  id: string;
  question_text: string;
  question_type?: string;
  question_subtype?: string;
  methodology_tags?: string[];
  industry_category?: string;
  research_goal?: string;
  quality_score?: number;
  usage_count: number;
}

interface GoldenSection {
  id: string;
  title: string;
  section_type?: string;
  methodology_tags?: string[];
  industry_category?: string;
  research_goal?: string;
  quality_score?: number;
  usage_count: number;
}

interface LLMAuditRecord {
  id: string;
  purpose: string;
  sub_purpose?: string;
  model_name: string;
  success: boolean;
  created_at: string;
}

export const SurveyInsightsPage: React.FC = () => {
  const { addToast } = useAppStore();
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'rfq' | 'golden-pairs' | 'golden-questions' | 'golden-sections' | 'generation-audit' | 'evaluation-audit' | 'quality-analysis'>('quality-analysis');
  
  // Data states
  const [goldenPairs, setGoldenPairs] = useState<GoldenPair[]>([]);
  const [goldenQuestions, setGoldenQuestions] = useState<GoldenQuestion[]>([]);
  const [goldenSections, setGoldenSections] = useState<GoldenSection[]>([]);
  const [evaluationAudits, setEvaluationAudits] = useState<LLMAuditRecord[]>([]);

  useEffect(() => {
    const loadSurveyInsights = async () => {
      try {
        setLoading(true);
        setError(null);

        // Extract survey ID from URL path
        const pathParts = window.location.pathname.split('/');
        const surveyId = pathParts[2]; // /surveys/{surveyId}/insights

        if (!surveyId) {
          throw new Error('No survey ID found in URL');
        }

        console.log('🔍 [Survey Insights] Loading insights for survey:', surveyId);

        // Load survey data
        const surveyData = await apiService.fetchSurvey(surveyId);
        setSurvey(surveyData);
        
        console.log('🔍 [Survey Insights] Survey data keys:', Object.keys(surveyData));
        console.log('🔍 [Survey Insights] Survey used_golden_examples:', surveyData.used_golden_examples);
        console.log('🔍 [Survey Insights] Survey used_golden_questions:', surveyData.used_golden_questions);
        console.log('🔍 [Survey Insights] Survey used_golden_sections:', surveyData.used_golden_sections);

        // Load golden content used by this survey
        const usedGoldenExamples = surveyData.used_golden_examples || [];
        const usedGoldenQuestions = surveyData.used_golden_questions || [];
        const usedGoldenSections = surveyData.used_golden_sections || [];

        console.log('🔍 [Survey Insights] Used golden content:', {
          examples: usedGoldenExamples.length,
          questions: usedGoldenQuestions.length,
          sections: usedGoldenSections.length
        });
        console.log('🔍 [Survey Insights] Used golden examples IDs:', usedGoldenExamples);

        // Fetch golden pairs if any were used
        if (usedGoldenExamples.length > 0) {
          try {
            const allGoldenPairs = await apiService.fetchGoldenPairs();
            console.log('🔍 [Survey Insights] All golden pairs:', allGoldenPairs.length);
            console.log('🔍 [Survey Insights] All golden pairs IDs:', allGoldenPairs.map((p: any) => p.id));
            
            const usedPairs = allGoldenPairs.filter((pair: any) => 
              usedGoldenExamples.includes(pair.id)
            );
            console.log('🔍 [Survey Insights] Filtered used pairs:', usedPairs.length);
            setGoldenPairs(usedPairs);
          } catch (err) {
            console.warn('Failed to fetch golden pairs:', err);
          }
        }

        // Fetch golden questions if any were used
        if (usedGoldenQuestions.length > 0) {
          try {
            const allGoldenQuestions = await apiService.fetchGoldenQuestions();
            const usedQuestions = allGoldenQuestions.filter((question: any) => 
              usedGoldenQuestions.includes(question.id)
            );
            setGoldenQuestions(usedQuestions);
          } catch (err) {
            console.warn('Failed to fetch golden questions:', err);
          }
        }

        // Fetch golden sections if any were used
        if (usedGoldenSections.length > 0) {
          try {
            const allGoldenSections = await apiService.fetchGoldenSections();
            const usedSections = allGoldenSections.filter((section: any) => 
              usedGoldenSections.includes(section.id)
            );
            setGoldenSections(usedSections);
          } catch (err) {
            console.warn('Failed to fetch golden sections:', err);
          }
        }

        // Load LLM audit records
        try {
          const auditRecords = await apiService.fetchSurveyLLMAudits(surveyId);
          console.log('🔍 [Survey Insights] All audit records:', auditRecords.length);
          console.log('🔍 [Survey Insights] Audit purposes:', auditRecords.map((a: any) => a.purpose));
          
          // Separate generation and evaluation audits
          const evalAudits = auditRecords.filter((audit: any) => 
            audit.purpose === 'evaluation' || 
            audit.purpose === 'pillar_evaluation' ||
            audit.sub_purpose === 'evaluation' ||
            audit.context_type === 'evaluation'
          );
          
          console.log('🔍 [Survey Insights] Evaluation audits found:', evalAudits.length);
          setEvaluationAudits(evalAudits);
        } catch (err) {
          console.warn('Failed to fetch LLM audits:', err);
        }

        console.log('✅ [Survey Insights] All data loaded successfully');

      } catch (err) {
        console.error('❌ [Survey Insights] Failed to load insights:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load survey insights';
        setError(errorMessage);
        addToast({
          type: 'error',
          title: 'Load Error',
          message: errorMessage,
          duration: 5000
        });
      } finally {
        setLoading(false);
      }
    };

    loadSurveyInsights();
  }, [addToast]);

  const handleBackToSurvey = () => {
    const pathParts = window.location.pathname.split('/');
    const surveyId = pathParts[2];
    window.location.href = `/surveys/${surveyId}`;
  };


  const tabs = [
    { id: 'quality-analysis', name: 'Quality Analysis', icon: ChartBarSquareIcon },
    { id: 'rfq', name: 'RFQ Used', icon: DocumentTextIcon },
    { id: 'golden-pairs', name: 'Golden Pairs', icon: StarIcon },
    { id: 'golden-questions', name: 'Golden Questions', icon: QuestionMarkCircleIcon },
    { id: 'golden-sections', name: 'Golden Sections', icon: RectangleStackIcon },
    { id: 'generation-audit', name: 'Generation LLM Audit', icon: ChartBarIcon },
    { id: 'evaluation-audit', name: 'Evaluation LLM Audit', icon: ClockIcon }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'quality-analysis':
        return (
          <div className="h-full">
            {survey?.survey_id ? (
              <SurveyInsights surveyId={survey.survey_id} />
            ) : (
              <div className="text-center py-12">
                <ChartBarSquareIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No survey ID available</h3>
              </div>
            )}
          </div>
        );
      
      case 'rfq':
        return (
          <div className="p-6">
            {survey?.rfq_data ? (
              <PreGenerationPreview 
                rfq={survey.rfq_data}
                // Read-only mode - no onGenerate or onEdit
              />
            ) : (
              <div className="text-center py-12">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No RFQ data available</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This survey may have been created before RFQ tracking was implemented.
                </p>
              </div>
            )}
          </div>
        );

      case 'golden-pairs':
        return (
          <div className="p-6">
            {goldenPairs.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Golden RFQ-Survey Pairs Used</h3>
                {goldenPairs.map((pair) => (
                  <div key={pair.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{pair.title || 'Untitled Pair'}</h4>
                        <p className="mt-1 text-sm text-gray-600 line-clamp-3">{pair.rfq_text}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <StarIcon className="h-4 w-4 mr-1" />
                            Quality: {pair.quality_score?.toFixed(2) || 'N/A'}
                          </span>
                          <span className="flex items-center">
                            <TagIcon className="h-4 w-4 mr-1" />
                            Used: {pair.usage_count} times
                          </span>
                          {pair.industry_category && (
                            <span>Industry: {pair.industry_category}</span>
                          )}
                        </div>
                        {pair.methodology_tags && pair.methodology_tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {pair.methodology_tags.map((tag, index) => (
                              <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <StarIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No golden pairs used</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This survey was not generated using any golden RFQ-survey pairs.
                </p>
                <div className="mt-4 text-xs text-gray-400">
                  <p>Debug info:</p>
                  <p>Used golden examples: {survey?.used_golden_examples?.length || 0}</p>
                  <p>Golden pairs loaded: {goldenPairs.length}</p>
                </div>
              </div>
            )}
          </div>
        );

      case 'golden-questions':
        return (
          <div className="p-6">
            {goldenQuestions.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Golden Questions Referenced</h3>
                {goldenQuestions.map((question) => {
                  // Helper function to get label color class based on category
                  const getLabelColorClass = (category: string) => {
                    const colorMap: Record<string, string> = {
                      'screener': 'bg-blue-100 text-blue-700',
                      'brand': 'bg-green-100 text-green-700',
                      'concept': 'bg-purple-100 text-purple-700',
                      'methodology': 'bg-orange-100 text-orange-700',
                      'additional': 'bg-gray-100 text-gray-700'
                    };
                    return colorMap[category] || 'bg-gray-100 text-gray-700';
                  };

                  // Section names for display
                  const sectionNames: Record<number, string> = {
                    1: 'Sample Plan',
                    2: 'Screener',
                    3: 'Brand/Product',
                    4: 'Concept',
                    5: 'Methodology',
                    6: 'Additional',
                    7: 'Programmer Instructions'
                  };

                  return (
                    <div key={question.id} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">{question.question_type || 'Question'}</h4>
                          <p className="mt-1 text-sm text-gray-600">{question.question_text}</p>
                          
                          {/* QNR Label Metadata - NEW */}
                          {(question as any).primary_label && (
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getLabelColorClass((question as any).label_category || '')}`}>
                                {(question as any).primary_label}
                              </span>
                              {(question as any).label_mandatory && (
                                <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                                  MANDATORY
                                </span>
                              )}
                              {(question as any).label_section_id && (
                                <span className="text-xs text-gray-500">
                                  {sectionNames[(question as any).label_section_id] || `Section ${(question as any).label_section_id}`}
                                </span>
                              )}
                            </div>
                          )}
                          {(question as any).label_description && (
                            <p className="mt-1 text-xs text-gray-500 italic">
                              {(question as any).label_description}
                            </p>
                          )}
                          
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                            <span className="flex items-center">
                              <StarIcon className="h-4 w-4 mr-1" />
                              Quality: {question.quality_score?.toFixed(2) || 'N/A'}
                            </span>
                            <span className="flex items-center">
                              <TagIcon className="h-4 w-4 mr-1" />
                              Used: {question.usage_count} times
                            </span>
                            {question.question_subtype && (
                              <span>Subtype: {question.question_subtype}</span>
                            )}
                          </div>
                          {question.methodology_tags && question.methodology_tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {question.methodology_tags.map((tag, index) => (
                                <span key={index} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <QuestionMarkCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No golden questions used</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This survey was not generated using any individual golden questions.
                </p>
              </div>
            )}
          </div>
        );

      case 'golden-sections':
        return (
          <div className="p-6">
            {goldenSections.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Golden Sections Referenced</h3>
                {goldenSections.map((section) => (
                  <div key={section.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{section.title}</h4>
                        <p className="mt-1 text-sm text-gray-600">{section.section_type || 'Section'}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <StarIcon className="h-4 w-4 mr-1" />
                            Quality: {section.quality_score?.toFixed(2) || 'N/A'}
                          </span>
                          <span className="flex items-center">
                            <TagIcon className="h-4 w-4 mr-1" />
                            Used: {section.usage_count} times
                          </span>
                        </div>
                        {section.methodology_tags && section.methodology_tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {section.methodology_tags.map((tag, index) => (
                              <span key={index} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No golden sections used</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This survey was not generated using any golden section templates.
                </p>
              </div>
            )}
          </div>
        );

      case 'generation-audit':
        return (
          <div className="h-full">
            <LLMAuditViewer 
              surveyId={survey?.survey_id}
              title="Survey Generation LLM Audit"
              showSummary={true}
              initialPurposeFilter="survey_generation"
            />
          </div>
        );

      case 'evaluation-audit':
        return (
          <div className="p-6">
            {evaluationAudits.length > 0 ? (
              <div className="h-full">
                <LLMAuditViewer 
                  surveyId={survey?.survey_id}
                  title="Survey Evaluation LLM Audit"
                  showSummary={true}
                  initialPurposeFilter="evaluation"
                />
              </div>
            ) : (
              <div className="text-center py-12">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No evaluation performed yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This survey has not been evaluated using the 5-pillar assessment system.
                </p>
                <div className="mt-4 text-xs text-gray-400">
                  <p>Debug info:</p>
                  <p>Evaluation audits found: {evaluationAudits.length}</p>
                  <p>Total audit records: {survey?.used_golden_examples?.length || 0}</p>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading survey insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.href = '/surveys'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Surveys
          </button>
        </div>
      </div>
    );
  }

  if (!survey) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-gray-600 text-xl mb-4">Survey not found</div>
          <button
            onClick={() => window.location.href = '/surveys'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Surveys
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBackToSurvey}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 group"
          >
            <svg className="h-5 w-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-900">
            Survey Insights: {survey.title || 'Untitled Survey'}
          </h1>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 px-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {renderTabContent()}
      </div>
    </div>
  );
};
