import React from 'react';
import { 
  SparklesIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface SurveyGenerationIndicatorProps {
  isGenerating: boolean;
  progress?: number;
  status?: 'started' | 'in_progress' | 'completed' | 'failed' | 'paused';
  message?: string;
  className?: string;
}

export const SurveyGenerationIndicator: React.FC<SurveyGenerationIndicatorProps> = ({
  isGenerating,
  progress = 0,
  status = 'in_progress',
  message,
  className = ''
}) => {
  if (!isGenerating) return null;

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />;
      case 'paused':
        return <ClockIcon className="w-4 h-4 text-yellow-600" />;
      default:
        return <SparklesIcon className="w-4 h-4 text-amber-600 animate-pulse" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-amber-100 text-amber-800 border-amber-200';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return 'Generation Complete';
      case 'failed':
        return 'Generation Failed';
      case 'paused':
        return 'Generation Paused';
      case 'started':
        return 'Starting Generation...';
      case 'in_progress':
        return 'Generating Survey...';
      default:
        return 'Processing...';
    }
  };

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 ${getStatusColor()} ${className}`}>
      {getStatusIcon()}
      <span className="flex-1 min-w-0">
        {getStatusText()}
        {message && (
          <span className="ml-1 text-xs opacity-75 truncate">
            - {message}
          </span>
        )}
      </span>
      {(status === 'in_progress' || status === 'started') && progress > 0 && (
        <span className="text-xs font-semibold">
          {Math.round(progress)}%
        </span>
      )}
    </div>
  );
};
