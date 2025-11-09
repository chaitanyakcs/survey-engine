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
  RectangleStackIcon,
  ChartBarIcon,
  TagIcon,
  ChartBarSquareIcon,
  InformationCircleIcon
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

// Simple inline tooltip component
const InlineTooltip: React.FC<{ description: string; position?: 'top' | 'bottom' }> = ({ 
  description, 
  position = 'top' 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block ml-1">
      <button
        type="button"
        className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
      >
        <InformationCircleIcon className="w-4 h-4" />
      </button>
      
      {isOpen && (
        <div className={`absolute z-50 w-72 p-3 ${position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'} left-0 bg-gray-900 text-white text-xs rounded-lg shadow-lg`}>
          <p className="leading-relaxed">{description}</p>
          <div className={`absolute ${position === 'top' ? 'top-full' : 'bottom-full'} left-4 w-0 h-0 border-l-4 border-r-4 ${position === 'top' ? 'border-t-4 border-t-gray-900' : 'border-b-4 border-b-gray-900'} border-transparent`}></div>
        </div>
      )}
    </div>
  );
};

export const SurveyInsightsPage: React.FC = () => {
  const { addToast } = useAppStore();
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'rfq' | 'reference-examples' | 'llm-audit' | 'quality-analysis'>('quality-analysis');
  const [activeSubTab, setActiveSubTab] = useState<'eight-questions' | 'manual-comment-digest' | 'golden-examples' | 'golden-sections'>('eight-questions');
  
  // Data states
  const [goldenPairs, setGoldenPairs] = useState<GoldenPair[]>([]);
  const [goldenQuestions, setGoldenQuestions] = useState<GoldenQuestion[]>([]);
  const [goldenSections, setGoldenSections] = useState<GoldenSection[]>([]);
  const [referenceExamplesData, setReferenceExamplesData] = useState<any>(null);
  const [loadingReferenceExamples, setLoadingReferenceExamples] = useState(false);

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

        // Fetch golden pairs if any were used
        if (usedGoldenExamples.length > 0) {
          try {
            const allGoldenPairs = await apiService.fetchGoldenPairs();
            console.log('🔍 [Survey Insights] All golden pairs:', allGoldenPairs.length);
            
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

        // LLM audit records will be loaded by the LLMAuditViewer component itself

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

  // Load reference examples data when tab is active
  useEffect(() => {
    const loadReferenceExamples = async () => {
      if (activeTab !== 'reference-examples' || !survey) {
        return;
      }

      try {
        setLoadingReferenceExamples(true);
        const pathParts = window.location.pathname.split('/');
        const surveyId = pathParts[2];
        
        if (!surveyId) {
          return;
        }

        const data = await apiService.fetchSurveyReferenceExamples(surveyId);
        setReferenceExamplesData(data);
      } catch (err) {
        console.error('Failed to load reference examples:', err);
        addToast({
          type: 'error',
          title: 'Load Error',
          message: 'Failed to load reference examples',
          duration: 5000
        });
      } finally {
        setLoadingReferenceExamples(false);
      }
    };

    loadReferenceExamples();
  }, [activeTab, survey, addToast]);

  const handleBackToSurvey = () => {
    const pathParts = window.location.pathname.split('/');
    const surveyId = pathParts[2];
    window.location.href = `/surveys/${surveyId}`;
  };

  const tabs = [
    { id: 'quality-analysis', name: 'Quality Analysis', icon: ChartBarSquareIcon },
    { id: 'rfq', name: 'RFQ Used', icon: DocumentTextIcon },
    { id: 'reference-examples', name: 'Reference Examples', icon: RectangleStackIcon },
    { id: 'llm-audit', name: 'LLM Audit', icon: ChartBarIcon }
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
                rfqId={survey.rfq_id}
              />
            ) : (
              <div className="text-center py-12">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No RFQ data available</h3>
              </div>
            )}
          </div>
        );

      case 'reference-examples':
        if (loadingReferenceExamples) {
          return (
            <div className="p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                <div className="h-32 bg-gray-200 rounded"></div>
                <div className="h-32 bg-gray-200 rounded"></div>
              </div>
            </div>
          );
        }

        if (!referenceExamplesData) {
          return (
            <div className="p-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="text-yellow-800 font-medium">Reference Examples Not Available</h3>
                <p className="text-yellow-700 text-sm mt-1">
                  Unable to load reference examples data for this survey.
                </p>
              </div>
            </div>
          );
        }

        const { survey_title, eight_questions_tab, manual_comment_digest_tab, golden_examples_tab, golden_sections_tab } = referenceExamplesData;
        
        const hasEightQuestions = eight_questions_tab?.questions && eight_questions_tab.questions.length > 0;
        const hasManualCommentDigest = manual_comment_digest_tab?.prompt_text && 
          manual_comment_digest_tab.prompt_text !== "No manual comment digest available.";
        const hasGoldenExamples = golden_examples_tab?.examples && golden_examples_tab.examples.length > 0;
        const hasGoldenSections = golden_sections_tab?.sections && golden_sections_tab.sections.length > 0;

        return (
          <div className="p-6 space-y-6">
            {/* Survey Title - Prominently Displayed */}
            <div className="border-b border-gray-200 pb-4">
              <h1 className="text-3xl font-bold text-gray-900">{survey_title}</h1>
              <p className="text-sm text-gray-500 mt-1">Reference examples used during survey generation</p>
            </div>

            {/* Sub-tabs for 8 Questions, Manual Comment Digest, and Golden Examples */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveSubTab('eight-questions')}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm flex items-center
                    ${activeSubTab === 'eight-questions'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  8 Questions
                  <InlineTooltip 
                    description="Shows the top 8 golden questions used as examples in the prompt. Includes both human-created and AI-generated questions, as long as AI-generated questions have been human-verified. These questions serve as templates for the LLM to generate similar high-quality questions."
                    position="bottom"
                  />
                </button>
                <button
                  onClick={() => setActiveSubTab('manual-comment-digest')}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm flex items-center
                    ${activeSubTab === 'manual-comment-digest'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  Manual Comment Digest
                  <InlineTooltip 
                    description="Shows a digest of expert feedback comments from annotated golden questions. Only includes comments that were manually created by human annotators (excludes AI-generated comments). This digest helps the LLM understand common patterns, recommendations, and issues to avoid when generating questions."
                    position="bottom"
                  />
                </button>
                <button
                  onClick={() => setActiveSubTab('golden-examples')}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm flex items-center
                    ${activeSubTab === 'golden-examples'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  Golden Examples
                  <InlineTooltip 
                    description="Shows complete golden RFQ-survey pairs used as reference examples. These are full examples of high-quality RFQ-to-survey transformations that the LLM uses to understand structure, flow, and quality standards."
                    position="bottom"
                  />
                </button>
                <button
                  onClick={() => setActiveSubTab('golden-sections')}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm flex items-center
                    ${activeSubTab === 'golden-sections'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  Golden Sections
                  <InlineTooltip 
                    description="Shows high-quality sections from verified surveys used as templates. These sections demonstrate proper structure, flow, and question organization that the LLM uses to generate well-structured survey sections."
                    position="bottom"
                  />
                </button>
              </nav>
            </div>

            {/* 8 Questions Tab Content */}
            {activeSubTab === 'eight-questions' && (
              <div className="space-y-6">
                {/* Prompt Text Section */}
                {eight_questions_tab?.prompt_text && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h2>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                        {eight_questions_tab.prompt_text}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Questions List Section */}
                {hasEightQuestions ? (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Questions Used</h2>
                    <div className="space-y-4">
                      {eight_questions_tab.questions.map((question: any, index: number) => (
                        <div key={question.id || index} className="bg-white border border-gray-200 rounded-lg p-5">
                          <div className="space-y-3">
                            {/* Question Type and Metadata */}
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                                {question.question_type || 'Question'}
                              </span>
                              {question.quality_score !== undefined && (
                                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                  Quality: {question.quality_score.toFixed(2)}/1.0
                                </span>
                              )}
                              {question.human_verified ? (
                                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium inline-flex items-center">
                                  ✅ Human Verified
                                  <InlineTooltip 
                                    description="This question has been reviewed and verified by a human expert. Even if originally AI-generated, human verification ensures quality and accuracy."
                                    position="bottom"
                                  />
                                </span>
                              ) : (
                                <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium inline-flex items-center">
                                  🤖 AI Generated
                                  <InlineTooltip 
                                    description="This question was generated by AI. In the 8 Questions tab, AI-generated questions are included only if they have been human-verified."
                                    position="bottom"
                                  />
                                </span>
                              )}
                            </div>

                            {/* Question Text */}
                            <div>
                              <p className="text-base text-gray-900 font-medium">"{question.question_text}"</p>
                            </div>

                            {/* Expert Guidance (Annotation Comment) */}
                            {question.annotation_comment && (
                              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                                <div className="flex items-start gap-2">
                                  <span className="text-green-600 font-semibold text-sm">Expert Guidance:</span>
                                </div>
                                <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">
                                  {question.annotation_comment}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No Questions Available</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      No golden questions were used during the generation of this survey.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Manual Comment Digest Tab Content */}
            {activeSubTab === 'manual-comment-digest' && (
              <div className="space-y-6">
                {/* Prompt Text Section */}
                {hasManualCommentDigest && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h2 className="text-lg font-semibold text-gray-900">What Went Into the Prompt</h2>
                      {manual_comment_digest_tab.is_reconstructed && (
                        <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                          Reconstructed
                        </span>
                      )}
                    </div>
                    {manual_comment_digest_tab.is_reconstructed && (
                      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-sm text-yellow-800">
                          <strong>Note:</strong> This manual comment digest may differ from what was used during generation, as it is reconstructed from current golden question data.
                        </p>
                      </div>
                    )}
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                        {manual_comment_digest_tab.prompt_text}
                      </pre>
                    </div>
                    {manual_comment_digest_tab.total_feedback_count > 0 && (
                      <p className="text-xs text-gray-600 mt-2">
                        Based on {manual_comment_digest_tab.total_feedback_count} question{manual_comment_digest_tab.total_feedback_count !== 1 ? 's' : ''} with human-generated comments
                      </p>
                    )}
                  </div>
                )}

                {/* Questions List Section */}
                {manual_comment_digest_tab?.questions && manual_comment_digest_tab.questions.length > 0 ? (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Questions Used</h2>
                    <div className="space-y-4">
                      {manual_comment_digest_tab.questions.map((question: any, index: number) => (
                        <div key={question.id || index} className="bg-white border border-gray-200 rounded-lg p-5">
                          <div className="space-y-3">
                            {/* Question Type and Metadata */}
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                                {question.question_type || 'Question'}
                              </span>
                              {question.quality_score !== undefined && (
                                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                  Quality: {question.quality_score.toFixed(2)}/1.0
                                </span>
                              )}
                              {question.human_verified && (
                                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium inline-flex items-center">
                                  ✅ Human Verified
                                  <InlineTooltip 
                                    description="This question has been reviewed and verified by a human expert."
                                    position="bottom"
                                  />
                                </span>
                              )}
                              {/* Show comment source indicator */}
                              {question.ai_generated === false && question.annotator_id !== 'ai_system' && (
                                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium inline-flex items-center">
                                  👤 Human Comment
                                  <InlineTooltip 
                                    description="The expert guidance comment for this question was created by a human annotator (not AI-generated). Only human-generated comments are included in the Manual Comment Digest."
                                    position="bottom"
                                  />
                                </span>
                              )}
                              {question.human_overridden && (
                                <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium inline-flex items-center">
                                  ✏️ Human Overridden
                                  <InlineTooltip 
                                    description="A human annotator has modified or overridden the original AI-generated comment, ensuring the feedback reflects expert judgment."
                                    position="bottom"
                                  />
                                </span>
                              )}
                            </div>

                            {/* Question Text */}
                            <div>
                              <p className="text-base text-gray-900 font-medium">"{question.question_text}"</p>
                            </div>

                            {/* Expert Guidance (Annotation Comment) */}
                            {question.annotation_comment && (
                              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                                <div className="flex items-start gap-2">
                                  <span className="text-green-600 font-semibold text-sm">Expert Guidance:</span>
                                </div>
                                <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">
                                  {question.annotation_comment}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No Questions Available</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      No questions with human-generated comments were used in the manual comment digest.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Golden Examples Tab Content */}
            {activeSubTab === 'golden-examples' && (
              <div className="space-y-6">
                {/* Prompt Text Section */}
                {golden_examples_tab?.prompt_text && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h2>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                        {golden_examples_tab.prompt_text}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Golden Examples List Section */}
                {hasGoldenExamples ? (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Golden RFQ-Survey Pairs Used</h2>
                    <div className="space-y-6">
                      {golden_examples_tab.examples.map((example: any, index: number) => (
                        <div key={example.id || index} className="bg-white border border-gray-200 rounded-lg p-6">
                          <div className="space-y-4">
                            {/* Header with Title and Metadata */}
                            <div className="border-b border-gray-200 pb-3">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900">{example.title}</h3>
                                  <p className="text-sm text-gray-600 mt-1">Survey: {example.survey_title}</p>
                                </div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {example.quality_score !== undefined && (
                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                      Quality: {example.quality_score.toFixed(2)}/1.0
                                    </span>
                                  )}
                                  {example.human_verified && (
                                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium inline-flex items-center">
                                      ✅ Human Verified
                                      <InlineTooltip 
                                        description="This golden example was created or verified by a human expert."
                                        position="bottom"
                                      />
                                    </span>
                                  )}
                                  {example.usage_count !== undefined && example.usage_count > 0 && (
                                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                                      Used {example.usage_count} time{example.usage_count !== 1 ? 's' : ''}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Metadata */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                              {example.methodology_tags && example.methodology_tags.length > 0 && (
                                <div>
                                  <span className="font-medium text-gray-700">Methodology:</span>
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {example.methodology_tags.map((tag: string, tagIndex: number) => (
                                      <span key={tagIndex} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {example.industry_category && (
                                <div>
                                  <span className="font-medium text-gray-700">Industry:</span>
                                  <p className="text-gray-600 mt-1">{example.industry_category}</p>
                                </div>
                              )}
                              {example.research_goal && (
                                <div>
                                  <span className="font-medium text-gray-700">Research Goal:</span>
                                  <p className="text-gray-600 mt-1">{example.research_goal}</p>
                                </div>
                              )}
                            </div>

                            {/* RFQ Text */}
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">RFQ Text:</h4>
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {example.rfq_text}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No Golden Examples Available</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      No golden RFQ-survey pairs were used during the generation of this survey.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Golden Sections Tab Content */}
            {activeSubTab === 'golden-sections' && (
              <div className="space-y-6">
                {/* Prompt Text Section */}
                {golden_sections_tab?.prompt_text && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h2>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                        {golden_sections_tab.prompt_text}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Golden Sections List Section */}
                {hasGoldenSections ? (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Golden Sections Used</h2>
                    <div className="space-y-6">
                      {golden_sections_tab.sections.map((section: any, index: number) => (
                        <div key={section.id || index} className="bg-white border border-gray-200 rounded-lg p-6">
                          <div className="space-y-4">
                            {/* Header with Title and Metadata */}
                            <div className="border-b border-gray-200 pb-3">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900">{section.section_title}</h3>
                                  <p className="text-sm text-gray-600 mt-1">Section ID: {section.section_id}</p>
                                </div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                                    {section.section_type || 'Section'}
                                  </span>
                                  {section.quality_score !== undefined && (
                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                      Quality: {section.quality_score.toFixed(2)}/1.0
                                    </span>
                                  )}
                                  {section.human_verified && (
                                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium inline-flex items-center">
                                      ✅ Human Verified
                                      <InlineTooltip 
                                        description="This golden section was created or verified by a human expert."
                                        position="bottom"
                                      />
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Metadata */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                              {section.methodology_tags && section.methodology_tags.length > 0 && (
                                <div>
                                  <span className="font-medium text-gray-700">Methodology:</span>
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {section.methodology_tags.map((tag: string, tagIndex: number) => (
                                      <span key={tagIndex} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {section.industry_keywords && section.industry_keywords.length > 0 && (
                                <div>
                                  <span className="font-medium text-gray-700">Industry Keywords:</span>
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {section.industry_keywords.map((keyword: string, keywordIndex: number) => (
                                      <span key={keywordIndex} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                                        {keyword}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Section Text */}
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Section Text:</h4>
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {section.section_text}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No Golden Sections Available</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      No golden sections were used during the generation of this survey.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 'llm-audit':
        return (
          <div className="h-full">
            <LLMAuditViewer 
              surveyId={survey?.survey_id}
              title="LLM Audit"
              showSummary={false}
              standalone={false}
            />
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
