import React, { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon, TagIcon } from '@heroicons/react/24/outline';
import {
  QuestionAnnotation,
  SectionAnnotation,
  SurveyLevelAnnotation
} from '../types';
import { useAppStore } from '../store/useAppStore';
import AnnotationSidePane from './AnnotationSidePane';

interface AnnotationModeProps {
  survey: any;
  currentAnnotations: any;
  onQuestionAnnotation: (annotation: QuestionAnnotation) => void;
  onSectionAnnotation: (annotation: SectionAnnotation) => void;
  onSurveyLevelAnnotation?: (annotation: SurveyLevelAnnotation) => void;
  onExitAnnotationMode: () => void;
}

const AnnotationMode: React.FC<AnnotationModeProps> = ({
  survey,
  currentAnnotations,
  onQuestionAnnotation,
  onSectionAnnotation,
  onSurveyLevelAnnotation,
  onExitAnnotationMode
}) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  
  // Annotation fixed pane state
  const [annotationPane, setAnnotationPane] = useState({
    type: null as 'question' | 'section' | 'survey' | null,
    target: null as any
  });
  
  // Debug: Log survey data structure
  console.log('🔍 [AnnotationMode] Survey data:', survey);
  console.log('🔍 [AnnotationMode] Survey sections:', survey?.sections);
  console.log('🔍 [AnnotationMode] Survey questions:', survey?.questions);
  console.log('🔍 [AnnotationMode] Survey final_output:', survey?.final_output);
  console.log('🔍 [AnnotationMode] Current annotations:', currentAnnotations);
  console.log('🔍 [AnnotationMode] Question annotations count:', currentAnnotations?.questionAnnotations?.length);
  console.log('🔍 [AnnotationMode] Section annotations count:', currentAnnotations?.sectionAnnotations?.length);
  
  // Handle nested survey data structure
  const actualSurvey = survey?.final_output || survey;
  console.log('🔍 [AnnotationMode] Actual survey data:', actualSurvey);
  console.log('🔍 [AnnotationMode] Actual survey sections:', actualSurvey?.sections);
  console.log('🔍 [AnnotationMode] Actual survey questions:', actualSurvey?.questions);
  
  // Handle both sections format and legacy questions format
  const hasSections = actualSurvey?.sections && actualSurvey.sections.length > 0;
  const hasQuestions = actualSurvey?.questions && actualSurvey.questions.length > 0;
  
  console.log('🔍 [AnnotationMode] Has sections:', hasSections);
  console.log('🔍 [AnnotationMode] Has questions:', hasQuestions);
  
  // If no sections but has questions, create a default section
  const sectionsToUse = hasSections ? actualSurvey.sections : (hasQuestions ? [{
    id: 'default',
    title: 'Survey Questions',
    description: 'All survey questions',
    questions: actualSurvey.questions
  }] : []);
  
  console.log('🔍 [AnnotationMode] Sections to use:', sectionsToUse);
  
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(sectionsToUse.map((s: any) => String(s.id || s.section_id))));
  
  // Use global state for selected question
  const selectedQuestion = selectedQuestionId;
  console.log('🔍 [AnnotationMode] Current selectedQuestion:', selectedQuestion);
  console.log('🔍 [AnnotationMode] Current annotationPane:', annotationPane);

  // When a question is selected, open fixed pane
  const handleQuestionSelect = (questionId: string) => {
    console.log('🔍 [AnnotationMode] Question selected:', questionId);
    const question = sectionsToUse.flatMap((s: any) => s.questions || []).find((q: any) => (q.question_id || q.id) === questionId);
    if (question) {
      // Update global selected question state
      setSelectedQuestion(questionId);
      setAnnotationPane({
        type: 'question',
        target: question
      });
    }
  };

  // When a section is selected, open fixed pane
  const handleSectionSelect = (sectionId: string) => {
    console.log('🔍 [AnnotationMode] Section selected:', sectionId);
    const section = sectionsToUse.find((s: any) => String(s.id || s.section_id) === sectionId);
    console.log('🔍 [AnnotationMode] Found section:', section);
    console.log('🔍 [AnnotationMode] Section ID structure:', section?.id, section?.section_id);
    if (section) {
      // Clear any selected question when selecting a section
      setSelectedQuestion(undefined);
      setAnnotationPane({
        type: 'section',
        target: section
      });
      console.log('🔍 [AnnotationMode] Set annotationPane to section:', section);
    }
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getQuestionAnnotation = (questionId: string) => {
    console.log('🔍 [AnnotationMode] Getting annotation for question:', questionId);
    console.log('🔍 [AnnotationMode] Current annotations:', currentAnnotations);
    console.log('🔍 [AnnotationMode] Question annotations:', currentAnnotations?.questionAnnotations);
    
    if (!currentAnnotations?.questionAnnotations) {
      console.log('🔍 [AnnotationMode] No question annotations available');
      return undefined;
    }
    
    // Handle both simple and prefixed question IDs
    const annotation = currentAnnotations.questionAnnotations.find((qa: QuestionAnnotation) => {
      // Direct match
      if (qa.questionId === questionId) {
        console.log('🔍 [AnnotationMode] Direct match found:', qa.questionId, 'AI:', qa.aiGenerated);
        return true;
      }
      // Match with survey ID prefix (if we have survey ID)
      if (survey?.survey_id && qa.questionId === `${survey.survey_id}_${questionId}`) {
        console.log('🔍 [AnnotationMode] Prefixed match found:', qa.questionId, 'AI:', qa.aiGenerated);
        return true;
      }
      // Match after removing survey ID prefix
      if (qa.questionId?.endsWith(`_${questionId}`)) {
        console.log('🔍 [AnnotationMode] Suffix match found:', qa.questionId, 'AI:', qa.aiGenerated);
        return true;
      }
      return false;
    });
    
    console.log('🔍 [AnnotationMode] Final annotation result:', annotation);
    return annotation;
  };

  const getSectionAnnotation = (sectionId: string) => {
    return currentAnnotations?.sectionAnnotations?.find((sa: SectionAnnotation) => sa.sectionId === sectionId);
  };


  return (
    <div className="w-full h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
            <h2 className="heading-3">Annotation Mode</h2>
            <div className="text-sm text-gray-500">
              {sectionsToUse.reduce((total: number, section: any) => total + (section.questions?.length || 0), 0)} questions • {sectionsToUse.length} sections
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onExitAnnotationMode}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
            >
              Save and Exit
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Survey Structure (45%) */}
        <div className="w-[45%] bg-white overflow-y-auto">
          <div className="p-4">
            <h3 
              className="heading-4 mb-4 cursor-pointer hover:text-primary-600 transition-colors flex items-center gap-2"
              onClick={() => setAnnotationPane({ type: 'survey', target: survey })}
            >
              Survey Structure
              <TagIcon className="w-4 h-4" />
            </h3>
            <div className="space-y-2">
              {sectionsToUse.map((section: any) => {
                const sectionId = String(section.id || section.section_id);
                return (
                <div key={sectionId} className={`border rounded-lg transition-all duration-200 ${
                  'border-gray-200 hover:border-gray-300'
                }`}>
                  {/* Section Header */}
                  <div className={`flex items-center justify-between p-3 transition-colors ${
                    (() => {
                      const targetSectionId = String(annotationPane.target?.id || annotationPane.target?.section_id);
                      const isSelected = annotationPane.type === 'section' && targetSectionId === sectionId;
                      console.log('🔍 [AnnotationMode] Section highlighting check:', {
                        sectionId,
                        annotationPaneType: annotationPane.type,
                        annotationPaneTargetId: annotationPane.target?.id,
                        annotationPaneTargetSectionId: annotationPane.target?.section_id,
                        targetSectionId,
                        isSelected
                      });
                      return isSelected;
                    })()
                      ? 'bg-amber-50 border-l-2 border-amber-300 shadow-sm ring-1 ring-amber-200'
                      : 'hover:bg-gray-50'
                  }`}>
                    <div 
                      className="flex items-center space-x-2 cursor-pointer flex-1"
                      onClick={() => handleSectionSelect(sectionId)}
                    >
                      <span className={`font-medium transition-colors ${
                        (() => {
                          const targetSectionId = String(annotationPane.target?.id || annotationPane.target?.section_id);
                          const isSelected = annotationPane.type === 'section' && targetSectionId === sectionId;
                          return isSelected;
                        })()
                          ? 'text-amber-800 font-semibold'
                          : 'text-gray-900'
                      }`}>{section.title}</span>
                      {(() => {
                        const annotation = getSectionAnnotation(sectionId);
                        if (annotation) {
                          if (annotation.aiGenerated) {
                            return (
                              <div className="flex items-center space-x-1 flex-shrink-0 ml-2">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  🤖 AI
                                </span>
                                {annotation.aiConfidence && (
                                  <span className="text-xs text-blue-600">
                                    {Math.round(annotation.aiConfidence * 100)}%
                                  </span>
                                )}
                              </div>
                            );
                          } else {
                            return (
                              <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                            );
                          }
                        }
                        return null;
                      })()}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSection(sectionId);
                      }}
                      className={`p-1 rounded transition-colors ${
                        'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {expandedSections.has(sectionId) ? (
                        <ChevronDownIcon className="w-4 h-4" />
                      ) : (
                        <ChevronRightIcon className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Section Questions */}
                  {expandedSections.has(sectionId) && (
                    <div className="border-t border-gray-200 bg-gray-50">
                      {section.questions && section.questions.length > 0 ? (
                        section.questions.map((question: any) => {
                          const questionId = question.question_id || question.id;
                          return (
                            <div 
                              key={questionId}
                              className={`flex items-center justify-between p-3 cursor-pointer transition-all duration-200 ${
                                selectedQuestion === questionId
                                  ? 'bg-amber-50 border-l-2 border-amber-300 shadow-sm ring-1 ring-amber-200'
                                  : 'hover:bg-gray-100'
                              }`}
                              onClick={() => handleQuestionSelect(questionId)}
                            >
                              <div className="flex items-center space-x-2 flex-1 min-w-0">
                                {selectedQuestion === questionId && (
                                  <div className="w-1 h-6 bg-amber-400 rounded-full flex-shrink-0"></div>
                                )}
                                <span className={`text-sm transition-colors flex-1 min-w-0 ${
                                  selectedQuestion === questionId
                                    ? 'text-amber-800 font-semibold'
                                    : 'text-gray-700'
                                }`}>
                                  {(() => {
                                    const fullText = question.question_text || question.text || 'No text';
                                    const words = fullText.split(' ');
                                    return words.length > 30 ? words.slice(0, 30).join(' ') + '...' : fullText;
                                  })()}
                                </span>
                                {(() => {
                                  const annotation = getQuestionAnnotation(questionId);
                                  if (annotation) {
                                    if (annotation.aiGenerated) {
                                      return (
                                        <div className="flex items-center space-x-1 flex-shrink-0 ml-2">
                                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                            🤖 AI
                                          </span>
                                          {annotation.aiConfidence && (
                                            <span className="text-xs text-blue-600">
                                              {Math.round(annotation.aiConfidence * 100)}%
                                            </span>
                                          )}
                                        </div>
                                      );
                                    } else {
                                      return (
                                        <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0 ml-2"></div>
                                      );
                                    }
                                  }
                                  return null;
                                })()}
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-4 text-center text-gray-500">
                          <p className="text-sm">No questions in this section</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Panel - Annotation Pane (55%) */}
        <div className="w-[55%]">
          <AnnotationSidePane
            annotationType={annotationPane.type}
            annotationTarget={annotationPane.target}
            currentAnnotations={currentAnnotations}
            onQuestionAnnotation={onQuestionAnnotation}
            onSectionAnnotation={onSectionAnnotation}
            onSurveyLevelAnnotation={onSurveyLevelAnnotation}
          />
        </div>
      </div>

    </div>
  );
};

export default AnnotationMode;