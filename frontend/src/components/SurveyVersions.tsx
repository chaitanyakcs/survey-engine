import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { SurveyVersion, SurveyDiff } from '../types';
import { ArrowPathIcon, CheckCircleIcon, ClockIcon, ChatBubbleLeftRightIcon, DocumentTextIcon, CodeBracketIcon, EyeIcon, TrashIcon } from '@heroicons/react/24/outline';
import { SurveyDiffViewer } from './SurveyDiffViewer';


interface SurveyVersionsProps {
  surveyId: string;
  hideHeader?: boolean;
}

export const SurveyVersions: React.FC<SurveyVersionsProps> = ({ surveyId, hideHeader = false }) => {
  const { getSurveyVersions, regenerateSurvey, addToast, currentSurvey, getAnnotationFeedbackPreview, getSurveyDiff, workflow, resetWorkflow } = useAppStore();
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
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [diffData, setDiffData] = useState<SurveyDiff | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(false);
  const [diffTargetVersion, setDiffTargetVersion] = useState<string | null>(null);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<Set<string>>(new Set());
  const [deletingVersion, setDeletingVersion] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [versionToDelete, setVersionToDelete] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'feedback' | 'prompt'>('feedback');
  
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

  // Auto-show diff after regeneration completes and close progress modal
  useEffect(() => {
    const checkForRegenerationCompletion = async () => {
      // Check if this is a regeneration workflow that just completed
      const isRegenerationWorkflow = workflow.workflow_id?.includes('regenerate') || 
                                     workflow.current_step === 'regenerating' ||
                                     workflow.current_step === 'regeneration_prep';
      
      // Close progress modal when regeneration completes or fails
      if ((workflow.status === 'completed' || workflow.status === 'failed') && isRegenerationWorkflow && showProgressModal) {
        setShowProgressModal(false);
      }
      
      if (workflow.status === 'completed' && isRegenerationWorkflow && workflow.survey_id) {
        // Use the new survey ID from workflow (this is the regenerated survey)
        const newSurveyId = workflow.survey_id;
        
        // Check if we've already shown the diff for this completion
        const lastShownDiff = sessionStorage.getItem(`diff_shown_${newSurveyId}`);
        if (lastShownDiff === newSurveyId) {
          return; // Already shown
        }
        
        // Small delay to ensure survey is loaded
        setTimeout(async () => {
          try {
            setLoadingDiff(true);
            setDiffTargetVersion(newSurveyId);
            // Call diff without compare_with to auto-compare with parent
            const diff = await getSurveyDiff(newSurveyId);
            setDiffData(diff);
            setShowDiffModal(true);
            // Mark as shown
            sessionStorage.setItem(`diff_shown_${newSurveyId}`, newSurveyId);
            
            addToast({
              type: 'info',
              title: 'Viewing Changes',
              message: 'Showing what changed in this regeneration',
              duration: 4000
            });
          } catch (error) {
            console.error('Failed to auto-load diff after regeneration:', error);
            // Don't show error toast - diff might not be available yet
          } finally {
            setLoadingDiff(false);
          }
        }, 2000);
      }
    };

    checkForRegenerationCompletion();
  }, [workflow.status, workflow.workflow_id, workflow.survey_id, workflow.current_step, surveyId, getSurveyDiff, addToast, showProgressModal]);

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

  // Auto-select sections with feedback when in surgical or targeted mode
  useEffect(() => {
    if ((regenerationMode === 'surgical' || regenerationMode === 'targeted') && feedbackPreview?.feedback_collected) {
      const sectionsWithFeedback = new Set<number>();
      
      // Add sections with section-level feedback
      feedbackPreview.feedback_collected.section_feedback?.sections_with_feedback?.forEach((section: any) => {
        if (section.section_id && section.comments?.length > 0) {
          sectionsWithFeedback.add(section.section_id);
        }
      });
      
      // Add sections with question-level feedback
      if (feedbackPreview.feedback_collected.question_feedback?.questions_with_feedback?.length > 0) {
        feedbackPreview.feedback_collected.question_feedback.questions_with_feedback.forEach((question: any) => {
          const latestComment = question.comments && question.comments.length > 0 
            ? question.comments[question.comments.length - 1] 
            : null;
          
          if (!latestComment?.comment) return;
          
          // Determine which section this question belongs to
          if (currentSurvey?.sections) {
            // New format: sections with questions
            for (const section of currentSurvey.sections) {
              const questionInSection = section.questions?.find((q: any) => q.id === question.question_id);
              if (questionInSection) {
                sectionsWithFeedback.add(section.id);
                break;
              }
            }
          } else if (currentSurvey?.questions) {
            // Legacy format: try to infer from category
            const foundQuestion = currentSurvey.questions.find((q: any) => q.id === question.question_id);
            if (foundQuestion?.category) {
              const categoryToSection: Record<string, number> = {
                'screener': 2,
                'awareness': 3,
                'concept': 4,
                'methodology': 5,
                'additional': 6,
                'programmer': 7
              };
              const inferredSection = categoryToSection[foundQuestion.category.toLowerCase()];
              if (inferredSection) {
                sectionsWithFeedback.add(inferredSection);
              }
            }
          }
        });
      }
      
      setSelectedSections(Array.from(sectionsWithFeedback));
    } else if (regenerationMode === 'full') {
      // In full mode, select all sections
      setSelectedSections([1, 2, 3, 4, 5, 6, 7]);
    }
  }, [regenerationMode, feedbackPreview, currentSurvey]);

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      
      // Close the modal immediately - show loading state in UI
      setShowRegenerateModal(false);
      
      // Determine target sections based on mode
      let targetSections: string[] | undefined;
      if (regenerationMode === 'targeted') {
        targetSections = selectedSections.map(s => s.toString());
      } else if (regenerationMode === 'surgical') {
        // Surgical mode: let backend auto-detect, but we can pass selected sections as hint
        targetSections = selectedSections.length > 0 ? selectedSections.map(s => s.toString()) : undefined;
      }
      // Full mode: don't pass target_sections, regenerate everything
      
      console.log('🔄 [SurveyVersions] Starting synchronous regeneration...');
      
      // This will WAIT for completion (no WebSocket, no progress modal)
      const result = await regenerateSurvey(surveyId, {
        includeAnnotations,
        versionNotes: versionNotes || undefined,
        focusOnAnnotatedAreas: true,
        regenerationMode,
        targetSections
      });
      
      console.log('✅ [SurveyVersions] Regeneration completed:', result);
      
      // Reset form state
      setVersionNotes('');
      setFeedbackPreview(null);
      setSelectedSections([]);
      setRegenerationMode('surgical');
      
      // Reload versions to show the new version
      await loadVersions();
      
      // Navigate to the new survey
      console.log('🔄 [SurveyVersions] Redirecting to new survey:', result.survey_id);
      window.location.href = `/surveys/${result.survey_id}`;
    } catch (error) {
      console.error('❌ [SurveyVersions] Failed to regenerate:', error);
      setRegenerating(false);
    }
  };

  const handleVersionClick = (versionId: string) => {
    // Navigate to view this version
    window.location.href = `/surveys/${versionId}`;
  };

  const handleViewChanges = async (e: React.MouseEvent, versionId: string) => {
    e.stopPropagation(); // Prevent version click
    try {
      setLoadingDiff(true);
      setDiffTargetVersion(versionId);
      
      // Find the version to get its parent
      const version = versions.find(v => v.id === versionId);
      if (!version) {
        throw new Error('Version not found');
      }
      
      // Compare this version with its parent, or with currently viewed if no parent
      const compareWith = version.parentSurveyId || (versionId !== currentlyViewedId ? currentlyViewedId : null);
      
      if (!compareWith) {
        addToast({
          type: 'error',
          title: 'Cannot Compare',
          message: 'No previous version to compare with',
          duration: 3000
        });
        return;
      }
      
      // Compare versionId (newer) with compareWith (older)
      const diff = await getSurveyDiff(versionId, compareWith);
      setDiffData(diff);
      setShowDiffModal(true);
    } catch (error) {
      console.error('Failed to load diff:', error);
      addToast({
        type: 'error',
        title: 'Diff Failed',
        message: error instanceof Error ? error.message : 'Failed to load survey diff',
        duration: 5000
      });
    } finally {
      setLoadingDiff(false);
    }
  };

  const handleDeleteVersion = async (e: React.MouseEvent, versionId: string) => {
    e.stopPropagation(); // Prevent version click
    setVersionToDelete(versionId);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteVersion = async () => {
    if (!versionToDelete) return;
    
    try {
      setDeletingVersion(versionToDelete);
      setShowDeleteConfirm(false);
      const response = await fetch(`/api/v1/survey/${versionToDelete}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete version');
      }
      
      addToast({
        type: 'success',
        title: 'Version Deleted',
        message: 'Survey version has been deleted successfully',
        duration: 3000
      });
      
      // Reload versions
      await loadVersions();
      
      // If deleted version was selected, remove from selection
      if (selectedVersions.has(versionToDelete)) {
        const newSelected = new Set(selectedVersions);
        newSelected.delete(versionToDelete);
        setSelectedVersions(newSelected);
      }
    } catch (error) {
      console.error('Failed to delete version:', error);
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: error instanceof Error ? error.message : 'Failed to delete version',
        duration: 5000
      });
    } finally {
      setDeletingVersion(null);
      setVersionToDelete(null);
    }
  };

  const handleVersionSelect = (versionId: string) => {
    const newSelected = new Set(selectedVersions);
    if (newSelected.has(versionId)) {
      newSelected.delete(versionId);
    } else {
      if (newSelected.size >= 2) {
        addToast({
          type: 'info',
          title: 'Selection Limit',
          message: 'You can only select 2 versions for comparison',
          duration: 3000
        });
        return;
      }
      newSelected.add(versionId);
    }
    setSelectedVersions(newSelected);
  };

  const handleCompareSelected = async () => {
    if (selectedVersions.size !== 2) {
      addToast({
        type: 'error',
        title: 'Invalid Selection',
        message: 'Please select exactly 2 versions to compare',
        duration: 3000
      });
      return;
    }
    
    const [versionId1, versionId2] = Array.from(selectedVersions);
    
    // Find the versions to get their version numbers
    const version1 = versions.find(v => v.id === versionId1);
    const version2 = versions.find(v => v.id === versionId2);
    
    if (!version1 || !version2) {
      addToast({
        type: 'error',
        title: 'Invalid Selection',
        message: 'Could not find version information',
        duration: 3000
      });
      return;
    }
    
    // Sort by version number: newer version first (higher version number)
    const newerVersion = version1.version > version2.version ? versionId1 : versionId2;
    const olderVersion = version1.version > version2.version ? versionId2 : versionId1;
    
    try {
      setLoadingDiff(true);
      // Compare newer version (first param) with older version (second param)
      const diff = await getSurveyDiff(newerVersion, olderVersion);
      setDiffData(diff);
      setShowDiffModal(true);
      setSelectedVersions(new Set()); // Clear selection after opening diff
    } catch (error) {
      console.error('Failed to load diff:', error);
      addToast({
        type: 'error',
        title: 'Diff Failed',
        message: error instanceof Error ? error.message : 'Failed to load survey diff',
        duration: 5000
      });
    } finally {
      setLoadingDiff(false);
    }
  };

  // Check if there's an active regeneration workflow
  const isRegenerationWorkflow = workflow.workflow_id?.includes('regenerate') || 
                                 workflow.current_step === 'regenerating' ||
                                 workflow.current_step === 'regeneration_prep';
  const hasActiveRegeneration = (workflow.status === 'started' || 
                                 workflow.status === 'in_progress' || 
                                 workflow.status === 'paused') && 
                                isRegenerationWorkflow;

  // Auto-open progress modal when regeneration starts
  useEffect(() => {
    if (hasActiveRegeneration && !showProgressModal) {
      setShowProgressModal(true);
    } else if ((!hasActiveRegeneration || workflow.status === 'completed' || workflow.status === 'failed') && showProgressModal) {
      // Auto-close when regeneration completes or fails
      setShowProgressModal(false);
    }
  }, [hasActiveRegeneration, showProgressModal, workflow.status, workflow.workflow_id, workflow.current_step]);

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

      {/* Regeneration in progress indicator */}
      {hasActiveRegeneration && !showProgressModal && (
        <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600"></div>
            <div>
              <p className="text-sm font-medium text-indigo-900">Regeneration in progress</p>
              <p className="text-xs text-indigo-700">Your survey is being regenerated</p>
            </div>
          </div>
          <button
            onClick={() => setShowProgressModal(true)}
            className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-100 hover:bg-indigo-200 rounded-md transition-colors"
          >
            View Progress
          </button>
        </div>
      )}

      {/* Compare selected versions */}
      {selectedVersions.size > 0 && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-blue-900">
              {selectedVersions.size} version{selectedVersions.size !== 1 ? 's' : ''} selected
            </span>
            <button
              onClick={() => setSelectedVersions(new Set())}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Clear
            </button>
          </div>
          {selectedVersions.size === 2 && (
            <button
              onClick={handleCompareSelected}
              disabled={loadingDiff}
              className="p-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Compare selected versions"
            >
              {loadingDiff ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <EyeIcon className="w-4 h-4" />
              )}
            </button>
          )}
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
              className={`flex items-center p-4 rounded-lg border transition-all duration-200 ${
                isCurrentlyViewed
                  ? 'bg-blue-100 border-blue-400 ring-2 ring-blue-300 shadow-md'
                  : version.isCurrent
                  ? 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100 hover:border-indigo-300 hover:shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300 hover:shadow-sm'
              } ${selectedVersions.has(version.id) ? 'ring-2 ring-blue-500' : ''}`}
            >
              {/* Selection checkbox */}
              <input
                type="checkbox"
                checked={selectedVersions.has(version.id)}
                onChange={() => handleVersionSelect(version.id)}
                onClick={(e) => e.stopPropagation()}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
              />
              
              <div 
                onClick={() => handleVersionClick(version.id)}
                className="flex items-center space-x-3 flex-1 min-w-0 cursor-pointer"
              >
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
                    {version.parentSurveyId && (
                      <span 
                        className="px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded"
                        title="This version was regenerated with comment tracking"
                      >
                        Regenerated
                      </span>
                    )}
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
              <div className="flex items-center gap-2 ml-2">
                {version.parentSurveyId && (
                  <button
                    onClick={(e) => handleViewChanges(e, version.id)}
                    disabled={loadingDiff && diffTargetVersion === version.id}
                    className="p-2 text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="View changes from previous version"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={(e) => handleDeleteVersion(e, version.id)}
                  disabled={deletingVersion === version.id || isCurrentlyViewed}
                  className="p-2 text-red-600 bg-red-50 hover:bg-red-100 rounded border border-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isCurrentlyViewed ? "Cannot delete the version you are currently viewing. Please navigate to a different version first." : "Delete this version"}
                >
                  {deletingVersion === version.id ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                  ) : (
                    <TrashIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            );
          })
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <TrashIcon className="h-6 w-6 text-red-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Delete Version?
              </h3>
              <p className="text-sm text-gray-600 text-center mb-6">
                Are you sure you want to delete this version? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setVersionToDelete(null);
                  }}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteVersion}
                  disabled={deletingVersion !== null}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deletingVersion ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Diff Modal */}
      {showDiffModal && diffData && (
        <SurveyDiffViewer
          diff={diffData}
          onClose={() => {
            setShowDiffModal(false);
            setDiffData(null);
            setDiffTargetVersion(null);
          }}
          isModal={true}
        />
      )}

      {/* Regeneration Progress Modal - Simple Loading State */}
      {showProgressModal && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
            <div className="flex flex-col items-center text-center space-y-6">
              {/* Animated Loading Icon */}
              <div className="relative">
                {/* Outer spinning ring */}
                <div className="w-24 h-24 rounded-full border-4 border-indigo-100"></div>
                <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-t-indigo-600 border-r-indigo-500 border-b-transparent border-l-transparent animate-spin"></div>
                
                {/* Inner pulsing circle */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-indigo-100 animate-pulse flex items-center justify-center">
                    <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Title and Description */}
              <div className="space-y-2">
                <h3 className="text-2xl font-bold text-gray-900">Regenerating Survey</h3>
                <p className="text-base text-gray-600 max-w-sm">
                  Processing your annotations and regenerating the survey. This typically takes 15-30 seconds.
                </p>
              </div>

              {/* Progress indicator */}
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>

              {/* Status text */}
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse"></div>
                <span className="font-medium">Please wait while we regenerate your survey...</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Modal */}
      {showRegenerateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto border w-full max-w-4xl shadow-lg rounded-md bg-white my-10 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
              <h3 className="text-xl font-semibold text-gray-900">Regenerate Survey</h3>
              <button
                onClick={() => {
                  setShowRegenerateModal(false);
                  setVersionNotes('');
                  setFeedbackPreview(null);
                  setSelectedSections([]);
                  setRegenerationMode('surgical');
                  setActiveTab('feedback');
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                title="Close"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
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

              {/* Tab Navigation */}
              {includeAnnotations && (
                <div className="mb-6 border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8">
                    <button
                      onClick={() => setActiveTab('feedback')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'feedback'
                          ? 'border-indigo-500 text-indigo-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <span className="flex items-center">
                        <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
                        Feedback & Sections
                      </span>
                    </button>
                    {feedbackPreview?.prompt_text && (
                      <button
                        onClick={() => setActiveTab('prompt')}
                        className={`py-4 px-1 border-b-2 font-medium text-sm ${
                          activeTab === 'prompt'
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <span className="flex items-center">
                          <CodeBracketIcon className="w-5 h-5 mr-2" />
                          Prompt Changes
                        </span>
                      </button>
                    )}
                  </nav>
                </div>
              )}

              {/* Tab Content */}
              {includeAnnotations && (
                <div className="mb-6">
                  {activeTab === 'feedback' && (
                    <div className="space-y-6">
                      {loadingPreview ? (
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
                          <p className="text-sm text-gray-600">Loading feedback preview...</p>
                        </div>
                      ) : feedbackPreview?.feedback_collected ? (
                        <>
                          {/* Survey-Level Feedback - Show at top if available */}
                          {feedbackPreview.feedback_collected.survey_feedback?.overall_comments?.length > 0 && (
                            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                              <div className="flex items-center mb-3">
                                <DocumentTextIcon className="w-5 h-5 text-indigo-600 mr-2" />
                                <h5 className="text-sm font-semibold text-indigo-900">
                                  Survey-Level Feedback
                                </h5>
                              </div>
                              <div className="space-y-2">
                                {feedbackPreview.feedback_collected.survey_feedback.overall_comments.map((item: any, idx: number) => {
                                  const comment = typeof item === 'string' ? item : item.comment;
                                  const version = typeof item === 'string' ? null : item.version;
                                  return (
                                    <div key={idx} className="bg-white border border-indigo-200 rounded p-3">
                                      {version && (
                                        <div className="text-xs font-semibold text-indigo-700 mb-1">
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

                          {/* Section Selection with Feedback */}
                      <div>
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
                            const latestSectionComment = sectionFeedback?.comments?.[sectionFeedback.comments.length - 1];
                            
                            // Find question-level feedback for this section
                            const questionsInSection: any[] = [];
                            if (feedbackPreview?.feedback_collected?.question_feedback?.questions_with_feedback) {
                              for (const question of feedbackPreview.feedback_collected.question_feedback.questions_with_feedback) {
                                const latestQuestionComment = question.comments && question.comments.length > 0 
                                  ? question.comments[question.comments.length - 1] 
                                  : null;
                                
                                if (!latestQuestionComment?.comment) continue;
                                
                                // Determine if this question belongs to this section
                                let belongsToSection = false;
                                if (currentSurvey?.sections) {
                                  const section = currentSurvey.sections.find((s: any) => s.id === sectionId);
                                  if (section?.questions?.find((q: any) => q.id === question.question_id)) {
                                    belongsToSection = true;
                                  }
                                } else if (currentSurvey?.questions) {
                                  // Legacy format: try to infer from category
                                  const foundQuestion = currentSurvey.questions.find((q: any) => q.id === question.question_id);
                                  if (foundQuestion?.category) {
                                    const categoryToSection: Record<string, number> = {
                                      'screener': 2,
                                      'awareness': 3,
                                      'concept': 4,
                                      'methodology': 5,
                                      'additional': 6,
                                      'programmer': 7
                                    };
                                    const inferredSection = categoryToSection[foundQuestion.category.toLowerCase()];
                                    if (inferredSection === sectionId) {
                                      belongsToSection = true;
                                    }
                                  }
                                }
                                
                                if (belongsToSection) {
                                  questionsInSection.push({
                                    question_id: question.question_id,
                                    comment: latestQuestionComment
                                  });
                                }
                              }
                            }
                            
                            const hasFeedback = latestSectionComment?.comment || questionsInSection.length > 0;
                            
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
                                      {latestSectionComment && (
                                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                                          latestSectionComment.quality < 3 
                                            ? 'bg-red-100 text-red-700' 
                                            : latestSectionComment.quality < 4
                                            ? 'bg-yellow-100 text-yellow-700'
                                            : 'bg-green-100 text-green-700'
                                        }`}>
                                          Quality: {latestSectionComment.quality}/5
                                        </span>
                                      )}
                                    </div>
                                    
                                    {/* Section-level feedback */}
                                    {latestSectionComment?.comment && (
                                      <div className="mt-2 text-sm text-gray-700 bg-white border border-gray-200 rounded p-2">
                                        <div className="text-xs text-gray-500 mb-1">
                                          Section Feedback (v{latestSectionComment.version || '?'}):
                                        </div>
                                        <p className="whitespace-pre-wrap">{latestSectionComment.comment}</p>
                                      </div>
                                    )}
                                    
                                    {/* Question-level feedback for this section */}
                                    {questionsInSection.length > 0 && (
                                      <div className="mt-2 space-y-2">
                                        {questionsInSection.map((q, idx) => (
                                          <div key={idx} className="text-sm text-gray-700 bg-white border border-gray-200 rounded p-2">
                                            <div className="text-xs text-gray-500 mb-1">
                                              Question {q.question_id} Feedback (v{q.comment.version || '?'}):
                                              {q.comment.quality !== undefined && (
                                                <span className={`ml-2 px-1.5 py-0.5 text-xs font-medium rounded ${
                                                  q.comment.quality < 3 
                                                    ? 'bg-red-100 text-red-700' 
                                                    : q.comment.quality < 4
                                                    ? 'bg-yellow-100 text-yellow-700'
                                                    : 'bg-green-100 text-green-700'
                                                }`}>
                                                  Quality: {q.comment.quality}/5
                                                </span>
                                              )}
                                            </div>
                                            <p className="whitespace-pre-wrap">{q.comment.comment}</p>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {!hasFeedback && regenerationMode === 'targeted' && (
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
                        </>
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

                  {activeTab === 'prompt' && feedbackPreview?.prompt_text && (
                    <div>
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
                    setActiveTab('feedback');
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

