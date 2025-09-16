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
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((currentValue - 1) / 4) * 100}%, #e5e7eb ${((currentValue - 1) / 4) * 100}%, #e5e7eb 100%)`
            }}
          />
        </div>
        
        <span className="text-xs text-gray-500 flex-shrink-0">{highLabel}</span>
        
        {/* Current value display */}
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 min-w-[24px] justify-center">
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
            background: #3b82f6;
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }
          
          .slider::-moz-range-thumb {
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: #3b82f6;
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