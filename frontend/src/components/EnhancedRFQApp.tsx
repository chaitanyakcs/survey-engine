import React, { useState, useEffect } from 'react';
import { EnhancedRFQEditor } from './EnhancedRFQEditor';
import { PreGenerationPreview } from './PreGenerationPreview';
import { ProgressStepper } from './ProgressStepper';
import { useAppStore } from '../store/useAppStore';

type ViewMode = 'editor' | 'preview';

export const EnhancedRFQApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('editor');
  const { enhancedRfq, submitEnhancedRFQ, workflow, clearEnhancedRfqState, resetWorkflow, addToast } = useAppStore();

  const handleShowPreview = () => {
    setCurrentView('preview');
  };

  const handleEditRequirements = () => {
    setCurrentView('editor');
  };

  const handleGenerate = async () => {
    try {
      console.log('🔍 [EnhancedRFQApp] handleGenerate called - submitting RFQ');
      await submitEnhancedRFQ(enhancedRfq);
      // Clear the form state after successful submission
      console.log('🔍 [EnhancedRFQApp] RFQ submitted successfully - clearing state');
      clearEnhancedRfqState();
    } catch (error) {
      console.error('Failed to generate survey:', error);
    }
  };

  // Check if there's an active workflow and redirect to progress stepper
  useEffect(() => {
    const hasActiveWorkflow = workflow.status === 'started' || 
                             workflow.status === 'in_progress' || 
                             workflow.status === 'paused' || 
                             workflow.status === 'completed';
    
    if (hasActiveWorkflow) {
      console.log('🔄 [EnhancedRFQApp] Active workflow detected, redirecting to progress stepper:', {
        status: workflow.status,
        workflowId: workflow.workflow_id,
        surveyId: workflow.survey_id
      });
      
      // Show notification to user
      addToast({
        type: 'info',
        title: 'Survey Generation in Progress',
        message: 'You have a survey generation in progress. Redirecting to progress view...',
        duration: 3000
      });
    }
  }, [workflow.status, workflow.workflow_id, workflow.survey_id, addToast]);

  // If workflow is active, show progress stepper instead of RFQ interface
  const hasActiveWorkflow = workflow.status === 'started' || 
                           workflow.status === 'in_progress' || 
                           workflow.status === 'paused' || 
                           workflow.status === 'completed';

  if (hasActiveWorkflow) {
    return (
      <div className="px-6">
        {/* Header explaining why user is seeing progress stepper */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Survey Generation in Progress
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>You have an active survey generation. You can monitor the progress below or cancel to start a new generation.</p>
              </div>
            </div>
          </div>
        </div>
        
        <ProgressStepper 
          onCancelGeneration={() => {
            console.log('🔄 [EnhancedRFQApp] Canceling generation from progress stepper');
            resetWorkflow();
          }}
        />
      </div>
    );
  }

  return (
    <div className="enhanced-rfq-app">
      {currentView === 'editor' && (
        <EnhancedRFQEditor onPreview={handleShowPreview} />
      )}

      {currentView === 'preview' && (
        <PreGenerationPreview
          rfq={enhancedRfq}
          onGenerate={handleGenerate}
          onEdit={handleEditRequirements}
        />
      )}
    </div>
  );
};

export default EnhancedRFQApp;