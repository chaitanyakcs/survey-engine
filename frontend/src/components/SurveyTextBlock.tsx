import React from 'react';
import { SurveyTextContent, TextContentType } from '../types';
import { InformationCircleIcon, ShieldCheckIcon, DocumentTextIcon, UserGroupIcon } from '@heroicons/react/24/outline';

interface SurveyTextBlockProps {
  textContent: SurveyTextContent;
  className?: string;
  showLabel?: boolean; // Whether to show the AiRA label for debugging
}

const SurveyTextBlock: React.FC<SurveyTextBlockProps> = ({
  textContent,
  className = '',
  showLabel = false
}) => {
  const getTextTypeIcon = (type: TextContentType) => {
    switch (type) {
      case 'study_intro':
        return <UserGroupIcon className="w-5 h-5" />;
      case 'concept_intro':
        return <DocumentTextIcon className="w-5 h-5" />;
      case 'confidentiality':
        return <ShieldCheckIcon className="w-5 h-5" />;
      case 'product_usage':
        return <InformationCircleIcon className="w-5 h-5" />;
      default:
        return <InformationCircleIcon className="w-5 h-5" />;
    }
  };

  const getTextTypeStyles = (type: TextContentType) => {
    switch (type) {
      case 'study_intro':
        return 'bg-blue-50 border-blue-200 text-blue-900';
      case 'concept_intro':
        return 'bg-purple-50 border-purple-200 text-purple-900';
      case 'confidentiality':
        return 'bg-amber-50 border-amber-200 text-amber-900';
      case 'product_usage':
        return 'bg-green-50 border-green-200 text-green-900';
      case 'instruction':
        return 'bg-gray-50 border-gray-200 text-gray-900';
      case 'transition':
        return 'bg-indigo-50 border-indigo-200 text-indigo-900';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-900';
    }
  };

  const getTextTypeLabel = (type: TextContentType) => {
    switch (type) {
      case 'study_intro':
        return 'Study Introduction';
      case 'concept_intro':
        return 'Concept Introduction';
      case 'confidentiality':
        return 'Confidentiality Agreement';
      case 'product_usage':
        return 'Product Usage';
      case 'instruction':
        return 'Instructions';
      case 'transition':
        return 'Section Transition';
      default:
        return 'Information';
    }
  };

  const typeStyles = getTextTypeStyles(textContent.type);
  const icon = getTextTypeIcon(textContent.type);
  const typeLabel = getTextTypeLabel(textContent.type);

  return (
    <div className={`${typeStyles} border rounded-lg p-6 mb-6 ${className}`}>
      {/* Header with icon and type label */}
      <div className="flex items-center mb-4">
        <div className="flex items-center space-x-2">
          {icon}
          <span className="font-medium text-sm">{typeLabel}</span>
        </div>

        {/* Show AiRA label for debugging/development */}
        {showLabel && textContent.label && (
          <span className="ml-auto text-xs bg-white bg-opacity-50 px-2 py-1 rounded">
            AiRA: {textContent.label}
          </span>
        )}

        {/* Show mandatory indicator */}
        {textContent.mandatory && (
          <span className="ml-auto text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
            Required
          </span>
        )}
      </div>

      {/* Text content */}
      <div className="prose prose-sm max-w-none">
        <p className="leading-relaxed whitespace-pre-wrap">
          {textContent.content}
        </p>
      </div>

      {/* Footer for additional context (development only) */}
      {process.env.NODE_ENV === 'development' && showLabel && (
        <div className="mt-4 pt-4 border-t border-opacity-20 border-gray-400">
          <div className="text-xs text-opacity-70 space-y-1">
            <div>ID: {textContent.id}</div>
            {textContent.section_id && <div>Section: {textContent.section_id}</div>}
            {textContent.order !== undefined && <div>Order: {textContent.order}</div>}
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveyTextBlock;