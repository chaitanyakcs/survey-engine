import React from 'react';
import { SurveySection, Question } from '../types';
import SurveyTextBlock from './SurveyTextBlock';

interface SurveySectionRendererProps {
  section: SurveySection;
  className?: string;
  showDebugInfo?: boolean; // Show AiRA labels and debugging info
  onQuestionResponse?: (questionId: string, response: any) => void;
}

interface QuestionRendererProps {
  question: Question;
  onResponse?: (questionId: string, response: any) => void;
}

// Simple question renderer - in a full implementation, this would handle different question types
const QuestionRenderer: React.FC<QuestionRendererProps> = ({ question, onResponse }) => {
  const handleResponse = (value: any) => {
    if (onResponse) {
      onResponse(question.id, value);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {question.text}
          {question.required && <span className="text-red-500 ml-1">*</span>}
        </h3>
      </div>

      {/* Render different question types */}
      {question.type === 'multiple_choice' && question.options && (
        <div className="space-y-2">
          {question.options.map((option, index) => (
            <label key={index} className="flex items-center space-x-3">
              <input
                type="radio"
                name={question.id}
                value={option}
                onChange={(e) => handleResponse(e.target.value)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <span className="text-gray-700">{option}</span>
            </label>
          ))}
        </div>
      )}

      {question.type === 'scale' && question.scale_labels && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm text-gray-600">
            {Object.entries(question.scale_labels).map(([key, label]) => (
              <span key={key}>{label}</span>
            ))}
          </div>
          <div className="flex justify-between">
            {Object.keys(question.scale_labels).map((key) => (
              <label key={key} className="flex flex-col items-center space-y-1">
                <input
                  type="radio"
                  name={question.id}
                  value={key}
                  onChange={(e) => handleResponse(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-xs text-gray-500">{key}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {question.type === 'text' && (
        <textarea
          placeholder="Please enter your response..."
          onChange={(e) => handleResponse(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          rows={3}
        />
      )}

      {question.type === 'ranking' && question.options && (
        <div className="space-y-2">
          <p className="text-sm text-gray-600 mb-3">
            Drag to rank these options in order of preference:
          </p>
          {question.options.map((option, index) => (
            <div key={index} className="bg-gray-50 p-3 rounded border cursor-move">
              <span className="font-medium mr-2">{index + 1}.</span>
              {option}
            </div>
          ))}
        </div>
      )}

      {/* Question category and metadata */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 space-y-1">
            <div>Category: {question.category}</div>
            <div>Type: {question.type}</div>
            <div>Required: {question.required ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

const SurveySectionRenderer: React.FC<SurveySectionRendererProps> = ({
  section,
  className = '',
  showDebugInfo = false,
  onQuestionResponse
}) => {
  return (
    <div className={`survey-section ${className}`}>
      {/* Section Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{section.title}</h2>
        {section.description && (
          <p className="text-gray-600 leading-relaxed">{section.description}</p>
        )}
      </div>

      {/* Introduction Text Block */}
      {section.introText && (
        <SurveyTextBlock
          textContent={section.introText}
          showLabel={showDebugInfo}
          className="mb-6"
        />
      )}

      {/* Additional Text Blocks (ordered) */}
      {section.textBlocks && section.textBlocks.length > 0 && (
        <div className="mb-6 space-y-4">
          {section.textBlocks
            .sort((a, b) => (a.order || 0) - (b.order || 0))
            .map((textBlock) => (
              <SurveyTextBlock
                key={textBlock.id}
                textContent={textBlock}
                showLabel={showDebugInfo}
              />
            ))}
        </div>
      )}

      {/* Questions */}
      {section.questions && section.questions.length > 0 && (
        <div className="space-y-4">
          {section.questions.map((question) => (
            <QuestionRenderer
              key={question.id}
              question={question}
              onResponse={onQuestionResponse}
            />
          ))}
        </div>
      )}

      {/* Closing Text Block */}
      {section.closingText && (
        <SurveyTextBlock
          textContent={section.closingText}
          showLabel={showDebugInfo}
          className="mt-6"
        />
      )}

      {/* Development debug info */}
      {process.env.NODE_ENV === 'development' && showDebugInfo && (
        <div className="mt-8 p-4 bg-gray-100 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Section Debug Info</h4>
          <div className="text-xs text-gray-600 space-y-1">
            <div>Section ID: {section.id}</div>
            <div>Questions: {section.questions?.length || 0}</div>
            <div>Text Blocks: {section.textBlocks?.length || 0}</div>
            <div>Has Intro Text: {section.introText ? 'Yes' : 'No'}</div>
            <div>Has Closing Text: {section.closingText ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveySectionRenderer;