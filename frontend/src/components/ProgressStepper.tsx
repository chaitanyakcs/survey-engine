import React, { useState, useEffect } from 'react';
import { CheckIcon, ClockIcon, SparklesIcon } from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';
import { HumanReviewPanel } from './HumanReviewPanel';

interface SubStep {
  key: string;
  label: string;
  backendStep: string;
  message: string;
}

interface MainWorkflowStep {
  key: string;
  label: string;
  description: string;
  icon: string;
  color: string;
  conditional?: boolean;
  percentRange: [number, number];
  subSteps: SubStep[];
  rightPanelType: 'substeps' | 'human_review' | 'survey_preview';
}

const MAIN_WORKFLOW_STEPS: MainWorkflowStep[] = [
  {
    key: 'building_context',
    label: 'Building Context',
    description: 'Analyzing requirements and gathering templates',
    icon: '🔗',
    color: 'gold',
    percentRange: [0, 40],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'parsing_rfq',
        label: 'Parsing RFQ requirements',
        backendStep: 'parsing_rfq',
        message: 'Analyzing and understanding your requirements'
      },
      {
        key: 'generating_embeddings',
        label: 'Generating semantic embeddings',
        backendStep: 'generating_embeddings',
        message: 'Creating vectors for similarity matching'
      },
      {
        key: 'rfq_parsed',
        label: 'Completing RFQ analysis',
        backendStep: 'rfq_parsed',
        message: 'Requirements analysis finished'
      },
      {
        key: 'matching_examples',
        label: 'Matching golden examples',
        backendStep: 'matching_golden_examples',
        message: 'Finding relevant survey templates'
      },
      {
        key: 'planning_methods',
        label: 'Planning methodologies',
        backendStep: 'planning_methodologies',
        message: 'Selecting research approaches'
      }
    ]
  },
  {
    key: 'human_review',
    label: 'Human Review',
    description: 'Expert validation of system prompts',
    icon: '👥',
    color: 'gold',
    conditional: true,
    percentRange: [40, 50],
    rightPanelType: 'human_review',
    subSteps: [
      {
        key: 'review_prompt',
        label: 'Reviewing system prompt',
        backendStep: 'human_review',
        message: 'Expert validation in progress'
      }
    ]
  },
  {
    key: 'question_generation',
    label: 'Question Generation',
    description: 'Creating your survey content',
    icon: '✍️',
    color: 'gold',
    percentRange: [50, 80],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'preparing_generation',
        label: 'Preparing generation pipeline',
        backendStep: 'preparing_generation',
        message: 'Setting up survey creation'
      },
      {
        key: 'llm_processing',
        label: 'LLM invocation and processing',
        backendStep: 'generating_questions',
        message: 'AI creating survey questions'
      },
      {
        key: 'parsing_output',
        label: 'Parsing LLM output to questions',
        backendStep: 'generating_questions',
        message: 'Structuring generated content'
      }
    ]
  },
  {
    key: 'quality_evaluation',
    label: 'Quality Evaluation',
    description: 'Comprehensive quality assessment',
    icon: '🔍',
    color: 'gold',
    percentRange: [80, 100],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'single_call_evaluator',
        label: 'Single-call comprehensive evaluation',
        backendStep: 'validation_scoring',
        message: 'Running AI-powered comprehensive quality assessment'
      },
      {
        key: 'pillar_scores_analysis',
        label: 'Pillar-based quality scoring',
        backendStep: 'validation_scoring',
        message: 'Analyzing methodological rigor, content validity, and clarity'
      },
      {
        key: 'fallback_evaluation',
        label: 'Quality assurance checks',
        backendStep: 'validation_scoring',
        message: 'Ensuring evaluation completeness and reliability'
      }
    ]
  },
  {
    key: 'completion',
    label: 'Survey Complete',
    description: 'Your professional survey is ready',
    icon: '🎉',
    color: 'gold',
    percentRange: [100, 100],
    rightPanelType: 'survey_preview',
    subSteps: [
      {
        key: 'completed',
        label: 'Survey ready for deployment',
        backendStep: 'completed',
        message: 'Generation completed successfully'
      }
    ]
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
  const [enabledSteps, setEnabledSteps] = useState<MainWorkflowStep[]>([]);
  
  // Get settings to determine if human review step should be shown
  const [showHumanReview, setShowHumanReview] = useState<boolean | null>(null); // null = loading, true/false = loaded
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Fetch settings to determine if human review is enabled
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch('/api/v1/settings/evaluation');
        if (response.ok) {
          const settings = await response.json();
          const humanReviewEnabled = settings.enable_prompt_review && settings.prompt_review_mode !== 'disabled';
          setShowHumanReview(humanReviewEnabled);
          setSettingsLoaded(true);
        } else {
          // Fallback to false if API fails
          setShowHumanReview(false);
          setSettingsLoaded(true);
        }
      } catch (error) {
        console.error('Failed to fetch settings:', error);
        // Fallback to false if API fails
        setShowHumanReview(false);
        setSettingsLoaded(true);
      }
    };
    fetchSettings();
  }, []);

  // Determine if human review should be shown based on workflow state
  useEffect(() => {
    if (!settingsLoaded) return; // Don't update until settings are loaded
    
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
      currentStep: workflow.current_step,
      settingsLoaded
    });

    setShowHumanReview(shouldShowHumanReview);
  }, [activeReview, workflow.workflow_paused, workflow.current_step, settingsLoaded]);
  
  useEffect(() => {
    // Don't filter steps until settings are loaded
    if (!settingsLoaded) {
      setEnabledSteps([]);
      return;
    }

    // Filter steps based on settings and actual workflow state
    const steps = MAIN_WORKFLOW_STEPS.filter(step => {
      // Always include non-conditional steps
      if (!step.conditional) return true;

      // For conditional steps like human_review, check if it should be shown
      if (step.key === 'human_review') {
        return showHumanReview;
      }

      return true;
    });
    setEnabledSteps(steps);
  }, [showHumanReview, settingsLoaded]);
  
  useEffect(() => {
    if (!workflow.current_step || enabledSteps.length === 0) return;

    // Find current step index by directly matching backend step names
    const currentStepIndex = enabledSteps.findIndex(step => step.key === workflow.current_step);

    console.log('🔍 [ProgressStepper] Step calculation:', {
      currentStepIndex,
      workflowStep: workflow.current_step,
      workflowProgress: workflow.progress,
      enabledStepsKeys: enabledSteps.map(s => s.key)
    });

    // Set current step index (use progress-based fallback if direct match fails)
    if (currentStepIndex !== -1) {
      setCurrentStepIndex(currentStepIndex);
    } else if (workflow.progress) {
      // Fallback: find step based on progress percentage
      const progressBasedIndex = enabledSteps.findIndex(step => {
        const [minPercent, maxPercent] = step.percentRange;
        return workflow.progress! >= minPercent && workflow.progress! <= maxPercent;
      });
      if (progressBasedIndex !== -1) {
        setCurrentStepIndex(progressBasedIndex);
      }
    }

    // Calculate completed steps based on workflow progress and current step
    const completed = [];

    if (workflowStatus === 'completed') {
      // All steps completed
      for (let i = 0; i < enabledSteps.length; i++) {
        completed.push(i);
      }
    } else {
      // Mark steps as completed based on progress or step position
      for (let i = 0; i < enabledSteps.length; i++) {
        const step = enabledSteps[i];
        const [minPercent] = step.percentRange;

        // Mark step as completed if:
        // 1. Current progress is beyond this step's start percentage
        // 2. OR we've passed this step in the workflow sequence
        if (workflow.progress && workflow.progress > minPercent) {
          completed.push(i);
        } else if (currentStepIndex > i) {
          completed.push(i);
        }
      }
    }

    console.log('🔍 [ProgressStepper] Completed steps calculation:', {
      currentStepIndex,
      completed,
      workflowStep: workflow.current_step,
      workflowProgress: workflow.progress,
      workflowPaused: workflow.workflow_paused
    });

    setCompletedSteps(completed);
  }, [workflow.current_step, workflow.progress, workflowStatus, workflow.workflow_paused, enabledSteps]);

  // No automatic redirection - we show survey preview inline now
  // useEffect(() => {
  //   if (workflowStatus === 'completed' && currentSurvey) {
  //     console.log('🎉 [ProgressStepper] Workflow completed, triggering automatic actions');
  //     // Small delay to let the UI update, then trigger completion action
  //     const timer = setTimeout(() => {
  //       console.log('🔍 [ProgressStepper] Auto-triggering onShowSurvey due to completion');
  //       onShowSurvey?.();
  //     }, 2000); // 2 second delay to show completion state
  //     return () => clearTimeout(timer);
  //   }
  // }, [workflowStatus, currentSurvey, onShowSurvey]);
  
  const getStepStatus = (index: number) => {
    if (workflowStatus === 'completed') return 'completed';
    if (completedSteps.includes(index)) return 'completed';
    if (index === currentStepIndex) return 'current';
    // Only mark previous steps as completed if they are actually finished
    // Don't auto-complete steps just because they come before current step
    return 'pending';
  };

  const getCurrentMainStep = () => {
    if (enabledSteps.length === 0) return null;
    return enabledSteps[currentStepIndex] || null;
  };

  const getCurrentSubStep = () => {
    const mainStep = getCurrentMainStep();
    if (!mainStep || !workflow.current_step) return null;

    // Find the sub-step that matches the current backend step
    return mainStep.subSteps.find(sub => sub.backendStep === workflow.current_step) || mainStep.subSteps[0];
  };

  const getColorClasses = (color: string) => {
    const colorMap = {
      gold: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      blue: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      purple: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      orange: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      green: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      yellow: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' },
      emerald: { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', light: 'bg-gradient-to-r from-yellow-50 to-amber-50', text: 'text-amber-800', ring: 'ring-yellow-400/30' }
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.gold;
  };

  const currentMainStep = getCurrentMainStep();
  const currentSubStep = getCurrentSubStep();
  const isHumanReviewActive =
    currentMainStep?.key === 'human_review' ||
    !!activeReview ||
    !!workflow.workflow_paused ||
    (workflow.current_step && (
      workflow.current_step.includes('review') ||
      workflow.current_step.includes('human') ||
      workflow.current_step === 'human_review'
    ));
  
  // Show loading state while settings are being fetched
  if (!settingsLoaded) {
    return (
      <div className="h-screen flex flex-col bg-white">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading settings...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <div className="flex-shrink-0 px-8 py-6 bg-white/80 backdrop-blur-sm border-b border-gray-200/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-r from-yellow-500 to-amber-600 rounded-xl">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-amber-900">Survey Generation</h1>
              <p className="text-amber-700">AI-powered survey creation in progress</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-amber-600 bg-clip-text text-transparent">
              {workflow.progress || 0}%
            </div>
            <div className="text-sm text-amber-600">Complete</div>
          </div>
        </div>
        
        {/* Overall Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 h-2 rounded-full transition-all duration-1000 ease-out relative"
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
              <h2 className="text-lg font-semibold text-amber-900 mb-6">Progress Timeline</h2>
              
              {/* Vertical Progress Timeline */}
              <div className="relative">
                {/* Connecting Line */}
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-amber-200 via-yellow-300 to-amber-200"></div>
                
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
                              ? 'bg-gradient-to-r from-yellow-500 to-amber-600 text-white shadow-md' 
                              : 'bg-gradient-to-r from-yellow-100 to-amber-100 text-amber-600'
                            }
                          `}>
                            {isCompleted ? (
                              <CheckIcon className="w-6 h-6" />
                            ) : isCurrent ? (
                              <div className="relative">
                                <div className="w-4 h-4 bg-white rounded-full animate-pulse"></div>
                                <div className="absolute inset-0 w-4 h-4 border-2 border-white rounded-full animate-spin border-t-transparent"></div>
                              </div>
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
                              isCurrent ? 'text-amber-900' : isCompleted ? 'text-amber-800' : 'text-amber-600'
                            }`}>
                              {step.label}
                            </h3>
                            <p className={`text-sm mb-3 transition-colors duration-300 ${
                              isCurrent ? 'text-amber-700' : isCompleted ? 'text-amber-600' : 'text-amber-500'
                            }`}>
                              {step.description}
                            </p>
                            
                            {/* Status Indicator */}
                            <div className="flex items-center space-x-2">
                              {isCurrent && (
                                <>
                                  <ClockIcon className="w-4 h-4 text-amber-600 animate-pulse" />
                                  <span className="text-sm font-medium text-amber-700">In Progress</span>
                                </>
                              )}
                              {isCompleted && (
                                <>
                                  <CheckIcon className="w-4 h-4 text-amber-600" />
                                  <span className="text-sm font-medium text-amber-700">Completed</span>
                                </>
                              )}
                              {isPending && (
                                <>
                                  <div className="w-4 h-4 rounded-full border-2 border-amber-300" />
                                  <span className="text-sm font-medium text-amber-500">Pending</span>
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
              ) : currentMainStep ? (
                <div className="space-y-6">
                  {/* Current Step Header */}
                  <div>
                    <div className="flex items-center space-x-3 mb-4">
                      <div className={`p-2 rounded-lg ${getColorClasses(currentMainStep?.color || 'blue').light}`}>
                        <span className="text-2xl">{currentMainStep?.icon}</span>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-amber-900">{currentMainStep.label}</h2>
                        <p className="text-amber-700">Step {currentStepIndex + 1} of {enabledSteps.length}</p>
                      </div>
                    </div>
                    
                    {/* Estimated Time */}
                    <div className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-yellow-50 to-amber-50 text-amber-700 rounded-full text-sm font-medium border border-amber-200">
                      <ClockIcon className="w-4 h-4 mr-2" />
                      {workflow.progress || 0}% Complete
                    </div>
                  </div>

                  {/* Description */}
                  <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-6 border border-amber-100">
                    <p className="text-amber-800 leading-relaxed">{currentMainStep.description}</p>
                  </div>

                  {/* Dynamic Right Panel Content Based on Step Type */}
                  {currentMainStep.rightPanelType === 'substeps' && (
                    <div>
                      <h3 className="text-lg font-semibold text-amber-900 mb-4">Current Tasks</h3>
                      <div className="space-y-3">
                        {currentMainStep.subSteps.map((subStep, index) => {
                          const isCurrentSubStep = currentSubStep?.key === subStep.key;
                          // More accurate completion logic based on backend step completion
                          const isCompletedSubStep = workflow.current_step &&
                            currentMainStep.subSteps.findIndex(s => s.backendStep === workflow.current_step) > index;
                          // Loading state: current step that's in progress
                          const isLoadingSubStep = isCurrentSubStep && workflow.status === 'in_progress';

                          return (
                            <div key={subStep.key} className="flex items-center space-x-3 p-3 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-lg border border-amber-200">
                              <div className="flex-shrink-0">
                                {isCompletedSubStep ? (
                                  <CheckIcon className="w-5 h-5 text-amber-600" />
                                ) : isLoadingSubStep ? (
                                  <div className="relative">
                                    <div className="w-5 h-5 border-2 border-amber-500 rounded-full border-t-transparent animate-spin"></div>
                                    <div className="absolute inset-1 w-3 h-3 bg-amber-500 rounded-full animate-pulse"></div>
                                  </div>
                                ) : isCurrentSubStep ? (
                                  <div className="w-5 h-5 border-2 border-amber-400 rounded-full border-dashed animate-pulse"></div>
                                ) : (
                                  <div className="w-5 h-5 rounded-full border-2 border-amber-300"></div>
                                )}
                              </div>
                              <div className="flex-1">
                                <span className={`text-sm font-medium ${
                                  isCompletedSubStep ? 'text-amber-700' :
                                  isLoadingSubStep ? 'text-amber-800 font-semibold' :
                                  isCurrentSubStep ? 'text-amber-700' : 'text-amber-600'
                                }`}>
                                  {subStep.label}
                                </span>
                                {isLoadingSubStep && workflow.message && (
                                  <p className="text-xs text-amber-700 mt-1 font-medium animate-pulse">🔄 {workflow.message}</p>
                                )}
                                {isCurrentSubStep && !isLoadingSubStep && workflow.message && (
                                  <p className="text-xs text-amber-600 mt-1">{workflow.message}</p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {currentMainStep.rightPanelType === 'survey_preview' && currentSurvey && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Survey Preview</h3>
                      <div className="bg-white border border-gray-200 rounded-xl p-4 max-h-96 overflow-y-auto">
                        <div className="space-y-4">
                          <div className="text-center pb-4 border-b border-gray-200">
                            <h4 className="text-xl font-bold text-gray-900">{currentSurvey.title}</h4>
                            <p className="text-sm text-gray-600 mt-1">{currentSurvey.description}</p>
                          </div>
                          {currentSurvey.sections?.map((section, sectionIndex) => (
                            <div key={section.id} className="space-y-3">
                              {section.title && (
                                <h5 className="font-medium text-gray-800 border-l-4 border-blue-500 pl-3">
                                  {section.title}
                                </h5>
                              )}
                              {section.questions?.map((question, questionIndex) => (
                                <div key={question.id} className="pl-4">
                                  <div className="flex items-start space-x-2">
                                    <span className="text-sm font-medium text-gray-500 mt-1">
                                      {sectionIndex + 1}.{questionIndex + 1}
                                    </span>
                                    <div className="flex-1">
                                      <p className="text-sm text-gray-700">{question.text}</p>
                                      {question.options && question.options.length > 0 && (
                                        <div className="mt-2 space-y-1">
                                          {question.options.map((option, optionIndex) => (
                                            <div key={optionIndex} className="flex items-center space-x-2 text-xs text-gray-600">
                                              <span className="w-4 h-4 border border-gray-300 rounded flex-shrink-0"></span>
                                              <span>{option}</span>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="mt-4 flex space-x-3">
                        <button
                          onClick={() => onShowSurvey && onShowSurvey()}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                          View Full Survey
                        </button>
                        <button className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors">
                          Export Survey
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Real-time Status Message */}
                  {workflow.message && currentMainStep.rightPanelType !== 'survey_preview' && (
                    <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border border-amber-200 rounded-xl p-4">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse mt-2"></div>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-amber-900 mb-1">Current Activity</h4>
                          <p className="text-sm text-amber-700">{workflow.message}</p>
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


    </div>
  );
};