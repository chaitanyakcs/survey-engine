import React, { useEffect, useState, useMemo } from 'react';
import { useAppStore } from '../store/useAppStore';
import { SurveyPreview } from '../components/SurveyPreview';
import { Survey } from '../types';

export const SurveyViewPage: React.FC = () => {
  const { fetchSurvey, addToast, isAnnotationMode, currentAnnotations, saveAnnotations, setAnnotationMode } = useAppStore();
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSurvey = async () => {
      try {
        setLoading(true);
        setError(null);

        // Extract survey ID from URL path
        const pathParts = window.location.pathname.split('/');
        const surveyId = pathParts[2]; // /surveys/{surveyId}

        if (!surveyId) {
          throw new Error('No survey ID found in URL');
        }

        console.log('🔍 [Survey View] Loading survey for viewing:', surveyId);

        // Load survey data
        await fetchSurvey(surveyId);
        
        // Get the loaded survey from store
        const loadedSurvey = useAppStore.getState().currentSurvey;
        if (loadedSurvey) {
          setSurvey(loadedSurvey);
          console.log('✅ [Survey View] Survey loaded successfully');
        } else {
          throw new Error('Failed to load survey data');
        }

      } catch (err) {
        console.error('❌ [Survey View] Failed to load survey:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load survey';
        setError(errorMessage);
        addToast({
          type: 'error',
          title: 'Load Error',
          message: errorMessage,
          duration: 5000
        });
      } finally {
        setLoading(false);
      }
    };

    loadSurvey();
  }, [fetchSurvey, addToast]);

  const handleSurveyChange = (updatedSurvey: Survey) => {
    console.log('🔄 [Survey View] Survey updated:', updatedSurvey.survey_id);
    setSurvey(updatedSurvey);
  };

  const handleExit = async () => {
    try {
      console.log('🚪 [Survey View] Exit annotation mode triggered');
      
      // Save any pending annotations before exiting
      if (currentAnnotations && survey?.survey_id) {
        console.log('💾 Saving annotations before exiting annotation mode...');
        await saveAnnotations(currentAnnotations);
        console.log('✅ Annotations saved successfully before exit');
      }
      
      // Exit annotation mode
      setAnnotationMode(false);
      
      // Navigate to survey view (reload the same page without annotation mode)
      if (survey?.survey_id) {
        console.log('🚪 [Survey View] Navigating to survey view:', `/surveys/${survey.survey_id}`);
        window.location.href = `/surveys/${survey.survey_id}`;
      } else {
        console.log('🚪 [Survey View] No survey ID, navigating to surveys list');
        window.location.href = '/surveys';
      }
    } catch (error) {
      console.error('Error exiting annotation mode:', error);
      // Still exit even if save fails
      setAnnotationMode(false);
      if (survey?.survey_id) {
        window.location.href = `/surveys/${survey.survey_id}`;
      } else {
        window.location.href = '/surveys';
      }
    }
  };

  const handleBackToList = () => {
    console.log('🔙 [Survey View] Back to list');
    window.location.href = '/surveys';
  };

  // Calculate total questions and instructions
  const countData = useMemo(() => {
    if (!survey) return { questions: 0, instructions: 0 };
    
    let totalQuestions = 0;
    let totalInstructions = 0;
    
    if (survey.sections && survey.sections.length > 0) {
      survey.sections.forEach(section => {
        section.questions?.forEach(q => {
          if (q.type === 'instruction') {
            totalInstructions++;
          } else {
            totalQuestions++;
          }
        });
        if (section.introText?.type === 'instruction') totalInstructions++;
        if (section.closingText?.type === 'instruction') totalInstructions++;
        if (section.textBlocks) {
          totalInstructions += section.textBlocks.filter(tb => tb.type === 'instruction').length;
        }
      });
    } else if (survey.questions) {
      survey.questions.forEach(q => {
        if (q.type === 'instruction') {
          totalInstructions++;
        } else {
          totalQuestions++;
        }
      });
    }
    
    return { questions: totalQuestions, instructions: totalInstructions };
  }, [survey]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading survey...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.href = '/surveys'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Surveys
          </button>
        </div>
      </div>
    );
  }

  if (!survey) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-gray-600 text-xl mb-4">Survey not found</div>
          <button
            onClick={() => window.location.href = '/surveys'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Surveys
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen flex flex-col">
      {/* Header with conditional button (Exit in annotation mode, Back otherwise) */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {!isAnnotationMode && (
              <button
                onClick={handleBackToList}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 group"
              >
                <svg className="h-5 w-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <h1 className="text-2xl font-bold text-gray-900">
              {survey.title || 'Survey View'}
            </h1>
            {/* Total questions and instructions count */}
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
              {countData.questions} {countData.questions === 1 ? 'Question' : 'Questions'}
              {countData.instructions > 0 && (
                <> • {countData.instructions} {countData.instructions === 1 ? 'Instruction' : 'Instructions'}</>
              )}
            </span>
          </div>
          
          {/* Exit button - only show in annotation mode */}
          {isAnnotationMode && (
            <button
              onClick={handleExit}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span>Exit</span>
            </button>
          )}
        </div>
        
        {/* Regeneration Banner */}
        {survey.used_annotation_comment_ids && (
          <div className="mt-3 bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <div className="text-sm font-semibold text-purple-900">Regenerated with Annotation Comments</div>
                <div className="text-xs text-purple-700 mt-1">
                  {survey.used_annotation_comment_ids.question_annotations && survey.used_annotation_comment_ids.question_annotations.length > 0 && (
                    <span>{survey.used_annotation_comment_ids.question_annotations.length} question comment{survey.used_annotation_comment_ids.question_annotations.length !== 1 ? 's' : ''}</span>
                  )}
                  {survey.used_annotation_comment_ids.section_annotations && survey.used_annotation_comment_ids.section_annotations.length > 0 && (
                    <>
                      {survey.used_annotation_comment_ids.question_annotations && survey.used_annotation_comment_ids.question_annotations.length > 0 && ' • '}
                      <span>{survey.used_annotation_comment_ids.section_annotations.length} section comment{survey.used_annotation_comment_ids.section_annotations.length !== 1 ? 's' : ''}</span>
                    </>
                  )}
                  {survey.used_annotation_comment_ids.survey_annotations && survey.used_annotation_comment_ids.survey_annotations.length > 0 && (
                    <>
                      {((survey.used_annotation_comment_ids.question_annotations && survey.used_annotation_comment_ids.question_annotations.length > 0) || 
                        (survey.used_annotation_comment_ids.section_annotations && survey.used_annotation_comment_ids.section_annotations.length > 0)) && ' • '}
                      <span>{survey.used_annotation_comment_ids.survey_annotations.length} survey comment{survey.used_annotation_comment_ids.survey_annotations.length !== 1 ? 's' : ''}</span>
                    </>
                  )}
                  {survey.comments_addressed && survey.comments_addressed.length > 0 && (
                    <> • <span className="font-medium">{survey.comments_addressed.length} addressed by LLM</span></>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Survey Preview in read-only mode */}
      <div className="flex-1 overflow-y-auto">
        <SurveyPreview
          survey={survey}
          onSurveyChange={handleSurveyChange}
          isInEditMode={false}
          hideHeader={true}
        />
      </div>
    </div>
  );
};
