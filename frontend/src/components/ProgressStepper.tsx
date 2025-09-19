import React, { useState, useEffect } from 'react';
import { CheckIcon, ClockIcon, SparklesIcon } from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';
import { HumanReviewPanel } from './HumanReviewPanel';

interface SimplifiedStep {
  key: string;
  label: string;
  description: string;
  icon: string;
  color: string;
  originalSteps: string[];
  conditional?: boolean;
  details: {
    title: string;
    content: string;
    subTasks: string[];
    estimatedTime: string;
  };
}

const SIMPLIFIED_STEPS: SimplifiedStep[] = [
  { 
    key: 'preparing_request', 
    label: 'Preparing Request', 
    description: 'Analyzing and understanding your requirements',
    icon: '📋',
    color: 'blue',
    originalSteps: ['initializing_workflow', 'parsing_rfq', 'generating_embeddings', 'rfq_parsed'],
    details: {
      title: 'Request Analysis & Setup',
      content: 'We\'re analyzing your RFQ to understand your research objectives, target audience, and key goals. This includes generating semantic embeddings to find the best matching examples and templates.',
      subTasks: [
        'Parsing research requirements',
        'Identifying target demographics', 
        'Extracting key objectives',
        'Creating semantic embeddings'
      ],
      estimatedTime: '30-60 seconds'
    }
  },
  { 
    key: 'building_context', 
    label: 'Building Context', 
    description: 'Assembling best practices and templates',
    icon: '🔗',
    color: 'purple',
    originalSteps: ['matching_golden_examples', 'planning_methodologies'],
    details: {
      title: 'Context Assembly & Template Matching',
      content: 'Finding the most relevant survey examples from our curated database and combining them with methodology blocks and industry best practices tailored to your research goals.',
      subTasks: [
        'Matching golden examples',
        'Selecting methodology blocks',
        'Assembling context framework',
        'Preparing generation templates'
      ],
      estimatedTime: '45-90 seconds'
    }
  },
  {
    key: 'human_review',
    label: 'Human Review',
    description: 'Expert validation of system prompts',
    icon: '👥',
    color: 'orange',
    originalSteps: ['human_review'], // Map backend step names
    conditional: true, // Only shown when prompt review is enabled
    details: {
      title: 'System Prompt Review & Approval',
      content: 'Our experts are reviewing the AI-generated system prompt to ensure it meets quality standards and aligns with your specific requirements before survey generation begins.',
      subTasks: [
        'Prompt quality assessment',
        'Methodology validation',
        'Bias detection review',
        'Approval workflow'
      ],
      estimatedTime: '2-24 hours (configurable)'
    }
  },
  { 
    key: 'creating_questions', 
    label: 'Creating Questions', 
    description: 'Generating your survey content',
    icon: '✍️',
    color: 'green',
    originalSteps: ['generating_questions'],
    details: {
      title: 'AI-Powered Survey Generation',
      content: 'Using advanced language models to craft clear, unbiased questions that drive actionable insights. Each question is designed to align with research best practices and your specific objectives.',
      subTasks: [
        'Generating question content',
        'Structuring survey flow',
        'Optimizing for clarity',
        'Ensuring methodological rigor'
      ],
      estimatedTime: '60-120 seconds'
    }
  },
  { 
    key: 'evaluating_quality', 
    label: 'Quality Evaluation', 
    description: 'Comprehensive quality assessment',
    icon: '🔍',
    color: 'yellow',
    originalSteps: ['validation_scoring'],
    details: {
      title: 'Advanced Pillar-Based Evaluation',
      content: 'Running comprehensive quality checks using our 5-pillar evaluation framework: methodological rigor, content validity, respondent experience, analytical value, and business impact.',
      subTasks: [
        'Methodological rigor assessment',
        'Content validity scoring',
        'User experience evaluation',
        'Business impact analysis'
      ],
      estimatedTime: '30-60 seconds'
    }
  },
  { 
    key: 'survey_complete', 
    label: 'Survey Complete', 
    description: 'Your professional survey is ready',
    icon: '🎉',
    color: 'emerald',
    originalSteps: ['completed'],
    details: {
      title: 'Survey Ready for Deployment',
      content: 'Your survey has been successfully generated and evaluated. It\'s now ready for deployment to your target audience with comprehensive quality scores and recommendations.',
      subTasks: [
        'Final quality verification',
        'Deployment preparation',
        'Performance optimization',
        'Ready for launch'
      ],
      estimatedTime: 'Complete'
    }
  }
];

interface ProgressStepperProps {
  onShowSurvey?: () => void;
  onCancelGeneration?: () => void;
  onShowSummary?: () => void;
}

export const ProgressStepper: React.FC<ProgressStepperProps> = ({ 
  onShowSurvey, 
  onCancelGeneration,
  onShowSummary
}) => {
  const { workflow, currentSurvey, activeReview } = useAppStore();
  const workflowStatus = workflow.status;
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [enabledSteps, setEnabledSteps] = useState<SimplifiedStep[]>([]);
  
  // Get settings to determine if human review step should be shown
  const [showHumanReview, setShowHumanReview] = useState(false);

  // Determine if human review should be shown based on workflow state
  useEffect(() => {
    const shouldShowHumanReview = Boolean(
      // There's an active review
      !!activeReview ||
      // Workflow is paused for human review
      (!!workflow.workflow_paused && workflow.current_step === 'human_review') ||
      // Current step is specifically human_review
      workflow.current_step === 'human_review'
    );

    console.log('🔍 [ProgressStepper] Human review check:', {
      shouldShowHumanReview,
      activeReview: !!activeReview,
      workflowPaused: workflow.workflow_paused,
      currentStep: workflow.current_step
    });

    setShowHumanReview(shouldShowHumanReview);
  }, [activeReview, workflow.workflow_paused, workflow.current_step]);
  
  useEffect(() => {
    // Fetch settings to determine if human review is enabled
    const fetchSettings = async () => {
      try {
        const response = await fetch('/api/v1/settings/evaluation');
        if (response.ok) {
          const settings = await response.json();
          setShowHumanReview(settings.enable_prompt_review && settings.prompt_review_mode !== 'disabled');
        }
      } catch (error) {
        console.error('Failed to fetch settings:', error);
      }
    };
    fetchSettings();
  }, []);
  
  useEffect(() => {
    // Filter steps based on settings
    const steps = SIMPLIFIED_STEPS.filter(step => 
      !step.conditional || (step.conditional && showHumanReview)
    );
    setEnabledSteps(steps);
  }, [showHumanReview]);
  
  useEffect(() => {
    if (!workflow.current_step || enabledSteps.length === 0) return;

    // Map original step names to simplified steps
    const currentStep = enabledSteps.findIndex(step => {
      if (workflow.current_step) {
        return step.originalSteps.includes(workflow.current_step) || step.key === workflow.current_step;
      }
      return false;
    });

    // If we can't find the current step in enabled steps, try to map it manually
    let mappedStep = currentStep;
    if (currentStep === -1 && workflow.current_step) {
      // Map specific workflow steps to simplified steps
      if (['initializing_workflow', 'parsing_rfq', 'generating_embeddings', 'rfq_parsed'].includes(workflow.current_step)) {
        mappedStep = 0; // preparing_request
      } else if (['matching_golden_examples', 'planning_methodologies'].includes(workflow.current_step)) {
        mappedStep = 1; // building_context
      } else if (workflow.current_step === 'human_review') {
        mappedStep = 2; // human_review
      } else if (['generating', 'validating', 'finalizing', 'resuming_generation'].includes(workflow.current_step)) {
        mappedStep = 3; // generating_survey
      } else if (['completed', 'finished'].includes(workflow.current_step)) {
        mappedStep = 4; // survey_complete
      }
    }

    console.log('🔍 [ProgressStepper] Step calculation:', {
      currentStep,
      mappedStep,
      workflowStep: workflow.current_step,
      enabledSteps: enabledSteps.map(s => ({ key: s.key, originalSteps: s.originalSteps }))
    });

    if (mappedStep !== -1) {
      setCurrentStepIndex(mappedStep);
    }

    // Update completed steps based on workflow state
    const completed = [];

    if (workflowStatus === 'completed') {
      // All steps completed
      for (let i = 0; i < enabledSteps.length; i++) {
        completed.push(i);
      }
    } else {
      // Mark steps as completed based on workflow progress
      for (let i = 0; i < enabledSteps.length; i++) {
        const step = enabledSteps[i];
        
        // If we're at human review step, only mark previous steps as completed
        if (workflow.current_step === 'human_review' || workflow.workflow_paused) {
          // Only mark steps BEFORE human review as completed
          if (i < mappedStep) {
            completed.push(i);
          }
        } else if (['generating', 'validating', 'resuming_generation'].includes(workflow.current_step)) {
          // If we're at generation/validation step (after human review), mark all previous steps as completed
          if (i < mappedStep) {
            completed.push(i);
          }
        } else if (workflow.current_step) {
          // Check if this step is actually completed based on workflow state
          const stepIsCompleted = step.originalSteps.some(originalStep => {
            // Check if we've moved past this step
            return workflow.current_step && 
                   (workflow.current_step.includes('completed') || 
                    workflow.current_step.includes('finished') ||
                    // If current step is in a later step's originalSteps
                    enabledSteps.slice(i + 1).some(laterStep => 
                      laterStep.originalSteps.includes(workflow.current_step!)
                    ));
          });
          
          if (stepIsCompleted) {
            completed.push(i);
          }
        }
      }
    }

    console.log('🔍 [ProgressStepper] Completed steps calculation:', {
      currentStep,
      mappedStep,
      completed,
      workflowStep: workflow.current_step,
      workflowPaused: workflow.workflow_paused
    });

    setCompletedSteps(completed);
  }, [workflow.current_step, workflow.progress, workflowStatus, enabledSteps]);

  // Handle automatic completion actions
  useEffect(() => {
    if (workflowStatus === 'completed' && currentSurvey) {
      console.log('🎉 [ProgressStepper] Workflow completed, triggering automatic actions');

      // Small delay to let the UI update, then trigger completion action
      const timer = setTimeout(() => {
        console.log('🔍 [ProgressStepper] Auto-triggering onShowSurvey due to completion');
        onShowSurvey?.();
      }, 2000); // 2 second delay to show completion state

      return () => clearTimeout(timer);
    }
  }, [workflowStatus, currentSurvey, onShowSurvey]);
  
  const getStepStatus = (index: number) => {
    if (workflowStatus === 'completed') return 'completed';
    if (completedSteps.includes(index)) return 'completed';
    if (index === currentStepIndex) return 'current';
    // Only mark previous steps as completed if they are actually finished
    // Don't auto-complete steps just because they come before current step
    return 'pending';
  };

  const getCurrentStepDetails = () => {
    if (enabledSteps.length === 0) return null;
    const currentStep = enabledSteps[currentStepIndex];
    return currentStep?.details || null;
  };

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: { bg: 'bg-blue-500', light: 'bg-blue-50', text: 'text-blue-700', ring: 'ring-blue-500/20' },
      purple: { bg: 'bg-purple-500', light: 'bg-purple-50', text: 'text-purple-700', ring: 'ring-purple-500/20' },
      orange: { bg: 'bg-orange-500', light: 'bg-orange-50', text: 'text-orange-700', ring: 'ring-orange-500/20' },
      green: { bg: 'bg-green-500', light: 'bg-green-50', text: 'text-green-700', ring: 'ring-green-500/20' },
      yellow: { bg: 'bg-yellow-500', light: 'bg-yellow-50', text: 'text-yellow-700', ring: 'ring-yellow-500/20' },
      emerald: { bg: 'bg-emerald-500', light: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-500/20' }
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
  };

  const currentDetails = getCurrentStepDetails();
  const isHumanReviewActive =
    enabledSteps[currentStepIndex]?.key === 'human_review' ||
    !!activeReview ||
    !!workflow.workflow_paused ||
    (workflow.current_step && (
      workflow.current_step.includes('review') ||
      workflow.current_step.includes('human') ||
      workflow.current_step === 'human_review'
    ));
  
  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="flex-shrink-0 px-8 py-6 bg-white/80 backdrop-blur-sm border-b border-gray-200/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Survey Generation</h1>
              <p className="text-gray-600">AI-powered survey creation in progress</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              {workflow.progress || 0}%
            </div>
            <div className="text-sm text-gray-500">Complete</div>
          </div>
        </div>
        
        {/* Overall Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-1000 ease-out relative"
              style={{ width: `${workflow.progress || 0}%` }}
            >
              <div className="absolute inset-0 bg-white/30 animate-pulse rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Split Screen */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Progress Steps */}
        <div className="w-1/2 border-r border-gray-200/50 bg-white/40 backdrop-blur-sm">
          <div className="h-full overflow-y-auto">
            <div className="p-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Progress Timeline</h2>
              
              {/* Vertical Progress Timeline */}
              <div className="relative">
                {/* Connecting Line */}
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-gray-200 via-blue-200 to-gray-200"></div>
                
                {enabledSteps.map((step, index) => {
                  const status = getStepStatus(index);
                  const colors = getColorClasses(step.color);
                  const isCurrent = status === 'current';
                  const isCompleted = status === 'completed';
                  const isPending = status === 'pending';
                  
                  return (
                    <div key={step.key} className="relative mb-8 last:mb-0">
                      {/* Step Indicator */}
                      <div className="flex items-start">
                        <div className="relative z-10 flex-shrink-0">
                          <div className={`
                            w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all duration-500
                            ${isCurrent 
                              ? `${colors.bg} text-white shadow-lg ${colors.ring} ring-8 scale-110` 
                              : isCompleted 
                              ? 'bg-green-500 text-white shadow-md' 
                              : 'bg-gray-200 text-gray-400'
                            }
                          `}>
                            {isCompleted ? (
                              <CheckIcon className="w-6 h-6" />
                            ) : isCurrent ? (
                              <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                            ) : (
                              <span>{step.icon}</span>
                            )}
                          </div>
                          
                          {/* Pulse Animation for Current Step */}
                          {isCurrent && (
                            <div className={`absolute inset-0 ${colors.bg} rounded-full animate-ping opacity-75`}></div>
                          )}
                        </div>
                        
                        {/* Step Content */}
                        <div className="ml-6 flex-1">
                          <div className="pb-8">
                            <h3 className={`text-lg font-semibold mb-1 transition-colors duration-300 ${
                              isCurrent ? 'text-gray-900' : isCompleted ? 'text-green-700' : 'text-gray-500'
                            }`}>
                              {step.label}
                            </h3>
                            <p className={`text-sm mb-3 transition-colors duration-300 ${
                              isCurrent ? 'text-gray-700' : isCompleted ? 'text-green-600' : 'text-gray-400'
                            }`}>
                              {step.description}
                            </p>
                            
                            {/* Status Indicator */}
                            <div className="flex items-center space-x-2">
                              {isCurrent && (
                                <>
                                  <ClockIcon className="w-4 h-4 text-blue-500 animate-pulse" />
                                  <span className="text-sm font-medium text-blue-600">In Progress</span>
                                </>
                              )}
                              {isCompleted && (
                                <>
                                  <CheckIcon className="w-4 h-4 text-green-500" />
                                  <span className="text-sm font-medium text-green-600">Completed</span>
                                </>
                              )}
                              {isPending && (
                                <>
                                  <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                                  <span className="text-sm font-medium text-gray-400">Pending</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Current Step Details */}
        <div className="w-1/2 bg-white/60 backdrop-blur-sm">
          <div className="h-full overflow-y-auto">
            <div className="p-8">
              {isHumanReviewActive ? (
                <HumanReviewPanel 
                  isActive={true}
                  workflowId={workflow.workflow_id}
                  surveyId={currentSurvey?.survey_id}
                />
              ) : currentDetails ? (
                <div className="space-y-6">
                  {/* Current Step Header */}
                  <div>
                    <div className="flex items-center space-x-3 mb-4">
                      <div className={`p-2 rounded-lg ${getColorClasses(enabledSteps[currentStepIndex]?.color || 'blue').light}`}>
                        <span className="text-2xl">{enabledSteps[currentStepIndex]?.icon}</span>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">{currentDetails.title}</h2>
                        <p className="text-gray-600">Step {currentStepIndex + 1} of {enabledSteps.length}</p>
                      </div>
                    </div>
                    
                    {/* Estimated Time */}
                    <div className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                      <ClockIcon className="w-4 h-4 mr-2" />
                      {currentDetails.estimatedTime}
                    </div>
                  </div>

                  {/* Description */}
                  <div className="bg-gray-50 rounded-xl p-6">
                    <p className="text-gray-700 leading-relaxed">{currentDetails.content}</p>
                  </div>

                  {/* Sub-tasks */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Tasks</h3>
                    <div className="space-y-3">
                      {currentDetails.subTasks.map((task, index) => {
                        // Calculate task status based on workflow progress and current step
                        const isCompleted = workflow.status === 'completed' || 
                          (workflow.current_step && 
                           workflow.current_step.includes('completed') && 
                           index < currentDetails.subTasks.length - 1);
                        
                        // For the current step, show the first sub-task as in progress
                        // This is simpler and more reliable than trying to map progress to specific sub-tasks
                        const isInProgress = !isCompleted && 
                          workflow.status !== 'completed' && 
                          workflow.status !== 'idle' &&
                          index === 0; // Show first sub-task as in progress for current step
                        
                        // const isPending = !isCompleted && !isInProgress;

                        return (
                          <div key={index} className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200">
                            <div className="flex-shrink-0">
                              {isCompleted ? (
                                <CheckIcon className="w-5 h-5 text-green-500" />
                              ) : isInProgress ? (
                                <div className="w-5 h-5 border-2 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                              ) : (
                                <div className="w-5 h-5 rounded-full border-2 border-gray-300"></div>
                              )}
                            </div>
                            <span className={`text-sm ${
                              isCompleted ? 'text-green-700' : 
                              isInProgress ? 'text-blue-700' : 'text-gray-500'
                            }`}>
                              {task}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Current Status Message */}
                  {workflow.message && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mt-2"></div>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-blue-900 mb-1">Live Update</h4>
                          <p className="text-sm text-blue-700">{workflow.message}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <SparklesIcon className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Preparing Generation</h3>
                    <p className="text-gray-500">Setting up your survey generation workflow...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex-shrink-0 bg-white/80 backdrop-blur-sm border-t border-gray-200/50 px-8 py-6">
        <div className="flex items-center justify-between">
          {/* Left side - Status */}
          <div className={`
            inline-flex items-center px-4 py-2 rounded-full text-sm font-medium
            ${workflowStatus === 'completed' 
              ? 'bg-emerald-100 text-emerald-800' 
              : workflowStatus === 'failed' 
              ? 'bg-red-100 text-red-800'
              : workflowStatus === 'started' || workflowStatus === 'in_progress'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-gray-100 text-gray-600'
            }
          `}>
            <div className={`
              w-2 h-2 rounded-full mr-2
              ${workflowStatus === 'completed' 
                ? 'bg-emerald-500' 
                : workflowStatus === 'failed' 
                ? 'bg-red-500'
                : workflowStatus === 'started' || workflowStatus === 'in_progress'
                ? 'bg-blue-500 animate-pulse'
                : 'bg-gray-400'
              }
            `} />
            {workflowStatus === 'completed' 
              ? 'Survey Generation Complete' 
              : workflowStatus === 'failed' 
              ? 'Generation Failed'
              : workflowStatus === 'started' || workflowStatus === 'in_progress'
              ? 'Generating Survey...'
              : 'Ready to Generate'
            }
          </div>

          {/* Right side - Actions */}
          <div className="flex space-x-4">
            {workflowStatus === 'completed' && currentSurvey ? (
              <>
                {/* Primary: View Summary Button */}
                <button
                  onClick={() => onShowSummary && onShowSummary()}
                  className="inline-flex items-center px-6 py-3 rounded-xl font-bold text-base transition-all duration-200 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  View AI Analysis
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                {/* Secondary: Direct Survey View */}
                <button
                  onClick={() => onShowSurvey && onShowSurvey()}
                  className="inline-flex items-center px-4 py-3 rounded-xl font-medium text-base transition-all duration-200 bg-gray-100 hover:bg-gray-200 text-gray-700 shadow-md hover:shadow-lg"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View Survey
                </button>
              </>
            ) : (
              <>
                {/* During generation or failed state */}
                <button
                  onClick={() => onShowSurvey && onShowSurvey()}
                  disabled={workflowStatus !== 'completed' || !currentSurvey}
                  className={`
                    inline-flex items-center px-6 py-3 rounded-xl font-medium text-base transition-all duration-200
                    ${workflowStatus === 'completed' && currentSurvey
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg hover:shadow-emerald-200 transform hover:scale-105'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View Survey
                  {workflowStatus === 'completed' && currentSurvey && (
                    <span className="ml-2 text-emerald-200">✓</span>
                  )}
                </button>

                {/* Cancel Generation Button */}
                <button
                  onClick={() => onCancelGeneration && onCancelGeneration()}
                  disabled={workflowStatus !== 'started' && workflowStatus !== 'in_progress'}
                  className={`
                    inline-flex items-center px-4 py-3 rounded-xl font-medium transition-all duration-200
                    ${workflowStatus === 'started' || workflowStatus === 'in_progress'
                      ? 'bg-red-100 hover:bg-red-200 text-red-700 border border-red-300 hover:border-red-400'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
                    }
                  `}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};