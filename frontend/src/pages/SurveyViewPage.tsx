import React, { useEffect, useState, useMemo } from 'react';
import { useAppStore } from '../store/useAppStore';
import { SurveyPreview } from '../components/SurveyPreview';
import { Survey } from '../types';

export const SurveyViewPage: React.FC = () => {
  const { fetchSurvey, addToast } = useAppStore();
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
      {/* Header with Back button only */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBackToList}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 group"
          >
            <svg className="h-5 w-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
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
