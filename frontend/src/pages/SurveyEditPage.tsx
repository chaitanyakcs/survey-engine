import React, { useEffect, useState, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import { SurveyPreview } from '../components/SurveyPreview';
import { Survey } from '../types';

export const SurveyEditPage: React.FC = () => {
  console.log('🚀 [SurveyEditPage] Component mounted');
  const { fetchSurvey, addToast } = useAppStore();
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const saveFunctionRef = useRef<(() => Promise<void>) | null>(null);

  useEffect(() => {
    const loadSurvey = async () => {
      try {
        setLoading(true);
        setError(null);

        // Extract survey ID from URL path
        const pathParts = window.location.pathname.split('/');
        const surveyId = pathParts[2]; // /surveys/{surveyId}/edit

        if (!surveyId) {
          throw new Error('No survey ID found in URL');
        }

        console.log('🔍 [Survey Edit] Loading survey for editing:', surveyId);

        // Load survey data
        await fetchSurvey(surveyId);
        
        // Get the loaded survey from store
        const loadedSurvey = useAppStore.getState().currentSurvey;
        if (loadedSurvey) {
          setSurvey(loadedSurvey);
          console.log('✅ [Survey Edit] Survey loaded successfully');
        } else {
          throw new Error('Failed to load survey data');
        }

      } catch (err) {
        console.error('❌ [Survey Edit] Failed to load survey:', err);
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
    console.log('🔄 [Survey Edit] Survey updated:', updatedSurvey.survey_id);
    setSurvey(updatedSurvey);
  };

  const handleExit = () => {
    console.log('🚪 [Survey Edit] Exit triggered - all changes are already saved immediately');
    
    // All changes are now saved immediately when editing, so just navigate away
    if (survey?.survey_id) {
      console.log('🚪 [Survey Edit] Navigating back to read-only view');
      window.location.href = `/surveys/${survey.survey_id}`;
    } else {
      console.log('🚪 [Survey Edit] Navigating back to surveys list');
      window.location.href = '/surveys';
    }
  };

  const handleCancel = () => {
    if (survey?.survey_id) {
      console.log('❌ [Survey Edit] Cancel - navigating back to read-only view');
      window.location.href = `/surveys/${survey.survey_id}`;
    } else {
      console.log('❌ [Survey Edit] Cancel - navigating back to surveys list');
      window.location.href = '/surveys';
    }
  };

  const handleSaveTrigger = (saveFn: () => Promise<void>) => {
    console.log('🔗 [Survey Edit] Save function received from SurveyPreview');
    saveFunctionRef.current = saveFn;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading survey for editing...</p>
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
      <SurveyPreview
        survey={survey}
        onSurveyChange={handleSurveyChange}
        isInEditMode={true}
        onSaveAndExit={handleExit}
        onCancel={handleCancel}
        hideRightPanel={true}
        onSaveTrigger={handleSaveTrigger}
      />
    </div>
  );
};
