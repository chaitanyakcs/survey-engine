import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, Survey, SurveySection, QuestionAnnotation, SectionAnnotation, SurveyAnnotations, SurveyLevelAnnotation, ConceptFile, SamplePlanTable } from '../types';
import AnnotationMode from './AnnotationMode';
import AnnotationSidePane from './AnnotationSidePane';
import SurveyTextBlock from './SurveyTextBlock';
import QuestionCard from './QuestionCard';
import { useSurveyEdit } from '../hooks/useSurveyEdit';
import { PencilIcon, ChevronDownIcon, ChevronRightIcon, TagIcon, TrashIcon, ChevronUpIcon, PlusIcon, TagIcon as LabelIcon, PhotoIcon, DocumentIcon } from '@heroicons/react/24/outline';


// Helper function to check if survey uses sections format
const hasSections = (survey: Survey): boolean => {
  return !!survey.sections && survey.sections.length > 0;
};

// Sample Plan Table Renderer Component
const SamplePlanTableRenderer: React.FC<{ data: SamplePlanTable }> = ({ data }) => {
  // Extract concept columns from subsamples or use default structure
  // The table format shows respondent types as rows and concepts as columns
  const subsamples = data.subsamples || [];
  
  // Get unique concept names from subsamples (if they have concept information)
  // For now, we'll use a simple structure based on subsamples
  // If subsamples have concept info, extract it; otherwise use subsample names as concepts
  const conceptColumns: string[] = [];
  const respondentRows: Array<{ name: string; values: number[] }> = [];
  
  // Try to extract concept columns from the data structure
  // This is a flexible approach that adapts to the data format
  if (subsamples.length > 0) {
    // For now, we'll create a simple table with respondent types
    // The actual concept columns might need to be extracted differently based on backend structure
    subsamples.forEach((subsample) => {
      respondentRows.push({
        name: subsample.name || 'Unknown',
        values: [subsample.totalSize || 0] // This will need to be adjusted based on actual data structure
      });
    });
  }
  
  // Calculate totals
  const totalRow = {
    name: 'TOTAL',
    total: data.overallSample?.totalSize || respondentRows.reduce((sum, row) => sum + (row.values[0] || 0), 0),
    values: respondentRows.reduce((acc, row) => {
      row.values.forEach((val, idx) => {
        acc[idx] = (acc[idx] || 0) + val;
      });
      return acc;
    }, [] as number[])
  };
  
  // Collect all recruiting criteria
  const recruitingCriteria = subsamples
    .filter(sub => sub.criteria)
    .map(sub => sub.criteria)
    .filter((criteria): criteria is string => !!criteria);
  
  // If no concept columns found, create a simple single-column table
  const hasMultipleConcepts = conceptColumns.length > 0;
  const displayColumns = hasMultipleConcepts ? conceptColumns : ['Count'];
  
  return (
    <div className="mb-6">
      {/* Sample Plan Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-300">
          <thead>
            <tr className="bg-gray-100 border-b-2 border-gray-300">
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-r border-gray-300">
                RESPONDENT TYPE
              </th>
              {displayColumns.map((col, idx) => (
                <th key={idx} className="px-4 py-3 text-center text-sm font-semibold text-gray-900 border-r border-gray-300 last:border-r-0">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {respondentRows.map((row, idx) => (
              <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r border-gray-300">
                  {row.name}
                </td>
                {row.values.map((val, valIdx) => (
                  <td key={valIdx} className="px-4 py-3 text-sm text-center text-gray-700 border-r border-gray-300 last:border-r-0">
                    {val}
                  </td>
                ))}
              </tr>
            ))}
            {/* Total Row */}
            <tr className="border-t-2 border-gray-400 bg-gray-50 font-semibold">
              <td className="px-4 py-3 text-sm font-bold text-gray-900 border-r border-gray-300">
                <span className="underline">TOTAL = {totalRow.total}</span>
              </td>
              {totalRow.values.map((val, idx) => (
                <td key={idx} className="px-4 py-3 text-sm text-center font-bold text-gray-900 border-r border-gray-300 last:border-r-0">
                  {val}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      
      {/* Recruiting Criteria Section */}
      {recruitingCriteria.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-bold text-gray-900 mb-3">RECRUITING CRITERIA :-</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            {recruitingCriteria.map((criteria, idx) => (
              <li key={idx}>{criteria}</li>
            ))}
          </ul>
        </div>
      )}
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
  conceptFiles?: ConceptFile[];
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
  currentAnnotations,
  conceptFiles = []
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
                {/* Question and instruction count badge */}
                {(() => {
                  const questionsCount = section.questions?.filter(q => q.type !== 'instruction').length || 0;
                  // Count instruction-type questions
                  const instructionQuestions = section.questions?.filter(q => q.type === 'instruction').length || 0;
                  // Count instruction-type text blocks
                  const instructionTextBlocks = 
                    (section.introText?.type === 'instruction' ? 1 : 0) +
                    (section.textBlocks?.filter(tb => tb.type === 'instruction').length || 0) +
                    (section.closingText?.type === 'instruction' ? 1 : 0);
                  const totalInstructions = instructionQuestions + instructionTextBlocks;
                  
                  return (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {questionsCount} {questionsCount === 1 ? 'Question' : 'Questions'}
                      {totalInstructions > 0 && (
                        <> • {totalInstructions} {totalInstructions === 1 ? 'Instruction' : 'Instructions'}</>
                      )}
                    </span>
                  );
                })()}
                {sectionAnnotation && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <TagIcon className="w-3 h-3" />
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
          {/* Check if this is a Sample Plan section */}
          {(() => {
            const isSamplePlan = sectionIndex === 0 || 
                                 section.title?.toLowerCase().includes('sample plan') || 
                                 !!section.samplePlanData;
            
            // Render Sample Plan table if samplePlanData exists
            if (isSamplePlan && section.samplePlanData) {
              return (
                <SamplePlanTableRenderer data={section.samplePlanData} />
              );
            }
            
            // Skip introText for Sample Plan sections, show it for others
            if (!isSamplePlan && section.introText) {
              return (
                <SurveyTextBlock
                  textContent={section.introText}
                  className="mb-6"
                />
              );
            }
            
            return null;
          })()}

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

          {/* Concept Files Display - Show in Section 4 (Concept Exposure) */}
          {(() => {
            const shouldShow = (section.title?.toLowerCase().includes('concept') || sectionIndex === 3) && conceptFiles.length > 0;
            if (sectionIndex === 3 || section.title?.toLowerCase().includes('concept')) {
              console.log(`🔍 [SurveyPreview] Section ${sectionIndex} (${section.title}): shouldShow=${shouldShow}, conceptFiles.length=${conceptFiles.length}`);
            }
            return shouldShow;
          })() && (
            <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="text-sm font-semibold text-purple-900 mb-3 flex items-center">
                <PhotoIcon className="w-5 h-5 mr-2 text-purple-600" />
                Concept Files
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {conceptFiles
                  .sort((a: ConceptFile, b: ConceptFile) => (a.display_order || 0) - (b.display_order || 0))
                  .map((file: ConceptFile) => {
                    const isImage = file.content_type?.startsWith('image/');
                    return (
                      <div
                        key={file.id}
                        className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                      >
                        {isImage ? (
                          <a
                            href={file.file_url || `/api/v1/rfq/concept/${file.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block"
                          >
                            <img
                              src={file.file_url || `/api/v1/rfq/concept/${file.id}`}
                              alt={file.original_filename || file.filename}
                              className="w-full h-32 object-cover"
                              onError={(e) => {
                                // Fallback to icon if image fails to load
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.nextElementSibling?.classList.remove('hidden');
                              }}
                            />
                            <div className="hidden p-8 flex items-center justify-center bg-gray-100">
                              <PhotoIcon className="w-12 h-12 text-gray-400" />
                            </div>
                          </a>
                        ) : (
                          <a
                            href={file.file_url || `/api/v1/rfq/concept/${file.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-6 flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition-colors"
                          >
                            <DocumentIcon className="w-12 h-12 text-gray-400 mb-2" />
                            <span className="text-xs text-gray-600 text-center truncate w-full">
                              {file.original_filename || file.filename}
                            </span>
                          </a>
                        )}
                        <div className="p-2 bg-white border-t border-gray-200">
                          <p className="text-xs text-gray-700 truncate" title={file.original_filename || file.filename}>
                            {file.original_filename || file.filename}
                          </p>
                          {file.file_size && (
                            <p className="text-xs text-gray-500">
                              {(file.file_size / 1024).toFixed(1)} KB
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Questions */}
          {(section.questions || []).map((question, index) => {
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
                canMoveDown={index < (section.questions?.length || 0) - 1}
                isEditingSurvey={isEditingSurvey}
                isAnnotationMode={isAnnotationMode}
                onOpenAnnotation={handleQuestionAnnotation}
                annotation={questionAnnotation}
              />
            );
          })}
          {(!section.questions || section.questions.length === 0) && 
           !(sectionIndex === 0 || section.title?.toLowerCase().includes('sample plan') || section.samplePlanData) && (
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
  onSaveTrigger?: (saveFunction: () => Promise<void>) => void;
}

export const SurveyPreview: React.FC<SurveyPreviewProps> = ({ 
  survey: propSurvey, 
  isEditable = false, 
  isInEditMode = false,
  onSurveyChange,
  onSaveAndExit,
  onCancel,
  hideHeader = false,
  hideRightPanel = false,
  onSaveTrigger
}) => {
  const { currentSurvey, isAnnotationMode, setAnnotationMode, currentAnnotations, saveAnnotations, loadAnnotations, triggerEvaluationAsync, evaluationInProgress, fetchConceptFiles, loadPillarScoresAsync } = useAppStore();
  const survey = propSurvey || currentSurvey;
  const [editedSurvey, setEditedSurvey] = useState<Survey | null>(null);
  const [isEditModeActive, setIsEditModeActive] = useState(isInEditMode);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [conceptFiles, setConceptFiles] = useState<ConceptFile[]>([]);
  
  // Track previous evaluation state to detect completion (must be at top level)
  const prevEvaluationStateRef = useRef<Record<string, boolean>>({});
  
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

  // All changes are now saved immediately, so this function just calls onSaveAndExit
  const handleSaveAllChanges = useCallback(async () => {
    console.log('🚪 [Save] All changes are already saved immediately, just exiting');
      
      // Call onSaveAndExit if provided (for separate edit route)
      if (onSaveAndExit) {
        onSaveAndExit();
      } else {
        // Fallback to old behavior (exit edit mode)
        setIsEditModeActive(false);
      }
  }, [onSaveAndExit]);

  // Expose save function to parent component - only when onSaveTrigger changes
  useEffect(() => {
    if (onSaveTrigger) {
      onSaveTrigger(handleSaveAllChanges);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onSaveTrigger]); // Intentionally exclude handleSaveAllChanges to prevent infinite loop

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
          format: 'pdf',
          filename: `survey-${surveyToDisplay.survey_id}.pdf`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to export PDF');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `survey-${surveyToDisplay.survey_id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Failed to export PDF');
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
      console.log('🔄 [Question Update] Starting update for question:', updatedQuestion.id);
      
      // First update local state
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        // Update in sections format
        updatedSurvey.sections = updatedSurvey.sections.map(section => ({
          ...section,
          questions: (section.questions || []).map(q =>
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
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      // Now save the question immediately to the backend
      console.log('💾 [Question Update] Saving question to backend:', updatedQuestion.id);
      await updateQuestion(updatedQuestion.id, updatedQuestion);
      console.log('✅ [Question Update] Question saved successfully');
      
      // Don't mark as unsaved since we just saved it
      setHasUnsavedChanges(false);
      
    } catch (error) {
      console.error('❌ [Question Update] Failed to update question:', error);
      // Mark as unsaved since the save failed
      setHasUnsavedChanges(true);
    }
  };

  const handleQuestionDelete = (questionId: string) => {
    if (editedSurvey) {
      const questions = editedSurvey.questions?.filter(q => q.id !== questionId) || [];
      setEditedSurvey({ ...editedSurvey, questions });
    }
  };

  const handleMoveQuestion = async (questionId: string, direction: 'up' | 'down') => {
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
        const questions = [...(section.questions || [])];
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
      if (onSurveyChange) onSurveyChange({ ...editedSurvey, sections: updatedSections });
      
      // Save the question reorder immediately to the backend
      console.log('💾 [Question Move] Saving question reorder to backend');
      const questionOrder = updatedSections.flatMap(s => s.questions || []).map(q => q.id);
      await reorderQuestions(questionOrder);
      console.log('✅ [Question Move] Question reorder saved successfully');
      
      // Don't mark as unsaved since we just saved it
      setHasUnsavedChanges(false);
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
        if (onSurveyChange) onSurveyChange({ ...editedSurvey, questions });
        
        // Save the question reorder immediately to the backend
        console.log('💾 [Question Move] Saving question reorder to backend (legacy format)');
        const questionOrder = questions.map(q => q.id);
        await reorderQuestions(questionOrder);
        console.log('✅ [Question Move] Question reorder saved successfully (legacy format)');
        
        // Don't mark as unsaved since we just saved it
        setHasUnsavedChanges(false);
      }
    }
  };

  // Section operation handlers
  const handleSectionUpdate = async (sectionId: number, updatedSection: SurveySection) => {
    if (!survey?.survey_id) return;
    
    try {
      console.log('🔄 [Section Update] Starting update for section:', sectionId);
      
      // First update local state
      const surveyToUpdate = editedSurvey || survey;
      let updatedSurvey = { ...surveyToUpdate };
      
      if (updatedSurvey.sections) {
        updatedSurvey.sections = updatedSurvey.sections.map(section =>
          section.id === sectionId ? updatedSection : section
        );
      }
      
      setEditedSurvey(updatedSurvey);
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      // Now save the section immediately to the backend
      console.log('💾 [Section Update] Saving section to backend:', sectionId);
      await updateSection(sectionId, updatedSection);
      console.log('✅ [Section Update] Section saved successfully');
      
      // Don't mark as unsaved since we just saved it
      setHasUnsavedChanges(false);
      
    } catch (error) {
      console.error('❌ [Section Update] Failed to update section:', error);
      // Mark as unsaved since the save failed
      setHasUnsavedChanges(true);
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
      if (onSurveyChange) onSurveyChange(updatedSurvey);
      
      // Save the section reorder immediately to the backend
      console.log('💾 [Section Move] Saving section reorder to backend');
      const sectionOrder = sections.map(s => s.id);
      await reorderSections(sectionOrder);
      console.log('✅ [Section Move] Section reorder saved successfully');
      
      // Don't mark as unsaved since we just saved it
      setHasUnsavedChanges(false);
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
              questions: [...(section.questions || []), newQuestion]
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

  // Watch for evaluation completion and refresh pillar scores
  useEffect(() => {
    const surveyId = survey?.survey_id;
    if (!surveyId || !loadPillarScoresAsync) return;

    const isEvaluating = evaluationInProgress[surveyId] || false;
    const wasEvaluating = prevEvaluationStateRef.current[surveyId] || false;
    
    // When evaluation completes (was evaluating, now not), reload pillar scores
    if (wasEvaluating && !isEvaluating) {
      // Evaluation just completed - reload pillar scores
      console.log('🔄 [SurveyPreview] Evaluation completed, reloading pillar scores for survey:', surveyId);
      loadPillarScoresAsync(surveyId).catch((error) => {
        console.error('❌ [SurveyPreview] Failed to reload pillar scores after evaluation:', error);
      });
    }
    
    // Update ref with current state
    prevEvaluationStateRef.current[surveyId] = isEvaluating;
  }, [evaluationInProgress, survey?.survey_id, loadPillarScoresAsync]);

  // Handle survey data structure
  const surveyToDisplay = editedSurvey || survey;
  const isCurrentlyEditing = isEditable || isEditModeActive;
  
  // Fetch concept files when survey has rfq_id
  useEffect(() => {
    const loadConceptFiles = async () => {
      // Check multiple sources for rfq_id
      // Also try to extract from rfq_data if available
      let rfqId = surveyToDisplay?.rfq_id || propSurvey?.rfq_id || survey?.rfq_id;
      
      // Fallback: Try to get rfq_id from rfq_data if it exists
      if (!rfqId) {
        const rfqData = surveyToDisplay?.rfq_data || propSurvey?.rfq_data || survey?.rfq_data;
        if (rfqData && (rfqData as any).rfq_id) {
          rfqId = (rfqData as any).rfq_id;
          console.log('🔍 [SurveyPreview] Found rfq_id in rfq_data:', rfqId);
        }
      }
      
      console.log('🔍 [SurveyPreview] Checking for rfq_id:', {
        surveyToDisplay_rfq_id: surveyToDisplay?.rfq_id,
        propSurvey_rfq_id: propSurvey?.rfq_id,
        survey_rfq_id: survey?.rfq_id,
        final_rfq_id: rfqId,
        surveyToDisplay_keys: surveyToDisplay ? Object.keys(surveyToDisplay) : [],
        hasFetchConceptFiles: !!fetchConceptFiles
      });
      
      if (rfqId && fetchConceptFiles) {
        try {
          console.log('🔍 [SurveyPreview] Fetching concept files for rfq_id:', rfqId);
          console.log('🔍 [SurveyPreview] Survey ID:', surveyToDisplay?.survey_id);
          const files = await fetchConceptFiles(rfqId);
          console.log('✅ [SurveyPreview] Loaded concept files:', files.length);
          if (files.length > 0) {
            console.log('📸 [SurveyPreview] Concept files details:', files.map(f => ({
              id: f.id,
              filename: f.filename,
              content_type: f.content_type,
              file_url: f.file_url
            })));
          } else {
            console.warn('⚠️ [SurveyPreview] No concept files found for rfq_id:', rfqId);
            console.warn('⚠️ [SurveyPreview] This could mean:');
            console.warn('  1. No concept files were uploaded for this RFQ');
            console.warn('  2. Concept files were uploaded but are associated with a different RFQ ID');
            console.warn('     (This can happen if the RFQ was edited/re-saved and got a new ID)');
            console.warn('  3. Concept files were uploaded before the RFQ was saved');
            console.warn('⚠️ [SurveyPreview] Solution: Re-upload concept files in the RFQ editor');
            console.warn('⚠️ [SurveyPreview] The backend logs show concept files exist but for different RFQ IDs');
          }
          setConceptFiles(files);
        } catch (error) {
          console.error('❌ [SurveyPreview] Failed to load concept files:', error);
          console.error('❌ [SurveyPreview] Error details:', error instanceof Error ? error.message : String(error));
          setConceptFiles([]);
        }
      } else {
        if (!rfqId) {
          console.log('⚠️ [SurveyPreview] No rfq_id available, clearing concept files.');
          console.log('⚠️ [SurveyPreview] Survey object:', surveyToDisplay ? {
            survey_id: surveyToDisplay.survey_id,
            title: surveyToDisplay.title,
            has_rfq_id: 'rfq_id' in (surveyToDisplay || {}),
            rfq_id_value: surveyToDisplay?.rfq_id,
            all_keys: Object.keys(surveyToDisplay)
          } : 'null');
        }
        if (!fetchConceptFiles) {
          console.warn('⚠️ [SurveyPreview] fetchConceptFiles function not available');
        }
        setConceptFiles([]);
      }
    };
    loadConceptFiles();
  }, [surveyToDisplay, propSurvey?.rfq_id, propSurvey?.rfq_data, survey?.rfq_id, survey?.rfq_data, fetchConceptFiles]);

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
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveAllChanges}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                  <span>Exit</span>
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
                      conceptFiles={conceptFiles}
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
              className="w-full flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 text-purple-600 hover:text-purple-700 border border-purple-200 rounded-lg transition-colors text-sm"
            >
              <LabelIcon className="w-4 h-4" />
              Annotate Survey
            </button>
            <button
              onClick={handleEditSurvey}
              className="w-full flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 text-blue-600 hover:text-blue-700 border border-blue-200 rounded-lg transition-colors text-sm"
            >
              <PencilIcon className="w-4 h-4" />
              Edit Survey
            </button>
            <button
              onClick={handleSaveAsReference}
              className="w-full flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 text-orange-600 hover:text-orange-700 border border-orange-200 rounded-lg transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Save as Reference
            </button>
            <button
              onClick={() => {
                if (!survey?.survey_id) {
                  alert('No survey ID available');
                  return;
                }
                window.location.href = `/surveys/${survey.survey_id}/insights`;
              }}
              className="w-full flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 text-indigo-600 hover:text-indigo-700 border border-indigo-200 rounded-lg transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              View Survey Insights
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

        {/* Evaluation Analysis Section */}
        {surveyToDisplay?.pillar_scores && Object.keys(surveyToDisplay.pillar_scores).length > 0 && (
          <div className="p-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              {(() => {
                // Determine evaluation type based on data
                const pillarScores = surveyToDisplay.pillar_scores;
                const hasValidScores = pillarScores.weighted_score !== undefined && pillarScores.weighted_score > 0;
                const isAIAnalysis = pillarScores.summary && (
                  pillarScores.summary.includes('Single-Call') || 
                  pillarScores.summary.includes('Multiple-Call') ||
                  pillarScores.summary.includes('Chain-of-Thought') ||
                  pillarScores.summary.includes('AI')
                );
                const isBasicAnalysis = pillarScores.summary && pillarScores.summary.includes('Basic');
                const isSkipped = pillarScores.summary && pillarScores.summary.includes('skipped');
                
                let evaluationType = 'Evaluation Analysis';
                let evaluationIcon = '🔍';
                let evaluationColor = 'blue';
                let evaluationDescription = 'Survey quality assessment';
                
                if (isSkipped || !hasValidScores) {
                  evaluationType = 'Evaluation Disabled';
                  evaluationIcon = '⏭️';
                  evaluationColor = 'gray';
                  evaluationDescription = 'AI evaluation was disabled for this survey';
                } else if (isAIAnalysis) {
                  evaluationType = 'AI Evaluation Analysis';
                  evaluationIcon = '🤖';
                  evaluationColor = 'blue';
                  evaluationDescription = 'AI-powered quality assessment';
                } else if (isBasicAnalysis) {
                  evaluationType = 'Basic Evaluation Analysis';
                  evaluationIcon = '📊';
                  evaluationColor = 'green';
                  evaluationDescription = 'Heuristic-based quality assessment';
                }

                const iconColorClass = evaluationColor === 'blue' ? 'bg-blue-100 text-blue-600' : 
                                     evaluationColor === 'green' ? 'bg-green-100 text-green-600' : 
                                     'bg-gray-100 text-gray-600';

                return (
                  <>
                    <div className="flex items-center gap-2 mb-4">
                      <div className={`w-6 h-6 ${iconColorClass} rounded-full flex items-center justify-center`}>
                        <span className="text-sm">{evaluationIcon}</span>
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-gray-900">{evaluationType}</h3>
                        <p className="text-xs text-gray-500">{evaluationDescription}</p>
                      </div>
                    </div>

                    {/* Overall Assessment - only show if we have valid scores */}
                    {hasValidScores && (
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-700">Overall Assessment</span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${(() => {
                            // Calculate grade if missing
                            let grade = pillarScores.overall_grade;
                            if (!grade || grade === 'N/A') {
                              const score = pillarScores.weighted_score || 0;
                              if (score >= 0.9) grade = 'A';
                              else if (score >= 0.8) grade = 'B';
                              else if (score >= 0.7) grade = 'C';
                              else if (score >= 0.6) grade = 'D';
                              else grade = 'F';
                            }
                            
                            // Return color class based on grade
                            switch (grade) {
                              case 'A': return 'bg-green-100 text-green-800';
                              case 'B': return 'bg-blue-100 text-blue-800';
                              case 'C': return 'bg-yellow-100 text-yellow-800';
                              case 'D': return 'bg-orange-100 text-orange-800';
                              default: return 'bg-red-100 text-red-800';
                            }
                          })()}`}>
                            Grade {(() => {
                              // Calculate grade if missing
                              if (pillarScores.overall_grade && pillarScores.overall_grade !== 'N/A') {
                                return pillarScores.overall_grade;
                              }
                              const score = pillarScores.weighted_score || 0;
                              if (score >= 0.9) return 'A';
                              if (score >= 0.8) return 'B';
                              if (score >= 0.7) return 'C';
                              if (score >= 0.6) return 'D';
                              return 'F';
                            })()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 mb-2">
                          {pillarScores.summary || 'Quality Assessment'} | Overall Score: {Math.round((pillarScores.weighted_score || 0) * 100)}% (Grade {(() => {
                            // Calculate grade if missing
                            if (pillarScores.overall_grade && pillarScores.overall_grade !== 'N/A') {
                              return pillarScores.overall_grade;
                            }
                            const score = pillarScores.weighted_score || 0;
                            if (score >= 0.9) return 'A';
                            if (score >= 0.8) return 'B';
                            if (score >= 0.7) return 'C';
                            if (score >= 0.6) return 'D';
                            return 'F';
                          })()})
                        </p>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-blue-600">Score: {Math.round((pillarScores.weighted_score || 0) * 100)}%</span>
                          {isAIAnalysis && (
                            <>
                              <span className="text-xs text-gray-500">•</span>
                              <span className="text-xs text-blue-600">AI-Powered Analysis</span>
                            </>
                          )}
                          {isBasicAnalysis && (
                            <>
                              <span className="text-xs text-gray-500">•</span>
                              <span className="text-xs text-green-600">Heuristic Analysis</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Show message when evaluation is disabled */}
                    {!hasValidScores && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">
                          {isSkipped ? 'AI evaluation was disabled for this survey generation.' : 'No evaluation data available for this survey.'}
                        </p>
                      </div>
                    )}
                  </>
                );
              })()}

              {/* Pillar Analysis - show if we have pillar breakdown data */}
              {(() => {
                const pillarScores = surveyToDisplay.pillar_scores;
                const hasValidScores = pillarScores.weighted_score !== undefined && pillarScores.weighted_score > 0;
                const hasPillarBreakdown = pillarScores.pillar_breakdown && Array.isArray(pillarScores.pillar_breakdown) && pillarScores.pillar_breakdown.length > 0;
                
                // Debug logging
                console.log('Pillar Analysis Debug:', {
                  hasValidScores,
                  hasPillarBreakdown,
                  pillarBreakdown: pillarScores.pillar_breakdown,
                  weightedScore: pillarScores.weighted_score
                });
                
                if (!hasPillarBreakdown) {
                  const surveyId = surveyToDisplay?.survey_id;
                  const isEvaluating = surveyId ? evaluationInProgress[surveyId] : false;
                  
                  return (
                    <div className="space-y-3 mb-4">
                      <h4 className="text-xs font-medium text-gray-900">Pillar Analysis</h4>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        {isEvaluating ? (
                          <div className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            <p className="text-sm text-gray-600">Evaluation in progress...</p>
                          </div>
                        ) : (
                          <div className="flex flex-col gap-2">
                            <p className="text-sm text-gray-600">
                              {hasValidScores ? 'Pillar breakdown data not available for this evaluation.' : 'No evaluation data available.'}
                            </p>
                            {surveyId && (
                              <button
                                onClick={() => triggerEvaluationAsync(surveyId)}
                                disabled={isEvaluating}
                                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                              >
                                <span>Run Evaluation</span>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }
                
                return (
                  <div className="space-y-3 mb-4">
                    <h4 className="text-xs font-medium text-gray-900">Pillar Analysis</h4>
                    {pillarScores.pillar_breakdown.slice(0, 3).map((pillar, index) => {
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
                );
              })()}

              {/* Recommendations - show section with helpful message if no recommendations */}
              {(() => {
                const pillarScores = surveyToDisplay.pillar_scores;
                const hasValidScores = pillarScores.weighted_score !== undefined && pillarScores.weighted_score > 0;
                const hasRecommendations = pillarScores.recommendations && pillarScores.recommendations.length > 0;
                
                return (
                  <div className="space-y-3">
                    <h4 className="text-xs font-medium text-gray-900">Recommendations</h4>
                    {hasRecommendations ? (
                      <div className="space-y-2">
                        {pillarScores.recommendations.slice(0, 4).map((recommendation, index) => {
                          const colors = ['blue', 'yellow', 'green', 'purple'] as const;
                          const color = colors[index % colors.length];
                          const colorClasses: Record<string, string> = {
                            blue: 'bg-blue-50 border-blue-200 text-blue-800',
                            yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
                            green: 'bg-green-50 border-green-200 text-green-800',
                            purple: 'bg-purple-50 border-purple-200 text-purple-800'
                          };
                          
                          return (
                            <div key={index} className={`p-2 ${colorClasses[color]} border rounded-lg`}>
                              <div className="flex items-start gap-2">
                                <div className={`w-4 h-4 bg-${color}-500 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0`}>
                                  <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                </div>
                                <p className={`text-xs ${colorClasses[color].split(' ')[2]}`}>{recommendation}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">
                          {hasValidScores ? 'No specific recommendations available for this evaluation.' : 'No evaluation data available.'}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}
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