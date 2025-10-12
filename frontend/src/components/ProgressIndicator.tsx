import React from 'react';

interface ProgressIndicatorProps {
  completed: number;
  total: number;
  label?: string;
  className?: string;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  completed,
  total,
  label = "Progress",
  className = ""
}) => {
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-blue-500';
    if (percentage >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm text-gray-500">{completed}/{total}</span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      <div className="text-xs text-gray-500 text-center">
        {percentage}% complete
      </div>
    </div>
  );
};

export default ProgressIndicator;
