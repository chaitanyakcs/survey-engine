import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, Survey, SurveySection, QuestionAnnotation, SectionAnnotation, SurveyAnnotations, SurveyLevelAnnotation } from '../types';
import AnnotationMode from './AnnotationMode';
import AnnotationSidePane from './AnnotationSidePane';
import SurveyTextBlock from './SurveyTextBlock';
import MatrixLikert from './MatrixLikert';
import ConstantSum from './ConstantSum';
import GaborGranger from './GaborGranger';
import NumericGrid from './NumericGrid';
import NumericOpen from './NumericOpen';
import { QuestionEditor } from './question/QuestionEditor';
import { useSurveyEdit } from '../hooks/useSurveyEdit';
import { PencilIcon, ChevronDownIcon, ChevronRightIcon, TagIcon, TrashIcon, ChevronUpIcon, PlusIcon } from '@heroicons/react/24/outline';


// Helper function to check if survey uses sections format
const hasSections = (survey: Survey): boolean => {
  return !!survey.sections && survey.sections.length > 0;
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
  onOpenAnnotation?: (question: Question) => void;
  annotation?: QuestionAnnotation;
}> = ({ question, index, onUpdate, onDelete, onMove, canMoveUp, canMoveDown, isEditingSurvey, isAnnotationMode, onOpenAnnotation, annotation }) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  const isSelected = selectedQuestionId === question.id;
  
  const [isEditing, setIsEditing] = useState(false);
  const [editedQuestion, setEditedQuestion] = useState<Question>(question);

  // Auto-enable edit mode when isEditingSurvey is true
  useEffect(() => {
    if (isEditingSurvey && !isEditing) {
      setIsEditing(true);
    } else if (!isEditingSurvey && isEditing) {
      setIsEditing(false);
    }
  }, [isEditingSurvey, isEditing]);

  const handleSaveEdit = async (updatedQuestion: Question) => {
    // In survey edit mode, just update local state - no immediate API call
    await onUpdate(updatedQuestion);
    // Only exit edit mode if not in survey edit mode
    if (!isEditingSurvey) {
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedQuestion(question);
    // Only exit edit mode if not in survey edit mode
    if (!isEditingSurvey) {
      setIsEditing(false);
    }
  };


  return (
    <div 
      className={`
        border rounded-lg p-4 cursor-pointer transition-all duration-200
        ${isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'}
      `}
      onClick={() => {
        if (isAnnotationMode && onOpenAnnotation) {
          // Open annotation pane
          onOpenAnnotation(question);
        } else {
          // Normal selection behavior
          setSelectedQuestion(isSelected ? undefined : question.id);
        }
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
          {/* Display auto-detected labels */}
          {question.labels && question.labels.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {question.labels.map((label, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {label}
                </span>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditingSurvey && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="p-1 text-gray-400 hover:text-red-600"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
              <div className="flex flex-col space-y-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMove(question.id, 'up');
                  }}
                  disabled={!canMoveUp}
                  className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                >
                  <ChevronUpIcon className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMove(question.id, 'down');
                  }}
                  disabled={!canMoveDown}
                  className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                >
                  <ChevronDownIcon className="h-3 w-3" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Question Content */}
      <div className="mb-4">
        {isEditing ? (
          <QuestionEditor
            question={editedQuestion}
            onSave={handleSaveEdit}
            onCancel={handleCancelEdit}
            isLoading={false}
            hideSaveButton={isEditingSurvey}
          />
        ) : (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {question.text}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Type: {question.type}{question.category && ` • Category: ${question.category}`}
            </p>
            
            {/* AI Annotation Information */}
            {annotation && annotation.aiGenerated && (
              <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      🤖 AI Annotated
                    </span>
                    {annotation.aiConfidence && (
                      <span className="text-xs text-blue-600">
                        Confidence: {Math.round(annotation.aiConfidence * 100)}%
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <span>Quality: {annotation.quality}/5</span>
                    <span>•</span>
                    <span>Relevant: {annotation.relevant}/5</span>
                  </div>
                </div>
                {annotation.comment && (
                  <p className="text-sm text-gray-700 italic">
                    "{annotation.comment}"
                  </p>
                )}
                <div className="mt-2 grid grid-cols-5 gap-2 text-xs">
                  <div className="text-center">
                    <div className="font-medium text-gray-600">Methodology</div>
                    <div className="text-blue-600">{annotation.pillars.methodologicalRigor}/5</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-600">Content</div>
                    <div className="text-blue-600">{annotation.pillars.contentValidity}/5</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-600">Experience</div>
                    <div className="text-blue-600">{annotation.pillars.respondentExperience}/5</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-600">Analytics</div>
                    <div className="text-blue-600">{annotation.pillars.analyticalValue}/5</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-600">Business</div>
                    <div className="text-blue-600">{annotation.pillars.businessImpact}/5</div>
                  </div>
                </div>
                {/* Debug logging for q1 */}
                {question.id === 'q1' && (
                  <div className="text-xs text-red-600 mt-1">
                    DEBUG: Pillars = {JSON.stringify(annotation.pillars)}
                  </div>
                )}
              </div>
            )}
            
            {/* Specialized Question Type Components */}
            {question.type === 'matrix_likert' && (
              <MatrixLikert 
                question={question} 
                isPreview={true}
              />
            )}
            
            {question.type === 'constant_sum' && (
              <ConstantSum 
                question={question} 
                isPreview={true}
              />
            )}
            
            {question.type === 'gabor_granger' && (
              <GaborGranger 
                question={question} 
                isPreview={true}
              />
            )}
            
            {question.type === 'numeric_grid' && (
              <NumericGrid 
                question={question} 
                isPreview={true}
              />
            )}
            
            {question.type === 'numeric_open' && (
              <NumericOpen 
                question={question} 
                isPreview={true}
              />
            )}
            

            {/* Multiple Select Questions */}
            {question.type === 'multiple_select' && question.options && question.options.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Options:</h4>
                {question.options.map((option, idx) => (
                  <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <input
                      type="checkbox"
                      disabled
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-3"
                    />
                    <span className="text-sm text-gray-700">{option}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Standard Question Types */}
            {!['matrix_likert', 'constant_sum', 'gabor_granger', 'numeric_grid', 'numeric_open', 'likert', 'multiple_select'].includes(question.type) && (
              <>
                {/* Question Options */}
                {question.options && question.options.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">Options:</h4>
                    {question.options.map((option, idx) => (
                      <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-600 rounded-full text-sm font-medium mr-3">
                          {idx + 1}
                        </div>
                        <span className="text-sm text-gray-700">{option}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Special Question Types */}
                {question.type === 'instruction' && (
                  <div className="bg-secondary-50 border-l-4 border-secondary-400 p-4 rounded-r-lg">
                    <h4 className="text-sm font-medium text-secondary-800 mb-2">Instruction</h4>
                    <p className="text-sm text-secondary-700">{question.text}</p>
                  </div>
                )}
              </>
            )}

            {/* Unknown Question Type */}
            {!['multiple_choice', 'scale', 'ranking', 'text', 'instruction', 'single_choice', 'matrix', 'numeric', 'date', 'boolean', 'open_text', 'multiple_select', 'matrix_likert', 'constant_sum', 'numeric_grid', 'numeric_open', 'likert', 'open_end', 'display_only', 'single_open', 'multiple_open', 'open_ended', 'gabor_granger'].includes(question.type) && (
              <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-warning-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium text-warning-800">Unknown Question Type: {question.type}</span>
                </div>
                <p className="text-xs text-warning-700 mt-2">
                  This question type is not yet supported for preview. Please review the raw JSON.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const SectionCard: React.FC<{
  section: SurveySection;
  sectionIndex: number; // Add this to show the correct visual order
  isEditingSurvey: boolean;
  isAnnotationMode: boolean;
  onQuestionUpdate: (updatedQuestion: Question) => void;
  onQuestionDelete: (questionId: string) => void;
  onQuestionMove: (questionId: string, direction: 'up' | 'down') => void;
  onAnnotateSection?: (annotation: SectionAnnotation) => void;
  onOpenAnnotation?: (section: SurveySection) => void;
  sectionAnnotation?: SectionAnnotation;
  onSectionUpdate?: (sectionId: number, updatedSection: SurveySection) => void;
  onSectionDelete?: (sectionId: number) => void;
  onSectionMoveUp?: () => void;
  onSectionMoveDown?: () => void;
  onAddQuestionToSection?: (sectionId: number) => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  surveyId?: string;
  currentAnnotations?: SurveyAnnotations;
}> = ({
  section,
  sectionIndex,
  isEditingSurvey,
  isAnnotationMode,
  onQuestionUpdate,
  onQuestionDelete,
  onQuestionMove,
  onAnnotateSection,
  onOpenAnnotation,
  sectionAnnotation,
  onSectionUpdate,
  onSectionDelete,
  onSectionMoveUp,
  onSectionMoveDown,
  onAddQuestionToSection,
  canMoveUp = false,
  canMoveDown = false,
  surveyId,
  currentAnnotations
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedTitle, setEditedTitle] = useState(section.title);
  const [editedDescription, setEditedDescription] = useState(section.description);

  // Update local state when section prop changes
  useEffect(() => {
    setEditedTitle(section.title);
    setEditedDescription(section.description);
  }, [section.title, section.description]);

  const handleTitleSave = () => {
    if (onSectionUpdate && editedTitle.trim() !== section.title) {
      onSectionUpdate(section.id, { ...section, title: editedTitle.trim() });
    }
    setIsEditingTitle(false);
  };

  const handleDescriptionSave = () => {
    if (onSectionUpdate && editedDescription !== section.description) {
      onSectionUpdate(section.id, { ...section, description: editedDescription });
    }
    setIsEditingDescription(false);
  };

  const handleTitleCancel = () => {
    setEditedTitle(section.title);
    setIsEditingTitle(false);
  };

  const handleDescriptionCancel = () => {
    setEditedDescription(section.description);
    setIsEditingDescription(false);
  };

  // Wrapper function to convert question annotation to the correct type
  const handleQuestionAnnotation = (question: Question) => {
    // For questions within sections, we need to call the question annotation handler directly
    // This is a bit of a hack since the SectionCard's onOpenAnnotation expects SurveySection
    // but we need to handle Question clicks
    if (onOpenAnnotation) {
      // Cast to any to bypass type checking since we know this will be handled correctly
      (onOpenAnnotation as any)(question);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Section Header */}
      <div
        className="bg-gradient-to-r from-primary-50 to-primary-100 px-6 py-4 border-b border-gray-200 cursor-pointer hover:from-primary-100 hover:to-primary-200 transition-colors"
        onClick={() => {
          if (isAnnotationMode && onOpenAnnotation) {
            // Open annotation pane for section
            onOpenAnnotation(section);
          } else {
            // Normal expand/collapse behavior
            setIsExpanded(!isExpanded);
          }
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-600 rounded-full font-semibold text-sm">
              {sectionIndex + 1}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                {isEditingTitle ? (
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleTitleSave();
                        } else if (e.key === 'Escape') {
                          handleTitleCancel();
                        }
                      }}
                      className="text-lg font-semibold text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTitleSave();
                      }}
                      className="text-green-600 hover:text-green-800"
                      title="Save"
                    >
                      ✓
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTitleCancel();
                      }}
                      className="text-red-600 hover:text-red-800"
                      title="Cancel"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <h3 
                    className="text-lg font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (isEditingSurvey) {
                        setIsEditingTitle(true);
                      }
                    }}
                    title={isEditingSurvey ? "Click to edit title" : ""}
                  >
                    {section.title}
                  </h3>
                )}
                {sectionAnnotation && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <TagIcon className="w-3 h-3 mr-1" />
                    Annotated
                  </span>
                )}
              </div>
              {isEditingDescription ? (
                <div className="flex items-start space-x-2 mt-1 w-full">
                  <div className="flex-1">
                    <textarea
                      value={editedDescription}
                      onChange={(e) => setEditedDescription(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          handleDescriptionSave();
                        } else if (e.key === 'Escape') {
                          handleDescriptionCancel();
                        }
                      }}
                      className="text-sm text-gray-600 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none w-full min-w-[300px]"
                      rows={2}
                      autoFocus
                    />
                  </div>
                  <div className="flex flex-col space-y-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDescriptionSave();
                      }}
                      className="text-green-600 hover:text-green-800"
                      title="Save"
                    >
                      ✓
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDescriptionCancel();
                      }}
                      className="text-red-600 hover:text-red-800"
                      title="Cancel"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mt-1">
                  {section.description ? (
                    <p 
                      className="text-sm text-gray-600 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (isEditingSurvey) {
                          setIsEditingDescription(true);
                        }
                      }}
                      title={isEditingSurvey ? "Click to edit description" : ""}
                    >
                      {section.description}
                    </p>
                  ) : (
                    <p 
                      className="text-sm text-gray-400 italic cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (isEditingSurvey) {
                          setIsEditingDescription(true);
                        }
                      }}
                      title={isEditingSurvey ? "Click to add description" : ""}
                    >
                      Click to add description...
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isEditingSurvey && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onSectionDelete) {
                      onSectionDelete(section.id);
                    }
                  }}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Delete Section"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
                <div className="flex flex-col space-y-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onSectionMoveUp) {
                        onSectionMoveUp();
                      }
                    }}
                    disabled={!canMoveUp}
                    className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded disabled:opacity-50"
                    title="Move Section Up"
                  >
                    <ChevronUpIcon className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('🔽 Move Section Down clicked for section:', section.id, section.title);
                      if (onSectionMoveDown) {
                        console.log('📞 Calling onSectionMoveDown');
                        onSectionMoveDown();
                      } else {
                        console.log('❌ onSectionMoveDown is not defined');
                      }
                    }}
                    disabled={!canMoveDown}
                    className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded disabled:opacity-50"
                    title="Move Section Down"
                  >
                    <ChevronDownIcon className="w-3 h-3" />
                  </button>
                </div>
              </>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isExpanded ? (
                <ChevronDownIcon className="w-5 h-5" />
              ) : (
                <ChevronRightIcon className="w-5 h-5" />
              )}
            </button>
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
          {section.questions.map((question, index) => {
            // Find the annotation for this question (store now handles deduplication)
            const questionAnnotation = currentAnnotations?.questionAnnotations?.find(
              (qa: QuestionAnnotation) => qa.questionId === question.id
            );
            
            // Debug logging
            if (questionAnnotation) {
              console.log(`🔍 [SurveyPreview] Found annotation for question ${question.id}:`, {
                questionId: question.id,
                annotationId: questionAnnotation.questionId,
                aiGenerated: questionAnnotation.aiGenerated,
                quality: questionAnnotation.quality,
                pillars: questionAnnotation.pillars
              });
            }
            
            return (
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
                onOpenAnnotation={handleQuestionAnnotation}
                annotation={questionAnnotation}
              />
            );
          })}
          {section.questions.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No questions in this section yet.</p>
            </div>
          )}

          {/* Add Question Button */}
          {isEditingSurvey && (
            <div className="flex justify-center pt-4">
              <button
                onClick={() => {
                  if (onAddQuestionToSection) {
                    onAddQuestionToSection(section.id);
                  }
                }}
                className="inline-flex items-center px-3 py-2 text-green-600 hover:text-green-800 hover:bg-green-50 rounded-md border border-green-200 transition-colors text-sm"
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Add Question to Section
              </button>
            </div>
          )}

          {/* Closing Text Block */}
          {section.closingText && (
            <SurveyTextBlock
              textContent={section.closingText}
              className="mt-6"
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
  isInEditMode?: boolean;
  onSurveyChange?: (survey: Survey) => void;
  onSaveAndExit?: () => void;
  onCancel?: () => void;
  hideHeader?: boolean;
  hideRightPanel?: boolean;
}

export const SurveyPreview: React.FC<SurveyPreviewProps> = ({ 
  survey: propSurvey, 
  isEditable = false, 
  isInEditMode = false,
  onSurveyChange,
  onSaveAndExit,
  onCancel,
  hideHeader = false,
  hideRightPanel = false
}) => {
  const { currentSurvey, isAnnotationMode, setAnnotationMode, currentAnnotations, saveAnnotations, loadAnnotations } = useAppStore();
  const survey = propSurvey || currentSurvey;
  const [editedSurvey, setEditedSurvey] = useState<Survey | null>(null);
  const [isEditModeActive, setIsEditModeActive] = useState(isInEditMode);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Initialize survey edit hook
  const { updateQuestion, updateSection, createSection, deleteSection, reorderSections, reorderQuestions } = useSurveyEdit({
    surveyId: survey?.survey_id || '',
    onSuccess: (message) => {
      console.log('Success:', message);
      // You can add toast notification here
    },
    onError: (error) => {
      console.error('Error:', error);
      // You can add error toast notification here
    }
  });
  
  // Annotation fixed pane state
  const [annotationPane, setAnnotationPane] = useState({
    type: null as 'question' | 'section' | 'survey' | null,
    target: null as any
  });

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
      console.log('Survey-level annotation saved successfully');
    } catch (error) {
      console.error('Error saving survey-level annotation:', error);
      alert('Failed to save survey-level annotation');
    }
  };

  const handleExitAnnotationMode = async () => {
    try {
      // Save any pending annotations before exiting
      if (currentAnnotations && survey?.survey_id) {
        console.log('💾 Saving annotations before exiting annotation mode...');
        await saveAnnotations(currentAnnotations);
        console.log('✅ Annotations saved successfully before exit');
      }
      
      setAnnotationMode(false);
      // Clear annotation pane state when exiting annotation mode
      setAnnotationPane({
        type: null,
        target: null
      });
      console.log('Exited annotation mode');
    } catch (error) {
      console.error('Error exiting annotation mode:', error);
      // Still exit even if save fails, but show error
      alert('Failed to save annotations before exit. Please try again.');
    }
  };

  // New functionality handlers
  const handleEditSurvey = () => {
    console.log('🖊️ [SurveyPreview] handleEditSurvey called');
    console.log('🖊️ [SurveyPreview] surveyToDisplay:', surveyToDisplay);
    console.log('🖊️ [SurveyPreview] surveyToDisplay.survey_id:', surveyToDisplay?.survey_id);
    
    if (surveyToDisplay?.survey_id) {
      console.log('🖊️ [SurveyPreview] Navigate to edit route for survey:', surveyToDisplay.survey_id);
      window.location.href = `/surveys/${surveyToDisplay.survey_id}/edit`;
    } else {
      console.log('❌ [SurveyPreview] No survey_id available for editing');
    }
  };

  const handleSaveAllChanges = async () => {
    if (!editedSurvey || !survey?.survey_id) {
      console.log('❌ [Save] Cannot save - missing editedSurvey or survey_id');
      console.log('❌ [Save] editedSurvey:', !!editedSurvey);
      console.log('❌ [Save] survey_id:', survey?.survey_id);
      return;
    }
    
    setIsSaving(true);
    try {
      console.log('💾 Saving all changes...');
      
      // Store the original survey data BEFORE any updates to avoid comparison issues
      // We need to get the data from the store directly, not from the survey prop which might be updated
      const storeState = useAppStore.getState();
      const originalSurveyData = JSON.parse(JSON.stringify(storeState.currentSurvey));
      
      console.log('📊 Current editedSurvey sections:', editedSurvey.sections?.map((s: any) => ({ id: s.id, title: s.title, order: s.order })));
      console.log('📊 Original survey sections:', originalSurveyData.sections?.map((s: any) => ({ id: s.id, title: s.title, order: s.order })));
      console.log('📊 hasUnsavedChanges:', hasUnsavedChanges);
      
      // Save section reordering if sections exist
      if (editedSurvey.sections && editedSurvey.sections.length > 0) {
        const sectionOrder = editedSurvey.sections.map(s => s.id);
        console.log('📤 Sending section order to backend:', sectionOrder);
        await reorderSections(sectionOrder);
        console.log('✅ Section order saved');
      }
      
      // Save question reordering - only for legacy flat format
      // For surveys with sections, question reordering is handled by section updates
      if (editedSurvey.questions && editedSurvey.questions.length > 0 && 
          (!editedSurvey.sections || editedSurvey.sections.length === 0)) {
        // Handle legacy flat questions format
        const questionOrder = editedSurvey.questions.map(q => q.id);
        console.log('📤 Sending question order to backend (legacy format):', questionOrder);
        await reorderQuestions(questionOrder);
        console.log('✅ Question order saved (legacy format)');
      }
      
      // Save individual section updates
      if (editedSurvey.sections && editedSurvey.sections.length > 0) {
        for (const section of editedSurvey.sections) {
          const originalSection = originalSurveyData.sections?.find((s: any) => s.id === section.id);
          if (originalSection) {
            // Check for changes in section properties (excluding questions)
            const originalSectionWithoutQuestions = { ...originalSection };
            const sectionWithoutQuestions = { ...section };
            // Remove questions property for comparison
            if ('questions' in originalSectionWithoutQuestions) {
              delete (originalSectionWithoutQuestions as any).questions;
            }
            if ('questions' in sectionWithoutQuestions) {
              delete (sectionWithoutQuestions as any).questions;
            }
            
            const sectionPropertiesChanged = JSON.stringify(originalSectionWithoutQuestions) !== JSON.stringify(sectionWithoutQuestions);
            
            // Check for changes in question order within the section
            const originalQuestionOrder = originalSection.questions?.map((q: any) => q.id) || [];
            const currentQuestionOrder = section.questions?.map((q: any) => q.id) || [];
            const questionOrderChanged = JSON.stringify(originalQuestionOrder) !== JSON.stringify(currentQuestionOrder);
            
            const hasChanges = sectionPropertiesChanged || questionOrderChanged;
            
            console.log(`🔍 [Save] Section ${section.id} changes detected:`, hasChanges);
            console.log(`🔍 [Save] Section ${section.id} properties changed:`, sectionPropertiesChanged);
            console.log(`🔍 [Save] Section ${section.id} question order changed:`, questionOrderChanged);
            console.log(`🔍 [Save] Section ${section.id} original question order:`, originalQuestionOrder);
            console.log(`🔍 [Save] Section ${section.id} current question order:`, currentQuestionOrder);
            console.log(`🔍 [Save] Section ${section.id} original section:`, originalSection);
            console.log(`🔍 [Save] Section ${section.id} current section:`, section);
            
            if (hasChanges) {
              console.log('📤 Saving updated section:', section.id);
              console.log('📊 Original section questions:', originalSection.questions?.map((q: any) => ({ id: q.id, order: q.order })));
              console.log('📊 Updated section questions:', section.questions?.map((q: any) => ({ id: q.id, order: q.order })));
              await updateSection(section.id, section);
            }
          }
        }
      }
      
      // Save individual question updates
      if (editedSurvey.sections && editedSurvey.sections.length > 0) {
        // Save questions within sections
        for (const section of editedSurvey.sections) {
          for (const question of section.questions) {
            // Check if question was modified by comparing with original
            const originalQuestion = originalSurveyData.sections?.find((s: any) => s.id === section.id)?.questions?.find((q: any) => q.id === question.id);
            if (originalQuestion && JSON.stringify(originalQuestion) !== JSON.stringify(question)) {
              console.log('📤 Saving updated question:', question.id);
              await updateQuestion(question.id, question);
            }
          }
        }
      } else if (editedSurvey.questions && editedSurvey.questions.length > 0) {
        // Save questions in legacy format
        for (const question of editedSurvey.questions) {
          const originalQuestion = originalSurveyData.questions?.find((q: any) => q.id === question.id);
          if (originalQuestion && JSON.stringify(originalQuestion) !== JSON.stringify(question)) {
            console.log('📤 Saving updated question:', question.id);
            await updateQuestion(question.id, question);
          }
        }
      }
      
      // Mark changes as saved
      setHasUnsavedChanges(false);
      
      // Update the main survey state
      if (onSurveyChange) {
        onSurveyChange(editedSurvey);
      }
      
      console.log('✅ All changes saved successfully');
      
      // Call onSaveAndExit if provided (for separate edit route)
      if (onSaveAndExit) {
        onSaveAndExit();
      } else {
        // Fallback to old behavior (exit edit mode)
        setIsEditModeActive(false);
      }
      
    } catch (error) {
      console.error('❌ Failed to save changes:', error);
      alert('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelChanges = async () => {
    try {
      console.log('🔄 Cancelling changes...');
      
      // Call onCancel if provided (for separate edit route)
      if (onCancel) {
        onCancel();
        return;
      }
      
      // Fallback to old behavior (refresh and exit edit mode)
      console.log('🔄 Refreshing survey data from API...');
      
      // Refresh survey data from API to get latest state
      if (survey?.survey_id) {
        const response = await fetch(`/api/v1/survey/${survey.survey_id}`);
        if (response.ok) {
          const freshSurveyData = await response.json();
          console.log('✅ Fresh survey data loaded from API');
          
          // Update the survey in the store with fresh data
          if (onSurveyChange) {
            onSurveyChange(freshSurveyData);
          }
        } else {
          console.warn('⚠️ Failed to refresh survey data, using cached data');
        }
      }
      
      setEditedSurvey(null);
      setHasUnsavedChanges(false);
      setIsEditModeActive(false);
      console.log('🔄 Changes cancelled and survey refreshed');
    } catch (error) {
      console.error('❌ Error refreshing survey data:', error);
      // Fallback to cached data if refresh fails
      setEditedSurvey(null);
      setHasUnsavedChanges(false);
      setIsEditModeActive(false);
      console.log('🔄 Changes cancelled (using cached data due to refresh error)');
    }
  };


  const handleSaveAsReference = async () => {
    if (!surveyToDisplay?.survey_id) {
      console.error('No survey ID available for saving as reference');
      return;
    }

    try {
      const response = await fetch('/api/v1/golden-pairs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rfq_text: surveyToDisplay.title || 'Generated Survey',
          survey_json: surveyToDisplay,
          title: surveyToDisplay.title,
          methodology_tags: surveyToDisplay.methodologies || [],
          industry_category: surveyToDisplay.metadata?.industry_category || '',
          research_goal: surveyToDisplay.metadata?.research_goal || '',
          quality_score: surveyToDisplay.confidence_score || 1.0
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save as reference');
      }

      const result = await response.json();
      console.log('Survey saved as reference:', result);
      alert('Survey saved as reference successfully!');
    } catch (error) {
      console.error('Error saving survey as reference:', error);
      alert('Failed to save survey as reference');
    }
  };

  const handleViewSystemPrompt = () => {
    if (surveyToDisplay?.metadata?.system_prompt) {
      // Open system prompt in a new window or modal
      const promptWindow = window.open('', '_blank', 'width=800,height=600');
      if (promptWindow) {
        promptWindow.document.write(`
          <html>
            <head><title>System Prompt</title></head>
            <body style="font-family: monospace; padding: 20px; white-space: pre-wrap;">
              ${surveyToDisplay.metadata.system_prompt}
            </body>
          </html>
        `);
      }
    } else {
      alert('No system prompt available for this survey');
    }
  };

  const handleExportJSON = () => {
    if (surveyToDisplay) {
      const dataStr = JSON.stringify(surveyToDisplay, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `survey-${surveyToDisplay.survey_id}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const handleExportPDF = async () => {
    if (!surveyToDisplay) {
      console.error('No survey data available for export');
      return;
    }

    try {
      const response = await fetch('/api/v1/export/survey', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          survey_data: surveyToDisplay,
          format: 'docx',
          filename: `survey-${surveyToDisplay.survey_id}.docx`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to export document');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `survey-${surveyToDisplay.survey_id}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting document:', error);
      alert('Failed to export document');
    }
  };

  const handleExportDOCX = async () => {
    if (!surveyToDisplay) {
      console.error('No survey data available for export');
      return;
    }

    try {
      const response = await fetch('/api/v1/export/survey', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          survey_data: surveyToDisplay,
          format: 'docx',
          filename: `survey-${surveyToDisplay.survey_id}.docx`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to export DOCX');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `survey-${surveyToDisplay.survey_id}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting DOCX:', error);
      alert('Failed to export DOCX');
    }
  };


  const handleQuestionUpdate = async (updatedQuestion: Question) => {
    if (!survey?.survey_id) return;
    
    try {
      // Update local state only - no immediate API call
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        // Update in sections format
        updatedSurvey.sections = updatedSurvey.sections.map(section => ({
          ...section,
          questions: section.questions.map(q =>
            q.id === updatedQuestion.id ? updatedQuestion : q
          )
        }));
      } else if (updatedSurvey.questions) {
        // Update in flat questions format
        updatedSurvey.questions = updatedSurvey.questions.map(q =>
          q.id === updatedQuestion.id ? updatedQuestion : q
        );
      }
      
      setEditedSurvey(updatedSurvey);
      setHasUnsavedChanges(true); // Mark as having unsaved changes
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      console.log('✅ Question updated locally, marked as unsaved');
      
    } catch (error) {
      console.error('Failed to update question locally:', error);
    }
  };

  const handleQuestionDelete = (questionId: string) => {
    if (editedSurvey) {
      const questions = editedSurvey.questions?.filter(q => q.id !== questionId) || [];
      setEditedSurvey({ ...editedSurvey, questions });
    }
  };

  const handleMoveQuestion = (questionId: string, direction: 'up' | 'down') => {
    if (!editedSurvey) {
      console.log('❌ [Move] Cannot move question - no editedSurvey');
      return;
    }
    
    console.log('🔄 Moving question:', { questionId, direction });
    console.log('📊 Current editedSurvey before move:', editedSurvey.sections?.map((s: any) => ({ 
      id: s.id, 
      title: s.title, 
      questions: s.questions?.map((q: any) => ({ id: q.id, order: q.order }))
    })));
    
    if (editedSurvey.sections && editedSurvey.sections.length > 0) {
      // Handle questions within sections
      const updatedSections = editedSurvey.sections.map(section => {
        const questions = [...section.questions];
        const currentIndex = questions.findIndex(q => q.id === questionId);
        
        if (currentIndex === -1) return section; // Question not in this section
        
        const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        
        if (newIndex >= 0 && newIndex < questions.length) {
          [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
          
          // Update order property for both questions
          questions[currentIndex].order = currentIndex + 1;
          questions[newIndex].order = newIndex + 1;
          
          console.log('✅ Question moved within section:', section.title);
          return { ...section, questions };
        }
        
        return section;
      });
      
      console.log('📊 Updated sections after move:', updatedSections.map(s => ({ 
        id: s.id, 
        title: s.title, 
        questions: s.questions?.map(q => ({ id: q.id, order: q.order }))
      })));
      
      setEditedSurvey({ ...editedSurvey, sections: updatedSections });
      setHasUnsavedChanges(true);
      console.log('✅ [Move] Set hasUnsavedChanges to true');
      if (onSurveyChange) onSurveyChange({ ...editedSurvey, sections: updatedSections });
    } else if (editedSurvey.questions) {
      // Handle legacy flat questions format
      const questions = [...editedSurvey.questions];
      const currentIndex = questions.findIndex(q => q.id === questionId);
      
      if (currentIndex === -1) return;
      
      const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
      
      if (newIndex >= 0 && newIndex < questions.length) {
        [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
        
        // Update order property for both questions
        questions[currentIndex].order = currentIndex + 1;
        questions[newIndex].order = newIndex + 1;
        
        console.log('✅ Question moved in legacy format');
        setEditedSurvey({ ...editedSurvey, questions });
        setHasUnsavedChanges(true);
        if (onSurveyChange) onSurveyChange({ ...editedSurvey, questions });
      }
    }
  };

  // Section operation handlers
  const handleSectionUpdate = async (sectionId: number, updatedSection: SurveySection) => {
    if (!survey?.survey_id) return;
    
    try {
      // Update local state only - no immediate API call
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        updatedSurvey.sections = updatedSurvey.sections.map(section =>
          section.id === sectionId ? updatedSection : section
        );
      }
      
      setEditedSurvey(updatedSurvey);
      setHasUnsavedChanges(true); // Mark as having unsaved changes
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      console.log('✅ Section updated locally, marked as unsaved');
      
    } catch (error) {
      console.error('Failed to update section locally:', error);
    }
  };

  const handleSectionDelete = async (sectionId: number) => {
    if (!survey?.survey_id) return;
    
    try {
      await deleteSection(sectionId);
      
      // Update local state
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        updatedSurvey.sections = updatedSurvey.sections.filter(section => section.id !== sectionId);
      }
      
      setEditedSurvey(updatedSurvey);
      setHasUnsavedChanges(true); // Mark as having unsaved changes
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
    } catch (error) {
      console.error('Failed to delete section:', error);
    }
  };

  const handleSectionMove = async (sectionId: number, direction: 'up' | 'down') => {
    const currentSurvey = editedSurvey || survey;
    
    if (!survey?.survey_id || !currentSurvey?.sections) {
      console.log('❌ Missing requirements:', { 
        hasSurveyId: !!survey?.survey_id, 
        hasCurrentSurvey: !!currentSurvey, 
        hasSections: !!currentSurvey?.sections 
      });
      return;
    }
    
    console.log('🔄 Starting section move:', { sectionId, direction });
    console.log('📋 Current sections:', currentSurvey.sections.map(s => ({ id: s.id, title: s.title })));
    
    const sections = [...currentSurvey.sections];
    const currentIndex = sections.findIndex(s => s.id === sectionId);
    
    if (currentIndex === -1) {
      console.log('❌ Section not found:', sectionId);
      return;
    }
    
    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    console.log('📍 Move details:', { currentIndex, newIndex, direction, sectionsLength: sections.length });
    
    if (newIndex >= 0 && newIndex < sections.length) {
      // Swap sections
      [sections[currentIndex], sections[newIndex]] = [sections[newIndex], sections[currentIndex]];
      
      // Update the order property to reflect the new position
      sections.forEach((section, index) => {
        section.order = index + 1;
      });
      
      console.log('🔄 After swap:', sections.map(s => ({ id: s.id, title: s.title, order: s.order })));
      
      // Update local state immediately
      const updatedSurvey = { ...currentSurvey, sections };
      console.log('💾 Updating state with:', updatedSurvey.sections.map(s => ({ id: s.id, title: s.title, order: s.order })));
      
      setEditedSurvey(updatedSurvey);
      setHasUnsavedChanges(true); // Mark as having unsaved changes
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      console.log('✅ Section reorder applied locally - use Save button to persist');
    } else {
      console.log('❌ Invalid move:', { currentIndex, newIndex, direction, sectionsLength: sections.length });
    }
  };

  const handleAddQuestionToSection = async (sectionId: number) => {
    if (!survey?.survey_id) return;
    
    // Create a new question
    const newQuestion: Question = {
      id: `q_${Date.now()}`, // Temporary ID
      text: 'New question',
      type: 'multiple_choice',
      options: ['Option 1', 'Option 2'],
      required: true,
      category: 'general',
      methodology: undefined,
      ai_rationale: undefined,
      label: undefined,
      description: undefined
    };
    
    try {
      // Update local state first
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        updatedSurvey.sections = updatedSurvey.sections.map(section => {
          if (section.id === sectionId) {
            return {
              ...section,
              questions: [...section.questions, newQuestion]
            };
          }
          return section;
        });
      }
      
      setEditedSurvey(updatedSurvey);
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      // TODO: Call backend API to persist the new question
      // This would require a new endpoint: POST /api/v1/survey/{survey_id}/sections/{section_id}/questions
      
    } catch (error) {
      console.error('Failed to add question to section:', error);
    }
  };

  const handleCreateSection = async () => {
    if (!survey?.survey_id) return;
    
    const surveyToUpdate = editedSurvey || survey;
    const hasExistingSections = hasSections(surveyToUpdate);
    
    if (!hasExistingSections && surveyToUpdate.questions && surveyToUpdate.questions.length > 0) {
      // Convert flat questions to sections format
      const newSection: SurveySection = {
        id: Date.now(), // Temporary ID
        title: 'Section 1',
        description: 'Survey questions',
        questions: [...surveyToUpdate.questions],
        order: 1
      };
      
      try {
        await createSection(newSection);
        
        // Update local state to sections format
        const updatedSurvey = {
          ...surveyToUpdate,
          sections: [newSection],
          questions: undefined // Remove flat questions
        };
        
        setEditedSurvey(updatedSurvey);
        if (onSurveyChange) onSurveyChange(updatedSurvey);
        
      } catch (error) {
        console.error('Failed to convert to sections:', error);
      }
    } else {
      // Create a new section
      const newSection: SurveySection = {
        id: Date.now(), // Temporary ID
        title: `Section ${(surveyToUpdate.sections?.length || 0) + 1}`,
        description: 'Section description',
        questions: [],
        order: (surveyToUpdate.sections?.length || 0) + 1
      };
      
      try {
        await createSection(newSection);
        
        // Update local state
        let updatedSurvey = { ...surveyToUpdate };
        
        if (!updatedSurvey.sections) {
          updatedSurvey.sections = [];
        }
        updatedSurvey.sections.push(newSection);
        
        setEditedSurvey(updatedSurvey);
        if (onSurveyChange) onSurveyChange(updatedSurvey);
        
      } catch (error) {
        console.error('Failed to create section:', error);
      }
    }
  };

  // Annotation handlers
  // Annotation fixed pane handlers
  const openAnnotationPane = (type: 'question' | 'section' | 'survey', target: any) => {
    setAnnotationPane({
      type,
      target
    });
  };

  const openQuestionAnnotation = (question: Question) => {
    console.log('🔍 [SurveyPreview] openQuestionAnnotation called with question:', question);
    console.log('🔍 [SurveyPreview] Question labels:', question.labels);
    openAnnotationPane('question', question);
  };

  const openSectionAnnotation = (section: SurveySection) => {
    openAnnotationPane('section', section);
  };


  const handleQuestionAnnotation = async (annotation: QuestionAnnotation) => {
    console.log('🔄 [SurveyPreview] handleQuestionAnnotation called with:', annotation);
    console.log('🔍 [SurveyPreview] Annotation removedLabels field:', annotation.removedLabels);
    
    let updatedAnnotations: SurveyAnnotations;
    
    if (!currentAnnotations) {
      updatedAnnotations = {
        surveyId: survey?.survey_id || '',
        questionAnnotations: [annotation],
        sectionAnnotations: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } else {
      const existingIndex = currentAnnotations.questionAnnotations?.findIndex(
        qa => qa.questionId === annotation.questionId
      ) ?? -1;
      
      const questionAnnotations = [...(currentAnnotations.questionAnnotations || [])];
      
      if (existingIndex >= 0) {
        // Preserve the originalQuestionId when updating an existing annotation
        const existingAnnotation = questionAnnotations[existingIndex];
        console.log('🔍 [SurveyPreview] Updating existing annotation:', {
          questionId: annotation.questionId,
          existingOriginalQuestionId: existingAnnotation.originalQuestionId,
          newOriginalQuestionId: annotation.originalQuestionId
        });
        questionAnnotations[existingIndex] = {
          ...annotation,
          originalQuestionId: existingAnnotation.originalQuestionId || annotation.originalQuestionId
        };
      } else {
        questionAnnotations.push(annotation);
      }
      
      updatedAnnotations = {
        ...currentAnnotations,
        questionAnnotations,
        updatedAt: new Date().toISOString()
      };
    }
    
    console.log('🔄 [SurveyPreview] Updated annotations to save:', updatedAnnotations);
    
    try {
      await saveAnnotations(updatedAnnotations);
      console.log('✅ [SurveyPreview] Question annotation saved successfully');
    } catch (error) {
      console.error('❌ [SurveyPreview] Error saving question annotation:', error);
      alert('Failed to save question annotation');
    }
  };

  const handleSectionAnnotation = async (annotation: SectionAnnotation) => {
    let updatedAnnotations: SurveyAnnotations;
    
    if (!currentAnnotations) {
      updatedAnnotations = {
        surveyId: survey?.survey_id || '',
        questionAnnotations: [],
        sectionAnnotations: [annotation],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } else {
      const existingIndex = currentAnnotations.sectionAnnotations?.findIndex(
        sa => sa.sectionId === annotation.sectionId
      ) ?? -1;
      
      const sectionAnnotations = [...(currentAnnotations.sectionAnnotations || [])];
      
      if (existingIndex >= 0) {
        sectionAnnotations[existingIndex] = annotation;
      } else {
        sectionAnnotations.push(annotation);
      }
      
      updatedAnnotations = {
        ...currentAnnotations,
        sectionAnnotations,
        updatedAt: new Date().toISOString()
      };
    }
    
    try {
      await saveAnnotations(updatedAnnotations);
      console.log('Section annotation saved successfully');
    } catch (error) {
      console.error('Error saving section annotation:', error);
      alert('Failed to save section annotation');
    }
  };

  // Initialize editedSurvey when survey changes
  useEffect(() => {
    if (survey && !editedSurvey) {
      console.log('🔄 Initializing editedSurvey with survey data');
      setEditedSurvey(survey);
    }
  }, [survey, editedSurvey]);

  // Handle survey data structure
  const surveyToDisplay = editedSurvey || survey;
  const isCurrentlyEditing = isEditable || isEditModeActive;

  if (!survey) {
    console.log('❌ [SurveyPreview] No survey available');
    return (
      <div className="w-full p-6 text-center">
        <p className="text-gray-500">No survey to preview yet.</p>
        <p className="text-sm text-gray-400 mt-2">Debug: survey is {typeof survey}</p>
      </div>
    );
  }

  // Check if it's an error response
  const isErrorResponse = surveyToDisplay && (
    typeof surveyToDisplay === 'object' && 
    'error' in surveyToDisplay && 
    surveyToDisplay.error === "Document Parse Error"
  );
  
  // Don't show error if we're still loading or if it's just a different format
  if (isErrorResponse) {
    return (
      <div className="w-full p-6 text-center">
        <div className="bg-error-50 border border-error-200 rounded-lg p-6">
          <div className="flex items-center justify-center mb-4">
            <svg className="h-8 w-8 text-error-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-error-800 mb-2">Document Parsing Failed</h3>
          <p className="text-error-600">Unable to process the uploaded document. Please try again.</p>
        </div>
      </div>
    );
  }
  
  // If it's not an error but still invalid, show a loading state instead of error
  if (!surveyToDisplay) {
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
    <div className={`w-full ${hideHeader ? 'h-full' : 'h-screen'} flex flex-col`}>
      {/* Header with Survey Title and Save Controls - conditionally rendered */}
      {!hideHeader && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {surveyToDisplay?.title || 'Survey Preview'}
              </h1>
              {hasUnsavedChanges && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Unsaved Changes
                </span>
              )}
            </div>
            
            {/* Save Controls */}
            {isCurrentlyEditing && (
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleCancelChanges}
                  disabled={isSaving}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveAllChanges}
                  disabled={isSaving}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  {isSaving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span>Save & Exit</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={`flex ${hideHeader ? 'flex-1 min-h-0' : 'flex-1'}`}>
        {/* Left Panel - Survey Content */}
        <div className={`${hideRightPanel ? 'w-full' : (isAnnotationMode || annotationPane.type) ? 'w-[45%]' : 'w-[75%]'} overflow-y-auto`}>
        <div className="p-6">
          <div className="space-y-8">
            {/* Annotation Mode Instructions */}
            {isAnnotationMode && (
              <div className="mb-6 bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-warning-100 rounded-full flex items-center justify-center">
                      <TagIcon className="w-5 h-5 text-warning-600" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-warning-800 mb-1">Annotation Mode Active</h3>
                    <p className="text-sm text-warning-700">
                      Click on any question or section below to add quality annotations. 
                      Your annotations are automatically saved and will help improve future survey generation.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Questions or Sections */}
            <div className="space-y-4">
              {hasSections(surveyToDisplay || {} as Survey) ? (
                // New sections format
                surveyToDisplay?.sections?.map((section, index) => {
                  const canMoveUp = index > 0;
                  const canMoveDown = index < (surveyToDisplay?.sections?.length || 0) - 1;
                  
                  console.log(`📍 Section ${index} (${section.title}):`, { 
                    canMoveUp, 
                    canMoveDown, 
                    totalSections: surveyToDisplay?.sections?.length 
                  });
                  
                  return (
                    <SectionCard
                      key={section.id}
                      section={section}
                      sectionIndex={index}
                      isEditingSurvey={isCurrentlyEditing}
                      isAnnotationMode={isAnnotationMode}
                      onQuestionUpdate={handleQuestionUpdate}
                      onQuestionDelete={handleQuestionDelete}
                      onQuestionMove={handleMoveQuestion}
                      onAnnotateSection={handleSectionAnnotation}
                      onOpenAnnotation={openSectionAnnotation}
                      sectionAnnotation={currentAnnotations?.sectionAnnotations?.find(a => a.sectionId === String(section.id))}
                      onSectionUpdate={handleSectionUpdate}
                      onSectionDelete={handleSectionDelete}
                      onSectionMoveUp={() => handleSectionMove(section.id, 'up')}
                      onSectionMoveDown={() => handleSectionMove(section.id, 'down')}
                      onAddQuestionToSection={handleAddQuestionToSection}
                      canMoveUp={canMoveUp}
                      canMoveDown={canMoveDown}
                      surveyId={survey?.survey_id}
                      currentAnnotations={currentAnnotations}
                    />
                  );
                })
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
                      isEditingSurvey={isCurrentlyEditing}
                      isAnnotationMode={isAnnotationMode}
                      onOpenAnnotation={openQuestionAnnotation}
                      annotation={currentAnnotations?.questionAnnotations?.find(a => a.questionId === question.id)}
                    />
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>No questions available for this survey.</p>
                  </div>
                )
              )}
              
              {/* Add New Section Button */}
              {isCurrentlyEditing && (
                <div className="flex justify-center pt-4">
                  <button
                    onClick={handleCreateSection}
                    className="inline-flex items-center px-4 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md border border-blue-200 transition-colors"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    {hasSections(surveyToDisplay || {} as Survey) ? 'Add New Section' : 'Convert to Sections'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Actions and AI Evaluation (25%) - conditionally rendered */}
      {!hideRightPanel && (
        <div className="w-[25%] bg-gray-50 border-l border-gray-200 flex flex-col">
        {/* Actions Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Actions</h3>
          <div className="space-y-2">
            <button
              onClick={async () => {
                console.log('🔍 [SurveyPreview] Entering annotation mode for survey:', surveyToDisplay?.survey_id);
                if (surveyToDisplay?.survey_id) {
                  await loadAnnotations(surveyToDisplay.survey_id);
                  console.log('🔍 [SurveyPreview] Annotations loaded, current annotations:', useAppStore.getState().currentAnnotations);
                }
                setAnnotationMode(true);
                openAnnotationPane('survey', surveyToDisplay);
              }}
              className="w-full flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm"
            >
              <PencilIcon className="w-4 h-4" />
              Annotate Survey
            </button>
            <button
              onClick={handleEditSurvey}
              className="w-full flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
            >
              <PencilIcon className="w-4 h-4" />
              Edit Survey
            </button>
            <button
              onClick={handleSaveAsReference}
              className="w-full flex items-center gap-2 px-3 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Save as Reference
            </button>
            <button
              onClick={handleViewSystemPrompt}
              className="w-full flex items-center gap-2 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              View System Prompt
            </button>
          </div>
        </div>

        {/* Export Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-900 mb-3">EXPORT</h3>
          <div className="space-y-2">
            <button
              onClick={handleExportJSON}
              className="w-full text-left text-blue-600 hover:text-blue-800 font-medium text-sm"
            >
              JSON Download JSON
            </button>
            <button
              onClick={handleExportPDF}
              className="w-full text-left text-red-600 hover:text-red-800 font-medium text-sm"
            >
              PDF Download DOCX (PDF coming soon)
            </button>
            <button
              onClick={handleExportDOCX}
              className="w-full text-left text-green-600 hover:text-green-800 font-medium text-sm"
            >
              DOCX Download DOCX
            </button>
          </div>
        </div>

        {/* AI Evaluation Analysis Section */}
        {surveyToDisplay?.pillar_scores && (
          <div className="p-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-gray-900">AI Evaluation Analysis</h3>
              </div>

              {/* Overall Assessment */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-700">Overall Assessment</span>
                  <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full">Grade B+</span>
                </div>
                <p className="text-xs text-gray-600 mb-2">Single-Call Comprehensive Analysis | Overall Score: {Math.round((surveyToDisplay.pillar_scores.weighted_score || 0) * 100)}% (Grade B+)</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-blue-600">Score: {Math.round((surveyToDisplay.pillar_scores.weighted_score || 0) * 100)}%</span>
                  <span className="text-xs text-gray-500">•</span>
                  <span className="text-xs text-blue-600">Chain-of-Thought Evaluation</span>
                </div>
              </div>

              {/* Pillar Analysis */}
              <div className="space-y-3 mb-4">
                <h4 className="text-xs font-medium text-gray-900">Pillar Analysis</h4>
                {surveyToDisplay.pillar_scores.pillar_breakdown?.slice(0, 3).map((pillar, index) => {
                  const score = pillar.score || 0;
                  const percentage = Math.round(score * 100);
                  const grade = percentage >= 90 ? 'A' : percentage >= 80 ? 'B' : percentage >= 70 ? 'C' : percentage >= 60 ? 'D' : 'F';
                  const gradeColor = grade === 'A' ? 'text-green-600' : grade === 'B' ? 'text-blue-600' : grade === 'C' ? 'text-yellow-600' : 'text-red-600';
                  const progressColor = score >= 0.9 ? 'bg-green-500' : score >= 0.8 ? 'bg-blue-500' : score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500';
                  
                  return (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-gray-700">
                          {pillar.display_name || pillar.pillar_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <div className="flex items-center gap-1">
                          <span className={`text-xs font-medium ${gradeColor}`}>{grade}</span>
                          <span className="text-xs text-gray-500">{percentage}%</span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div 
                          className={`h-1.5 rounded-full transition-all duration-300 ${progressColor}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{pillar.criteria_met || 0}/{pillar.total_criteria || 0} criteria met</span>
                        <span>Weight: {Math.round((pillar.weight || 0) * 100)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* AI Recommendations */}
              <div className="space-y-3">
                <h4 className="text-xs font-medium text-gray-900">AI Recommendations</h4>
                <div className="space-y-2">
                  <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                        <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="text-xs text-blue-800">Consider adding more demographic questions to improve respondent segmentation</p>
                    </div>
                  </div>
                  <div className="p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                        <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="text-xs text-yellow-800">Some questions may be too complex for mobile completion</p>
                    </div>
                  </div>
                  <div className="p-2 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                        <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="text-xs text-green-800">Good use of skip logic and branching improves user experience</p>
                    </div>
                  </div>
                  <div className="p-2 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <div className="w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                        <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="text-xs text-purple-800">Consider adding validation rules for numeric inputs</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      )}

        {/* Annotation Pane - Show when annotation mode is active OR when there's an active annotation pane */}
        {(() => {
          const shouldShow = isAnnotationMode || annotationPane.type;
          console.log('🔍 [SurveyPreview] Annotation pane condition:', {
            isAnnotationMode,
            annotationPaneType: annotationPane.type,
            shouldShow,
            annotationTarget: annotationPane.target
          });
          return shouldShow;
        })() && (
          <div className="w-[55%]">
            <AnnotationSidePane
              annotationType={annotationPane.type}
              annotationTarget={(() => {
                console.log('🔍 [SurveyPreview] Passing annotationTarget to AnnotationSidePane:', annotationPane.target);
                console.log('🔍 [SurveyPreview] Question labels:', annotationPane.target?.labels);
                return annotationPane.target;
              })()}
              currentAnnotations={currentAnnotations}
              onQuestionAnnotation={handleQuestionAnnotation}
              onSectionAnnotation={handleSectionAnnotation}
              onSurveyLevelAnnotation={handleSurveyLevelAnnotation}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default SurveyPreview;