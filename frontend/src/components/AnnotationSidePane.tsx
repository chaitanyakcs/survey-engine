import React, { useEffect } from 'react';
import { TagIcon } from '@heroicons/react/24/outline';
import { QuestionAnnotation, SectionAnnotation, SurveyLevelAnnotation } from '../types';
import QuestionAnnotationPanel from './QuestionAnnotationPanel';
import SectionAnnotationPanel from './SectionAnnotationPanel';
import SurveyLevelAnnotationPanel from './SurveyLevelAnnotationPanel';

interface AnnotationSidePaneProps {
  annotationType: 'question' | 'section' | 'survey' | null;
  annotationTarget: any; // question, section, or survey object
  currentAnnotations: any;
  onQuestionAnnotation: (annotation: QuestionAnnotation) => void;
  onSectionAnnotation: (annotation: SectionAnnotation) => void;
  onSurveyLevelAnnotation?: (annotation: SurveyLevelAnnotation) => void;
}

export const AnnotationSidePane: React.FC<AnnotationSidePaneProps> = ({
  annotationType,
  annotationTarget,
  currentAnnotations,
  onQuestionAnnotation,
  onSectionAnnotation,
  onSurveyLevelAnnotation
}) => {
  // Log when props change to track data flow
  useEffect(() => {
    console.log('🔍 [AnnotationSidePane] Props changed:', {
      annotationType,
      annotationTargetId: annotationTarget?.id || annotationTarget?.question_id,
      annotationTargetLabels: annotationTarget?.labels,
      hasCurrentAnnotations: !!currentAnnotations
    });
  }, [annotationType, annotationTarget, currentAnnotations]);

  const getAnnotationData = () => {
    if (!annotationTarget) return null;

    switch (annotationType) {
      case 'question':
        console.log('🔍 [AnnotationSidePane] Looking for annotation for question:', {
          questionId: annotationTarget.id,
          questionLabels: annotationTarget.labels,
          availableAnnotations: currentAnnotations?.questionAnnotations?.map((qa: QuestionAnnotation) => qa.questionId)
        });
        const foundAnnotation = currentAnnotations?.questionAnnotations?.find(
          (qa: QuestionAnnotation) => qa.questionId === annotationTarget.id
        );
        console.log('🔍 [AnnotationSidePane] Found annotation:', {
          found: !!foundAnnotation,
          annotationLabels: foundAnnotation?.labels
        });
        return foundAnnotation;
      case 'section':
        return currentAnnotations?.sectionAnnotations?.find(
          (sa: SectionAnnotation) => sa.sectionId === String(annotationTarget.id)
        );
      case 'survey':
        return currentAnnotations?.surveyLevelAnnotation;
      default:
        return null;
    }
  };

  const renderAnnotationContent = () => {
    console.log('🔍 [AnnotationSidePane] renderAnnotationContent called with:', {
      annotationTarget,
      annotationType,
      hasAnnotationTarget: !!annotationTarget,
      hasAnnotationType: !!annotationType
    });
    
    if (!annotationTarget || !annotationType) {
      console.log('🔍 [AnnotationSidePane] No annotation target or type, showing placeholder');
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <TagIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select an Item to Annotate</h3>
            <p className="text-gray-500">Click on a question, section, or survey to start annotating</p>
          </div>
        </div>
      );
    }

    const annotation = getAnnotationData();
    console.log('🔍 [AnnotationSidePane] getAnnotationData() returned:', annotation);

    switch (annotationType) {
      case 'question':
        console.log('🔍 [AnnotationSidePane] Rendering QuestionAnnotationPanel with:', {
          question: annotationTarget,
          annotation: annotation,
          questionLabels: annotationTarget?.labels
        });
        return (
          <QuestionAnnotationPanel
            question={annotationTarget}
            annotation={annotation}
            onSave={onQuestionAnnotation}
            onCancel={() => {}} // No cancel needed in fixed pane
          />
        );
      case 'section':
        return (
          <SectionAnnotationPanel
            section={annotationTarget}
            annotation={annotation}
            onSave={onSectionAnnotation}
            onCancel={() => {}} // No cancel needed in fixed pane
          />
        );
      case 'survey':
        return (
          <SurveyLevelAnnotationPanel
            surveyId={annotationTarget.survey_id || annotationTarget.id || 'unknown'}
            annotation={annotation}
            onSave={(annotation) => {
              if (onSurveyLevelAnnotation) {
                onSurveyLevelAnnotation(annotation);
              }
            }}
            onCancel={() => {}} // No cancel needed in fixed pane
            isModal={false} // Render as pane content, not modal
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-full bg-white flex flex-col">
      {/* Content - No header needed, panels have their own */}
      <div className="flex-1 overflow-y-auto">
        {renderAnnotationContent()}
      </div>
    </div>
  );
};

export default AnnotationSidePane;
