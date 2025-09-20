import React from 'react';
import { LikertScale as LikertScaleType } from '../types';

interface LikertScaleProps {
  label: string;
  value: LikertScaleType | undefined;
  onChange: (value: LikertScaleType) => void;
  lowLabel?: string;
  highLabel?: string;
  className?: string;
}

const LikertScale: React.FC<LikertScaleProps> = ({
  label,
  value,
  onChange,
  lowLabel = "Very Poor",
  highLabel = "Excellent",
  className = ""
}) => {
  const currentValue = value || 3; // Default to 3 if undefined
  
  const handleSliderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(event.target.value) as LikertScaleType;
    onChange(newValue);
  };

  // Color coding based on Likert scale value
  const getValueColor = (val: number) => {
    switch (val) {
      case 1: return 'bg-red-100 text-red-800 border-red-200';
      case 2: return 'bg-orange-100 text-orange-800 border-orange-200';
      case 3: return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 4: return 'bg-amber-100 text-amber-800 border-amber-200';
      case 5: return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSliderColor = (val: number) => {
    switch (val) {
      case 1: return '#ef4444'; // red-500
      case 2: return '#f97316'; // orange-500
      case 3: return '#eab308'; // yellow-500
      case 4: return '#f59e0b'; // amber-500
      case 5: return '#22c55e'; // green-500
      default: return '#f59e0b'; // amber-500
    }
  };
  
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <label className="text-sm font-medium text-gray-700 w-32 flex-shrink-0">
        {label}
      </label>
      
      <div className="flex-1 flex items-center gap-3">
        <span className="text-xs text-gray-500 flex-shrink-0">{lowLabel}</span>
        
        {/* Slider */}
        <div className="flex-1 relative">
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            value={currentValue}
            onChange={handleSliderChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, ${getSliderColor(currentValue)} 0%, ${getSliderColor(currentValue)} ${((currentValue - 1) / 4) * 100}%, #e5e7eb ${((currentValue - 1) / 4) * 100}%, #e5e7eb 100%)`
            }}
          />
        </div>
        
        <span className="text-xs text-gray-500 flex-shrink-0">{highLabel}</span>
        
        {/* Current value display */}
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border min-w-[24px] justify-center ${getValueColor(currentValue)}`}>
          {currentValue}
        </span>
      </div>
      
      <style dangerouslySetInnerHTML={{
        __html: `
          .slider::-webkit-slider-thumb {
            appearance: none;
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: ${getSliderColor(currentValue)};
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }
          
          .slider::-moz-range-thumb {
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: ${getSliderColor(currentValue)};
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }
        `
      }} />
    </div>
  );
};

export default LikertScale;