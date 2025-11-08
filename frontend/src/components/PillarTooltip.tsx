import React from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/solid';

interface PillarTooltipProps {
  pillarName: string;
  description: string;
  examples?: {
    high: string;
    low: string;
  };
}

const PillarTooltip: React.FC<PillarTooltipProps> = ({
  pillarName,
  description,
  examples
}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
      >
        <InformationCircleIcon className="w-3 h-3 text-white" />
      </button>
      
      {isOpen && (
        <div className="absolute z-10 w-80 p-3 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-900">{pillarName}</h4>
            <p className="text-sm text-gray-700">{description}</p>
            
            {examples && (
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-medium text-green-700">High Score Example:</span>
                  <p className="text-xs text-gray-600">{examples.high}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-red-700">Low Score Example:</span>
                  <p className="text-xs text-gray-600">{examples.low}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PillarTooltip;
