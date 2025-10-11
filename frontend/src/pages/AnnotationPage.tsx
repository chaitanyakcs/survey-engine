import React, { useEffect, useState, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import AnnotationMode from '../components/AnnotationMode';

const AnnotationPage: React.FC = () => {
  const { 
    currentSurvey, 
    currentAnnotations, 
    loadAnnotations, 
    saveAnnotations,
    addToast 
  } = useAppStore();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasLoaded = useRef(false);

  // Extract survey ID from URL
  const surveyId = window.location.pathname.split('/')[2];

  useEffect(() => {
    const loadSurveyData = async () => {
      if (!surveyId) {
        setError('No survey ID provided');
        setLoading(false);
        return;
      }

      // Prevent multiple loads
      if (hasLoaded.current) {
        return;
      }

      try {
        setLoading(true);
        setError(null);
        hasLoaded.current = true;
        
        // Load annotations for this survey
        await loadAnnotations(surveyId);
        
        // If no current survey is loaded, load it from the API
        if (!currentSurvey || currentSurvey.survey_id !== surveyId) {
          console.log('Loading survey data for ID:', surveyId);
          
          // Fetch survey data from API
          const response = await fetch(`/api/v1/survey/${surveyId}`);
          if (!response.ok) {
            throw new Error(`Failed to load survey: ${response.statusText}`);
          }
          
          const surveyData = await response.json();
          console.log('Loaded survey data:', surveyData);
          
          // Set the survey in the store
          const { setSurvey } = useAppStore.getState();
          setSurvey(surveyData);
        }
        
      } catch (err) {
        console.error('Failed to load survey data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load survey data');
        addToast({
          type: 'error',
          title: 'Load Error',
          message: 'Failed to load survey data for annotation',
          duration: 5000
        });
      } finally {
        setLoading(false);
      }
    };

    loadSurveyData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [surveyId]); // Only depend on surveyId to prevent infinite loop

  const handleQuestionAnnotation = async (annotation: any) => {
    try {
      if (!currentAnnotations) {
        throw new Error('No current annotations available');
      }

      // Update the question annotation in the current annotations
      const updatedAnnotations = {
        ...currentAnnotations,
        questionAnnotations: currentAnnotations.questionAnnotations.map(qa => 
          qa.questionId === annotation.questionId ? annotation : qa
        ).concat(
          currentAnnotations.questionAnnotations.find(qa => qa.questionId === annotation.questionId) 
            ? [] 
            : [annotation]
        )
      };

      await saveAnnotations(updatedAnnotations);
      addToast({
        type: 'success',
        title: 'Annotation Saved',
        message: 'Question annotation saved successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to save question annotation:', error);
      addToast({
        type: 'error',
        title: 'Save Error',
        message: 'Failed to save question annotation',
        duration: 5000
      });
    }
  };

  const handleSectionAnnotation = async (annotation: any) => {
    try {
      if (!currentAnnotations) {
        throw new Error('No current annotations available');
      }

      // Update the section annotation in the current annotations
      const updatedAnnotations = {
        ...currentAnnotations,
        sectionAnnotations: currentAnnotations.sectionAnnotations.map(sa => 
          sa.sectionId === annotation.sectionId ? annotation : sa
        ).concat(
          currentAnnotations.sectionAnnotations.find(sa => sa.sectionId === annotation.sectionId) 
            ? [] 
            : [annotation]
        )
      };

      await saveAnnotations(updatedAnnotations);
      addToast({
        type: 'success',
        title: 'Annotation Saved',
        message: 'Section annotation saved successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to save section annotation:', error);
      addToast({
        type: 'error',
        title: 'Save Error',
        message: 'Failed to save section annotation',
        duration: 5000
      });
    }
  };

  const handleSurveyLevelAnnotation = async (annotation: any) => {
    try {
      if (!currentAnnotations) {
        throw new Error('No current annotations available');
      }

      // Update the survey-level annotation in the current annotations
      const updatedAnnotations = {
        ...currentAnnotations,
        surveyLevelAnnotation: annotation
      };

      await saveAnnotations(updatedAnnotations);
      addToast({
        type: 'success',
        title: 'Annotation Saved',
        message: 'Survey-level annotation saved successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to save survey-level annotation:', error);
      addToast({
        type: 'error',
        title: 'Save Error',
        message: 'Failed to save survey-level annotation',
        duration: 5000
      });
    }
  };

  const handleExitAnnotationMode = () => {
    // Navigate back to the survey preview or generator
    window.history.back();
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading survey for annotation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Survey</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!currentSurvey) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 text-6xl mb-4">📋</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Survey Not Found</h2>
          <p className="text-gray-600 mb-4">The requested survey could not be loaded.</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <AnnotationMode
      survey={currentSurvey}
      currentAnnotations={currentAnnotations}
      onQuestionAnnotation={handleQuestionAnnotation}
      onSectionAnnotation={handleSectionAnnotation}
      onSurveyLevelAnnotation={handleSurveyLevelAnnotation}
      onExitAnnotationMode={handleExitAnnotationMode}
    />
  );
};

export default AnnotationPage;
