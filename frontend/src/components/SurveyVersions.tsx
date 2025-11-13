import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { SurveyVersion } from '../types';
import { ArrowPathIcon, CheckCircleIcon, ClockIcon, ChatBubbleLeftRightIcon, DocumentTextIcon, CodeBracketIcon } from '@heroicons/react/24/outline';

interface SurveyVersionsProps {
  surveyId: string;
  hideHeader?: boolean;
}

export const SurveyVersions: React.FC<SurveyVersionsProps> = ({ surveyId, hideHeader = false }) => {
  const { getSurveyVersions, regenerateSurvey, addToast, currentSurvey, getAnnotationFeedbackPreview } = useAppStore();
  const [versions, setVersions] = useState<SurveyVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [versionNotes, setVersionNotes] = useState('');
  const [includeAnnotations, setIncludeAnnotations] = useState(true);
  const [regenerationMode, setRegenerationMode] = useState('surgical');
  const [selectedSections, setSelectedSections] = useState<number[]>([]);
  const [feedbackPreview, setFeedbackPreview] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  
  // Section names mapping
  const sectionNames: Record<number, string> = {
    1: "Sample Plan",
    2: "Screener",
    3: "Brand/Product Awareness",
    4: "Concept Exposure",
    5: "Methodology",
    6: "Additional Questions",
    7: "Programmer Instructions"
  };
  
  // Get the currently viewed survey ID
  const currentlyViewedId = currentSurvey?.survey_id || surveyId;

  useEffect(() => {
    loadVersions();
  }, [surveyId]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      const versionList = await getSurveyVersions(surveyId);
      // Normalize the response - API returns created_at (snake_case) but type expects createdAt (camelCase)
      const normalizedVersions = versionList.map((v: any) => ({
        ...v,
        createdAt: v.created_at || v.createdAt,
        isCurrent: v.is_current !== undefined ? v.is_current : v.isCurrent,
        parentSurveyId: v.parent_survey_id || v.parentSurveyId,
        versionNotes: v.version_notes || v.versionNotes
      }));
      setVersions(normalizedVersions);
    } catch (error) {
      console.error('Failed to load versions:', error);
      addToast({
        type: 'error',
        title: 'Load Failed',
        message: 'Failed to load survey versions'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadFeedbackPreview = async () => {
    if (!includeAnnotations) {
      setFeedbackPreview(null);
      return;
    }
    
    try {
      setLoadingPreview(true);
      const preview = await getAnnotationFeedbackPreview(surveyId);
      setFeedbackPreview(preview);
    } catch (error) {
      console.error('Failed to load feedback preview:', error);
      setFeedbackPreview(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  useEffect(() => {
    if (showRegenerateModal) {
      loadFeedbackPreview();
    }
  }, [showRegenerateModal, includeAnnotations]);

  // Auto-select sections with feedback when in surgical mode
  useEffect(() => {
    if (regenerationMode === 'surgical' && feedbackPreview?.feedback_collected) {
      const sectionsWithFeedback = new Set<number>();
      
      // Add sections with section-level feedback
      feedbackPreview.feedback_collected.section_feedback?.sections_with_feedback?.forEach((section: any) => {
        if (section.section_id && section.comments?.length > 0) {
          sectionsWithFeedback.add(section.section_id);
        }
      });
      
      // Add sections with question-level feedback (we'll need to infer section from question)
      // For now, we'll include all sections that have any question feedback
      if (feedbackPreview.feedback_collected.question_feedback?.questions_with_feedback?.length > 0) {
        // In surgical mode, we'll let the backend determine which sections need regeneration
        // But we can show all sections with feedback as selected
      }
      
      setSelectedSections(Array.from(sectionsWithFeedback));
    } else if (regenerationMode === 'targeted') {
      // In targeted mode, keep user selections
      // Don't auto-select
    } else if (regenerationMode === 'full') {
      // In full mode, select all sections
      setSelectedSections([1, 2, 3, 4, 5, 6, 7]);
    }
  }, [regenerationMode, feedbackPreview]);

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      
      // Determine target sections based on mode
      let targetSections: string[] | undefined;
      if (regenerationMode === 'targeted') {
        targetSections = selectedSections.map(s => s.toString());
      } else if (regenerationMode === 'surgical') {
        // Surgical mode: let backend auto-detect, but we can pass selected sections as hint
        targetSections = selectedSections.length > 0 ? selectedSections.map(s => s.toString()) : undefined;
      }
      // Full mode: don't pass target_sections, regenerate everything
      
      const result = await regenerateSurvey(surveyId, {
        includeAnnotations,
        versionNotes: versionNotes || undefined,
        focusOnAnnotatedAreas: true,
        regenerationMode,
        targetSections
      });
      
      setShowRegenerateModal(false);
      setVersionNotes('');
      setFeedbackPreview(null);
      setSelectedSections([]);
      setRegenerationMode('surgical');
      
      // Reload versions after a short delay
      setTimeout(() => {
        loadVersions();
      }, 2000);
    } catch (error) {
      console.error('Failed to regenerate:', error);
    } finally {
      setRegenerating(false);
    }
  };

  const handleVersionClick = (versionId: string) => {
    // Navigate to view this version
    window.location.href = `/surveys/${versionId}`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const currentVersion = versions.find(v => v.isCurrent);

  return (
    <div className="bg-white rounded-lg">
      {!hideHeader && (
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Survey Versions</h3>
          <button
            onClick={() => setShowRegenerateModal(true)}
            disabled={regenerating}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1.5" />
            Regenerate
          </button>
        </div>
      )}
      {hideHeader && (
        <div className="flex justify-end mb-5">
          <button
            onClick={() => setShowRegenerateModal(true)}
            disabled={regenerating}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1.5" />
            Regenerate
          </button>
        </div>
      )}

      <div className="space-y-3">
        {versions.length === 0 ? (
          <p className="text-gray-500 text-sm">No versions found</p>
        ) : (
          versions.map((version) => {
            const isCurrentlyViewed = version.id === currentlyViewedId;
            return (
            <div
              key={version.id}
              onClick={() => handleVersionClick(version.id)}
              className={`flex items-center p-4 rounded-lg border transition-all duration-200 cursor-pointer ${
                isCurrentlyViewed
                  ? 'bg-blue-100 border-blue-400 ring-2 ring-blue-300 shadow-md'
                  : version.isCurrent
                  ? 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100 hover:border-indigo-300 hover:shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {isCurrentlyViewed ? (
                  <CheckCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0" />
                ) : version.isCurrent ? (
                  <CheckCircleIcon className="h-5 w-5 text-indigo-600 flex-shrink-0" />
                ) : (
                  <ClockIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 flex-wrap gap-1.5">
                    <span className={`font-semibold text-sm ${
                      isCurrentlyViewed ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      Version {version.version}
                    </span>
                    {isCurrentlyViewed && (
                      <span className="px-2 py-0.5 text-xs font-semibold bg-blue-600 text-white rounded shadow-sm">
                        Viewing
                      </span>
                    )}
                    {version.isCurrent && !isCurrentlyViewed && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-800 rounded">
                        Current
                      </span>
                    )}
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                      version.status === 'validated'
                        ? 'bg-green-100 text-green-800'
                        : version.status === 'draft'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {version.status}
                    </span>
                  </div>
                  <div className={`text-xs mt-1.5 ${
                    isCurrentlyViewed ? 'text-blue-700' : 'text-gray-500'
                  }`}>
                    {(() => {
                      try {
                        const date = new Date(version.createdAt);
                        if (isNaN(date.getTime())) {
                          // Try parsing ISO string or other formats
                          const parsed = Date.parse(version.createdAt);
                          if (!isNaN(parsed)) {
                            const validDate = new Date(parsed);
                            return `${validDate.toLocaleDateString()} at ${validDate.toLocaleTimeString()}`;
                          }
                          return 'Date not available';
                        }
                        return `${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
                      } catch (e) {
                        return 'Date not available';
                      }
                    })()}
                  </div>
                  {version.versionNotes && (
                    <div className={`text-xs mt-1.5 leading-relaxed ${
                      isCurrentlyViewed ? 'text-blue-800' : 'text-gray-600'
                    }`}>
                      {version.versionNotes}
                    </div>
                  )}
                </div>
              </div>
            </div>
            );
          })
        )}
      </div>

      {/* Regenerate Modal */}
      {showRegenerateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-full max-w-4xl shadow-lg rounded-md bg-white my-10 max-h-[90vh] overflow-y-auto">
            <div className="mt-3">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Regenerate Survey</h3>
              
              <div className="mb-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeAnnotations}
                    onChange={(e) => setIncludeAnnotations(e.target.checked)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Include annotation feedback from all previous versions
                  </span>
                </label>
              </div>

              {/* Feedback Preview Section */}
              {includeAnnotations && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900 flex items-center">
                      <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2 text-indigo-600" />
                      Feedback That Will Be Used
                    </h4>
                    {loadingPreview && (
                      <div className="text-sm text-gray-500">Loading...</div>
                    )}
                  </div>

                  {loadingPreview ? (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
                      <p className="text-sm text-gray-600">Loading feedback preview...</p>
                    </div>
                  ) : feedbackPreview?.feedback_collected ? (
                    <div className="space-y-4">
                      {/* Section Feedback */}
                      {feedbackPreview.feedback_collected.section_feedback?.sections_with_feedback?.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-5">
                          <div className="flex items-center mb-3">
                            <DocumentTextIcon className="w-5 h-5 text-indigo-600 mr-2" />
                            <h5 className="text-base font-semibold text-gray-900">
                              Section-Level Feedback ({feedbackPreview.feedback_collected.section_feedback.total_count})
                            </h5>
                          </div>
                          <div className="space-y-3">
                            {feedbackPreview.feedback_collected.section_feedback.sections_with_feedback.slice(0, 10).map((section: any, idx: number) => {
                              const sectionNames: Record<number, string> = {
                                1: "Sample Plan",
                                2: "Screener",
                                3: "Brand/Product Awareness",
                                4: "Concept Exposure",
                                5: "Methodology",
                                6: "Additional Questions",
                                7: "Programmer Instructions"
                              };
                              const sectionName = sectionNames[section.section_id] || `Section ${section.section_id}`;
                              const latestComment = section.comments && section.comments.length > 0 
                                ? section.comments[section.comments.length - 1] 
                                : null;
                              
                              if (!latestComment?.comment) return null;
                              
                              return (
                                <div key={idx} className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                  <div className="flex items-start justify-between mb-2">
                                    <span className="text-sm font-semibold text-indigo-900">
                                      {sectionName} (v{latestComment.version || '?'})
                                    </span>
                                    {latestComment.quality !== undefined && (
                                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                                        latestComment.quality < 3 
                                          ? 'bg-red-100 text-red-700' 
                                          : latestComment.quality < 4
                                          ? 'bg-yellow-100 text-yellow-700'
                                          : 'bg-green-100 text-green-700'
                                      }`}>
                                        Quality: {latestComment.quality}/5
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                    {latestComment.comment}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Question Feedback */}
                      {feedbackPreview.feedback_collected.question_feedback?.questions_with_feedback?.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-5">
                          <div className="flex items-center mb-3">
                            <ChatBubbleLeftRightIcon className="w-5 h-5 text-indigo-600 mr-2" />
                            <h5 className="text-base font-semibold text-gray-900">
                              Question-Level Feedback ({feedbackPreview.feedback_collected.question_feedback.total_count})
                            </h5>
                          </div>
                          <div className="space-y-3">
                            {feedbackPreview.feedback_collected.question_feedback.questions_with_feedback.slice(0, 10).map((question: any, idx: number) => {
                              const latestComment = question.comments && question.comments.length > 0 
                                ? question.comments[question.comments.length - 1] 
                                : null;
                              
                              if (!latestComment?.comment) return null;
                              
                              return (
                                <div key={idx} className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                  <div className="flex items-start justify-between mb-2">
                                    <span className="text-sm font-semibold text-indigo-900">
                                      Question {question.question_id} (v{latestComment.version || '?'})
                                    </span>
                                    {latestComment.quality !== undefined && (
                                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                                        latestComment.quality < 3 
                                          ? 'bg-red-100 text-red-700' 
                                          : latestComment.quality < 4
                                          ? 'bg-yellow-100 text-yellow-700'
                                          : 'bg-green-100 text-green-700'
                                      }`}>
                                        Quality: {latestComment.quality}/5
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                    {latestComment.comment}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Survey-Level Feedback */}
                      {feedbackPreview.feedback_collected.survey_feedback?.overall_comments?.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-5">
                          <div className="flex items-center mb-3">
                            <DocumentTextIcon className="w-5 h-5 text-indigo-600 mr-2" />
                            <h5 className="text-base font-semibold text-gray-900">
                              Survey-Level Feedback ({feedbackPreview.feedback_collected.survey_feedback.total_count})
                            </h5>
                          </div>
                          <div className="space-y-2">
                            {feedbackPreview.feedback_collected.survey_feedback.overall_comments.map((item: any, idx: number) => {
                              const comment = typeof item === 'string' ? item : item.comment;
                              const version = typeof item === 'string' ? null : item.version;
                              return (
                                <div key={idx} className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                  {version && (
                                    <div className="text-xs font-semibold text-indigo-700 mb-2">
                                      Version {version}
                                    </div>
                                  )}
                                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{comment}</p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* No Feedback Message */}
                      {(!feedbackPreview.feedback_collected.section_feedback?.sections_with_feedback?.length && 
                        !feedbackPreview.feedback_collected.question_feedback?.questions_with_feedback?.length &&
                        !feedbackPreview.feedback_collected.survey_feedback?.overall_comments?.length) && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                          <ChatBubbleLeftRightIcon className="w-12 h-12 text-yellow-400 mx-auto mb-2" />
                          <h3 className="text-sm font-medium text-yellow-900 mb-1">No Feedback Available</h3>
                          <p className="text-sm text-yellow-700">
                            No annotation feedback found from previous versions. The regeneration will proceed without feedback.
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                      <ChatBubbleLeftRightIcon className="w-12 h-12 text-yellow-400 mx-auto mb-2" />
                      <h3 className="text-sm font-medium text-yellow-900 mb-1">No Feedback Available</h3>
                      <p className="text-sm text-yellow-700">
                        No annotation feedback found from previous versions. The regeneration will proceed without feedback.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Prompt Preview Section */}
              {includeAnnotations && feedbackPreview?.prompt_text && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900 flex items-center">
                      <CodeBracketIcon className="w-5 h-5 mr-2 text-indigo-600" />
                      Regeneration Section (Appended to Prompt)
                    </h4>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="mb-3 text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded-md p-3">
                      <strong>Note:</strong> This section is <strong>appended to the main prompt</strong>, not the entire prompt. 
                      The main prompt includes RFQ context, golden examples, and methodology rules. 
                      This regeneration section adds feedback and instructions for the selected sections.
                    </div>
                    <div className="mb-2 text-xs text-gray-600 font-medium">
                      Regeneration section that will be appended:
                    </div>
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono bg-white border border-gray-200 rounded p-4 max-h-96 overflow-y-auto">
                      {feedbackPreview.prompt_text}
                    </pre>
                    <div className="mt-2 text-xs text-gray-500">
                      This section: {feedbackPreview.prompt_text.length.toLocaleString()} chars
                      {regenerationMode === 'surgical' && (
                        <span className="ml-2 text-green-600">
                          (Optimized - only includes selected sections)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Regeneration Mode Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Regeneration Mode
                </label>
                <select
                  value={regenerationMode}
                  onChange={(e) => {
                    setRegenerationMode(e.target.value);
                    // Reset selections when mode changes
                    if (e.target.value === 'full') {
                      setSelectedSections([1, 2, 3, 4, 5, 6, 7]);
                    } else if (e.target.value === 'targeted') {
                      setSelectedSections([]);
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="surgical">
                    🔬 Surgical - Auto-select sections with feedback (recommended)
                  </option>
                  <option value="targeted">
                    🎯 Targeted - Manually select sections to regenerate
                  </option>
                  <option value="full">
                    🔄 Full - Regenerate entire survey from scratch
                  </option>
                </select>
                
                <div className="mt-3 space-y-2 text-sm">
                  {regenerationMode === 'surgical' && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                      <strong className="text-blue-900">Surgical Mode:</strong>
                      <ul className="mt-1 space-y-1 text-blue-800 list-disc list-inside">
                        <li>Automatically selects sections with feedback comments</li>
                        <li>Feedback is <strong>appended to the prompt</strong> as a separate section</li>
                        <li>Only selected sections are regenerated; others are preserved</li>
                        <li>Minimal prompt size - only includes context for selected sections</li>
                      </ul>
                    </div>
                  )}
                  
                  {regenerationMode === 'targeted' && (
                    <div className="bg-purple-50 border border-purple-200 rounded-md p-3">
                      <strong className="text-purple-900">Targeted Mode:</strong>
                      <ul className="mt-1 space-y-1 text-purple-800 list-disc list-inside">
                        <li>You manually select which sections to regenerate</li>
                        <li>Feedback is <strong>appended to the prompt</strong> as a separate section</li>
                        <li>Only selected sections are regenerated; others are preserved</li>
                        <li>Use when you want precise control over what changes</li>
                      </ul>
                    </div>
                  )}
                  
                  {regenerationMode === 'full' && (
                    <div className="bg-orange-50 border border-orange-200 rounded-md p-3">
                      <strong className="text-orange-900">Full Mode:</strong>
                      <ul className="mt-1 space-y-1 text-orange-800 list-disc list-inside">
                        <li>Regenerates entire survey from scratch</li>
                        <li>Feedback is <strong>appended to the prompt</strong> as a separate section</li>
                        <li>All sections are regenerated; nothing is preserved</li>
                        <li>Use only if you want a completely fresh survey</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Section Selection with Feedback */}
              {includeAnnotations && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Sections to Regenerate
                    {regenerationMode === 'surgical' && (
                      <span className="ml-2 text-xs font-normal text-gray-500">
                        (auto-selected based on feedback)
                      </span>
                    )}
                    {regenerationMode === 'targeted' && (
                      <span className="ml-2 text-xs font-normal text-gray-500">
                        (select manually)
                      </span>
                    )}
                    {regenerationMode === 'full' && (
                      <span className="ml-2 text-xs font-normal text-gray-500">
                        (all sections will be regenerated)
                      </span>
                    )}
                  </label>
                  
                  <div className="space-y-3 border border-gray-200 rounded-lg p-4 bg-gray-50">
                    {[1, 2, 3, 4, 5, 6, 7].map((sectionId) => {
                      const sectionName = sectionNames[sectionId];
                      const isSelected = selectedSections.includes(sectionId);
                      
                      // Find feedback for this section
                      const sectionFeedback = feedbackPreview?.feedback_collected?.section_feedback?.sections_with_feedback?.find(
                        (s: any) => s.section_id === sectionId
                      );
                      const latestComment = sectionFeedback?.comments?.[sectionFeedback.comments.length - 1];
                      
                      return (
                        <div
                          key={sectionId}
                          className={`border rounded-lg p-4 ${
                            isSelected
                              ? 'bg-indigo-50 border-indigo-300'
                              : 'bg-white border-gray-200'
                          }`}
                        >
                          <div className="flex items-start">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => {
                                if (regenerationMode === 'full') {
                                  // Full mode: can't uncheck (all must be selected)
                                  return;
                                }
                                if (e.target.checked) {
                                  setSelectedSections([...selectedSections, sectionId]);
                                } else {
                                  setSelectedSections(selectedSections.filter(s => s !== sectionId));
                                }
                              }}
                              disabled={regenerationMode === 'full'}
                              className="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <div className="ml-3 flex-1">
                              <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-gray-900 cursor-pointer">
                                  {sectionName} (Section {sectionId})
                                </label>
                                {latestComment && (
                                  <span className={`px-2 py-1 text-xs font-medium rounded ${
                                    latestComment.quality < 3 
                                      ? 'bg-red-100 text-red-700' 
                                      : latestComment.quality < 4
                                      ? 'bg-yellow-100 text-yellow-700'
                                      : 'bg-green-100 text-green-700'
                                  }`}>
                                    Quality: {latestComment.quality}/5
                                  </span>
                                )}
                              </div>
                              
                              {latestComment?.comment && (
                                <div className="mt-2 text-sm text-gray-700 bg-white border border-gray-200 rounded p-2">
                                  <div className="text-xs text-gray-500 mb-1">
                                    Feedback (v{latestComment.version || '?'}):
                                  </div>
                                  <p className="whitespace-pre-wrap">{latestComment.comment}</p>
                                </div>
                              )}
                              
                              {!latestComment && regenerationMode === 'targeted' && (
                                <p className="mt-1 text-xs text-gray-500">
                                  No feedback for this section
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {regenerationMode !== 'full' && (
                    <div className="mt-3 flex items-center justify-between text-sm">
                      <span className="text-gray-600">
                        {selectedSections.length} of 7 sections selected
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          if (selectedSections.length === 7) {
                            setSelectedSections([]);
                          } else {
                            setSelectedSections([1, 2, 3, 4, 5, 6, 7]);
                          }
                        }}
                        className="text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        {selectedSections.length === 7 ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version Notes (Optional)
                </label>
                <textarea
                  value={versionNotes}
                  onChange={(e) => setVersionNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Describe what changed in this version..."
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowRegenerateModal(false);
                    setVersionNotes('');
                    setFeedbackPreview(null);
                    setSelectedSections([]);
                    setRegenerationMode('surgical');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {regenerating ? 'Regenerating...' : 'Regenerate'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

