import React, { useState, useEffect, useCallback } from 'react';
import { EnhancedRFQRequest } from '../types';

interface PromptPreviewProps {
  rfq: EnhancedRFQRequest;
  onPromptEdited?: (editedPrompt: string) => void;
}

interface PromptPreviewResponse {
  rfq_id?: string;
  prompt: string;
  prompt_length: number;
  context_info: {
    rfq_title: string;
    rfq_description_length: number;
    product_category: string;
    target_segment: string;
    research_goal: string;
    enhanced_rfq_fields: number;
  };
  methodology_tags: string[];
  golden_examples_count: number;
  methodology_blocks_count: number;
  enhanced_rfq_used: boolean;
  reference_examples?: {
    eight_questions_tab: {
      prompt_text: string;
      questions: Array<{
        id: string;
        question_text: string;
        question_type: string;
        annotation_comment?: string;
        quality_score?: number;
        human_verified?: boolean;
      }>;
    };
    manual_comment_digest_tab: {
      prompt_text: string;
      questions: Array<{
        id: string;
        question_text: string;
        question_type: string;
        annotation_comment?: string;
        quality_score?: number;
        human_verified?: boolean;
      }>;
      is_reconstructed: boolean;
      total_feedback_count: number;
    };
    golden_examples_tab: {
      prompt_text: string;
      examples: Array<{
        id: string;
        title: string;
        rfq_text: string;
        survey_title: string;
        methodology_tags?: string[];
        industry_category?: string;
        research_goal?: string;
        quality_score?: number;
        human_verified?: boolean;
        usage_count?: number;
      }>;
    };
    golden_sections_tab: {
      prompt_text: string;
      sections: Array<{
        id: string;
        section_id: string;
        section_title: string;
        section_text: string;
        section_type: string;
        methodology_tags?: string[];
        industry_keywords?: string[];
        quality_score?: number;
        human_verified?: boolean;
      }>;
    };
  };
}

export const PromptPreview: React.FC<PromptPreviewProps> = ({ rfq, onPromptEdited }) => {
  const [promptData, setPromptData] = useState<PromptPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullPrompt, setShowFullPrompt] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState<string>('');
  const [activePrompt, setActivePrompt] = useState<string>(''); // Stores the current prompt being displayed
  const [activeTab, setActiveTab] = useState<'prompt' | 'reference-examples'>('prompt');
  const [activeSubTab, setActiveSubTab] = useState<'eight-questions' | 'manual-comment-digest' | 'golden-examples' | 'golden-sections'>('eight-questions');

  const fetchPromptPreview = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Convert Enhanced RFQ to the format expected by the API
      const requestData = {
        rfq_id: `preview-${Date.now()}`, // Generate a unique RFQ ID for preview
        title: rfq.title,
        description: rfq.description,
        product_category: rfq.advanced_classification?.industry_classification || 'General',
        target_segment: rfq.research_objectives?.research_audience || 'General',
        research_goal: rfq.research_objectives?.success_criteria || 'Market research',
        enhanced_rfq_data: rfq
      };

      console.log('🔍 [PromptPreview] Sending request:', requestData);
      console.log('🔍 [PromptPreview] Generation config:', rfq.generation_config);

      const response = await fetch('/api/v1/rfq/preview-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PromptPreviewResponse = await response.json();
      setPromptData(data);
      setActivePrompt(data.prompt); // Initialize active prompt with original
      console.log('✅ [PromptPreview] Received prompt data:', data);
    } catch (err) {
      console.error('❌ [PromptPreview] Error fetching prompt preview:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch prompt preview');
    } finally {
      setIsLoading(false);
    }
  }, [rfq]);

  useEffect(() => {
    fetchPromptPreview();
  }, [fetchPromptPreview]);

  const handleStartEdit = () => {
    if (promptData) {
      setEditedPrompt(promptData.prompt);
      setIsEditing(true);
    }
  };

  const handleSaveEdit = () => {
    if (onPromptEdited) {
      onPromptEdited(editedPrompt);
    }
    // Update active prompt to show the edited version
    setActivePrompt(editedPrompt);
    setIsEditing(false);
    setError(null);
  };

  const handleCancelEdit = () => {
    setEditedPrompt('');
    setIsEditing(false);
    setError(null);
  };

  const handleRestoreOriginal = () => {
    if (promptData) {
      setEditedPrompt(promptData.prompt);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Generating prompt preview...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-red-800 font-semibold">Error Loading Prompt Preview</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
              <button
                onClick={fetchPromptPreview}
                className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!promptData) {
    return null;
  }

  // Use activePrompt (which may be edited) or original promptData.prompt
  const displayedPrompt = activePrompt || promptData.prompt;
  const promptPreview = showFullPrompt 
    ? displayedPrompt
    : displayedPrompt.substring(0, 5000) + (displayedPrompt.length > 5000 ? '...' : '');

  return (
    <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
      
      {/* Warning Banner */}
      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start">
        <span className="text-yellow-600 text-lg mr-2">⚠️</span>
        <p className="text-yellow-800 text-sm">
          <strong>Note:</strong> Any custom edits to this prompt will be lost if you navigate away without generating the survey.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('prompt')}
            className={`
              py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'prompt'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            Prompt
          </button>
          {promptData.reference_examples && (
            <button
              onClick={() => setActiveTab('reference-examples')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'reference-examples'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Reference Examples
            </button>
          )}
        </nav>
      </div>

      {/* Reference Examples Tab */}
      {activeTab === 'reference-examples' && promptData.reference_examples && (
        <div className="space-y-6">
          {/* Sub-tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveSubTab('eight-questions')}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm
                  ${activeSubTab === 'eight-questions'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                8 Questions
              </button>
              <button
                onClick={() => setActiveSubTab('manual-comment-digest')}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm
                  ${activeSubTab === 'manual-comment-digest'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                Manual Comment Digest
              </button>
              <button
                onClick={() => setActiveSubTab('golden-examples')}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm
                  ${activeSubTab === 'golden-examples'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                Golden Examples
              </button>
            </nav>
          </div>

          {/* 8 Questions Tab Content */}
          {activeSubTab === 'eight-questions' && (
            <div className="space-y-6">
              {promptData.reference_examples.eight_questions_tab.prompt_text && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {promptData.reference_examples.eight_questions_tab.prompt_text}
                    </pre>
                  </div>
                </div>
              )}
              {promptData.reference_examples.eight_questions_tab.questions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Questions Used</h3>
                  <div className="space-y-4">
                    {promptData.reference_examples.eight_questions_tab.questions.map((question, index) => (
                      <div key={question.id || index} className="bg-white border border-gray-200 rounded-lg p-5">
                        <div className="space-y-3">
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
                              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                                ✅ Human Verified
                              </span>
                            )}
                          </div>
                          <p className="text-base text-gray-900 font-medium">"{question.question_text}"</p>
                          {question.annotation_comment && (
                            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                              <span className="text-green-600 font-semibold text-sm">Expert Guidance:</span>
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
              )}
            </div>
          )}

          {/* Manual Comment Digest Tab Content */}
          {activeSubTab === 'manual-comment-digest' && (
            <div className="space-y-6">
              {promptData.reference_examples.manual_comment_digest_tab.prompt_text && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {promptData.reference_examples.manual_comment_digest_tab.prompt_text}
                    </pre>
                  </div>
                  {promptData.reference_examples.manual_comment_digest_tab.total_feedback_count > 0 && (
                    <p className="text-xs text-gray-600 mt-2">
                      Based on {promptData.reference_examples.manual_comment_digest_tab.total_feedback_count} questions with human-generated comments
                    </p>
                  )}
                </div>
              )}
              {promptData.reference_examples.manual_comment_digest_tab.questions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Questions Used</h3>
                  <div className="space-y-4">
                    {promptData.reference_examples.manual_comment_digest_tab.questions.map((question, index) => (
                      <div key={question.id || index} className="bg-white border border-gray-200 rounded-lg p-5">
                        <div className="space-y-3">
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
                              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                                ✅ Human Verified
                              </span>
                            )}
                          </div>
                          <p className="text-base text-gray-900 font-medium">"{question.question_text}"</p>
                          {question.annotation_comment && (
                            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                              <span className="text-green-600 font-semibold text-sm">Expert Guidance:</span>
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
              )}
            </div>
          )}

          {/* Golden Examples Tab Content */}
          {activeSubTab === 'golden-examples' && (
            <div className="space-y-6">
              {promptData.reference_examples.golden_examples_tab.prompt_text && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {promptData.reference_examples.golden_examples_tab.prompt_text}
                    </pre>
                  </div>
                </div>
              )}
              {promptData.reference_examples.golden_examples_tab.examples.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Golden RFQ-Survey Pairs Used</h3>
                  <div className="space-y-6">
                    {promptData.reference_examples.golden_examples_tab.examples.map((example, index) => (
                      <div key={example.id || index} className="bg-white border border-gray-200 rounded-lg p-6">
                        <div className="space-y-4">
                          <div className="border-b border-gray-200 pb-3">
                            <div className="flex items-start justify-between">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900">{example.title}</h4>
                                <p className="text-sm text-gray-600 mt-1">Survey: {example.survey_title}</p>
                              </div>
                              <div className="flex items-center gap-2 flex-wrap">
                                {example.quality_score !== undefined && (
                                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                    Quality: {example.quality_score.toFixed(2)}/1.0
                                  </span>
                                )}
                                {example.human_verified && (
                                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                                    ✅ Human Verified
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            {example.methodology_tags && example.methodology_tags.length > 0 && (
                              <div>
                                <span className="font-medium text-gray-700">Methodology:</span>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {example.methodology_tags.map((tag, tagIndex) => (
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
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">RFQ Text:</h5>
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
              )}
            </div>
          )}

          {/* Golden Sections Tab Content */}
          {activeSubTab === 'golden-sections' && (
            <div className="space-y-6">
              {promptData.reference_examples.golden_sections_tab.prompt_text && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">What Went Into the Prompt</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {promptData.reference_examples.golden_sections_tab.prompt_text}
                    </pre>
                  </div>
                </div>
              )}
              {promptData.reference_examples.golden_sections_tab.sections.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Golden Sections Used</h3>
                  <div className="space-y-6">
                    {promptData.reference_examples.golden_sections_tab.sections.map((section, index) => (
                      <div key={section.id || index} className="bg-white border border-gray-200 rounded-lg p-6">
                        <div className="space-y-4">
                          <div className="border-b border-gray-200 pb-3">
                            <div className="flex items-start justify-between">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900">{section.section_title}</h4>
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
                                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                                    ✅ Human Verified
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            {section.methodology_tags && section.methodology_tags.length > 0 && (
                              <div>
                                <span className="font-medium text-gray-700">Methodology:</span>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {section.methodology_tags.map((tag, tagIndex) => (
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
                                  {section.industry_keywords.map((keyword, keywordIndex) => (
                                    <span key={keywordIndex} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                                      {keyword}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">Section Text:</h5>
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
              )}
            </div>
          )}
        </div>
      )}

      {/* Prompt Tab Content */}
      {activeTab === 'prompt' && (
        <>
      {/* Prompt Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-xl">
          <h4 className="font-semibold text-blue-800 mb-1">Prompt Length</h4>
          <p className="text-blue-700 text-lg font-bold">{promptData.prompt_length.toLocaleString()} chars</p>
        </div>
        <div className="p-4 bg-green-50 rounded-xl">
          <h4 className="font-semibold text-green-800 mb-1">Golden Examples</h4>
          <p className="text-green-700 text-lg font-bold">{promptData.golden_examples_count}</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-xl">
          <h4 className="font-semibold text-purple-800 mb-1">Methodology Blocks</h4>
          <p className="text-purple-700 text-lg font-bold">{promptData.methodology_blocks_count}</p>
        </div>
      </div>

      {/* Methodology Tags */}
      {promptData.methodology_tags.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-800 mb-3">Methodology Tags</h3>
          <div className="flex flex-wrap gap-2">
            {promptData.methodology_tags.map((tag, index) => (
              <span key={index} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Context Information */}
      <div className="mb-6 p-4 bg-gray-50 rounded-xl">
        <h3 className="font-semibold text-gray-800 mb-3">Context Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Title:</span>
            <span className="ml-2 font-medium">{promptData.context_info.rfq_title || 'Untitled'}</span>
          </div>
          <div>
            <span className="text-gray-600">Description Length:</span>
            <span className="ml-2 font-medium">{promptData.context_info.rfq_description_length} chars</span>
          </div>
          <div>
            <span className="text-gray-600">Product Category:</span>
            <span className="ml-2 font-medium">{promptData.context_info.product_category}</span>
          </div>
          <div>
            <span className="text-gray-600">Target Segment:</span>
            <span className="ml-2 font-medium">{promptData.context_info.target_segment}</span>
          </div>
          <div>
            <span className="text-gray-600">Research Goal:</span>
            <span className="ml-2 font-medium">{promptData.context_info.research_goal}</span>
          </div>
          <div>
            <span className="text-gray-600">Enhanced Fields:</span>
            <span className="ml-2 font-medium">{promptData.context_info.enhanced_rfq_fields}</span>
          </div>
        </div>
      </div>

      {/* Prompt Content */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">Generated Prompt</h3>
          <div className="flex items-center space-x-2">
            {!isEditing && (
              <>
                  <button
                  onClick={handleStartEdit}
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
                >
                  {activePrompt !== promptData.prompt ? '✏️ Re-edit Prompt' : '✏️ Edit Prompt'}
                </button>
                {activePrompt !== promptData.prompt && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium flex items-center">
                    <span className="mr-1">✏️</span>
                    Custom Prompt Active
                  </span>
                )}
                <button
                  onClick={() => setShowFullPrompt(!showFullPrompt)}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm"
                >
                  {showFullPrompt ? 'Show Less' : 'Show Full Prompt'}
                </button>
              </>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleRestoreOriginal}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                >
                  Restore Original
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  ✓ Save Changes
                </button>
              </>
            )}
          </div>
        </div>
        
        {isEditing ? (
          <>
            <textarea
              value={editedPrompt}
              onChange={(e) => setEditedPrompt(e.target.value)}
              className="w-full bg-gray-900 text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto"
              style={{
                minHeight: '400px',
                resize: 'vertical',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace'
              }}
            />
            <div className="mt-2 text-sm text-gray-600">
              Character count: {editedPrompt.length.toLocaleString()} chars
            </div>
          </>
        ) : (
          <>
            <div className="bg-gray-900 text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto">
              <pre className="whitespace-pre-wrap">{promptPreview}</pre>
            </div>
            
            {!showFullPrompt && displayedPrompt.length > 1000 && (
              <p className="text-gray-500 text-sm mt-2 text-center">
                Showing first 1,000 characters of {displayedPrompt.length.toLocaleString()} total characters
              </p>
            )}
          </>
        )}
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchPromptPreview}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Refresh Preview
        </button>
      </div>
        </>
      )}
    </div>
  );
};
