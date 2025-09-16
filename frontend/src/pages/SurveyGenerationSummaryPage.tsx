import React, { useEffect, useState } from 'react';
import { SurveyGenerationSummary } from '../components/SurveyGenerationSummary';
import { Survey } from '../types';

export const SurveyGenerationSummaryPage: React.FC = () => {
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [pillarScores, setPillarScores] = useState(null);
  const [loading, setLoading] = useState(true);
  const [surveyId, setSurveyId] = useState<string | null>(null);

  useEffect(() => {
    // Extract survey ID from URL path
    const path = window.location.pathname;
    const id = path.split('/summary/')[1];
    setSurveyId(id);

    const fetchSurveyData = async () => {
      if (!id) {
        setLoading(false);
        return;
      }

      try {
        // Fetch survey data
        const surveyResponse = await fetch(`/api/v1/survey/${id}`);
        if (surveyResponse.ok) {
          const surveyData = await surveyResponse.json();
          setSurvey(surveyData);
        } else {
          console.error('Failed to fetch survey:', surveyResponse.status);
          setLoading(false);
          return;
        }

        // Fetch pillar scores
        const pillarResponse = await fetch(`/api/v1/pillar-scores/${id}`);
        if (pillarResponse.ok) {
          const scores = await pillarResponse.json();
          setPillarScores(scores);
        }
      } catch (error) {
        console.error('Failed to fetch survey data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSurveyData();
  }, []);

  const handleViewSurvey = () => {
    if (surveyId) {
      window.location.href = `/preview?surveyId=${surveyId}`;
    } else {
      window.location.href = '/surveys';
    }
  };

  const handleEditSurvey = () => {
    if (surveyId) {
      window.location.href = `/preview?surveyId=${surveyId}&edit=true`;
    }
  };

  const handleStartNew = () => {
    window.location.href = '/';
  };

  if (!loading && !survey) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🤔</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No Survey Found</h2>
          <p className="text-gray-600 mb-8">We couldn't find the survey you're looking for.</p>
          <button
            onClick={() => window.location.href = '/'}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-xl"
          >
            Generate New Survey
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-emerald-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AI analysis results...</p>
        </div>
      </div>
    );
  }

  return (
    <SurveyGenerationSummary
      survey={survey!}
      pillarScores={pillarScores}
      onViewSurvey={handleViewSurvey}
      onEditSurvey={handleEditSurvey}
      onStartNew={handleStartNew}
    />
  );
};