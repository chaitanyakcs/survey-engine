import React from 'react';
import { EnhancedRFQRequest } from '../types';
import { PreGenerationPreview } from './PreGenerationPreview';

interface SurveyMetadataModalProps {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  rfqData?: EnhancedRFQRequest;
}

export const SurveyMetadataModal: React.FC<SurveyMetadataModalProps> = ({
  isOpen,
  onClose,
  surveyId,
  rfqData
}) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-white z-[9998] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <h2 className="text-xl font-bold text-gray-900">RFQ Used</h2>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-200"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-4">
          {rfqData ? (
            <PreGenerationPreview 
              rfq={rfqData}
              // Don't pass onGenerate or onEdit - makes it read-only
            />
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No RFQ data available for this survey</p>
              <p className="text-gray-400 text-sm mt-2">This survey may have been created before RFQ tracking was implemented.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
