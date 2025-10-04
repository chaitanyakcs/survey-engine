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
    percentRange: [10, 25],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'initializing_workflow',
        label: 'Initializing workflow',
        backendStep: 'initializing_workflow',
        message: 'Starting survey generation workflow...'
      },
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
      },
      {
        key: 'build_context',
        label: 'Building context',
        backendStep: 'build_context',
        message: 'Finalizing context and templates'
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
    percentRange: [30, 35],
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
    percentRange: [35, 60],
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
        label: 'LLM Processing',
        backendStep: 'generating_questions', // Primary step
        message: 'AI creating and processing survey questions'
      },
      {
        key: 'parsing_output',
        label: 'Parsing LLM output to questions',
        backendStep: 'parsing_output',
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
    percentRange: [65, 85],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'validation_scoring',
        label: 'Initializing quality evaluation',
        backendStep: 'validation_scoring',
        message: 'Setting up comprehensive quality assessment'
      },
      {
        key: 'llm_evaluation',
        label: 'AI Quality Assessment',
        backendStep: 'single_call_evaluator',
        message: 'Running AI-powered comprehensive quality evaluation'
      },
      {
        key: 'pillar_analysis',
        label: 'Pillar Analysis & Scoring',
        backendStep: 'evaluating_pillars',
        message: 'Analyzing quality across all pillars and methodologies'
      },
      {
        key: 'quality_assurance',
        label: 'Quality Assurance',
        backendStep: 'fallback_evaluation',
        message: 'Final quality checks and validation'
      }
    ]
  },
  {
    key: 'completion',
    label: 'Survey Complete',
    description: 'Ready for deployment',
    icon: '🎉',
    color: 'gold',
    percentRange: [100, 100],
    rightPanelType: 'substeps',
    subSteps: [
      {
        key: 'finalizing',
        label: 'Finalizing generation',
        backendStep: 'finalizing',
        message: 'Finalizing survey generation...'
      },
      {
        key: 'completed',
        label: 'Ready for deployment',
        backendStep: 'completed',
        message: 'Survey generated successfully'
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
  const { workflow, currentSurvey, activeReview, addToast } = useAppStore();
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

    // Use the predefined progress ranges from ProgressTracker
    const stepsWithAdjustedPercentages = filteredSteps;

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

    // Special handling for completed workflow
    if (workflowStatus === 'completed') {
      // When completed, show the completion step (last step)
      const completionStepIndex = enabledSteps.findIndex(step => step.key === 'completion');
      if (completionStepIndex !== -1) {
        setCurrentStepIndex(completionStepIndex);
        return;
      }
    }

    // Map backend step names to frontend step keys
    const stepMapping: Record<string, string> = {
      // Workflow node names
      'generate': 'question_generation',
      'validate': 'quality_evaluation',
      'parse_rfq': 'building_context',
      'retrieve_golden': 'building_context',
      'build_context': 'building_context',
      'prompt_review': 'human_review',
      
      // Progress tracker step names
      'initializing_workflow': 'building_context',
      'parsing_rfq': 'building_context',
      'generating_embeddings': 'building_context',
      'rfq_parsed': 'building_context',
      'matching_golden_examples': 'building_context',
      'planning_methodologies': 'building_context',
      'building_context': 'building_context',
      
      'human_review': 'human_review',
      
      'preparing_generation': 'question_generation',
      'generating_questions': 'question_generation',
      'llm_processing': 'question_generation',
      'parsing_output': 'question_generation',
      'resuming_generation': 'question_generation',
      
      'validation_scoring': 'quality_evaluation',
      'evaluating_pillars': 'quality_evaluation',
      'single_call_evaluator': 'quality_evaluation',
      'pillar_scores_analysis': 'quality_evaluation',
      'advanced_evaluation': 'quality_evaluation',
      'legacy_evaluation': 'quality_evaluation',
      'fallback_evaluation': 'quality_evaluation',
      
      // Map additional evaluation steps to the combined substeps
      'llm_evaluation': 'quality_evaluation',
      'pillar_analysis': 'quality_evaluation',
      'quality_assurance': 'quality_evaluation',
      
      'finalizing': 'completion',
      'resuming_from_human_review': 'question_generation',
      'completion_handler': 'completion',
      'completed': 'completion'
    };

    // Find current step index by mapping backend step to frontend step
    const frontendStepKey = stepMapping[workflow.current_step] || workflow.current_step;
    let newStepIndex = enabledSteps.findIndex(step => step.key === frontendStepKey);

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
      frontendStepKey,
      workflowProgress: workflow.progress,
      workflowStatus,
      enabledStepsKeys: enabledSteps.map(s => s.key),
      stepMappingResult: stepMapping[workflow.current_step],
      isStepMapped: stepMapping[workflow.current_step] !== undefined
    });

    // Additional debug logging for human review resumption
    if (workflow.current_step === 'generating_questions' || workflow.current_step === 'resuming_from_human_review') {
      console.log('🔄 [ProgressStepper] Human review resumption debug:', {
        currentStep: workflow.current_step,
        workflowStatus,
        newStepIndex,
        currentStepIndex,
        enabledSteps: enabledSteps.map(s => ({ key: s.key, subSteps: s.subSteps?.map(sub => sub.backendStep) }))
      });
    }

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
        } else if (currentStep?.key === 'quality_evaluation' && targetStep?.key === 'question_generation') {
          // Allow transition from quality_evaluation back to question_generation after human review completion
          console.log('✅ [ProgressStepper] Allowing transition from quality_evaluation to question_generation after human review');
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow.current_step, workflow.progress, workflowStatus, workflow.workflow_paused, enabledSteps]);

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

    // Find the substep that matches the current backend step
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
            <h1 className="text-2xl font-bold text-amber-900">Survey Generation</h1>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-amber-600 bg-clip-text text-transparent">
              {workflowStatus === 'completed' ? 100 : (workflow.progress || 0)}%
            </div>
            <div className="text-sm text-amber-600">Complete</div>
          </div>
        </div>
        
        {/* Overall Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 h-2 rounded-full transition-all duration-1000 ease-out relative"
              style={{ width: `${workflowStatus === 'completed' ? 100 : (workflow.progress || 0)}%` }}
            >
              <div className="absolute inset-0 bg-white/30 animate-pulse rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Split Screen */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Progress Steps */}
        <div className="w-1/4 border-r border-gray-200/50 bg-white/40 backdrop-blur-sm">
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
        <div className="w-3/4 bg-white/60 backdrop-blur-sm">
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
                    
                  </div>


                  {/* Dynamic Right Panel Content Based on Step Type */}
                  {currentMainStep.rightPanelType === 'substeps' && (
                    <div>
                      {/* Substeps List */}
                      <div className="space-y-3 mb-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Process Steps</h3>
                        {currentMainStep.subSteps.map((subStep, index) => {
                          // Handle multiple backend steps for the same substep
                          const isActive = (
                            (subStep.backendStep === workflow.current_step) ||
                            (subStep.key === 'llm_processing' && (workflow.current_step === 'generating_questions' || workflow.current_step === 'resuming_generation'))
                          ) && workflowStatus === 'in_progress';
                          
                          // Debug logging for substep status
                          if (subStep.key === 'llm_processing') {
                            console.log('🔍 [ProgressStepper] LLM Processing substep check:', {
                              backendStep: subStep.backendStep,
                              currentStep: workflow.current_step,
                              workflowStatus,
                              isActive,
                              isMatch: subStep.backendStep === workflow.current_step,
                              isResumingGeneration: workflow.current_step === 'resuming_generation'
                            });
                          }
                          
                          // Mark substeps as completed if:
                          // 1. The entire workflow is completed, OR
                          // 2. We're on a later substep (current step is after this substep)
                          const currentSubStepIndex = currentMainStep.subSteps.findIndex(s => s.backendStep === workflow.current_step);
                          
                          // Additional check: if we're on a step that comes after this substep in the workflow
                          const stepOrder = ['preparing_generation', 'generating_questions', 'resuming_generation', 'parsing_output'];
                          const currentStepOrderIndex = workflow.current_step ? stepOrder.indexOf(workflow.current_step) : -1;
                          const thisStepOrderIndex = stepOrder.indexOf(subStep.backendStep);
                          
                          const isCompleted = workflowStatus === 'completed' || 
                            (currentSubStepIndex !== -1 && currentSubStepIndex > index) ||
                            (currentStepOrderIndex !== -1 && thisStepOrderIndex !== -1 && currentStepOrderIndex > thisStepOrderIndex) ||
                            // Special case: resuming_generation should be treated as generating_questions for completion logic
                            (workflow.current_step === 'resuming_generation' && subStep.backendStep === 'preparing_generation');
                          
                          // Debug logging for substep completion
                          if (subStep.key === 'preparing_generation') {
                            console.log('🔍 [ProgressStepper] Preparing generation substep check:', {
                              subStepKey: subStep.key,
                              backendStep: subStep.backendStep,
                              currentStep: workflow.current_step,
                              currentSubStepIndex,
                              index,
                              currentStepOrderIndex,
                              thisStepOrderIndex,
                              isCompleted,
                              workflowStatus
                            });
                          }
                          
                          return (
                            <div
                              key={subStep.key}
                              data-testid={`substep-${subStep.backendStep}`}
                              className={`flex items-center space-x-3 p-3 rounded-lg border transition-all duration-200 ${
                                isActive
                                  ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 shadow-sm'
                                  : isCompleted
                                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                                isActive
                                  ? 'bg-blue-500 text-white animate-pulse'
                                  : isCompleted
                                  ? 'bg-green-500 text-white'
                                  : 'bg-gray-300 text-gray-600'
                              }`}>
                                {isCompleted ? '✓' : index + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className={`text-sm font-medium ${
                                  isActive ? 'text-blue-900' : isCompleted ? 'text-green-900' : 'text-gray-700'
                                }`}>
                                  {subStep.label}
                                </h4>
                                <p className={`text-xs ${
                                  isActive ? 'text-blue-700' : isCompleted ? 'text-green-700' : 'text-gray-500'
                                }`}>
                                  {isActive ? workflow.message || subStep.message : subStep.message}
                                </p>
                              </div>
                              {isActive && (
                                <div className="flex-shrink-0">
                                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {/* Show streaming UI for LLM processing */}
                      {currentMainStep.key === 'question_generation' &&
                       currentSubStep?.key === 'llm_processing' &&
                       workflow.streamingStats && (
                        <div className="space-y-4 mb-6">
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                            <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse mr-3"></div>
                              AI Survey Generation in Progress
                            </h3>

                            {/* Live Generation Stats */}
                            <div className="grid grid-cols-2 gap-4 mb-4">
                              <div className="bg-white/60 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-blue-800">{workflow.streamingStats.questionCount}</div>
                                <div className="text-xs text-blue-600">Questions Generated</div>
                              </div>
                              <div className="bg-white/60 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-blue-800">{workflow.streamingStats.sectionCount}</div>
                                <div className="text-xs text-blue-600">Sections Created</div>
                              </div>
                            </div>

                            {/* Current Activity */}
                            <div className="bg-white/80 rounded-lg p-4 mb-4">
                              <div className="flex items-center space-x-2 mb-2">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                <span className="text-sm font-medium text-gray-800">Currently Creating</span>
                              </div>
                              <p className="text-sm text-gray-700 animate-pulse">
                                {workflow.streamingStats.currentActivity || "Initializing survey generation..."}
                              </p>
                            </div>

                            {/* Live Question Preview */}
                            {workflow.streamingStats.latestQuestions.length > 0 && (
                              <div className="bg-white/80 rounded-lg p-4 mb-4">
                                <h4 className="text-sm font-medium text-gray-800 mb-3 flex items-center">
                                  <svg className="w-4 h-4 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  Latest Questions
                                </h4>
                                <div className="space-y-3">
                                  {workflow.streamingStats.latestQuestions.slice(-3).map((question, idx) => (
                                    <div key={idx} className="flex items-start space-x-3 p-2 bg-green-50 rounded border-l-4 border-green-400">
                                      <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-xs font-medium text-green-700">
                                        {workflow.streamingStats ? workflow.streamingStats.questionCount - workflow.streamingStats.latestQuestions.length + idx + 1 : idx + 1}
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-sm text-gray-800 leading-relaxed">{question.text || 'Question text not available'}</p>
                                        {question.type && (
                                          <div className="mt-1 inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                                            {question.type.replace('_', ' ')}
                                            {question.hasOptions && ' • with options'}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Section Progress */}
                            {workflow.streamingStats.currentSections.length > 0 && (
                              <div className="bg-white/80 rounded-lg p-4 mb-4">
                                <h4 className="text-sm font-medium text-gray-800 mb-3 flex items-center">
                                  <svg className="w-4 h-4 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                                  </svg>
                                  Survey Sections
                                </h4>
                                <div className="space-y-2">
                                  {workflow.streamingStats.currentSections.map((section, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-2 bg-purple-50 rounded">
                                      <span className="text-sm font-medium text-purple-900">{section.title || 'Section'}</span>
                                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">
                                        {section.questionCount || 0} questions
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Generation Progress Bar */}
                            <div className="bg-white/80 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700">Generation Progress</span>
                                <span className="text-sm text-gray-600">{Math.round(workflow.streamingStats.estimatedProgress || 0)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500 ease-out"
                                  style={{ width: `${workflow.streamingStats.estimatedProgress || 0}%` }}
                                />
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                Estimated based on content complexity and generation patterns
                              </p>
                              {workflow.streamingStats.elapsedTime && (
                                <p className="text-xs text-gray-500">
                                  Elapsed time: {Math.round(workflow.streamingStats.elapsedTime)}s
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}


                      {/* Add completion section with quality results when workflow is completed */}
                      {workflowStatus === 'completed' && (
                        <div className="mt-6 pt-6 border-t border-amber-200">
                          {/* Success Header */}
                          <div className="text-center mb-6">
                            <div className="mx-auto w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mb-4">
                              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                            <h3 className="text-2xl font-bold text-green-900 mb-2">Survey Generated Successfully!</h3>
                            <p className="text-green-700">Your AI-powered survey is ready for review and deployment.</p>
                          </div>
                          {/* Survey Summary */}
                          {currentSurvey && (
                            <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
                              <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
                                <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                </svg>
                                Survey Summary
                              </h4>
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-600">Title:</span>
                                  <p className="font-medium text-gray-900">{currentSurvey.title || 'Generated Survey'}</p>
                                </div>
                                <div>
                                  <span className="text-gray-600">Questions:</span>
                                  <p className="font-medium text-gray-900">
                                    {currentSurvey.sections?.reduce((total, section) => total + (section.questions?.length || 0), 0) ||
                                     currentSurvey.questions?.length || 0} questions
                                  </p>
                                </div>
                                <div>
                                  <span className="text-gray-600">Sections:</span>
                                  <p className="font-medium text-gray-900">{currentSurvey.sections?.length || 1} sections</p>
                                </div>
                                <div>
                                  <span className="text-gray-600">Survey ID:</span>
                                  <p className="font-medium text-gray-900 font-mono text-xs">{currentSurvey.survey_id}</p>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Quality Assessment Results */}
                          {currentSurvey?.pillar_scores && (
                            <div className="mb-6">
                              <h4 className="text-md font-semibold text-amber-900 mb-3 flex items-center">
                                <svg className="w-5 h-5 mr-2 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Quality Assessment
                              </h4>
                              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center space-x-2">
                                    <div className="text-2xl font-bold text-blue-800">
                                      {currentSurvey.pillar_scores.overall_grade || 'B'}
                                    </div>
                                    <div className="text-sm text-blue-700">
                                      ({Math.round((currentSurvey.pillar_scores.weighted_score || 0.8) * 100)}%)
                                    </div>
                                  </div>
                                  <div className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                    AI Quality Score
                                  </div>
                                </div>

                                {/* Pillar Breakdown */}
                                {currentSurvey.pillar_scores.pillar_breakdown && (
                                  <div className="space-y-2">
                                    {currentSurvey.pillar_scores.pillar_breakdown.map((pillar) => {
                                      const formattedPillar = pillar.display_name || pillar.pillar_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                      const scoreValue = pillar.score || 0.8;
                                      const passed = scoreValue >= 0.75;
                                      return (
                                        <div key={pillar.pillar_name} className="flex items-center justify-between text-xs">
                                          <span className={passed ? 'text-blue-700' : 'text-orange-700'}>
                                            {formattedPillar}
                                          </span>
                                          <div className="flex items-center space-x-1">
                                            <span className={passed ? 'text-blue-700' : 'text-orange-700'}>
                                              {Math.round(scoreValue * 100)}%
                                            </span>
                                            {passed ? (
                                              <div className="w-3 h-3 text-green-500">✓</div>
                                            ) : (
                                              <div className="w-3 h-3 text-orange-500">⚠</div>
                                            )}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}

                                {/* Quality Message */}
                                {currentSurvey.pillar_scores.weighted_score && currentSurvey.pillar_scores.weighted_score < 0.75 && (
                                  <div className="mt-3 text-xs text-orange-700 bg-orange-50 p-2 rounded border border-orange-200">
                                    ⚠️ Some quality aspects could be improved, but the survey is ready to use.
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Action Buttons */}
                          <h4 className="text-md font-semibold text-amber-900 mb-4">What would you like to do next?</h4>

                          {/* Primary Action - View/Edit Survey */}
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 mb-4">
                            <div className="flex items-start space-x-3">
                              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-blue-900 mb-1">Review & Deploy Your Survey</h5>
                                <p className="text-sm text-blue-700 mb-3">View the complete survey, make any final adjustments, and prepare for deployment.</p>
                                <button
                                  onClick={() => {
                                    if (currentSurvey?.survey_id) {
                                      window.location.href = `/surveys?id=${currentSurvey.survey_id}`;
                                    }
                                  }}
                                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-2.5 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center text-sm"
                                >
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  View & Edit Survey
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Secondary Action - Create New Survey */}
                          <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-xl p-4 mb-4">
                            <div className="flex items-start space-x-3">
                              <div className="flex-shrink-0 w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-yellow-900 mb-1">Create Another Survey</h5>
                                <p className="text-sm text-yellow-700 mb-3">Start fresh with a new RFQ document or requirements. Your previous surveys are saved in the dashboard.</p>
                                <button
                                  onClick={() => {
                                    console.log('🔄 [ProgressStepper] User requested new survey creation');
                                    if (onCancelGeneration) {
                                      onCancelGeneration();
                                    }
                                  }}
                                  className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-white px-6 py-2.5 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center text-sm"
                                >
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                  </svg>
                                  Create New Survey
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Tertiary Action - Generate from Same Requirements */}
                          <div className="bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-xl p-4">
                            <div className="flex items-start space-x-3">
                              <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-gray-900 mb-1">Try Different Variations</h5>
                                <p className="text-sm text-gray-600 mb-3">Generate another version using the same requirements to explore alternative approaches or question styles.</p>
                                <button
                                  onClick={() => {
                                    console.log('🔄 [ProgressStepper] User requested regeneration with same requirements');
                                    // Store current survey info before regenerating
                                    addToast({
                                      type: 'info',
                                      title: 'Generating Alternative Version',
                                      message: 'Creating a new survey variation with your existing requirements.',
                                      duration: 5000
                                    });
                                    // Reset workflow but keep the enhanced RFQ state
                                    if (onCancelGeneration) {
                                      onCancelGeneration();
                                    }
                                  }}
                                  className="bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 px-6 py-2.5 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center text-sm border border-gray-300"
                                >
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                  </svg>
                                  Generate Alternative
                                </button>
                              </div>
                            </div>
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
                                            <p className="text-sm text-gray-700">{question.text || 'Question text not available'}</p>
                                            {question.options && question.options.length > 0 && (
                                              <div className="mt-2 space-y-1">
                                                {question.options.map((option, optionIndex) => (
                                                  <div key={optionIndex} className="flex items-center space-x-2 text-xs text-gray-600">
                                                    <span className="w-4 h-4 border border-gray-300 rounded flex-shrink-0"></span>
                                                    <span>{typeof option === 'string' ? option : ((option as any).text || (option as any).label || 'Option')}</span>
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
                                          <p className="text-sm text-gray-700">{question.text || 'Question text not available'}</p>
                                          {question.options && question.options.length > 0 && (
                                            <div className="mt-2 space-y-1">
                                              {question.options.map((option, optionIndex) => (
                                                <div key={optionIndex} className="flex items-center space-x-2 text-xs text-gray-600">
                                                  <span className="w-4 h-4 border border-gray-300 rounded flex-shrink-0"></span>
                                                  <span>{typeof option === 'string' ? option : ((option as any).text || (option as any).label || 'Option')}</span>
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
                            <h4 className="text-lg font-semibold text-yellow-900 mb-2">Survey Complete!</h4>
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