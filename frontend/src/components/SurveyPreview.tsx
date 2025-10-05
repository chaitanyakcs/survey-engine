import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, Survey, SurveySection, QuestionAnnotation, SectionAnnotation, SurveyAnnotations, SurveyLevelAnnotation } from '../types';
import QuestionAnnotationPanel from './QuestionAnnotationPanel';
import SectionAnnotationPanel from './SectionAnnotationPanel';
import AnnotationMode from './AnnotationMode';
import { SurveyLevelAnnotationPanel } from './SurveyLevelAnnotationPanel';
import MatrixLikert from './MatrixLikert';
import ConstantSum from './ConstantSum';
import NumericGrid from './NumericGrid';
import NumericOpen from './NumericOpen';
import GaborGranger from './GaborGranger';
import SurveyTextBlock from './SurveyTextBlock';
import { PencilIcon, ChevronDownIcon, ChevronRightIcon, TagIcon, CheckIcon, XMarkIcon, StarIcon, TrashIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

// Helper function to extract all questions from survey (supports both formats)
const extractAllQuestions = (survey: Survey): Question[] => {
  if (survey.sections) {
    return survey.sections.flatMap(section => section.questions);
  } else if (survey.questions) {
    return survey.questions;
  }
  return [];
};

// Helper function to check if survey uses sections format
const hasSections = (survey: Survey): boolean => {
  return !!survey.sections && survey.sections.length > 0;
};

// Utility function to safely render values that might be objects
const safeRenderValue = (value: any): string => {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return String(value);
  if (value === null || value === undefined) return '';
  if (typeof value === 'object') {
    return (value as any)?.text || (value as any)?.label || (value as any)?.name || JSON.stringify(value);
  }
  return String(value);
};

const QuestionCard: React.FC<{ 
  question: Question; 
  index: number; 
  onUpdate: (updatedQuestion: Question) => void; 
  onDelete: () => void;
  onMove: (questionId: string, direction: 'up' | 'down') => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isEditingSurvey: boolean;
  isAnnotationMode: boolean;
  onAnnotate?: (annotation: QuestionAnnotation) => void;
  annotation?: QuestionAnnotation;
}> = ({ question, index, onUpdate, onDelete, onMove, canMoveUp, canMoveDown, isEditingSurvey, isAnnotationMode, onAnnotate, annotation }) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  const isSelected = selectedQuestionId === question.id;
  
  console.log('🔍 [QuestionCard] Rendered with:', {
    questionId: question.id,
    isSelected,
    selectedQuestionId,
    isAnnotationMode,
    hasAnnotation: !!annotation
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editedQuestion, setEditedQuestion] = useState<Question>(question);

  const handleSaveEdit = () => {
    onUpdate(editedQuestion);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedQuestion(question);
    setIsEditing(false);
  };

  const updateQuestionField = (field: keyof Question, value: any) => {
    setEditedQuestion(prev => ({ ...prev, [field]: value }));
  };

  const addOption = () => {
    const newOptions = [...(editedQuestion.options || []), ''];
    updateQuestionField('options', newOptions);
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...(editedQuestion.options || [])];
    newOptions[index] = value;
    updateQuestionField('options', newOptions);
  };

  const removeOption = (index: number) => {
    const newOptions = editedQuestion.options?.filter((_, i) => i !== index) || [];
    updateQuestionField('options', newOptions);
  };

  const handleAnnotationSave = (newAnnotation: QuestionAnnotation) => {
    if (onAnnotate) {
      onAnnotate(newAnnotation);
    }
  };

  const handleAnnotationCancel = () => {
    // No-op since we're not using intermediate state
  };

  return (
    <div 
      className={`
        border rounded-lg p-4 cursor-pointer transition-all duration-200
        ${isSelected ? 'border-amber-500 bg-amber-50' : 'border-gray-200 hover:border-gray-300'}
      `}
      onClick={() => {
        console.log('🔍 [QuestionCard] Question clicked:', {
          questionId: question.id,
          isSelected,
          willSelect: !isSelected
        });
        setSelectedQuestion(isSelected ? undefined : question.id);
      }}
    >
      {/* Question Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {question.type !== 'instruction' && (
            <span className="text-sm font-medium text-gray-500">Q{index + 1}</span>
          )}
          {question.methodology && question.type !== 'instruction' && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {question.methodology}
            </span>
          )}
          <span className={`
            inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
            ${question.category === 'screening' ? 'bg-yellow-100 text-yellow-800' :
              question.category === 'pricing' ? 'bg-green-100 text-green-800' :
              question.category === 'features' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'}
          `}>
            {question.category}
          </span>
          {annotation && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              <TagIcon className="w-3 h-3 mr-1" />
              Annotated
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {question.required && (
            <span className="text-red-500 text-sm">*</span>
          )}
          {/* X button to exit edit mode */}
          {isEditing && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleCancelEdit();
              }}
              className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
              title="Exit edit mode"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Question Text - only show for non-instruction types */}
      {question.type !== 'instruction' && (
        <>
          {isEditing ? (
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">Question Text</label>
              <textarea
                value={editedQuestion.text}
                onChange={(e) => updateQuestionField('text', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                rows={2}
              />
            </div>
          ) : (
            <h3 className="font-medium text-gray-900 mb-3">
              {question.text || 'Question text not available'}
            </h3>
          )}
        </>
      )}

      {/* Question Options/Input */}
      <div className="mb-3">
        {question.type === 'multiple_choice' && (
          <div className="space-y-2">
            {isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Options</label>
                <div className="space-y-2">
                  {editedQuestion.options?.map((option, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={typeof option === 'string' ? option : 
                               typeof option === 'object' && option !== null ? 
                                 (option as any)?.text || (option as any)?.label || 'Option' : 
                                 String(option)}
                        onChange={(e) => updateOption(idx, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        placeholder={`Option ${idx + 1}`}
                      />
                      <button
                        onClick={() => removeOption(idx)}
                        className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addOption}
                    className="px-3 py-2 text-sm text-amber-600 border border-amber-300 rounded-md hover:bg-amber-50"
                  >
                    Add Option
                  </button>
                </div>
              </div>
            ) : (
              question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center">
                  <input
                    type="radio"
                    disabled
                    className="h-4 w-4 text-amber-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {typeof option === 'string' ? option : 
                     typeof option === 'object' && option !== null ? 
                       (option as any)?.text || (option as any)?.label || 'Option' : 
                       String(option)}
                  </label>
                </div>
              ))
            )}
          </div>
        )}
        
        {question.type === 'scale' && (
          <div className="space-y-3">
            {/* Scale options as radio buttons */}
            <div className="space-y-2">
              {question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center">
                  <input
                    type="radio"
                    disabled
                    className="h-4 w-4 text-amber-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {typeof option === 'string' ? option : 
                     typeof option === 'object' && option !== null ? 
                       (option as any)?.text || (option as any)?.label || 'Option' : 
                       String(option)}
                  </label>
                </div>
              ))}
            </div>
            
            {/* Scale labels if available */}
            {question.scale_labels && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md">
                <div className="text-xs font-medium text-gray-600 mb-2">Scale Labels:</div>
                <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                  {Object.entries(question.scale_labels).map(([key, value]) => (
                    <span key={key} className="flex items-center">
                      <span className="font-medium">{key}:</span>
                      <span className="ml-1">{value}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {question.type === 'ranking' && (
          <div className="space-y-3">
            <div className="text-sm text-gray-600 mb-3">
              Please rank the following options in order of importance (drag to reorder):
            </div>
            <div className="space-y-2">
              {question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-center w-6 h-6 bg-amber-100 text-amber-600 rounded-full text-sm font-medium mr-3">
                    {idx + 1}
                  </div>
                  <span className="text-sm text-gray-700 flex-1">{typeof option === 'string' ? option : 
                     typeof option === 'object' && option !== null ? 
                       (option as any)?.text || (option as any)?.label || 'Option' : 
                       String(option)}</span>
                  <div className="flex space-x-1">
                    <button
                      disabled
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      disabled
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Move down"
                    >
                      ↓
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {question.type === 'text' && (
          <input
            type="text"
            disabled
            placeholder="Respondent will enter text here..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
          />
        )}

        {question.type === 'instruction' && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
            <div className="mb-2">
              {/* Extract first words before colon as heading */}
              {(() => {
                const text = question.text || '';
                const colonIndex = text.indexOf(':');
                const heading = colonIndex > 0 ? text.substring(0, colonIndex).trim() : 'Instructions';
                const content = colonIndex > 0 ? text.substring(colonIndex + 1).trim() : text;
                
                return (
                  <>
                    <h4 className="text-lg font-bold text-blue-900 mb-2">{heading}</h4>
                    <div className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                      {content}
                    </div>
                  </>
                );
              })()}
              
              {question.description && (
                <div className="mt-2 text-xs text-blue-600 italic">
                  {question.description}
                </div>
              )}
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

        {question.type === 'single_choice' && (
          <div className="space-y-2">
            {question.options?.map((option, idx) => (
              <div key={idx} className="flex items-center">
                <input
                  type="radio"
                  disabled
                  className="h-4 w-4 text-amber-600 border-gray-300"
                />
                <label className="ml-2 text-sm text-gray-700">
                  {typeof option === 'string' ? option : 
                     typeof option === 'object' && option !== null ? 
                       (option as any)?.text || (option as any)?.label || 'Option' : 
                       String(option)}
                </label>
              </div>
            ))}
          </div>
        )}

        {question.type === 'matrix' && (
          <div className="overflow-x-auto">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="text-sm font-medium text-gray-800 mb-3">Matrix Question</div>
              <div className="text-sm text-gray-600 mb-4">
                Please rate each item using the scale provided:
              </div>
              {question.options && question.options.length > 0 && (
                <div className="space-y-3">
                  {question.options.slice(0, 3).map((option, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border">
                      <span className="text-sm text-gray-700">
                        {typeof option === 'string' ? option : 
                         typeof option === 'object' && option !== null ? 
                           (option as any)?.text || (option as any)?.label || 'Item' : 
                           String(option)}
                      </span>
                      <div className="flex space-x-2">
                        {[1,2,3,4,5].map(num => (
                          <label key={num} className="flex items-center">
                            <input type="radio" disabled className="h-3 w-3 text-amber-600" />
                            <span className="ml-1 text-xs text-gray-500">{num}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                  {question.options.length > 3 && (
                    <div className="text-xs text-gray-500 italic">
                      ... and {question.options.length - 3} more items
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {question.type === 'numeric' && (
          <input
            type="number"
            disabled
            placeholder="Enter a number..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
          />
        )}

        {question.type === 'date' && (
          <input
            type="date"
            disabled
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
          />
        )}

        {question.type === 'boolean' && (
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="radio"
                disabled
                className="h-4 w-4 text-amber-600 border-gray-300"
              />
              <label className="ml-2 text-sm text-gray-700">Yes</label>
            </div>
            <div className="flex items-center">
              <input
                type="radio"
                disabled
                className="h-4 w-4 text-amber-600 border-gray-300"
              />
              <label className="ml-2 text-sm text-gray-700">No</label>
            </div>
          </div>
        )}

        {question.type === 'open_text' && (
          <textarea
            disabled
            placeholder="Respondent will enter their response here..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 resize-vertical"
            rows={4}
          />
        )}

        {question.type === 'multiple_select' && (
          <div className="space-y-2">
            {question.options?.map((option, idx) => (
              <div key={idx} className="flex items-center">
                <input
                  type="checkbox"
                  disabled
                  className="h-4 w-4 text-amber-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">
                  {typeof option === 'string' ? option : 
                     typeof option === 'object' && option !== null ? 
                       (option as any)?.text || (option as any)?.label || 'Option' : 
                       String(option)}
                </label>
              </div>
            ))}
          </div>
        )}

        {question.type === 'matrix_likert' && (
          <MatrixLikert question={question} isPreview={true} />
        )}

        {question.type === 'constant_sum' && (
          <ConstantSum question={question} isPreview={true} />
        )}

        {question.type === 'gabor_granger' && (
          <GaborGranger question={question} isPreview={true} />
        )}

        {question.type === 'numeric_grid' && (
          <NumericGrid question={question} isPreview={true} />
        )}

        {question.type === 'numeric_open' && (
          <NumericOpen question={question} isPreview={true} />
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
                    name={`${question.id}_likert`}
                    value={value}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    disabled={true}
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
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-gray-50"
            rows={3}
            disabled={true}
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
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
            disabled={true}
          />
        )}

        {question.type === 'multiple_open' && (
          <textarea
            placeholder="Please enter your response..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-gray-50"
            rows={4}
            disabled={true}
          />
        )}

        {question.type === 'open_ended' && (
          <textarea
            placeholder="Please provide your detailed response..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-gray-50"
            rows={5}
            disabled={true}
          />
        )}

        {/* Default fallback for unknown question types */}
        {!['multiple_choice', 'scale', 'ranking', 'text', 'instruction', 'single_choice', 'matrix', 'numeric', 'date', 'boolean', 'open_text', 'multiple_select', 'matrix_likert', 'constant_sum', 'numeric_grid', 'numeric_open', 'likert', 'open_end', 'display_only', 'single_open', 'multiple_open', 'open_ended', 'gabor_granger'].includes(question.type) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-yellow-800">Unknown Question Type</span>
            </div>
            <div className="mt-2 text-sm text-yellow-700">
              Question type "{question.type}" is not yet supported in the preview.
            </div>
            <div className="mt-2 text-xs text-yellow-600">
              This question will still be included in the generated survey.
            </div>
          </div>
        )}
      </div>

      
      {/* Question Controls (when expanded and in edit mode) */}
      {isSelected && isEditingSurvey && (
        <div className="mt-4 flex space-x-2">
          {isEditing ? (
            <>
              <button 
                onClick={handleSaveEdit}
                className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              >
                Save
              </button>
              <button 
                onClick={handleCancelEdit}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button 
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Edit
              </button>
              <button 
                onClick={() => onMove(question.id, 'up')}
                disabled={!canMoveUp}
                className="p-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 transition-colors"
                title="Move up"
              >
                <ChevronUpIcon className="w-4 h-4" />
              </button>
              <button 
                onClick={() => onMove(question.id, 'down')}
                disabled={!canMoveDown}
                className="p-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 transition-colors"
                title="Move down"
              >
                <ChevronDownIcon className="w-4 h-4" />
              </button>
              <button 
                onClick={onDelete}
                className="p-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                title="Delete question"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      )}

      {/* Annotation Panel - Show directly when in annotation mode and question is selected */}
      {isSelected && isAnnotationMode && (
        <QuestionAnnotationPanel
          question={question}
          annotation={annotation}
          onSave={handleAnnotationSave}
          onCancel={handleAnnotationCancel}
        />
      )}
    </div>
  );
};

const SectionCard: React.FC<{
  section: SurveySection;
  isEditingSurvey: boolean;
  isAnnotationMode: boolean;
  onQuestionUpdate: (updatedQuestion: Question) => void;
  onQuestionDelete: (questionId: string) => void;
  onQuestionMove: (questionId: string, direction: 'up' | 'down') => void;
  onAnnotateSection?: (annotation: SectionAnnotation) => void;
  sectionAnnotation?: SectionAnnotation;
}> = ({
  section,
  isEditingSurvey,
  isAnnotationMode,
  onQuestionUpdate,
  onQuestionDelete,
  onQuestionMove,
  onAnnotateSection,
  sectionAnnotation
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAnnotationSave = (newAnnotation: SectionAnnotation) => {
    if (onAnnotateSection) {
      onAnnotateSection(newAnnotation);
    }
    // Close the annotation panel after saving
    setIsExpanded(false);
  };

  const handleAnnotationCancel = () => {
    // Close the annotation panel when canceling
    setIsExpanded(false);
  };


  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Section Header */}
      <div
        className="bg-gradient-to-r from-yellow-50 to-amber-50 px-6 py-4 border-b border-gray-200 cursor-pointer hover:from-yellow-100 hover:to-amber-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 bg-amber-100 text-amber-600 rounded-full font-semibold text-sm">
              {section.id}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                {sectionAnnotation && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <TagIcon className="w-3 h-3 mr-1" />
                    Annotated
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600">{section.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-500">
              {section.questions.length} question{section.questions.length !== 1 ? 's' : ''}
            </span>
            {isExpanded ? (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Section Questions */}
      {isExpanded && (
        <div className="p-6 space-y-4">
          {/* Introduction Text Block */}
          {section.introText && (
            <SurveyTextBlock
              textContent={section.introText}
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
                  />
                ))}
            </div>
          )}

          {/* Questions */}
          {section.questions.map((question, index) => (
            <QuestionCard
              key={question.id}
              question={question}
              index={index}
              onUpdate={onQuestionUpdate}
              onDelete={() => onQuestionDelete(question.id)}
              onMove={onQuestionMove}
              canMoveUp={index > 0}
              canMoveDown={index < section.questions.length - 1}
              isEditingSurvey={isEditingSurvey}
              isAnnotationMode={isAnnotationMode}
            />
          ))}
          {section.questions.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No questions in this section yet.</p>
            </div>
          )}

          {/* Closing Text Block */}
          {section.closingText && (
            <SurveyTextBlock
              textContent={section.closingText}
              className="mt-6"
            />
          )}

          {/* Section Annotation Panel - Show when expanded and in annotation mode */}
          {isAnnotationMode && (
            <SectionAnnotationPanel
              section={section}
              annotation={sectionAnnotation}
              onSave={handleAnnotationSave}
              onCancel={handleAnnotationCancel}
            />
          )}
        </div>
      )}
    </div>
  );
};

interface SurveyPreviewProps {
  survey?: Survey;
  isEditable?: boolean;
  onSurveyChange?: (survey: Survey) => void;
}

export const SurveyPreview: React.FC<SurveyPreviewProps> = ({ 
  survey: propSurvey, 
  isEditable = false, 
  onSurveyChange 
}) => {
  const { currentSurvey, setSurvey, rfqInput, createGoldenExample, isAnnotationMode, setAnnotationMode, currentAnnotations, setCurrentAnnotations, loadAnnotations, saveAnnotations } = useAppStore();
  const survey = propSurvey || currentSurvey;
  const [editedSurvey, setEditedSurvey] = useState<Survey | null>(null);
  const [isEditingSurvey, setIsEditingSurvey] = useState(isEditable);
  const [showGoldenModal, setShowGoldenModal] = useState(false);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [goldenFormData, setGoldenFormData] = useState({
    title: '',
    industry_category: '',
    research_goal: '',
    methodology_tags: [] as string[],
    quality_score: 0.9
  });
  const [showSurveyLevelAnnotation, setShowSurveyLevelAnnotation] = useState(false);

  const handleSurveyLevelAnnotation = async (annotation: SurveyLevelAnnotation) => {
    if (!survey?.survey_id) {
      console.error('No survey ID available for annotation');
      return;
    }

    try {
      // Update the current annotations with the survey-level annotation
      const updatedAnnotations: SurveyAnnotations = {
        surveyId: survey.survey_id,
        questionAnnotations: currentAnnotations?.questionAnnotations || [],
        sectionAnnotations: currentAnnotations?.sectionAnnotations || [],
        overallComment: currentAnnotations?.overallComment,
        annotatorId: currentAnnotations?.annotatorId,
        createdAt: currentAnnotations?.createdAt,
        updatedAt: currentAnnotations?.updatedAt,
        detected_labels: currentAnnotations?.detected_labels,
        compliance_report: currentAnnotations?.compliance_report,
        advanced_metadata: currentAnnotations?.advanced_metadata,
        surveyLevelAnnotation: annotation
      };
      
      await saveAnnotations(updatedAnnotations);
      setShowSurveyLevelAnnotation(false);
      console.log('Survey-level annotation saved successfully');
    } catch (error) {
      console.error('Error saving survey-level annotation:', error);
      alert('Failed to save survey-level annotation');
    }
  };



  // Close export dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showExportDropdown) {
        const target = event.target as Element;
        if (!target.closest('.export-dropdown')) {
          setShowExportDropdown(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportDropdown]);

  // Comprehensive debug logging
  React.useEffect(() => {
    console.log('🔍 [SurveyPreview] ===== COMPONENT STATE UPDATE =====');
    console.log('🔍 [SurveyPreview] currentSurvey from store:', currentSurvey);
    console.log('🔍 [SurveyPreview] propSurvey from props:', propSurvey);
    console.log('🔍 [SurveyPreview] survey (propSurvey || currentSurvey):', survey);
    console.log('🔍 [SurveyPreview] isEditingSurvey:', isEditingSurvey);
    console.log('🔍 [SurveyPreview] editedSurvey:', editedSurvey);
    
    if (survey) {
      console.log('📊 [SurveyPreview] Survey structure analysis:');
      console.log('  - survey_id:', survey.survey_id);
      console.log('  - title:', survey.title);
      console.log('  - questions type:', typeof survey.questions);
      console.log('  - questions length:', survey.questions?.length);
      console.log('  - methodologies:', survey.methodologies);
      console.log('  - confidence_score:', survey.confidence_score);
      console.log('  - Has final_output:', !!survey.final_output);
      console.log('  - Has raw_output:', !!survey.raw_output);
      
      // Check if this looks like a valid survey
      const isValidSurvey = survey.title && survey.questions && Array.isArray(survey.questions);
      console.log('✅ [SurveyPreview] Is valid survey structure:', isValidSurvey);
    } else {
      console.log('❌ [SurveyPreview] No survey data available');
    }
    console.log('🔍 [SurveyPreview] ===== END STATE UPDATE =====');
  }, [currentSurvey, propSurvey, survey, isEditingSurvey, editedSurvey]);

  // Initialize edited survey when survey changes
  React.useEffect(() => {
    if (survey && !isEditingSurvey) {
      setEditedSurvey({ ...survey });
    }
  }, [survey, isEditingSurvey]);

  // Prepopulate golden form data when modal opens
  React.useEffect(() => {
    if (showGoldenModal && survey && rfqInput) {
      setGoldenFormData({
        title: survey.title || rfqInput.title || '',
        industry_category: rfqInput.product_category || '',
        research_goal: rfqInput.research_goal || '',
        methodology_tags: survey.methodologies || [],
        quality_score: survey.confidence_score || 0.9
      });
    }
  }, [showGoldenModal, survey, rfqInput]);

  const surveyToDisplay = isEditingSurvey ? editedSurvey : survey;

  const handleStartEditing = () => {
    setEditedSurvey({ ...survey! });
    setIsEditingSurvey(true);
  };

  const handleSaveEdits = () => {
    if (editedSurvey) {
      if (onSurveyChange) {
        onSurveyChange(editedSurvey);
      } else {
        setSurvey(editedSurvey);
      }
      setIsEditingSurvey(false);
    }
  };

  const handleCancelEdits = () => {
    setEditedSurvey({ ...survey! });
    setIsEditingSurvey(false);
  };

  const handleQuestionUpdate = (updatedQuestion: Question) => {
    if (!editedSurvey) return;
    
    if (hasSections(editedSurvey)) {
      // Update question in sections format
      const updatedSections = editedSurvey.sections?.map(section => ({
        ...section,
        questions: section.questions.map(q =>
          q.id === updatedQuestion.id ? updatedQuestion : q
        )
      }));
      setEditedSurvey({ ...editedSurvey, sections: updatedSections });
    } else if (editedSurvey.questions) {
      // Update question in legacy format
      const updatedQuestions = editedSurvey.questions.map(q =>
        q.id === updatedQuestion.id ? updatedQuestion : q
      );
      setEditedSurvey({ ...editedSurvey, questions: updatedQuestions });
    }
  };

  const handleQuestionDelete = (questionId: string) => {
    if (!editedSurvey) return;
    
    if (hasSections(editedSurvey)) {
      // Delete question from sections format
      const updatedSections = editedSurvey.sections?.map(section => ({
        ...section,
        questions: section.questions.filter(q => q.id !== questionId)
      }));
      setEditedSurvey({ ...editedSurvey, sections: updatedSections });
    } else if (editedSurvey.questions) {
      // Delete question from legacy format
      const updatedQuestions = editedSurvey.questions.filter(q => q.id !== questionId);
      setEditedSurvey({ ...editedSurvey, questions: updatedQuestions });
    }
  };


  const handleMoveQuestion = (questionId: string, direction: 'up' | 'down') => {
    if (!editedSurvey) return;
    
    if (hasSections(editedSurvey)) {
      // Move question within its section
      const updatedSections = editedSurvey.sections?.map(section => {
        const questions = [...section.questions];
        const currentIndex = questions.findIndex(q => q.id === questionId);
        
        if (currentIndex === -1) return section; // Question not in this section
        
        let newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex < 0 || newIndex >= questions.length) return section; // Can't move
        
        // Swap questions within the section
        [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
        
        return { ...section, questions };
      });
      setEditedSurvey({ ...editedSurvey, sections: updatedSections });
    } else if (editedSurvey.questions) {
      // Move question in legacy format
      const questions = [...editedSurvey.questions];
      const currentIndex = questions.findIndex(q => q.id === questionId);
      
      if (currentIndex === -1) return;
      
      let newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
      if (newIndex < 0 || newIndex >= questions.length) return;
      
      // Swap questions
      [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
      setEditedSurvey({ ...editedSurvey, questions });
    }
  };

  // Annotation handlers
  const handleQuestionAnnotation = async (annotation: QuestionAnnotation) => {
    let updatedAnnotations: SurveyAnnotations;
    
    if (!currentAnnotations) {
      updatedAnnotations = {
        surveyId: survey?.survey_id || '',
        questionAnnotations: [annotation],
        sectionAnnotations: [],
        annotatorId: 'current-user', // TODO: Get from auth
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } else {
      updatedAnnotations = {
        ...currentAnnotations,
        questionAnnotations: [
          ...(currentAnnotations.questionAnnotations || []).filter(a => a.questionId !== annotation.questionId),
          annotation
        ],
        updatedAt: new Date().toISOString()
      };
    }
    
    setCurrentAnnotations(updatedAnnotations);
    
    // Auto-save annotations
    if (survey?.survey_id) {
      try {
        await saveAnnotations(updatedAnnotations);
        console.log('Question annotation auto-saved');
      } catch (error) {
        console.error('Failed to auto-save question annotation:', error);
      }
    }
  };

  const handleSectionAnnotation = async (annotation: SectionAnnotation) => {
    let updatedAnnotations: SurveyAnnotations;
    
    if (!currentAnnotations) {
      updatedAnnotations = {
        surveyId: survey?.survey_id || '',
        questionAnnotations: [],
        sectionAnnotations: [annotation],
        annotatorId: 'current-user', // TODO: Get from auth
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } else {
      updatedAnnotations = {
        ...currentAnnotations,
        sectionAnnotations: [
          ...(currentAnnotations.sectionAnnotations || []).filter(a => a.sectionId !== annotation.sectionId),
          annotation
        ],
        updatedAt: new Date().toISOString()
      };
    }
    
    setCurrentAnnotations(updatedAnnotations);
    
    // Auto-save annotations
    if (survey?.survey_id) {
      try {
        await saveAnnotations(updatedAnnotations);
        console.log('Section annotation auto-saved');
      } catch (error) {
        console.error('Failed to auto-save section annotation:', error);
      }
    }
  };

  const handleExitAnnotationMode = async () => {
    // Save annotations before exiting if there are any
    if (currentAnnotations && survey?.survey_id) {
      try {
        await saveAnnotations(currentAnnotations);
        console.log('Annotations saved successfully before exiting annotation mode');
      } catch (error) {
        console.error('Failed to save annotations before exiting:', error);
        // Still exit annotation mode even if save fails
      }
    }
    setAnnotationMode(false);
  };

  const handleExportSurvey = async (format: 'json' | 'pdf' | 'docx') => {
    if (!surveyToDisplay) return;

    switch (format) {
      case 'json':
        // Download as JSON file
        const surveyData = JSON.stringify(surveyToDisplay, null, 2);
        const blob = new Blob([surveyData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${surveyToDisplay.title || 'survey'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        break;

      case 'pdf':
        // Generate PDF from survey data
        const pdfContent = generatePDFContent(surveyToDisplay);
        const pdfBlob = new Blob([pdfContent], { type: 'application/pdf' });
        const pdfUrl = URL.createObjectURL(pdfBlob);
        const pdfLink = document.createElement('a');
        pdfLink.href = pdfUrl;
        pdfLink.download = `${surveyToDisplay.title || 'survey'}.pdf`;
        document.body.appendChild(pdfLink);
        pdfLink.click();
        document.body.removeChild(pdfLink);
        URL.revokeObjectURL(pdfUrl);
        break;

      case 'docx':
        try {
          // Export survey to DOCX using backend API
          const response = await fetch('/api/v1/export/survey', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              survey_data: surveyToDisplay,
              format: 'docx',
              filename: `${surveyToDisplay.title || 'survey'}.docx`
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Export failed');
          }

          // Download the file
          const docxBlob = await response.blob();
          const docxUrl = URL.createObjectURL(docxBlob);
          const docxLink = document.createElement('a');
          docxLink.href = docxUrl;
          docxLink.download = `${surveyToDisplay.title || 'survey'}.docx`;
          document.body.appendChild(docxLink);
          docxLink.click();
          document.body.removeChild(docxLink);
          URL.revokeObjectURL(docxUrl);
         } catch (error) {
           console.error('Error exporting to DOCX:', error);
           const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
           alert(`Failed to export DOCX: ${errorMessage}`);
         }
        break;
    }
  };

  const generatePDFContent = (survey: Survey) => {
    // Simple PDF generation - in a real app, you'd use a proper PDF library
    const content = `
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 750 Td
(${survey.title || 'Survey'}) Tj
0 -20 Td
(${survey.description || 'Survey Description'}) Tj
0 -40 Td
(Generated on: ${new Date().toLocaleDateString()}) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000525 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
625
%%EOF
    `;
    return content;
  };

  const handleSaveAsGoldenExample = async () => {
    if (!surveyToDisplay || !rfqInput.description) return;

    try {
      await createGoldenExample({
        title: goldenFormData.title,
        rfq_text: rfqInput.description,
        survey_json: surveyToDisplay,
        methodology_tags: goldenFormData.methodology_tags,
        industry_category: goldenFormData.industry_category,
        research_goal: goldenFormData.research_goal,
        quality_score: goldenFormData.quality_score
      });
      setShowGoldenModal(false);
      alert('Successfully saved as golden example!');
    } catch (error) {
      alert('Failed to save as golden example. Please try again.');
    }
  };


  // Validate survey data before rendering
  const isValidSurvey = survey && 
                       typeof survey === 'object' && 
                       survey.title && 
                       (survey.questions || survey.sections) && 
                       (Array.isArray(survey.questions) || Array.isArray(survey.sections));

  if (!survey) {
    console.log('❌ [SurveyPreview] No survey available');
    return (
      <div className="w-full p-6 text-center">
        <p className="text-gray-500">No survey to preview yet.</p>
        <p className="text-sm text-gray-400 mt-2">Debug: survey is {typeof survey}</p>
      </div>
    );
  }

  if (!isValidSurvey) {
    console.log('❌ [SurveyPreview] Survey data is invalid or malformed');
    console.log('❌ [SurveyPreview] Survey structure:', {
      hasTitle: !!survey.title,
      hasQuestions: !!survey.questions,
      hasSections: !!survey.sections,
      questionsIsArray: Array.isArray(survey.questions),
      sectionsIsArray: Array.isArray(survey.sections),
      questionsLength: survey.questions?.length,
      sectionsLength: survey.sections?.length,
      surveyKeys: Object.keys(survey || {})
    });
    
    // Check if this is an error response from the API
    const isErrorResponse = survey && (
      survey.title === "Document Parse Error" || 
      survey.description?.includes("Failed to parse document") ||
      survey.raw_output?.error ||
      survey.final_output?.title === "Document Parse Error"
    );
    
    // Don't show error if we're still loading or if it's just a different format
    if (isErrorResponse) {
      return (
        <div className="w-full p-6 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-red-800 mb-2">Document Parsing Failed</h3>
            <p className="text-red-600">Unable to process the uploaded document. Please try again.</p>
          </div>
        </div>
      );
    }
    
    // If it's not an error but still invalid, show a loading state instead of error
    return (
      <div className="w-full p-6 text-center">
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <p className="text-gray-500">Loading survey preview...</p>
        </div>
      </div>
    );
  }

  // If in annotation mode, show the new annotation interface
  if (isAnnotationMode) {
    return (
      <AnnotationMode
        survey={survey}
        currentAnnotations={currentAnnotations}
        onQuestionAnnotation={handleQuestionAnnotation}
        onSectionAnnotation={handleSectionAnnotation}
        onSurveyLevelAnnotation={handleSurveyLevelAnnotation}
        onExitAnnotationMode={handleExitAnnotationMode}
      />
    );
  }

  return (
    <div className="w-full p-6">
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Survey Preview */}
        <div className="lg:col-span-2">
          {/* Survey Header */}
          <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg">
            {/* Annotation Mode Instructions */}
            {isAnnotationMode && (
              <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                      <TagIcon className="w-5 h-5 text-yellow-600" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-yellow-800 mb-1">Annotation Mode Active</h3>
                    <p className="text-sm text-yellow-700">
                      Click on any question or section below to add quality annotations. 
                      Your annotations are automatically saved and will help improve future survey generation.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Survey Title and Description */}
            <div className="mb-6">
              {isEditingSurvey ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Survey Title</label>
                    <input
                      type="text"
                      value={editedSurvey?.title || ''}
                      onChange={(e) => setEditedSurvey(prev => prev ? { ...prev, title: e.target.value } : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-2xl font-bold"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Survey Description</label>
                    <textarea
                      value={editedSurvey?.description || ''}
                      onChange={(e) => setEditedSurvey(prev => prev ? { ...prev, description: e.target.value } : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      rows={3}
                    />
                  </div>
                </div>
              ) : (
                <>
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">
                    {surveyToDisplay?.title}
                  </h1>
                  <p className="text-gray-600 mb-4">
                    {surveyToDisplay?.description}
                  </p>
                </>
              )}
              <div className="flex items-center space-x-4 text-sm text-gray-500 mt-4">
                <span>⏱️ ~{surveyToDisplay?.estimated_time} minutes</span>
                <span>📊 {extractAllQuestions(surveyToDisplay || {} as Survey).length} questions</span>
                {hasSections(surveyToDisplay || {} as Survey) && (
                  <span>📋 {surveyToDisplay?.sections?.length} sections</span>
                )}
              </div>
            </div>
          </div>

          {/* Questions or Sections */}
          <div className="space-y-4">
            {hasSections(surveyToDisplay || {} as Survey) ? (
              // New sections format
              surveyToDisplay?.sections?.map((section) => (
                <SectionCard
                  key={section.id}
                  section={section}
                  isEditingSurvey={isEditingSurvey}
                  isAnnotationMode={isAnnotationMode}
                  onQuestionUpdate={handleQuestionUpdate}
                  onQuestionDelete={handleQuestionDelete}
                  onQuestionMove={handleMoveQuestion}
                  onAnnotateSection={handleSectionAnnotation}
                  sectionAnnotation={currentAnnotations?.sectionAnnotations?.find(a => a.sectionId === String(section.id))}
                />
              ))
            ) : (
              // Legacy questions format
              surveyToDisplay?.questions && surveyToDisplay.questions.length > 0 ? (
                surveyToDisplay.questions?.map((question, index) => (
                  <QuestionCard
                    key={question.id}
                    question={question}
                    index={index}
                    onUpdate={handleQuestionUpdate}
                    onDelete={() => handleQuestionDelete(question.id)}
                    onMove={handleMoveQuestion}
                    canMoveUp={index > 0}
                    canMoveDown={index < (surveyToDisplay?.questions?.length || 0) - 1}
                    isEditingSurvey={isEditingSurvey}
                    isAnnotationMode={isAnnotationMode}
                    onAnnotate={handleQuestionAnnotation}
                    annotation={currentAnnotations?.questionAnnotations?.find(a => a.questionId === question.id)}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No questions available for this survey.</p>
                </div>
              )
            )}
          </div>

        </div>

        {/* Right Sidebar - Shows pillar scores in normal mode, annotation progress in annotation mode */}
        {!isAnnotationMode ? (
          <div className="lg:col-span-1 space-y-6">

          {/* Action Buttons */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              {/* Annotation Button */}
              <button 
                onClick={async () => {
                  if (!isAnnotationMode && survey?.survey_id) {
                    // Entering annotation mode - ensure annotations are loaded
                    if (!currentAnnotations || currentAnnotations.surveyId !== survey.survey_id) {
                      console.log('🔍 [SurveyPreview] Loading annotations before entering annotation mode');
                      await loadAnnotations(survey.survey_id);
                    }
                    setAnnotationMode(true);
                  } else {
                    // Exiting annotation mode - save annotations first
                    await handleExitAnnotationMode();
                  }
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                  isAnnotationMode 
                    ? 'bg-yellow-600 text-white hover:bg-yellow-700 shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                }`}
              >
                <TagIcon className="w-5 h-5" />
                <span className="text-sm font-semibold">
                  {isAnnotationMode ? 'Exit Annotation' : 'Annotate Survey'}
                </span>
              </button>
              
              {isAnnotationMode && (
                <div className="flex items-center gap-2 text-sm text-yellow-600 font-medium px-3 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  Auto-saving
                </div>
              )}

              {/* Survey Action Buttons */}
              {isEditingSurvey ? (
                <>
                  <button 
                    onClick={handleSaveEdits}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors shadow-lg"
                  >
                    <CheckIcon className="w-5 h-5" />
                    <span className="text-sm font-semibold">Save Changes</span>
                  </button>
                  <button 
                    onClick={handleCancelEdits}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                    <span className="text-sm font-semibold">Cancel</span>
                  </button>
                  
                  <button 
                    onClick={() => {
                      // Pre-populate form with survey methodologies
                      setGoldenFormData(prev => ({
                        ...prev,
                        methodology_tags: surveyToDisplay?.methodologies || [],
                        industry_category: rfqInput.product_category || '',
                        research_goal: rfqInput.research_goal || ''
                      }));
                      setShowGoldenModal(true);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 transition-colors shadow-lg"
                  >
                    <StarIcon className="w-5 h-5" />
                    <span className="text-sm font-semibold">Save as Reference Example</span>
                  </button>
                </>
              ) : (
                <>
                  <button 
                    onClick={handleStartEditing}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-lg"
                  >
                    <PencilIcon className="w-5 h-5" />
                    <span className="text-sm font-semibold">Edit Survey</span>
                  </button>
                  
                  <button 
                    onClick={() => {
                      // Pre-populate form with survey methodologies
                      setGoldenFormData(prev => ({
                        ...prev,
                        methodology_tags: surveyToDisplay?.methodologies || [],
                        industry_category: rfqInput.product_category || '',
                        research_goal: rfqInput.research_goal || ''
                      }));
                      setShowGoldenModal(true);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 transition-colors shadow-lg"
                  >
                    <StarIcon className="w-5 h-5" />
                    <span className="text-sm font-semibold">Save as Reference Example</span>
                  </button>
                </>
              )}

              
              <button 
                onClick={() => window.location.href = `/llm-audit/survey/${survey?.survey_id}`}
                className="w-full flex items-center gap-3 px-4 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors shadow-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span className="text-sm font-semibold">View System Prompt</span>
              </button>
              
              {/* Export Buttons */}
              <div className="border-t border-gray-200 pt-3">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Export</h4>
                <div className="space-y-2">
                  <button
                    onClick={() => handleExportSurvey('json')}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <div className="w-6 h-6 bg-blue-100 rounded flex items-center justify-center">
                      <span className="text-blue-600 font-bold text-xs">JSON</span>
                    </div>
                    <span>Download JSON</span>
                  </button>
                  <button
                    onClick={() => handleExportSurvey('pdf')}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <div className="w-6 h-6 bg-red-100 rounded flex items-center justify-center">
                      <span className="text-red-600 font-bold text-xs">PDF</span>
                    </div>
                    <span>Download PDF</span>
                  </button>
                  <button
                    onClick={() => handleExportSurvey('docx')}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <div className="w-6 h-6 bg-green-100 rounded flex items-center justify-center">
                      <span className="text-green-600 font-bold text-xs">DOCX</span>
                    </div>
                    <span>Download DOCX</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Evaluation LLM Output */}
          {surveyToDisplay?.pillar_scores && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                AI Evaluation Analysis
              </h3>
              
              {/* Overall Summary */}
              <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">Overall Assessment</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    surveyToDisplay.pillar_scores.overall_grade === 'A' ? 'bg-green-100 text-green-800' :
                    surveyToDisplay.pillar_scores.overall_grade === 'B' ? 'bg-blue-100 text-blue-800' :
                    surveyToDisplay.pillar_scores.overall_grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                    surveyToDisplay.pillar_scores.overall_grade === 'D' ? 'bg-orange-100 text-orange-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    Grade {surveyToDisplay.pillar_scores.overall_grade}
                  </span>
                </div>
                <p className="text-sm text-blue-800 mb-2">{surveyToDisplay.pillar_scores.summary}</p>
                <div className="flex items-center text-xs text-blue-600">
                  <span className="font-medium">Score: {Math.round(surveyToDisplay.pillar_scores.weighted_score * 100)}%</span>
                  <span className="mx-2">•</span>
                  <span>Chain-of-Thought Evaluation</span>
                </div>
              </div>

              {/* Detailed Pillar Breakdown */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Pillar Analysis</h4>
                {surveyToDisplay.pillar_scores.pillar_breakdown?.map((pillar, index) => (
                  <div key={pillar.pillar_name} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">{pillar.display_name}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                          pillar.grade === 'A' ? 'bg-green-100 text-green-800' :
                          pillar.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                          pillar.grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                          pillar.grade === 'D' ? 'bg-orange-100 text-orange-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {pillar.grade}
                        </span>
                        <span className="text-xs text-gray-500">{Math.round(pillar.score * 100)}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className={`h-2 rounded-full ${
                          pillar.score >= 0.8 ? 'bg-green-500' :
                          pillar.score >= 0.6 ? 'bg-blue-500' :
                          pillar.score >= 0.4 ? 'bg-yellow-500' :
                          pillar.score >= 0.2 ? 'bg-orange-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${pillar.score * 100}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{pillar.criteria_met}/{pillar.total_criteria} criteria met</span>
                      <span>Weight: {Math.round(pillar.weight * 100)}%</span>
                    </div>
                  </div>
                )) || []}
              </div>

              {/* Recommendations */}
              {surveyToDisplay.pillar_scores.recommendations && surveyToDisplay.pillar_scores.recommendations.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">AI Recommendations</h4>
                  <div className="space-y-2">
                    {surveyToDisplay.pillar_scores.recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <p className="text-xs text-gray-600">{recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          </div>
        ) : (
          <div className="lg:col-span-1 space-y-6">
            {/* Annotation Summary */}
            {currentAnnotations && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                  <TagIcon className="w-4 h-4 mr-2 text-yellow-600" />
                  Annotation Progress
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Questions Annotated:</span>
                    <span className="font-medium">
                      {currentAnnotations?.questionAnnotations?.length || 0} / {extractAllQuestions(surveyToDisplay || {} as Survey).length}
                    </span>
                  </div>
                  {hasSections(surveyToDisplay || {} as Survey) && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sections Annotated:</span>
                      <span className="font-medium">
                        {currentAnnotations?.sectionAnnotations?.length || 0} / {surveyToDisplay?.sections?.length || 0}
                      </span>
                    </div>
                  )}
                  <div className="pt-2 border-t border-yellow-200">
                    <div className="text-xs text-gray-500">
                      Last updated: {new Date(currentAnnotations?.updatedAt || currentAnnotations?.createdAt || '').toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Save as Golden Example Modal */}
      {showGoldenModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">Save Survey as Reference Example</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={goldenFormData.title}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="Enter a title for this golden example"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry Category</label>
                <select
                  value={goldenFormData.industry_category}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, industry_category: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select Industry</option>
                  <option value="Consumer Electronics">Consumer Electronics</option>
                  <option value="B2B Technology">B2B Technology</option>
                  <option value="Automotive">Automotive</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Financial Services">Financial Services</option>
                  <option value="Retail">Retail</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Research Goal</label>
                <select
                  value={goldenFormData.research_goal}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, research_goal: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select Research Goal</option>
                  <option value="pricing">Pricing Research</option>
                  <option value="feature_prioritization">Feature Prioritization</option>
                  <option value="brand_perception">Brand Perception</option>
                  <option value="purchase_journey">Purchase Journey</option>
                  <option value="market_segmentation">Market Segmentation</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Methodology Tags</label>
                <input
                  type="text"
                  value={goldenFormData.methodology_tags.join(', ')}
                  onChange={(e) => setGoldenFormData(prev => ({ 
                    ...prev, 
                    methodology_tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) 
                  }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="van_westendorp, conjoint, maxdiff, etc."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quality Score</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={goldenFormData.quality_score}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, quality_score: parseFloat(e.target.value) || 0.9 }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div className="bg-gray-50 p-3 rounded-md">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Preview</h4>
                
                {/* RFQ Preview - First 5 lines */}
                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">RFQ (first 5 lines):</p>
                  <div className="text-xs text-gray-600 mt-1">
                    {rfqInput.description.split('\n').slice(0, 5).map((line, idx) => (
                      <p key={idx} className="truncate">{line}</p>
                    ))}
                    {rfqInput.description.split('\n').length > 5 && (
                      <p className="text-gray-500">... ({rfqInput.description.split('\n').length - 5} more lines)</p>
                    )}
                  </div>
                </div>

                <p className="text-sm text-gray-600 mt-1"><strong>Survey Title:</strong> {surveyToDisplay?.title}</p>
                <p className="text-sm text-gray-600 mt-1"><strong>Total Questions:</strong> {extractAllQuestions(surveyToDisplay || {} as Survey).length}</p>
                
                {/* Sample Questions - First 5 questions */}
                {(() => {
                  const allQuestions = extractAllQuestions(surveyToDisplay || {} as Survey);
                  return allQuestions.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-gray-700">Sample Questions:</p>
                      <ul className="text-xs text-gray-600 mt-1 space-y-1">
                        {allQuestions.slice(0, 5).map((q, idx) => (
                          <li key={idx} className="truncate">• {q.text}</li>
                        ))}
                        {allQuestions.length > 5 && (
                          <li className="text-gray-500">... and {allQuestions.length - 5} more questions</li>
                        )}
                      </ul>
                    </div>
                  );
                })()}
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowGoldenModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAsGoldenExample}
                disabled={!goldenFormData.industry_category || !goldenFormData.research_goal}
                className="px-4 py-2 bg-gradient-to-r from-yellow-600 to-amber-600 text-white rounded-md text-sm hover:from-yellow-700 hover:to-amber-700 disabled:opacity-50 transition-all duration-200"
              >
                Save as Reference Example
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Survey-Level Annotation Panel */}
      {showSurveyLevelAnnotation && survey?.survey_id && (
        <SurveyLevelAnnotationPanel
          surveyId={survey.survey_id}
          annotation={currentAnnotations?.surveyLevelAnnotation}
          onSave={handleSurveyLevelAnnotation}
          onCancel={() => setShowSurveyLevelAnnotation(false)}
        />
      )}
    </div>
  );
};