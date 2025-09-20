import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, Survey, SurveySection, QuestionAnnotation, SectionAnnotation, SurveyAnnotations } from '../types';
import PillarScoresDisplay from './PillarScoresDisplay';
import QuestionAnnotationPanel from './QuestionAnnotationPanel';
import SectionAnnotationPanel from './SectionAnnotationPanel';
import AnnotationMode from './AnnotationMode';
import { SystemPromptViewer } from './SystemPromptViewer';
import { PencilIcon, BookmarkIcon, ArrowDownTrayIcon, ChevronDownIcon, ChevronRightIcon, TagIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

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
        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
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
          <span className="text-sm font-medium text-gray-500">Q{index + 1}</span>
          {question.methodology && (
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

      {/* Question Text */}
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
          {question.text}
        </h3>
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
                        value={option}
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
                    className="px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
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
                    className="h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {option}
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
                    className="h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {option}
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
                  <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 rounded-full text-sm font-medium mr-3">
                    {idx + 1}
                  </div>
                  <span className="text-sm text-gray-700 flex-1">{option}</span>
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
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
              >
                Move Up
              </button>
              <button 
                onClick={() => onMove(question.id, 'down')}
                disabled={!canMoveDown}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
              >
                Move Down
              </button>
              <button 
                onClick={onDelete}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                Delete
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
            <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold text-sm">
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
  const [showSystemPromptModal, setShowSystemPromptModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [goldenFormData, setGoldenFormData] = useState({
    title: '',
    industry_category: '',
    research_goal: '',
    methodology_tags: [] as string[],
    quality_score: 0.9
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.docx')) {
      setUploadStatus('error');
      setUploadMessage('Please select a DOCX file');
      setTimeout(() => setUploadStatus('idle'), 3000);
      return;
    }

    setIsUploading(true);
    setUploadStatus('idle');
    setUploadMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/golden-pairs/parse-document', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to parse document');
      }

      const result = await response.json();
      
      // Update the survey with the LLM-parsed data (same as golden example creation)
      if (result.survey_json) {
        setSurvey(result.survey_json);
        
        // Call the parent's onSurveyChange if provided (for golden example editing)
        if (onSurveyChange) {
          onSurveyChange(result.survey_json);
        }
        
        // Reset the file input
        event.target.value = '';
        
        // Show success message
        setUploadStatus('success');
        setUploadMessage('Document successfully parsed and converted to survey!');
        
        // Clear success message after 5 seconds
        setTimeout(() => setUploadStatus('idle'), 5000);
      }

    } catch (error) {
      console.error('Document upload failed:', error);
      setUploadStatus('error');
      setUploadMessage(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Clear error message after 5 seconds
      setTimeout(() => setUploadStatus('idle'), 5000);
    } finally {
      setIsUploading(false);
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

  const handleExportSurvey = (format: 'json' | 'clipboard' | 'qualtrics') => {
    if (!surveyToDisplay) return;
    
    const surveyData = JSON.stringify(surveyToDisplay, null, 2);
    
    switch (format) {
      case 'json':
        // Download as JSON file
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
        
      case 'clipboard':
        // Copy to clipboard
        navigator.clipboard.writeText(surveyData).then(() => {
          alert('Survey data copied to clipboard!');
        }).catch(() => {
          alert('Failed to copy to clipboard');
        });
        break;
        
      case 'qualtrics':
        // TODO: Implement Qualtrics integration
        alert('Qualtrics integration coming soon!');
        break;
    }
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
                       survey.questions && 
                       Array.isArray(survey.questions);

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
      questionsIsArray: Array.isArray(survey.questions),
      questionsLength: survey.questions?.length,
      surveyKeys: Object.keys(survey || {})
    });
    
    // Check if this is an error response from the API
    const isErrorResponse = survey && (
      survey.title === "Document Parse Error" || 
      survey.description?.includes("Failed to parse document") ||
      survey.raw_output?.error ||
      survey.final_output?.title === "Document Parse Error"
    );
    
    return (
      <div className="w-full p-6">
        {isErrorResponse ? (
          <div className="bg-white rounded-lg shadow-lg border border-red-200">
            {/* Header */}
            <div className="bg-red-50 px-6 py-4 border-b border-red-200 rounded-t-lg">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-red-800">Document Parsing Failed</h3>
                  <p className="text-sm text-red-600 mt-1">Unable to process the uploaded document</p>
                </div>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-6 py-4">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">AI Service Configuration Required</h3>
                <p className="text-gray-700 mb-4">
                  This application uses AI to automatically generate surveys from your documents. 
                  To enable this feature, an AI service needs to be configured.
                </p>
                
                <div className="space-y-4">
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-amber-800 mb-2">What's happening?</h4>
                    <p className="text-sm text-amber-700">
                      The AI service that converts documents to surveys isn't set up yet. 
                      This is a one-time configuration that your administrator needs to complete.
                    </p>
                  </div>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-blue-800 mb-3">How to get this working:</h4>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-sm font-medium text-blue-700 mb-1">Option 1: Replicate (Recommended)</h5>
                        <ul className="text-xs text-blue-600 space-y-1 ml-4">
                          <li>• Visit <a href="https://replicate.com" target="_blank" rel="noopener noreferrer" className="underline">replicate.com</a> and create a free account</li>
                          <li>• Generate an API token from your account settings</li>
                          <li>• Share the token with your administrator</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="text-sm font-medium text-blue-700 mb-1">Option 2: OpenAI (Alternative)</h5>
                        <ul className="text-xs text-blue-600 space-y-1 ml-4">
                          <li>• Visit <a href="https://platform.openai.com" target="_blank" rel="noopener noreferrer" className="underline">platform.openai.com</a></li>
                          <li>• Create an account and generate an API key</li>
                          <li>• Share the key with your administrator</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">In the meantime, you can:</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Use the manual survey builder to create surveys</li>
                      <li>• Copy and paste text from your document into the RFQ editor</li>
                      <li>• Contact your administrator about setting up AI services</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-3">
                <label className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer transition-all duration-200 ${
                  isUploading 
                    ? 'text-blue-700 bg-blue-100 cursor-not-allowed' 
                    : 'text-white bg-blue-600 hover:bg-blue-700'
                }`}>
                  {isUploading ? (
                    <div className="animate-spin rounded-full h-4 w-4 mr-2 border-2 border-blue-600 border-t-transparent"></div>
                  ) : (
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  )}
                  {isUploading ? 'Parsing with AI...' : 'Upload & Parse with AI'}
                  <input
                    type="file"
                    accept=".docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="retry-document-upload"
                    disabled={isUploading}
                  />
                </label>
                <button 
                  onClick={() => window.history.back()} 
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Go Back
                </button>
              </div>

              {/* Status Notification */}
              {uploadStatus !== 'idle' && (
                <div className="mt-4">
                  {uploadStatus === 'success' && (
                    <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-green-800">Document Parsed Successfully!</h3>
                        <p className="text-sm text-green-700 mt-1">{uploadMessage}</p>
                        <p className="text-xs text-green-600 mt-2">The survey preview above has been updated with the new content.</p>
                      </div>
                    </div>
                  )}
                  
                  {uploadStatus === 'error' && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-red-800">Upload Failed</h3>
                        <p className="text-sm text-red-700 mt-1">{uploadMessage}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {/* Technical Details (Collapsible) */}
            <details className="border-t border-gray-200">
              <summary className="px-6 py-3 text-sm text-gray-500 hover:text-gray-700 cursor-pointer bg-gray-50">
                Show Technical Details
              </summary>
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                <pre className="text-xs text-gray-600 overflow-auto max-h-64 bg-white p-3 rounded border">
                  {JSON.stringify(survey, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Invalid Survey Data</h3>
            <p className="mt-1 text-sm text-gray-500">The survey data appears to be malformed or incomplete.</p>
            <div className="mt-6">
              <button 
                onClick={() => window.location.reload()} 
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Refresh Page
              </button>
            </div>
          </div>
        )}
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
            {/* Action Buttons */}
            <div className="mb-6">
              {/* Primary Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                {/* Left side - Annotation Mode */}
                <div className="flex items-center gap-3">
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
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                      isAnnotationMode 
                        ? 'bg-yellow-600 text-white hover:bg-yellow-700 shadow-lg' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                    }`}
                  >
                    <TagIcon className="w-5 h-5" />
                    <span className="text-sm">
                      {isAnnotationMode ? 'Exit Annotation' : 'Annotate Survey'}
                    </span>
                  </button>
                  
                  {isAnnotationMode && (
                    <div className="flex items-center gap-2 text-sm text-yellow-600 font-medium px-3 py-1 bg-yellow-50 rounded-lg border border-yellow-200">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      Auto-saving
                    </div>
                  )}
                </div>

                {/* Right side - Survey Actions */}
                <div className="flex items-center gap-3">
                  {isEditingSurvey ? (
                    <>
                      <button 
                        onClick={handleSaveEdits}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors shadow-lg"
                      >
                        <CheckIcon className="w-5 h-5" />
                        <span className="text-sm">Save Changes</span>
                      </button>
                      <button 
                        onClick={handleCancelEdits}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
                      >
                        <XMarkIcon className="w-5 h-5" />
                        <span className="text-sm">Cancel</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button 
                        onClick={handleStartEditing}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-lg"
                      >
                        <PencilIcon className="w-5 h-5" />
                        <span className="text-sm">Edit Survey</span>
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
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors shadow-lg"
                      >
                        <BookmarkIcon className="w-5 h-5" />
                        <span className="text-sm">Save as Golden Example</span>
                      </button>
                      
                      <button 
                        onClick={() => setShowSystemPromptModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-lg"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <span className="text-sm">View System Prompt</span>
                      </button>
                      
                      <div className="relative export-dropdown">
                        <button 
                          onClick={() => setShowExportDropdown(!showExportDropdown)}
                          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors shadow-lg"
                        >
                          <ArrowDownTrayIcon className="w-5 h-5" />
                          <span className="text-sm">Export</span>
                        </button>
                        {showExportDropdown && (
                          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-10 overflow-hidden">
                            <div className="py-2">
                              <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide border-b border-gray-100">
                                Export Options
                              </div>
                              <button
                                onClick={() => {
                                  handleExportSurvey('json');
                                  setShowExportDropdown(false);
                                }}
                                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                              >
                                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                  <span className="text-blue-600 font-bold text-xs">JSON</span>
                                </div>
                                <div className="text-left">
                                  <div className="font-medium">Download JSON</div>
                                  <div className="text-xs text-gray-500">Raw survey data</div>
                                </div>
                              </button>
                              <button
                                onClick={() => {
                                  handleExportSurvey('clipboard');
                                  setShowExportDropdown(false);
                                }}
                                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                              >
                                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                                  <span className="text-green-600 font-bold text-xs">📋</span>
                                </div>
                                <div className="text-left">
                                  <div className="font-medium">Copy to Clipboard</div>
                                  <div className="text-xs text-gray-500">Quick sharing</div>
                                </div>
                              </button>
                              <button
                                onClick={() => {
                                  handleExportSurvey('qualtrics');
                                  setShowExportDropdown(false);
                                }}
                                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                              >
                                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                                  <span className="text-orange-600 font-bold text-xs">Q</span>
                                </div>
                                <div className="text-left">
                                  <div className="font-medium">Export for Qualtrics</div>
                                  <div className="text-xs text-gray-500">Survey platform integration</div>
                                </div>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Annotation Mode Instructions */}
              {isAnnotationMode && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
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
            </div>

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
            {/* Pillar Scores - Moved to top for better visibility */}
            {surveyToDisplay?.pillar_scores && (
              <PillarScoresDisplay 
                pillarScores={surveyToDisplay.pillar_scores}
                className="mb-6"
                compact={true}
              />
            )}

          {/* Quality Score - Always use advanced pillar scores */}
          {surveyToDisplay?.pillar_scores && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">Quality Score (Advanced)</h3>
              <div className="flex items-center">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full"
                    style={{ 
                      width: `${surveyToDisplay.pillar_scores.weighted_score * 100}%` 
                    }}
                  />
                </div>
                <span className="ml-3 text-sm font-medium text-gray-700">
                  {Math.round(surveyToDisplay.pillar_scores.weighted_score * 100)}%
                </span>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                Grade: {surveyToDisplay.pillar_scores.overall_grade} • Chain-of-Thought Evaluation
              </div>
            </div>
          )}

          {/* Methodologies */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Methodologies</h3>
            <div className="flex flex-wrap gap-2">
              {surveyToDisplay?.methodologies?.map((method) => (
                <span 
                  key={method}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                >
                  {method.replace('_', ' ')}
                </span>
              )) || []}
            </div>
          </div>

          {/* Reference Examples */}
          {surveyToDisplay?.golden_examples && surveyToDisplay.golden_examples.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">Reference Examples</h3>
              <div className="space-y-2">
                {surveyToDisplay.golden_examples?.map((example) => (
                  <div key={example.id} className="p-2 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-700">{example.industry_category}</p>
                    <p className="text-xs text-gray-500">{example.research_goal}</p>
                  </div>
                )) || []}
              </div>
            </div>
          )}

          {/* Export Options */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Export Options</h3>
            <div className="space-y-2">
              <button 
                onClick={() => handleExportSurvey('json')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                📄 Download JSON
              </button>
              <button 
                onClick={() => handleExportSurvey('clipboard')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                📋 Copy to Clipboard
              </button>
              <button 
                onClick={() => handleExportSurvey('qualtrics')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                🔗 Send to Qualtrics
              </button>
            </div>
          </div>
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
            <h2 className="text-lg font-semibold mb-4">Save Survey as Golden Example</h2>
            
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
                className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                Save as Golden Example
              </button>
            </div>
          </div>
        </div>
      )}

      {/* System Prompt Modal */}
      {showSystemPromptModal && (
        <SystemPromptViewer
          surveyId={survey?.survey_id || ''}
          onClose={() => setShowSystemPromptModal(false)}
        />
      )}
    </div>
  );
};