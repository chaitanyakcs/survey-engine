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

interface ReviewData {
  id: string;
  prompt: string;
  rfq_content: string;
  generated_at: string;
  status: 'pending' | 'approved' | 'rejected' | 'in_review';
  reviewer?: string;
  review_notes?: string;
  reviewed_at?: string;
  estimated_completion?: string;
}

interface HumanReviewPanelProps {
  isActive: boolean;
  surveyId?: string;
}

export const HumanReviewPanel: React.FC<HumanReviewPanelProps> = ({ 
  isActive, 
  surveyId 
}) => {
  const [reviewData, setReviewData] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showFullPrompt, setShowFullPrompt] = useState(false);

  useEffect(() => {
    if (isActive && surveyId) {
      fetchReviewData();
    }
  }, [isActive, surveyId]);

  const fetchReviewData = async () => {
    setLoading(true);
    try {
      // Mock data for now - replace with actual API call
      const mockData: ReviewData = {
        id: 'review-123',
        prompt: `You are an expert survey methodologist tasked with creating a comprehensive customer satisfaction survey for a mid-sized e-commerce company. The survey should focus on:

1. Overall satisfaction with the shopping experience
2. Product quality and variety assessment
3. Website usability and navigation
4. Customer service interactions
5. Shipping and delivery experience
6. Return and refund process evaluation
7. Likelihood to recommend to others

Please ensure the survey:
- Uses a mix of question types (Likert scales, multiple choice, open-ended)
- Maintains respondent engagement (10-12 minutes max)
- Follows survey methodology best practices
- Avoids leading or biased questions
- Includes demographic questions for segmentation
- Provides actionable insights for business improvement

Target audience: Online shoppers aged 25-55 who have made at least one purchase in the last 6 months.`,
        rfq_content: 'Customer satisfaction survey for e-commerce platform focusing on user experience, product quality, and service effectiveness.',
        generated_at: new Date().toISOString(),
        status: 'pending',
        estimated_completion: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString() // 2 hours from now
      };
      
      setReviewData(mockData);
    } catch (error) {
      console.error('Failed to fetch review data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!reviewData) return;
    
    setSubmitting(true);
    try {
      // API call to approve the prompt
      console.log('Approving prompt with notes:', reviewNotes);
      
      setReviewData({
        ...reviewData,
        status: 'approved',
        reviewer: 'Dr. Sarah Mitchell',
        review_notes: reviewNotes,
        reviewed_at: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to approve prompt:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!reviewData) return;
    
    setSubmitting(true);
    try {
      // API call to reject the prompt
      console.log('Rejecting prompt with notes:', reviewNotes);
      
      setReviewData({
        ...reviewData,
        status: 'rejected',
        reviewer: 'Dr. Sarah Mitchell',
        review_notes: reviewNotes,
        reviewed_at: new Date().toISOString()
      });
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

  if (!reviewData) {
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
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(reviewData.status)}`}>
            {getStatusIcon(reviewData.status)}
            <span className="ml-2 capitalize">{reviewData.status.replace('_', ' ')}</span>
          </div>
        </div>
        
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div className="flex items-center">
            <CalendarIcon className="w-4 h-4 mr-2" />
            Generated: {new Date(reviewData.generated_at).toLocaleString()}
          </div>
          {reviewData.estimated_completion && (
            <div className="flex items-center">
              <ClockIcon className="w-4 h-4 mr-2" />
              Est. Completion: {new Date(reviewData.estimated_completion).toLocaleString()}
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
        <p className="text-blue-800 text-sm leading-relaxed">{reviewData.rfq_content}</p>
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
            {showFullPrompt ? reviewData.prompt : reviewData.prompt.substring(0, 300) + '...'}
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
      {(reviewData.status === 'pending' || reviewData.status === 'in_review') && (
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
      {(reviewData.status === 'approved' || reviewData.status === 'rejected') && reviewData.reviewer && (
        <div className="bg-gray-50 rounded-xl p-4">
          <div className="flex items-center mb-3">
            <UserIcon className="w-5 h-5 text-gray-600 mr-2" />
            <span className="font-medium text-gray-900">Review by {reviewData.reviewer}</span>
            <span className="text-gray-500 text-sm ml-2">
              • {new Date(reviewData.reviewed_at!).toLocaleString()}
            </span>
          </div>
          {reviewData.review_notes && (
            <p className="text-gray-700 text-sm leading-relaxed">{reviewData.review_notes}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {(reviewData.status === 'pending' || reviewData.status === 'in_review') && (
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
      {reviewData.status === 'approved' && (
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
      {reviewData.status === 'rejected' && (
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