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
        backendStep: 'single_call_evaluator',
        message: 'Running AI-powered comprehensive quality assessment'
      },
      {
        key: 'pillar_scores_analysis',
        label: 'Pillar-based quality scoring',
        backendStep: 'pillar_scores_analysis',
        message: 'Analyzing methodological rigor, content validity, and clarity'
      },
      {
        key: 'fallback_evaluation',
        label: 'Quality assurance checks',
        backendStep: 'fallback_evaluation',
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
    rightPanelType: 'substeps',
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
}

export const ProgressStepper: React.FC<ProgressStepperProps> = ({
  onShowSurvey,
  onCancelGeneration
}) => {
  const { workflow, currentSurvey, activeReview } = useAppStore();
  const workflowStatus = workflow.status;
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [enabledSteps, setEnabledSteps] = useState<MainWorkflowStep[]>([]);
  
  // Get settings to determine if human review step should be shown
  const [showHumanReview, setShowHumanReview] = useState<boolean | null>(null); // null = loading, true/false = loaded
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Debug survey structure when it changes
  useEffect(() => {
    if (currentSurvey) {
      console.log('🔍 [ProgressStepper] Survey structure debug:', {
        survey_id: currentSurvey.survey_id,
        title: currentSurvey.title,
        sections: currentSurvey.sections?.length || 0,
        questions: currentSurvey.questions?.length || 0,
        sectionsData: currentSurvey.sections,
        questionsData: currentSurvey.questions
      });
    }
  }, [currentSurvey]);

  // Fetch settings to determine step visibility
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch('/api/v1/settings/evaluation');
        if (response.ok) {
          const settings = await response.json();
          console.log('🔍 [ProgressStepper] Loaded settings for step filtering:', settings);

          // Determine human review visibility based on multiple factors
          const humanReviewEnabled = Boolean(
            settings.enable_prompt_review &&
            settings.prompt_review_mode &&
            settings.prompt_review_mode !== 'disabled'
          );

          setShowHumanReview(humanReviewEnabled);
          setSettingsLoaded(true);
        } else {
          console.warn('⚠️ [ProgressStepper] Settings API failed, using fallback step configuration');
          // Fallback to false if API fails
          setShowHumanReview(false);
          setSettingsLoaded(true);
        }
      } catch (error) {
        console.error('❌ [ProgressStepper] Failed to fetch settings:', error);
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

    // Dynamic step filtering based on settings and workflow state
    const filteredSteps = MAIN_WORKFLOW_STEPS.filter(step => {
      // Always include non-conditional steps
      if (!step.conditional) return true;

      // Handle conditional steps dynamically
      switch (step.key) {
        case 'human_review':
          // Include human review step if:
          // 1. Settings enable it, OR
          // 2. Workflow is currently in human review state, OR
          // 3. There's an active review
          return Boolean(
            showHumanReview ||
            workflow.current_step === 'human_review' ||
            workflow.workflow_paused ||
            activeReview
          );

        // Future conditional steps can be added here
        // case 'quality_assurance':
        //   return settings.enable_qa_step;
        // case 'advanced_validation':
        //   return settings.enable_advanced_validation;

        default:
          return true;
      }
    });

    // Recalculate step percentages to ensure smooth distribution
    const redistributePercentages = (steps: MainWorkflowStep[]) => {
      if (steps.length === 0) return steps;

      const totalSteps = MAIN_WORKFLOW_STEPS.length;
      const enabledSteps = steps.length;
      const percentagePerStep = 100 / enabledSteps;

      return steps.map((step, index) => ({
        ...step,
        percentRange: [
          Math.round(index * percentagePerStep),
          Math.round((index + 1) * percentagePerStep)
        ] as [number, number]
      }));
    };

    const stepsWithAdjustedPercentages = redistributePercentages(filteredSteps);

    console.log('🔍 [ProgressStepper] Dynamic step filtering result:', {
      originalSteps: MAIN_WORKFLOW_STEPS.length,
      filteredSteps: filteredSteps.length,
      showHumanReview,
      workflowState: workflow.current_step,
      adjustedPercentages: stepsWithAdjustedPercentages.map(s => ({ key: s.key, percentRange: s.percentRange }))
    });

    setEnabledSteps(stepsWithAdjustedPercentages);
  }, [showHumanReview, settingsLoaded, workflow.current_step, workflow.workflow_paused, activeReview]);
  
  useEffect(() => {
    if (!workflow.current_step || enabledSteps.length === 0) return;

    // Find current step index by directly matching backend step names
    let newStepIndex = enabledSteps.findIndex(step => step.key === workflow.current_step);

    // If direct match fails, try matching substeps
    if (newStepIndex === -1) {
      newStepIndex = enabledSteps.findIndex(step =>
        step.subSteps.some(subStep => subStep.backendStep === workflow.current_step)
      );
    }

    console.log('🔍 [ProgressStepper] Step calculation:', {
      newStepIndex,
      currentStepIndex,
      workflowStep: workflow.current_step,
      workflowProgress: workflow.progress,
      enabledStepsKeys: enabledSteps.map(s => s.key)
    });

    // Apply smooth transition logic to prevent jumps
    if (newStepIndex !== -1) {
      // Only allow forward transitions or stay in same step
      // Prevent backward jumps unless workflow explicitly restarted
      if (newStepIndex >= currentStepIndex || workflow.progress === 0) {
        setCurrentStepIndex(newStepIndex);
      } else {
        // If trying to go backward, only allow if it's a valid transition
        // (e.g., human review completion moving to next step)
        const currentStep = enabledSteps[currentStepIndex];
        const targetStep = enabledSteps[newStepIndex];

        if (currentStep?.key === 'human_review' && targetStep) {
          // Allow transition from human_review to next step
          setCurrentStepIndex(newStepIndex);
        } else {
          // Otherwise, keep current step to prevent jarring jumps
          console.log('🚫 [ProgressStepper] Preventing backward step jump from', currentStepIndex, 'to', newStepIndex);
        }
      }
    } else if (workflow.progress) {
      // Fallback: find step based on progress percentage, but only move forward
      const progressBasedIndex = enabledSteps.findIndex(step => {
        const [minPercent, maxPercent] = step.percentRange;
        return workflow.progress! >= minPercent && workflow.progress! <= maxPercent;
      });

      if (progressBasedIndex !== -1 && progressBasedIndex >= currentStepIndex) {
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
      // Only mark steps as completed if we've actually moved past them
      // Don't mark current step as completed if it has substeps in progress
      for (let i = 0; i < enabledSteps.length; i++) {
        const step = enabledSteps[i];
        const [, maxPercent] = step.percentRange;

        // Mark step as completed if:
        // 1. We're past the current step index (moved to next step)
        // 2. OR workflow progress is beyond this step's end percentage
        if (currentStepIndex > i) {
          completed.push(i);
        } else if (workflow.progress && workflow.progress >= maxPercent) {
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
    
    // If this is the current step, check if it has substeps in progress
    if (index === currentStepIndex) {
      const step = enabledSteps[index];
      if (step && step.subSteps) {
        // Check if any substeps are still in progress
        const hasInProgressSubSteps = step.subSteps.some(subStep => {
          // Check if this substep matches the current backend step and workflow is in progress
          return subStep.backendStep === workflow.current_step && workflowStatus === 'in_progress';
        });
        
        // If workflow is in progress and we have substeps, show as current (in progress)
        if (hasInProgressSubSteps || workflowStatus === 'in_progress') {
          return 'current';
        }
      }
      return 'current';
    }
    
    // Only mark steps as completed if they are actually finished
    if (completedSteps.includes(index)) return 'completed';
    
    return 'pending';
  };

  const getCurrentMainStep = () => {
    if (enabledSteps.length === 0) return null;
    return enabledSteps[currentStepIndex] || null;
  };

  const getCurrentSubStep = () => {
    const mainStep = getCurrentMainStep();
    if (!mainStep || !workflow.current_step) return null;

    // For evaluation steps, use more sophisticated matching
    if (mainStep.key === 'quality_evaluation') {
      // Check if workflow.current_step is one of the evaluation substep names
      const evalSubStep = mainStep.subSteps.find(sub => sub.backendStep === workflow.current_step);
      if (evalSubStep) {
        return evalSubStep;
      }

      // If workflow.current_step is 'validation_scoring', determine active substep based on progress
      if (workflow.current_step === 'validation_scoring') {
        const progress = workflow.progress || 0;
        if (progress >= 85) {
          return mainStep.subSteps.find(sub => sub.key === 'fallback_evaluation') || mainStep.subSteps[2];
        } else if (progress >= 82) {
          return mainStep.subSteps.find(sub => sub.key === 'pillar_scores_analysis') || mainStep.subSteps[1];
        } else {
          return mainStep.subSteps.find(sub => sub.key === 'single_call_evaluator') || mainStep.subSteps[0];
        }
      }
    }

    // Find the sub-step that matches the current backend step
    const matchingSubStep = mainStep.subSteps.find(sub => sub.backendStep === workflow.current_step);
    return matchingSubStep || mainStep.subSteps[0];
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

                          // Enhanced completion logic for evaluation substeps
                          let isCompletedSubStep = false;
                          if (currentMainStep.key === 'quality_evaluation') {
                            // For evaluation, check if current substep index is greater than this one
                            const currentSubStepIndex = currentMainStep.subSteps.findIndex(s => s.key === currentSubStep?.key);
                            isCompletedSubStep = currentSubStepIndex > index;

                            // Also consider progress-based completion
                            const progress = workflow.progress || 0;
                            if (subStep.key === 'single_call_evaluator' && progress >= 82) {
                              isCompletedSubStep = true;
                            } else if (subStep.key === 'pillar_scores_analysis' && progress >= 85) {
                              isCompletedSubStep = true;
                            }
                          } else {
                            // Standard completion logic for other steps
                            isCompletedSubStep = Boolean(workflow.current_step &&
                              currentMainStep.subSteps.findIndex(s => s.backendStep === workflow.current_step) > index);
                          }

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

                      {/* Add completion buttons when workflow is completed */}
                      {currentMainStep.key === 'completion' && workflowStatus === 'completed' && (
                        <div className="mt-6 pt-6 border-t border-amber-200">
                          <h4 className="text-md font-semibold text-amber-900 mb-4">Next Steps</h4>
                          <div className="flex justify-center">
                            <button
                              onClick={() => {
                                if (currentSurvey?.survey_id) {
                                  // Navigate to surveys list with the specific survey ID
                                  window.location.href = `/surveys?id=${currentSurvey.survey_id}`;
                                }
                              }}
                              className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-white px-8 py-3 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center"
                            >
                              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                              </svg>
                              View Survey
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {currentMainStep.rightPanelType === 'survey_preview' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Survey Preview</h3>

                      {currentSurvey ? (
                        // Survey successfully loaded
                        <>
                          <div className="bg-white border border-gray-200 rounded-xl p-4 max-h-96 overflow-y-auto">
                            <div className="space-y-4">
                              <div className="text-center pb-4 border-b border-gray-200">
                                <h4 className="text-xl font-bold text-gray-900">{currentSurvey.title}</h4>
                                <p className="text-sm text-gray-600 mt-1">{currentSurvey.description}</p>
                              </div>
                              {/* Handle both sections and questions format */}
                              {currentSurvey.sections && currentSurvey.sections.length > 0 ? (
                                // Sections-based format
                                currentSurvey.sections.map((section, sectionIndex) => (
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
                                ))
                              ) : currentSurvey.questions && currentSurvey.questions.length > 0 ? (
                                // Questions-only format (fallback)
                                <div className="space-y-3">
                                  <h5 className="font-medium text-gray-800 border-l-4 border-blue-500 pl-3">
                                    Survey Questions
                                  </h5>
                                  {currentSurvey.questions.map((question, questionIndex) => (
                                    <div key={question.id || questionIndex} className="pl-4">
                                      <div className="flex items-start space-x-2">
                                        <span className="text-sm font-medium text-gray-500 mt-1">
                                          {questionIndex + 1}.
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
                              ) : (
                                // No questions found
                                <div className="text-center py-8 text-gray-500">
                                  <p>Survey structure loading...</p>
                                  <p className="text-xs mt-1">Questions are being processed</p>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="mt-4 flex space-x-3">
                            <button
                              onClick={() => {
                                if (currentSurvey?.survey_id) {
                                  // Open survey preview in new tab to keep user in ProgressStepper
                                  window.open(`/preview?surveyId=${currentSurvey.survey_id}`, '_blank');
                                }
                              }}
                              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              View Survey
                            </button>
                            <button
                              onClick={() => {
                                if (currentSurvey?.survey_id) {
                                  // Open survey preview in same tab for editing
                                  window.location.href = `/preview?surveyId=${currentSurvey.survey_id}`;
                                }
                              }}
                              className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              Edit Survey
                            </button>
                          </div>
                        </>
                      ) : workflow.survey_fetch_failed ? (
                        // Survey fetch failed - show fallback UI
                        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                          <div className="text-center">
                            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                              </svg>
                            </div>
                            <h4 className="text-lg font-semibold text-yellow-900 mb-2">Survey Generated Successfully!</h4>
                            <p className="text-yellow-800 mb-4">
                              Your survey was created, but there's a temporary issue loading the preview.
                            </p>
                            <div className="space-y-3">
                              <button
                                onClick={() => {
                                  if (workflow.survey_id) {
                                    // Clear the failed state and retry
                                    const { setWorkflowState, fetchSurvey } = useAppStore.getState();
                                    setWorkflowState({ survey_fetch_failed: false, survey_fetch_error: undefined });
                                    fetchSurvey(workflow.survey_id);
                                  }
                                }}
                                className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium"
                              >
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Try Loading Again
                              </button>
                              <div className="mt-2">
                                <button
                                  onClick={() => window.location.reload()}
                                  className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                                >
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                  </svg>
                                  Refresh Page
                                </button>
                              </div>
                            </div>
                            {workflow.survey_fetch_error && (
                              <div className="mt-4 text-xs text-yellow-700 bg-yellow-100 rounded p-2">
                                Error details: {workflow.survey_fetch_error}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        // Still loading survey
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                          <div className="text-center">
                            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                              <div className="w-6 h-6 border-2 border-amber-600 rounded-full border-t-transparent animate-spin"></div>
                            </div>
                            <h4 className="text-lg font-semibold text-blue-900 mb-2">Loading Survey Preview</h4>
                            <p className="text-blue-800">Please wait while we load your generated survey...</p>
                          </div>
                        </div>
                      )}
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