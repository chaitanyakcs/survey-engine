import React, { useState, useEffect } from 'react';
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
import { PendingReview, ReviewDecision } from '../types';

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
    workflow 
  } = useAppStore();
  
  const [loading, setLoading] = useState(true);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showFullPrompt, setShowFullPrompt] = useState(false);

  useEffect(() => {
    if (isActive && (workflowId || workflow.workflow_id)) {
      fetchReviewData();
    }
  }, [isActive, workflowId, workflow.workflow_id]);

  const fetchReviewData = async () => {
    setLoading(true);
    try {
      const targetWorkflowId = workflowId || workflow.workflow_id;
      if (!targetWorkflowId) {
        setLoading(false);
        return;
      }
      
      await fetchReviewByWorkflow(targetWorkflowId);
    } catch (error) {
      console.error('Failed to fetch review data:', error);
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">System Prompt Review</h2>
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(activeReview.review_status)}`}>
            {getStatusIcon(activeReview.review_status)}
            <span className="ml-2 capitalize">{activeReview.review_status.replace('_', ' ')}</span>
          </div>
        </div>
        
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div className="flex items-center">
            <CalendarIcon className="w-4 h-4 mr-2" />
            Generated: {new Date(activeReview.created_at).toLocaleString()}
          </div>
          {activeReview.review_deadline && (
            <div className="flex items-center">
              <ClockIcon className="w-4 h-4 mr-2" />
              Deadline: {new Date(activeReview.review_deadline).toLocaleString()}
            </div>
          )}
        </div>
      </div>

      {/* Original RFQ Context */}
      <div className="bg-blue-50 rounded-xl p-4">
        <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
          <DocumentTextIcon className="w-5 h-5 mr-2" />
          Original Request Context
        </h3>
        <p className="text-blue-800 text-sm leading-relaxed">{activeReview.original_rfq}</p>
      </div>

      {/* Generated Prompt */}
      <div className="bg-white border border-gray-200 rounded-xl">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 flex items-center">
              <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
              AI-Generated System Prompt
            </h3>
            <button
              onClick={() => setShowFullPrompt(!showFullPrompt)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              {showFullPrompt ? 'Show Less' : 'Show Full Prompt'}
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className={`text-gray-800 text-sm leading-relaxed whitespace-pre-wrap ${!showFullPrompt ? 'line-clamp-6' : ''}`}>
            {showFullPrompt ? activeReview.prompt_data : activeReview.prompt_data.substring(0, 300) + '...'}
          </div>
        </div>
      </div>

      {/* Review Criteria Checklist */}
      <div className="bg-gray-50 rounded-xl p-4">
        <h3 className="font-semibold text-gray-900 mb-4">Review Criteria</h3>
        <div className="space-y-3">
          {[
            'Clear and specific instructions',
            'Appropriate question types and methodology',
            'No leading or biased language',
            'Suitable length and complexity',
            'Demographic considerations included',
            'Actionable insights potential'
          ].map((criteria, index) => (
            <div key={index} className="flex items-center space-x-3">
              <input
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                defaultChecked={false}
              />
              <span className="text-sm text-gray-700">{criteria}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Review Notes */}
      {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Review Notes (Optional)
          </label>
          <textarea
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            rows={3}
            placeholder="Add any comments, suggestions, or concerns about this prompt..."
          />
        </div>
      )}

      {/* Existing Review (if completed) */}
      {(activeReview.review_status === 'approved' || activeReview.review_status === 'rejected') && activeReview.reviewer_id && (
        <div className="bg-gray-50 rounded-xl p-4">
          <div className="flex items-center mb-3">
            <UserIcon className="w-5 h-5 text-gray-600 mr-2" />
            <span className="font-medium text-gray-900">Review by {activeReview.reviewer_id}</span>
            <span className="text-gray-500 text-sm ml-2">
              • {new Date(activeReview.updated_at).toLocaleString()}
            </span>
          </div>
          {activeReview.reviewer_notes && (
            <p className="text-gray-700 text-sm leading-relaxed">{activeReview.reviewer_notes}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {(activeReview.review_status === 'pending' || activeReview.review_status === 'in_review') && (
        <div className="flex space-x-4 pt-4 border-t border-gray-200">
          <button
            onClick={handleReject}
            disabled={submitting}
            className="flex-1 inline-flex items-center justify-center px-6 py-3 border border-red-300 rounded-xl text-red-700 bg-red-50 hover:bg-red-100 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircleIcon className="w-5 h-5 mr-2" />
            {submitting ? 'Processing...' : 'Reject Prompt'}
          </button>
          <button
            onClick={handleApprove}
            disabled={submitting}
            className="flex-1 inline-flex items-center justify-center px-6 py-3 border border-green-300 rounded-xl text-green-700 bg-green-50 hover:bg-green-100 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircleIcon className="w-5 h-5 mr-2" />
            {submitting ? 'Processing...' : 'Approve Prompt'}
          </button>
        </div>
      )}

      {/* Success State */}
      {activeReview.review_status === 'approved' && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="w-6 h-6 text-green-600 mr-3" />
            <div>
              <h4 className="text-green-900 font-medium">Prompt Approved</h4>
              <p className="text-green-700 text-sm">Survey generation will continue automatically.</p>
            </div>
          </div>
        </div>
      )}

      {/* Rejection State */}
      {activeReview.review_status === 'rejected' && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center">
            <XCircleIcon className="w-6 h-6 text-red-600 mr-3" />
            <div>
              <h4 className="text-red-900 font-medium">Prompt Rejected</h4>
              <p className="text-red-700 text-sm">A new prompt will be generated for review.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};