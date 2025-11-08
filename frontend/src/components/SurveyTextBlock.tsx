import React from 'react';
import { SurveyTextContent, TextContentType } from '../types';
import { InformationCircleIcon, ShieldCheckIcon, DocumentTextIcon, UserGroupIcon } from '@heroicons/react/24/outline';

interface SurveyTextBlockProps {
  textContent: SurveyTextContent | { text: string } | string;
  className?: string;
  showLabel?: boolean; // Whether to show the AiRA label for debugging
}

const SurveyTextBlock: React.FC<SurveyTextBlockProps> = ({
  textContent,
  className = '',
  showLabel = false
}) => {
  // Handle both SurveyTextContent structure and simple text blocks
  const getTextContent = () => {
    if (typeof textContent === 'string') {
      return textContent;
    }
    if ('content' in textContent && textContent.content) {
      return textContent.content;
    }
    if ('text' in textContent && textContent.text) {
      return textContent.text;
    }
    return '';
  };

  const getTextType = (): TextContentType => {
    if (typeof textContent === 'string') {
      return 'instruction';
    }
    if ('type' in textContent && textContent.type) {
      return textContent.type;
    }
    // Default to instruction for simple text blocks
    return 'instruction';
  };

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

  const textType = getTextType();
  const typeLabel = getTextTypeLabel(textType);
  const typeStyles = getTextTypeStyles(textType);
  const icon = getTextTypeIcon(textType);
  const content = getTextContent();

  // For instructions, use lean design with just blue info icon - no type labels
  if (textType === 'instruction') {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm p-5 mb-4 ${className}`}>
        <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-400">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">i</span>
              </div>
            </div>
            
            {/* Instruction text */}
            <div className="flex-1">
              <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                {content}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // For other types, show full header
  return (
    <div className={`${typeStyles} border rounded-lg p-6 mb-6 ${className}`}>
      {/* Header with prominent Instructions and small purple tag */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex flex-col">
          {/* Prominent Instructions heading */}
          <div className="flex items-center space-x-2 mb-1">
            {icon}
            <span className="font-bold text-lg">{typeLabel}</span>
          </div>
          
          {/* Small purple tag (label) */}
          {typeof textContent === 'object' && 'label' in textContent && textContent.label && (
            <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded ml-6 w-fit">
              {textContent.label}
            </span>
          )}
        </div>

        {/* Show mandatory indicator */}
        {typeof textContent === 'object' && 'mandatory' in textContent && textContent.mandatory && (
          <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
            Required
          </span>
        )}
      </div>

      {/* Text content */}
      <div className="prose prose-sm max-w-none">
        <p className="leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
      </div>

      {/* Footer for additional context (development only) */}
      {process.env.NODE_ENV === 'development' && showLabel && (
        <div className="mt-4 pt-4 border-t border-opacity-20 border-gray-400">
          <div className="text-xs text-opacity-70 space-y-1">
            {typeof textContent === 'object' && 'id' in textContent && textContent.id && <div>ID: {textContent.id}</div>}
            {typeof textContent === 'object' && 'section_id' in textContent && textContent.section_id && <div>Section: {textContent.section_id}</div>}
            {typeof textContent === 'object' && 'order' in textContent && textContent.order !== undefined && <div>Order: {textContent.order}</div>}
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveyTextBlock;