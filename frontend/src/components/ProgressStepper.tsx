import React, { useState, useEffect } from 'react';
import { CheckIcon, ClockIcon, SparklesIcon } from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';
import { WorkflowState } from '../types';

const STEPS = [
  { 
    key: 'initializing_workflow', 
    label: 'Starting Workflow', 
    description: 'Initializing survey generation process',
    icon: '🚀',
    color: 'blue',
    details: 'Setting up the AI-powered survey generation workflow'
  },
  { 
    key: 'parsing_rfq', 
    label: 'Analyzing Request', 
    description: 'Understanding your research requirements',
    icon: '📋',
    color: 'blue',
    details: 'Extracting research objectives, target audience, and key goals from your RFQ'
  },
  { 
    key: 'generating_embeddings', 
    label: 'Generating Embeddings', 
    description: 'Creating semantic search vectors',
    icon: '🧠',
    color: 'purple',
    details: 'Converting your request into searchable vectors for finding similar surveys'
  },
  { 
    key: 'rfq_parsed', 
    label: 'RFQ Analysis Complete', 
    description: 'Request analysis finished',
    icon: '✅',
    color: 'green',
    details: 'Successfully analyzed your research request and generated embeddings'
  },
  { 
    key: 'matching_golden_examples', 
    label: 'Finding Best Practices', 
    description: 'Sourcing proven survey templates',
    icon: '🔍',
    color: 'purple',
    details: 'Matching your needs with our database of high-performing surveys'
  },
  { 
    key: 'building_context', 
    label: 'Building Context', 
    description: 'Assembling research context',
    icon: '📚',
    color: 'indigo',
    details: 'Combining golden examples, methodology blocks, and templates'
  },
  { 
    key: 'generating_questions', 
    label: 'Crafting Questions', 
    description: 'Creating engaging survey content',
    icon: '✍️',
    color: 'green',
    details: 'Developing clear, unbiased questions that drive actionable insights'
  },
  { 
    key: 'validation_scoring', 
    label: 'Quality Assurance', 
    description: 'Validating survey effectiveness',
    icon: '✅',
    color: 'yellow',
    details: 'Scoring and optimizing questions for maximum response quality'
  },
  { 
    key: 'finalizing', 
    label: 'Finalizing Survey', 
    description: 'Preparing your professional survey',
    icon: '🎯',
    color: 'emerald',
    details: 'Final review and preparation for deployment to respondents'
  },
  { 
    key: 'completed', 
    label: 'Survey Ready!', 
    description: 'Your survey is complete and ready to view',
    icon: '🎉',
    color: 'emerald',
    details: 'Survey generation completed successfully!'
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
  const { workflow, currentSurvey } = useAppStore();
  const workflowStatus = workflow.status;
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  
  useEffect(() => {
    if (!workflow.current_step) return;
    
    const stepIndex = STEPS.findIndex(step => step.key === workflow.current_step);
    if (stepIndex !== -1) {
      setCurrentStepIndex(stepIndex);
    }
    
    // Update completed steps based on progress
    const progress = workflow.progress || 0;
    const completed = [];
    for (let i = 0; i < STEPS.length; i++) {
      const stepProgress = ((i + 1) / STEPS.length) * 100;
      if (progress >= stepProgress) {
        completed.push(i);
      }
    }
    setCompletedSteps(completed);
  }, [workflow.current_step, workflow.progress]);
  
  const getStepStatus = (index: number) => {
    // If workflow is completed, all steps should be completed
    if (workflowStatus === 'completed') return 'completed';
    
    if (completedSteps.includes(index)) return 'completed';
    if (index === currentStepIndex) return 'current';
    if (index < currentStepIndex) return 'completed';
    return 'pending';
  };

  const getColorClasses = (color: string, status: string) => {
    const colorMap = {
      blue: {
        bg: 'bg-blue-500',
        border: 'border-blue-500',
        light: 'bg-blue-50',
        text: 'text-blue-700',
        ring: 'ring-blue-200'
      },
      purple: {
        bg: 'bg-purple-500',
        border: 'border-purple-500',
        light: 'bg-purple-50',
        text: 'text-purple-700',
        ring: 'ring-purple-200'
      },
      orange: {
        bg: 'bg-orange-500',
        border: 'border-orange-500',
        light: 'bg-orange-50',
        text: 'text-orange-700',
        ring: 'ring-orange-200'
      },
      indigo: {
        bg: 'bg-indigo-500',
        border: 'border-indigo-500',
        light: 'bg-indigo-50',
        text: 'text-indigo-700',
        ring: 'ring-indigo-200'
      },
      green: {
        bg: 'bg-green-500',
        border: 'border-green-500',
        light: 'bg-green-50',
        text: 'text-green-700',
        ring: 'ring-green-200'
      },
      yellow: {
        bg: 'bg-yellow-500',
        border: 'border-yellow-500',
        light: 'bg-yellow-50',
        text: 'text-yellow-700',
        ring: 'ring-yellow-200'
      },
      emerald: {
        bg: 'bg-emerald-500',
        border: 'border-emerald-500',
        light: 'bg-emerald-50',
        text: 'text-emerald-700',
        ring: 'ring-emerald-200'
      }
    };
    
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Overall Progress Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center space-x-3 mb-4">
          <SparklesIcon className="w-8 h-8 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-900">Survey Generation Progress</h2>
        </div>
        <div className="w-full max-w-md mx-auto">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Overall Progress</span>
            <span className="font-semibold">{workflow.progress || 0}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-emerald-500 h-3 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${workflow.progress || 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stacked Progress Tiles */}
      <div className="relative">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-white opacity-60 rounded-3xl" />
        <div className="relative grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4">
          {STEPS.map((step, index) => {
            const status = getStepStatus(index);
            const colors = getColorClasses(step.color, status);
            const isCurrent = status === 'current';
            const isCompleted = status === 'completed';
            const isPending = status === 'pending';
            
            return (
              <div
                key={step.key}
                className={`
                  relative transform transition-all duration-700 ease-out
                  ${isCurrent 
                    ? 'scale-105 z-10 shadow-2xl' 
                    : isCompleted 
                    ? 'scale-100 z-5 shadow-lg' 
                    : 'scale-95 z-0 shadow-md'
                  }
                  ${isCurrent ? 'animate-pulse' : ''}
                `}
                style={{
                  animationDelay: `${index * 100}ms`,
                  transform: isCurrent ? 'translateY(-8px)' : 'translateY(0)'
                }}
              >
                {/* Tile Container */}
                <div className={`
                  relative overflow-hidden rounded-2xl border-2 transition-all duration-500 backdrop-blur-sm h-full flex flex-col
                  ${isCurrent 
                    ? `${colors.border} ${colors.light} ring-4 ${colors.ring} shadow-2xl` 
                    : isCompleted 
                    ? 'border-green-300 bg-green-50/80 shadow-lg' 
                    : 'border-gray-200 bg-gradient-to-br from-gray-50 to-gray-100/80 shadow-md hover:shadow-lg'
                  }
                `}>
                  {/* Animated Border for Current Step */}
                  {isCurrent && (
                    <div className="absolute inset-0 rounded-2xl">
                      <div className={`
                        absolute inset-0 rounded-2xl animate-spin
                        ${colors.bg} opacity-20
                      `} style={{ animationDuration: '3s' }} />
                    </div>
                  )}
                  
                  {/* Content */}
                  <div className="relative p-6 flex-1 flex flex-col">
                    {/* Header */}
                    <div className="flex items-center space-x-4 mb-4">
                      {/* Icon */}
                      <div className={`
                        w-12 h-12 rounded-xl flex items-center justify-center text-2xl
                        transition-all duration-500
                        ${isCurrent 
                          ? `${colors.bg} text-white shadow-lg` 
                          : isCompleted 
                          ? 'bg-green-500 text-white' 
                          : 'bg-gray-100 text-gray-400'
                        }
                      `}>
                        {isCompleted ? (
                          <CheckIcon className="w-6 h-6" />
                        ) : (
                          <span>{step.icon}</span>
                        )}
                      </div>
                      
                      {/* Step Info */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className={`
                            font-bold text-lg
                            ${isCurrent || isCompleted ? 'text-gray-900' : 'text-gray-500'}
                          `}>
                            {step.label}
                          </h3>
                          {isCurrent && (
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            </div>
                          )}
                        </div>
                        <p className={`
                          text-sm font-medium
                          ${isCurrent ? colors.text : isCompleted ? 'text-green-700' : 'text-gray-400'}
                        `}>
                          {step.description}
                        </p>
                      </div>
                    </div>
                    
                    {/* Details */}
                    <div className={`
                      text-sm leading-relaxed flex-1
                      ${isCurrent ? 'text-gray-600' : isCompleted ? 'text-green-600' : 'text-gray-400'}
                    `}>
                      {step.details}
                    </div>
                    
                    {/* Status Indicator */}
                    <div className="mt-4 flex items-center justify-between">
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
                      
                      {/* Step Number */}
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                        ${isCurrent 
                          ? `${colors.bg} text-white` 
                          : isCompleted 
                          ? 'bg-green-500 text-white' 
                          : 'bg-gray-200 text-gray-500'
                        }
                      `}>
                        {index + 1}
                      </div>
                    </div>
                  </div>
                  
                  {/* Progress Bar for Current Step */}
                  {isCurrent && workflow.message && (
                    <div className="px-6 pb-4">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`${colors.bg} h-2 rounded-full transition-all duration-1000`}
                          style={{ width: '100%' }}
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-2 text-center">
                        {workflow.message}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-center space-x-4">
        {/* Show buttons based on status */}
        {workflowStatus === 'completed' && currentSurvey ? (
          <>
            {/* Primary: View Summary Button */}
            <button
              onClick={() => onShowSummary && onShowSummary()}
              className="inline-flex items-center px-10 py-4 rounded-xl font-bold text-lg transition-all duration-200 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white shadow-xl hover:shadow-2xl transform hover:scale-105"
            >
              <SparklesIcon className="w-6 h-6 mr-3" />
              View AI Analysis Summary
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            {/* Secondary: Direct Survey View */}
            <button
              onClick={() => onShowSurvey && onShowSurvey()}
              className="inline-flex items-center px-6 py-4 rounded-xl font-medium text-lg transition-all duration-200 bg-gray-100 hover:bg-gray-200 text-gray-700 shadow-lg hover:shadow-xl"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                inline-flex items-center px-8 py-3 rounded-xl font-medium text-lg transition-all duration-200
                ${workflowStatus === 'completed' && currentSurvey
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg hover:shadow-emerald-200 transform hover:scale-105'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              View Survey
              {workflowStatus === 'completed' && currentSurvey && (
                <span className="ml-2 text-emerald-200">✓</span>
              )}
            </button>

            {/* Cancel Generation Button - enabled only during generation */}
            <button
              onClick={() => onCancelGeneration && onCancelGeneration()}
              disabled={workflowStatus !== 'started' && workflowStatus !== 'in_progress'}
              className={`
                inline-flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200
                ${workflowStatus === 'started' || workflowStatus === 'in_progress'
                  ? 'bg-red-100 hover:bg-red-200 text-red-700 border border-red-300 hover:border-red-400'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
                }
              `}
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel Generation
            </button>
          </>
        )}
      </div>

      {/* Status Information */}
      <div className="mt-6 text-center">
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
      </div>
    </div>
  );
};