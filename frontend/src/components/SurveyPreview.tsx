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
import { PencilIcon, ChevronDownIcon, ChevronRightIcon, TagIcon, TrashIcon, ChevronUpIcon, ChartBarIcon } from '@heroicons/react/24/outline';

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

  const handleSaveEdit = () => {
    onUpdate(editedQuestion);
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

  const updateQuestionField = (field: keyof Question, value: any) => {
    setEditedQuestion(prev => ({ ...prev, [field]: value }));
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
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditingSurvey && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(!isEditing);
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
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
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Question Text</label>
                <textarea
                  value={editedQuestion.text || ''}
                  onChange={(e) => updateQuestionField('text', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Question Type</label>
              <select
                value={editedQuestion.type}
                onChange={(e) => updateQuestionField('type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="multiple_choice">Multiple Choice</option>
                <option value="multiple_select">Multiple Select</option>
                <option value="single_choice">Single Choice</option>
                <option value="text">Text</option>
                <option value="scale">Scale</option>
                <option value="ranking">Ranking</option>
                <option value="instruction">Instruction</option>
                <option value="matrix">Matrix</option>
                <option value="numeric">Numeric</option>
                <option value="date">Date</option>
                <option value="boolean">Boolean</option>
                <option value="matrix_likert">Matrix Likert</option>
                <option value="constant_sum">Constant Sum</option>
                <option value="gabor_granger">Gabor Granger</option>
                <option value="numeric_grid">Numeric Grid</option>
                <option value="numeric_open">Numeric Open</option>
                <option value="likert">Likert Scale</option>
              </select>
            </div>

            {/* Options editing for question types that need them */}
            {['multiple_choice', 'multiple_select', 'single_choice', 'ranking', 'matrix_likert', 'constant_sum', 'gabor_granger', 'likert'].includes(editedQuestion.type) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Options</label>
                <div className="space-y-2">
                  {(editedQuestion.options || []).map((option, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={option}
                        onChange={(e) => {
                          const newOptions = [...(editedQuestion.options || [])];
                          newOptions[index] = e.target.value;
                          updateQuestionField('options', newOptions);
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                        placeholder={`Option ${index + 1}`}
                      />
                      <button
                        onClick={() => {
                          const newOptions = (editedQuestion.options || []).filter((_, i) => i !== index);
                          updateQuestionField('options', newOptions);
                        }}
                        className="px-2 py-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                        type="button"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      const newOptions = [...(editedQuestion.options || []), ''];
                      updateQuestionField('options', newOptions);
                    }}
                    className="px-3 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded border border-blue-200"
                    type="button"
                  >
                    + Add Option
                  </button>
                </div>
              </div>
            )}

            {/* Scale labels editing for scale questions */}
            {editedQuestion.type === 'scale' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scale Labels</label>
                <div className="space-y-2">
                  {editedQuestion.scale_labels && Object.entries(editedQuestion.scale_labels).map(([key, label]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <span className="w-16 text-sm text-gray-600">{key}:</span>
                      <input
                        type="text"
                        value={label}
                        onChange={(e) => {
                          const newScaleLabels = { ...editedQuestion.scale_labels };
                          newScaleLabels[key] = e.target.value;
                          updateQuestionField('scale_labels', newScaleLabels);
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="flex space-x-2">
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {question.text}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Type: {question.type}{question.category && ` • Category: ${question.category}`}
            </p>
            
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
  isEditingSurvey: boolean;
  isAnnotationMode: boolean;
  onQuestionUpdate: (updatedQuestion: Question) => void;
  onQuestionDelete: (questionId: string) => void;
  onQuestionMove: (questionId: string, direction: 'up' | 'down') => void;
  onAnnotateSection?: (annotation: SectionAnnotation) => void;
  onOpenAnnotation?: (section: SurveySection) => void;
  sectionAnnotation?: SectionAnnotation;
}> = ({
  section,
  isEditingSurvey,
  isAnnotationMode,
  onQuestionUpdate,
  onQuestionDelete,
  onQuestionMove,
  onAnnotateSection,
  onOpenAnnotation,
  sectionAnnotation
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

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
              {section.description && (
                <p className="text-sm text-gray-600 mt-1">{section.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
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
              onOpenAnnotation={handleQuestionAnnotation}
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
  const { currentSurvey, isAnnotationMode, setAnnotationMode, currentAnnotations, saveAnnotations } = useAppStore();
  const survey = propSurvey || currentSurvey;
  const [editedSurvey, setEditedSurvey] = useState<Survey | null>(null);
  const [isEditingMode, setIsEditingMode] = useState(false);
  
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
      setAnnotationMode(false);
      // Clear annotation pane state when exiting annotation mode
      setAnnotationPane({
        type: null,
        target: null
      });
      console.log('Exited annotation mode');
    } catch (error) {
      console.error('Error exiting annotation mode:', error);
    }
  };

  // New functionality handlers
  const handleEditSurvey = () => {
    if (surveyToDisplay) {
      setEditedSurvey(surveyToDisplay);
      setIsEditingMode(true);
      console.log('Entered edit mode for survey:', surveyToDisplay.survey_id);
    }
  };

  const handleSaveEdit = () => {
    if (editedSurvey && onSurveyChange) {
      onSurveyChange(editedSurvey);
      setIsEditingMode(false);
      console.log('Survey changes saved');
    }
  };

  const handleCancelEdit = () => {
    setEditedSurvey(null);
    setIsEditingMode(false);
    console.log('Edit mode cancelled');
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

  const handleExportPDF = () => {
    alert('PDF export functionality is not yet implemented');
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


  const handleQuestionUpdate = (updatedQuestion: Question) => {
    if (editedSurvey) {
      const questions = editedSurvey.questions?.map(q => 
        q.id === updatedQuestion.id ? updatedQuestion : q
      ) || [];
      setEditedSurvey({ ...editedSurvey, questions });
    }
  };

  const handleQuestionDelete = (questionId: string) => {
    if (editedSurvey) {
      const questions = editedSurvey.questions?.filter(q => q.id !== questionId) || [];
      setEditedSurvey({ ...editedSurvey, questions });
    }
  };

  const handleMoveQuestion = (questionId: string, direction: 'up' | 'down') => {
    if (!editedSurvey?.questions) return;
    
    const questions = [...editedSurvey.questions];
    const currentIndex = questions.findIndex(q => q.id === questionId);
    
    if (currentIndex === -1) return;
    
    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    if (newIndex >= 0 && newIndex < questions.length) {
      [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
      setEditedSurvey({ ...editedSurvey, questions });
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
    openAnnotationPane('question', question);
  };

  const openSectionAnnotation = (section: SurveySection) => {
    openAnnotationPane('section', section);
  };


  const handleQuestionAnnotation = async (annotation: QuestionAnnotation) => {
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
        questionAnnotations[existingIndex] = annotation;
      } else {
        questionAnnotations.push(annotation);
      }
      
      updatedAnnotations = {
        ...currentAnnotations,
        questionAnnotations,
        updatedAt: new Date().toISOString()
      };
    }
    
    try {
      await saveAnnotations(updatedAnnotations);
      console.log('Question annotation saved successfully');
    } catch (error) {
      console.error('Error saving question annotation:', error);
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

  // Handle survey data structure
  const surveyToDisplay = editedSurvey || survey;
  const isInEditMode = isEditable || isEditingMode;

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
    <div className="w-full h-screen flex">
          {/* Left Panel - Survey Content */}
          <div className={`${(isAnnotationMode || annotationPane.type) ? 'w-[45%]' : 'w-[75%]'} overflow-y-auto`}>
        <div className="p-6">
          <div className="space-y-8">
            {/* Survey Header */}
            <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg">
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

              {/* Survey Title and Description */}
              <div className="mb-6">
                {isInEditMode ? (
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
                    <div className="flex space-x-3">
                      <button
                        onClick={handleSaveEdit}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Save Changes
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                      >
                        Cancel
                      </button>
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
                    isEditingSurvey={isInEditMode}
                    isAnnotationMode={isAnnotationMode}
                    onQuestionUpdate={handleQuestionUpdate}
                    onQuestionDelete={handleQuestionDelete}
                    onQuestionMove={handleMoveQuestion}
                    onAnnotateSection={handleSectionAnnotation}
                    onOpenAnnotation={openSectionAnnotation}
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
                      isEditingSurvey={isInEditMode}
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
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Actions and AI Evaluation (25%) */}
      <div className="w-[25%] bg-gray-50 border-l border-gray-200 flex flex-col">
        {/* Actions Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Actions</h3>
          <div className="space-y-2">
            <button
              onClick={() => {
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
              PDF Download PDF
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
          <div className="flex-1 p-4">
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

        {/* Annotation Pane - Show when annotation mode is active OR when there's an active annotation pane */}
        {(isAnnotationMode || annotationPane.type) && (
          <div className="w-[55%]">
            <AnnotationSidePane
              annotationType={annotationPane.type}
              annotationTarget={annotationPane.target}
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