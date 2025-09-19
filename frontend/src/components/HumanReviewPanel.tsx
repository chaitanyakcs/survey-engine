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
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';
import { ReviewDecision } from '../types';

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'in_review': return 'text-blue-600 bg-blue-50';
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
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
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activeReview.review_status)}`}>
          {getStatusIcon(activeReview.review_status)}
          <span className="ml-1 capitalize">{activeReview.review_status.replace('_', ' ')}</span>
        </div>
      </div>
      
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
      <div className="bg-blue-50 rounded-lg p-3">
        <h3 className="font-medium text-blue-900 mb-1 flex items-center text-sm">
          <DocumentTextIcon className="w-4 h-4 mr-1" />
          Original Request Context
        </h3>
        <p className="text-blue-800 text-xs leading-relaxed">{activeReview.original_rfq}</p>
      </div>

      {/* Generated Prompt */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-medium text-gray-900 flex items-center text-sm">
            <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
            AI-Generated System Prompt
          </h3>
          <button
            onClick={() => setShowFullPrompt(!showFullPrompt)}
            className="text-blue-600 hover:text-blue-800 text-xs font-medium"
          >
            {showFullPrompt ? 'Show Less' : 'Show Full'}
          </button>
        </div>
        <div className="p-3">
          <div className={`text-gray-800 text-xs leading-relaxed whitespace-pre-wrap ${!showFullPrompt ? 'line-clamp-4' : ''}`}>
            {showFullPrompt ? activeReview.prompt_data : activeReview.prompt_data.substring(0, 200) + '...'}
          </div>
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
                className="w-3 h-3 text-blue-600 rounded focus:ring-blue-500"
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
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
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
      {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
        <div className="flex space-x-2 pt-2 border-t border-gray-200">
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