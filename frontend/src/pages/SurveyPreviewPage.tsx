import React, { useEffect, useState } from 'react';
import { SurveyPreview } from '../components/SurveyPreview';
import { ProgressStepper } from '../components/ProgressStepper';
import { useAppStore } from '../store/useAppStore';
import { getQuestionCount } from '../types';

export const SurveyPreviewPage: React.FC = () => {
  const {
    currentSurvey,
    workflow,
    setWorkflowState,
    connectWebSocket,
    fetchReviewByWorkflow,
    setActiveReview
  } = useAppStore();
  const [isPending, setIsPending] = useState(false);
  const [pendingType, setPendingType] = useState<'generation' | 'review' | null>(null);

  // Check if survey is pending (either generation or human review)
  useEffect(() => {
    if (currentSurvey) {
      const questionCount = getQuestionCount(currentSurvey);
      const isDraft = currentSurvey.metadata?.status === 'draft' ||
                     (currentSurvey as any).status === 'draft';
      const hasNoQuestions = questionCount === 0;

      console.log('🔍 [SurveyPreviewPage] Survey analysis:', {
        surveyId: currentSurvey.survey_id,
        questionCount,
        isDraft,
        hasNoQuestions,
        metadata: currentSurvey.metadata
      });

      // Check for human review pending state
      const checkForPendingReview = async () => {
        try {
          // Generate a workflow ID based on survey ID for review lookup
          const workflowId = `survey-gen-${currentSurvey.survey_id.replace('survey-', '')}`;
          const review = await fetchReviewByWorkflow(workflowId);

          if (review && (review.review_status === 'pending' || review.review_status === 'in_review')) {
            console.log('👥 [SurveyPreviewPage] Survey has pending human review, showing progress stepper');
            setIsPending(true);
            setPendingType('review');
            setActiveReview(review);

            // Set workflow state for human review
            setWorkflowState({
              status: 'in_progress',
              workflow_id: workflowId,
              survey_id: currentSurvey.survey_id,
              current_step: 'human_review',
              progress: 60,
              message: 'Waiting for human review approval...'
            });
            return;
          }
        } catch (error) {
          console.warn('⚠️ [SurveyPreviewPage] Failed to check for pending review:', error);
        }

        // If survey is in draft status and has no questions, it's still being generated
        if (isDraft && hasNoQuestions) {
          console.log('📊 [SurveyPreviewPage] Survey is still being generated, showing progress stepper');
          setIsPending(true);
          setPendingType('generation');

          // Try to reconnect to workflow if possible
          const workflowId = `survey-gen-${currentSurvey.survey_id.replace('survey-', '')}`;

          // Set workflow state to indicate generation in progress
          setWorkflowState({
            status: 'in_progress',
            workflow_id: workflowId,
            survey_id: currentSurvey.survey_id,
            current_step: 'generating_questions',
            progress: 50,
            message: 'Reconnecting to survey generation...'
          });

          // Try to connect to WebSocket
          try {
            connectWebSocket(workflowId);
          } catch (error) {
            console.warn('⚠️ [SurveyPreviewPage] Failed to reconnect to WebSocket:', error);
          }
        } else {
          setIsPending(false);
          setPendingType(null);
        }
      };

      checkForPendingReview();
    }
  }, [currentSurvey, setWorkflowState, connectWebSocket, fetchReviewByWorkflow, setActiveReview]);

  // Monitor workflow completion
  useEffect(() => {
    if (isPending && workflow.status === 'completed') {
      console.log('✅ [SurveyPreviewPage] Process completed, switching to preview');
      setIsPending(false);
      setPendingType(null);
    }
  }, [workflow.status, isPending]);

  // Note: Pillar scores are no longer automatically loaded
  // Users must manually trigger evaluation via the "Run Evaluation" button

  const getPageTitle = () => {
    if (pendingType === 'review') return 'Survey Review';
    if (pendingType === 'generation') return 'Survey Generation';
    return 'Survey Preview';
  };

  const getPageDescription = () => {
    if (pendingType === 'review') return 'Survey is pending human review and approval';
    if (pendingType === 'generation') return 'Your survey is being generated with AI-powered methodologies';
    return 'Review and refine your generated survey';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  {getPageTitle()}
                </h1>
                <p className="text-gray-600">{getPageDescription()}</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <a
                href="/"
                className="px-4 py-2 text-sm bg-gray-200 text-black rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Generator
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="py-8">
        {isPending ? (
          <div className="space-y-8">
            {/* Progress Stepper Section */}
            <div className="max-w-4xl mx-auto px-4">
              <ProgressStepper
                onShowSurvey={() => {
                  if (currentSurvey?.survey_id) {
                    // Refresh the page to show the completed survey
                    window.location.reload();
                  }
                }}
                onCancelGeneration={() => {
                  // Go back to generator
                  window.location.href = '/';
                }}
              />
            </div>

            {/* Show survey preview below progress stepper if survey has content */}
            {currentSurvey && getQuestionCount(currentSurvey) > 0 && (
              <div className="border-t border-gray-200 pt-8">
                <div className="max-w-6xl mx-auto px-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center space-x-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h3 className="text-blue-900 font-medium">
                        {pendingType === 'review' ? 'Survey Pending Review' : 'Survey Being Generated'}
                      </h3>
                    </div>
                    <p className="text-blue-700 text-sm mt-1">
                      {pendingType === 'review'
                        ? 'The survey below is awaiting human review. Changes may be made based on the review.'
                        : 'You can preview the current version below while generation continues.'
                      }
                    </p>
                  </div>
                  <SurveyPreview />
                </div>
              </div>
            )}
          </div>
        ) : (
          <SurveyPreview />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-300 mt-16">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Survey Generation Engine - Powered by AI & Golden Standard Examples
          </p>
        </div>
      </footer>
    </div>
  );
};












