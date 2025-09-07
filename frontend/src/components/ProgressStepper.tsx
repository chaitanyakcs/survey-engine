import React from 'react';
import { CheckIcon } from '@heroicons/react/24/solid';
import { useAppStore } from '../store/useAppStore';

const STEPS = [
  { key: 'parsing_rfq', label: 'Parsing RFQ', description: 'Analyzing requirements' },
  { key: 'matching_golden_examples', label: 'Finding Templates', description: 'Matching relevant examples' },
  { key: 'planning_methodologies', label: 'Planning Methods', description: 'Selecting research approaches' },
  { key: 'generating_questions', label: 'Creating Questions', description: 'Generating survey content' },
  { key: 'validation_scoring', label: 'Validation', description: 'Quality checking' },
  { key: 'finalizing', label: 'Finalizing', description: 'Saving survey' }
];

export const ProgressStepper: React.FC = () => {
  const { workflow } = useAppStore();
  
  const getStepStatus = (stepKey: string, index: number) => {
    if (!workflow.progress) return 'pending';
    
    const stepProgress = ((index + 1) / STEPS.length) * 100;
    
    if (workflow.current_step === stepKey) return 'current';
    if (workflow.progress >= stepProgress) return 'completed';
    return 'pending';
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
          <span>Progress</span>
          <span>{workflow.progress || 0}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${workflow.progress || 0}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="flex justify-between">
        {STEPS.map((step, index) => {
          const status = getStepStatus(step.key, index);
          
          return (
            <div key={step.key} className="flex flex-col items-center text-center max-w-24">
              {/* Step Circle */}
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center mb-2 border-2 transition-all duration-300
                ${status === 'completed' 
                  ? 'bg-green-500 border-green-500 text-white' 
                  : status === 'current'
                  ? 'bg-blue-500 border-blue-500 text-white animate-pulse'
                  : 'bg-white border-gray-300 text-gray-500'
                }
              `}>
                {status === 'completed' ? (
                  <CheckIcon className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-semibold">{index + 1}</span>
                )}
              </div>
              
              {/* Step Label */}
              <h3 className={`
                font-medium text-sm mb-1
                ${status === 'completed' || status === 'current' ? 'text-gray-900' : 'text-gray-500'}
              `}>
                {step.label}
              </h3>
              
              {/* Step Description */}
              <p className="text-xs text-gray-400">
                {step.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Current Message */}
      {workflow.message && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800 text-sm">
            {workflow.message}
          </p>
        </div>
      )}
    </div>
  );
};