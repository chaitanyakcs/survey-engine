import React, { useState, useEffect, useCallback } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  UserIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  PencilIcon,
  ArrowUturnLeftIcon
} from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';
import { ReviewDecision, EditPromptRequest } from '../types';

interface HumanReviewPanelProps {
  isActive: boolean;
  workflowId?: string;
  surveyId?: string;
}

export const HumanReviewPanel: React.FC<HumanReviewPanelProps> = ({ 
  isActive, 
  workflowId,
  surveyId 
}) => {
  const { 
    activeReview, 
    fetchReviewByWorkflow, 
    submitReviewDecision, 
    setActiveReview,
    workflow 
  } = useAppStore();
  
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showFullPrompt, setShowFullPrompt] = useState(false);
  const [showFullOriginalRequest, setShowFullOriginalRequest] = useState(false);

  // Prompt editing state
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState('');
  const [editReason, setEditReason] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Timeout state
  const [timeoutRemaining, setTimeoutRemaining] = useState(30 * 60); // 30 minutes in seconds
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);

  // Helper function to truncate text to approximately 4 lines
  const truncateToLines = (text: string, maxLines: number = 4) => {
    const lines = text.split('\n');
    if (lines.length <= maxLines) return text;
    return lines.slice(0, maxLines).join('\n');
  };

  const fetchReviewData = useCallback(async (currentRetryCount = 0) => {
    const maxRetries = 3;
    const baseDelay = 1000; // 1 second base delay
    
    setLoading(true);
    setRetryCount(currentRetryCount);
    
    try {
      const targetWorkflowId = workflowId || workflow.workflow_id;
      if (!targetWorkflowId) {
        setLoading(false);
        return;
      }
      
      console.log(`🔄 [HumanReviewPanel] Fetching review data (attempt ${currentRetryCount + 1}/${maxRetries + 1})...`);
      const review = await fetchReviewByWorkflow(targetWorkflowId);
      
      if (review) {
        setActiveReview(review);
        console.log('✅ [HumanReviewPanel] Review data loaded:', review);
        setLoading(false);
        return;
      } else {
        console.log(`⚠️ [HumanReviewPanel] No review found for workflow: ${targetWorkflowId} (attempt ${currentRetryCount + 1})`);
        
        // Retry if we haven't exceeded max retries
        if (currentRetryCount < maxRetries) {
          const delay = baseDelay * Math.pow(2, currentRetryCount); // Exponential backoff
          console.log(`⏳ [HumanReviewPanel] Retrying in ${delay}ms...`);
          
          setTimeout(() => {
            fetchReviewData(currentRetryCount + 1);
          }, delay);
          return;
        } else {
          console.error('❌ [HumanReviewPanel] Max retries exceeded, review not found');
          setLoading(false);
        }
      }
    } catch (error) {
      console.error(`❌ [HumanReviewPanel] Failed to fetch review data (attempt ${currentRetryCount + 1}):`, error);
      
      // Retry on error if we haven't exceeded max retries
      if (currentRetryCount < maxRetries) {
        const delay = baseDelay * Math.pow(2, currentRetryCount); // Exponential backoff
        console.log(`⏳ [HumanReviewPanel] Retrying after error in ${delay}ms...`);
        
        setTimeout(() => {
          fetchReviewData(currentRetryCount + 1);
        }, delay);
        return;
      } else {
        console.error('❌ [HumanReviewPanel] Max retries exceeded after errors');
        setLoading(false);
      }
    }
  }, [workflowId, workflow.workflow_id, fetchReviewByWorkflow, setActiveReview]);

  useEffect(() => {
    if (isActive && (workflowId || workflow.workflow_id)) {
      console.log('🔄 [HumanReviewPanel] Starting review data fetch with retry logic...');
      fetchReviewData();
    }
  }, [isActive, workflowId, workflow.workflow_id, fetchReviewData]);

  // Timeout countdown effect
  useEffect(() => {
    if (!isActive || !activeReview || submitting) return;

    const interval = setInterval(() => {
      setTimeoutRemaining(prev => {
        const newTime = prev - 1;

        // Show warning at 5 minutes remaining
        if (newTime === 5 * 60 && !showTimeoutWarning) {
          setShowTimeoutWarning(true);
          // Add toast notification
          useAppStore.getState().addToast({
            type: 'warning',
            title: 'Review Timeout Warning',
            message: 'You have 5 minutes remaining to complete the review. The workflow will auto-resume with the default prompt if no action is taken.',
            duration: 10000
          });
        }

        // Auto-resume at timeout
        if (newTime <= 0) {
          console.log('⏰ [HumanReviewPanel] Review timeout reached - auto-resuming with default prompt');

          useAppStore.getState().addToast({
            type: 'warning',
            title: 'Review Timeout',
            message: 'Review timed out after 30 minutes. Workflow resumed with default prompt.',
            duration: 8000
          });

          // Auto-approve with timeout reason
          const timeoutDecision: ReviewDecision = {
            decision: 'approve',
            notes: 'Auto-approved due to 30-minute timeout',
            reason: 'Review timed out - proceeding with default prompt to prevent workflow hanging'
          };

          submitReviewDecision(activeReview.id, timeoutDecision).catch((error) => {
            console.error('❌ [HumanReviewPanel] Failed to auto-approve on timeout:', error);
          });

          clearInterval(interval);
          return 0;
        }

        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, activeReview, submitting, showTimeoutWarning, submitReviewDecision]);

  // Format time remaining for display
  const formatTimeRemaining = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const handleApprove = async () => {
    if (!activeReview) return;
    
    setSubmitting(true);
    try {
      const decision: ReviewDecision = {
        decision: 'approve',
        notes: reviewNotes,
        reason: 'Prompt meets quality standards and methodology requirements'
      };
      
      await submitReviewDecision(activeReview.id, decision);
      setReviewNotes(''); // Clear notes after submission
    } catch (error) {
      console.error('Failed to approve prompt:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!activeReview) return;

    setSubmitting(true);
    try {
      const decision: ReviewDecision = {
        decision: 'reject',
        notes: reviewNotes,
        reason: 'Prompt requires revision to meet quality standards'
      };

      await submitReviewDecision(activeReview.id, decision);
      setReviewNotes(''); // Clear notes after submission
    } catch (error) {
      console.error('Failed to reject prompt:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApproveWithEdits = async () => {
    if (!activeReview) return;

    setSubmitting(true);
    try {
      const decision: ReviewDecision = {
        decision: 'approve_with_edits',
        notes: reviewNotes,
        reason: 'Prompt approved with manual edits applied'
      };

      await submitReviewDecision(activeReview.id, decision);
      setReviewNotes(''); // Clear notes after submission
    } catch (error) {
      console.error('Failed to approve prompt with edits:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartEdit = () => {
    if (!activeReview) return;

    // Initialize edit with current prompt (edited or original)
    const currentPrompt = activeReview.edited_prompt_data || activeReview.prompt_data;
    setEditedPrompt(currentPrompt);
    setEditReason('');
    setEditingPrompt(true);
  };

  const handleCancelEdit = () => {
    setEditingPrompt(false);
    setEditedPrompt('');
    setEditReason('');
  };

  const handleSaveEdit = async () => {
    if (!activeReview || !editedPrompt.trim()) return;

    setSavingEdit(true);
    try {
      const editRequest: EditPromptRequest = {
        edited_prompt: editedPrompt.trim(),
        edit_reason: editReason.trim() || undefined
      };

      const response = await fetch(`/api/v1/reviews/${activeReview.id}/edit-prompt`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editRequest),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save prompt edit');
      }

      const updatedReview = await response.json();
      setActiveReview(updatedReview);
      setEditingPrompt(false);
      setEditedPrompt('');
      setEditReason('');

      console.log('✅ [HumanReviewPanel] Prompt edit saved successfully');
    } catch (error) {
      console.error('❌ [HumanReviewPanel] Failed to save prompt edit:', error);
      // You could add a toast notification here
    } finally {
      setSavingEdit(false);
    }
  };

  const resetToOriginal = () => {
    if (!activeReview?.original_prompt_data) return;
    setEditedPrompt(activeReview.original_prompt_data);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'in_review': return 'text-yellow-600 bg-yellow-50';
      case 'approved': return 'text-green-600 bg-green-50';
      case 'rejected': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <ClockIcon className="w-4 h-4" />;
      case 'in_review': return <EyeIcon className="w-4 h-4" />;
      case 'approved': return <CheckCircleIcon className="w-4 h-4" />;
      case 'rejected': return <XCircleIcon className="w-4 h-4" />;
      default: return <ClockIcon className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Review Data</h3>
          {retryCount > 0 && (
            <p className="text-sm text-gray-600">
              Attempt {retryCount + 1} of 4 - Retrying...
            </p>
          )}
          <p className="text-sm text-gray-500">
            {retryCount === 0 
              ? "Fetching review data..." 
              : "Review not ready yet, retrying with exponential backoff..."
            }
          </p>
        </div>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!activeReview) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Review Data</h3>
          <p className="text-gray-500">Unable to load prompt review information.</p>
        </div>
      </div>
    );
  }

  console.log('🔍 [HumanReviewPanel] Rendering with activeReview:', {
    id: activeReview.id,
    status: activeReview.review_status,
    canApprove: activeReview.review_status === 'pending' || activeReview.review_status === 'in_review'
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">System Prompt Review</h2>
        <div className="flex items-center space-x-3">
          {/* Timeout Display */}
          {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              showTimeoutWarning
                ? 'text-red-700 bg-red-100'
                : timeoutRemaining <= 10 * 60
                  ? 'text-yellow-700 bg-yellow-100'
                  : 'text-gray-700 bg-gray-100'
            }`}>
              <ClockIcon className="w-3 h-3 mr-1" />
              <span>
                {showTimeoutWarning ? '⚠️ ' : ''}
                {formatTimeRemaining(timeoutRemaining)} remaining
              </span>
            </div>
          )}

          {/* Status Badge */}
          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activeReview.review_status)}`}>
            {getStatusIcon(activeReview.review_status)}
            <span className="ml-1 capitalize">{activeReview.review_status.replace('_', ' ')}</span>
          </div>
        </div>
      </div>

      {/* Timeout Warning Message */}
      {showTimeoutWarning && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-2 mt-0.5" />
            <div>
              <h4 className="text-red-900 font-medium text-sm">Review Timeout Warning</h4>
              <p className="text-red-700 text-xs mt-1">
                Only <strong>{formatTimeRemaining(timeoutRemaining)}</strong> remaining!
                The workflow will auto-resume with the default prompt if no action is taken.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Metadata */}
      <div className="flex gap-4 text-xs text-gray-600">
        <div className="flex items-center">
          <CalendarIcon className="w-3 h-3 mr-1" />
          {new Date(activeReview.created_at).toLocaleString()}
        </div>
        {activeReview.review_deadline && (
          <div className="flex items-center">
            <ClockIcon className="w-3 h-3 mr-1" />
            {new Date(activeReview.review_deadline).toLocaleString()}
          </div>
        )}
      </div>

      {/* Original RFQ Context */}
      <div className="bg-yellow-50 rounded-lg p-3">
        <h3 className="font-medium text-yellow-900 mb-1 flex items-center text-sm">
          <DocumentTextIcon className="w-4 h-4 mr-1" />
          Original Request Context
        </h3>
        <div className="text-yellow-800 text-xs leading-relaxed">
          <pre className="whitespace-pre-wrap font-sans">
            {showFullOriginalRequest ? activeReview.original_rfq : truncateToLines(activeReview.original_rfq)}
          </pre>
          {activeReview.original_rfq.split('\n').length > 4 && (
            <button
              onClick={() => setShowFullOriginalRequest(!showFullOriginalRequest)}
              className="mt-2 text-yellow-700 hover:text-yellow-900 font-medium text-xs underline focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-opacity-50 rounded"
            >
              {showFullOriginalRequest ? 'Read less' : 'Read more'}
            </button>
          )}
        </div>
      </div>

      {/* System Prompt Section */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-medium text-gray-900 flex items-center text-sm">
            <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
            System Prompt
            {activeReview.prompt_edited && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                Edited
              </span>
            )}
          </h3>
          <div className="flex items-center space-x-2">
            {!editingPrompt && (activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
              <button
                onClick={handleStartEdit}
                className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center"
              >
                <PencilIcon className="w-3 h-3 mr-1" />
                Edit
              </button>
            )}
            <button
              onClick={() => setShowFullPrompt(!showFullPrompt)}
              className="text-yellow-600 hover:text-yellow-800 text-xs font-medium"
            >
              {showFullPrompt ? 'Show Less' : 'Show Full'}
            </button>
          </div>
        </div>

        <div className="p-3">
          {editingPrompt ? (
            // Editing Mode
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Edit System Prompt
                </label>
                <textarea
                  value={editedPrompt}
                  onChange={(e) => setEditedPrompt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-xs leading-relaxed font-mono resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  rows={12}
                  placeholder="Enter the revised system prompt..."
                />
                <div className="mt-2 text-xs text-gray-500">
                  {editedPrompt.length} characters {editedPrompt.length < 10 && '(minimum 10 required)'}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Edit Reason (Optional)
                </label>
                <textarea
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-xs resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="Explain why you're editing the prompt..."
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex space-x-2">
                  {activeReview.original_prompt_data && (
                    <button
                      onClick={resetToOriginal}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      <ArrowUturnLeftIcon className="w-3 h-3 mr-1" />
                      Reset to Original
                    </button>
                  )}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleCancelEdit}
                    disabled={savingEdit}
                    className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    disabled={savingEdit || editedPrompt.trim().length < 10}
                    className="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {savingEdit ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            // Display Mode
            <div className="space-y-2">
              <div className={`text-gray-800 text-xs leading-relaxed whitespace-pre-wrap font-mono ${!showFullPrompt ? 'line-clamp-4' : ''}`}>
                {(() => {
                  const currentPrompt = activeReview.edited_prompt_data || activeReview.prompt_data;
                  return showFullPrompt ? currentPrompt : currentPrompt.substring(0, 200) + '...';
                })()}
              </div>

              {activeReview.prompt_edited && activeReview.edited_by && (
                <div className="text-xs text-gray-500 border-t pt-2">
                  <div className="flex items-center justify-between">
                    <span>Edited by {activeReview.edited_by}</span>
                    {activeReview.prompt_edit_timestamp && (
                      <span>{new Date(activeReview.prompt_edit_timestamp).toLocaleString()}</span>
                    )}
                  </div>
                  {activeReview.edit_reason && (
                    <div className="mt-1 text-gray-600 italic">
                      "{activeReview.edit_reason}"
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Review Criteria Checklist */}
      <div className="bg-gray-50 rounded-lg p-3">
        <h3 className="font-medium text-gray-900 mb-2 text-sm">Review Criteria</h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            'Clear instructions',
            'Appropriate methodology',
            'No biased language',
            'Suitable length',
            'Demographics included',
            'Actionable insights'
          ].map((criteria, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="checkbox"
                className="w-3 h-3 text-yellow-600 rounded focus:ring-yellow-500"
                defaultChecked={false}
              />
              <span className="text-xs text-gray-700">{criteria}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Review Notes */}
      {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Review Notes (Optional)
          </label>
          <textarea
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-yellow-500 focus:border-yellow-500 resize-none"
            rows={2}
            placeholder="Add comments or concerns..."
          />
        </div>
      )}

      {/* Existing Review (if completed) */}
      {(activeReview.review_status === 'approved' || activeReview.review_status === 'rejected') && activeReview.reviewer_id && (
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center mb-1">
            <UserIcon className="w-4 h-4 text-gray-600 mr-1" />
            <span className="font-medium text-gray-900 text-sm">Review by {activeReview.reviewer_id}</span>
            <span className="text-gray-500 text-xs ml-1">
              • {new Date(activeReview.updated_at).toLocaleString()}
            </span>
          </div>
          {activeReview.reviewer_notes && (
            <p className="text-gray-700 text-xs leading-relaxed">{activeReview.reviewer_notes}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && !editingPrompt && (
        <div className="space-y-2 pt-2 border-t border-gray-200">
          {/* Primary Actions */}
          <div className="flex space-x-2">
            <button
              onClick={handleReject}
              disabled={submitting}
              className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-red-300 rounded-lg text-red-700 bg-red-50 hover:bg-red-100 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <XCircleIcon className="w-4 h-4 mr-1" />
              {submitting ? 'Processing...' : 'Reject'}
            </button>
            <button
              onClick={handleApprove}
              disabled={submitting}
              className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-green-300 rounded-lg text-green-700 bg-green-50 hover:bg-green-100 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              {submitting ? 'Processing...' : 'Approve'}
            </button>
          </div>

          {/* Approve with Edits - Only show if prompt has been edited */}
          {activeReview.prompt_edited && (
            <button
              onClick={handleApproveWithEdits}
              disabled={submitting}
              className="w-full inline-flex items-center justify-center px-3 py-2 border border-blue-300 rounded-lg text-blue-700 bg-blue-50 hover:bg-blue-100 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              {submitting ? 'Processing...' : 'Approve with Edits'}
            </button>
          )}
        </div>
      )}

      {/* Status Messages */}
      {activeReview.review_status === 'approved' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-center">
            <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
            <div>
              <h4 className="text-green-900 font-medium text-sm">Prompt Approved</h4>
              <p className="text-green-700 text-xs">Survey generation will continue automatically.</p>
            </div>
          </div>
        </div>
      )}

      {activeReview.review_status === 'rejected' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center">
            <XCircleIcon className="w-5 h-5 text-red-600 mr-2" />
            <div>
              <h4 className="text-red-900 font-medium text-sm">Prompt Rejected</h4>
              <p className="text-red-700 text-xs">A new prompt will be generated for review.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};