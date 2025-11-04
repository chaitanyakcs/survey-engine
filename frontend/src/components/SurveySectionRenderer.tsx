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
  const [selectedValues, setSelectedValues] = React.useState<string[]>([]);
  
  const handleResponse = (value: any) => {
    if (onResponse) {
      onResponse(question.id, value);
    }
  };

  const handleCheckboxChange = (option: string, checked: boolean) => {
    const newValues = checked 
      ? [...selectedValues, option]
      : selectedValues.filter((v: string) => v !== option);
    setSelectedValues(newValues);
    handleResponse(newValues);
  };

  // Generate question text fallback - use text, label, or generate from ID
  const getQuestionText = () => {
    if (question.text && question.text.trim()) {
      return question.text;
    }
    // Fallback to label if available
    if (question.label && question.label.trim()) {
      // Convert label to readable format (e.g., "informed_consent" -> "Informed Consent")
      const labelText = question.label
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
      return labelText;
    }
    // Fallback to question ID or default message
    if (question.id) {
      return `${question.id.replace('_', ' ')} - Please answer the question below`;
    }
    return 'Question text not available';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {getQuestionText()}
          {question.required && <span className="text-red-500 ml-1">*</span>}
        </h3>
        {/* Always show question type for clarity */}
        <div className="text-sm text-gray-500 mb-2">
          Type: {question.type.replace('_', ' ')}
        </div>
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

      {question.type === 'multiple_select' && question.options && (
        <div className="space-y-2">
          {question.options.map((option, index) => (
            <label key={index} className="flex items-center space-x-3">
              <input
                type="checkbox"
                name={question.id}
                value={option}
                checked={selectedValues.includes(option)}
                onChange={(e) => handleCheckboxChange(option, e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
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

      {question.type === 'likert' && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Very Unlikely</span>
            <span>Unlikely</span>
            <span>Neutral</span>
            <span>Likely</span>
            <span>Very Likely</span>
          </div>
          <div className="flex justify-between">
            {[1, 2, 3, 4, 5].map((value) => (
              <label key={value} className="flex flex-col items-center space-y-1">
                <input
                  type="radio"
                  name={question.id}
                  value={value}
                  onChange={(e) => handleResponse(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-xs text-gray-500">{value}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {question.type === 'open_end' && (
        <textarea
          placeholder="Please enter your response..."
          onChange={(e) => handleResponse(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          rows={3}
        />
      )}

      {question.type === 'display_only' && (
        <div className="bg-gray-50 border-l-4 border-gray-400 p-4 rounded-r-lg">
          <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {question.text}
          </div>
          {question.description && (
            <div className="mt-2 text-xs text-gray-600 italic">
              {question.description}
            </div>
          )}
          <div className="mt-3 flex items-center justify-between">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              Display Only
            </span>
            <span className="text-xs text-gray-600">
              No response required
            </span>
          </div>
        </div>
      )}

      {question.type === 'single_open' && (
        <input
          type="text"
          placeholder="Please enter your response..."
          onChange={(e) => handleResponse(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      )}

      {question.type === 'multiple_open' && (
        <textarea
          placeholder="Please enter your response..."
          onChange={(e) => handleResponse(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          rows={4}
        />
      )}

      {question.type === 'open_ended' && (
        <textarea
          placeholder="Please provide your detailed response..."
          onChange={(e) => handleResponse(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          rows={5}
        />
      )}

      {question.type === 'yes_no' && (
        <div className="space-y-2">
          {/* Ensure we have options, default to Yes/No if missing */}
          {(question.options && question.options.length > 0) ? (
            question.options.map((option, index) => (
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
            ))
          ) : (
            // Default Yes/No options if not provided
            <>
              <label className="flex items-center space-x-3">
                <input
                  type="radio"
                  name={question.id}
                  value="Yes"
                  onChange={(e) => handleResponse(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-gray-700">Yes</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="radio"
                  name={question.id}
                  value="No"
                  onChange={(e) => handleResponse(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-gray-700">No</span>
              </label>
            </>
          )}
        </div>
      )}

      {question.type === 'instruction' && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
          <div className="mb-2">
            {/* Always show "Instructions" as the main heading */}
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">i</span>
              </div>
              <h4 className="text-lg font-bold text-blue-900">Instructions</h4>
            </div>
            
            {/* Display the instruction content */}
            <div className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap ml-8">
              {question.text || 'No instruction text provided'}
            </div>
          </div>
          
          <div className="mt-3 flex items-center justify-between">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Instruction Block
            </span>
            <span className="text-xs text-blue-600">
              No response required
            </span>
          </div>
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