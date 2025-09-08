import React, { useEffect } from 'react';
import { useAppStore } from './store/useAppStore';
import { SurveyGeneratorPage, SurveyPreviewPage } from './pages';
import { RulesPage } from './pages/RulesPage';
import { SurveysPage } from './pages/SurveysPage';
import { ToastContainer } from './components/Toast';

function App() {
  const { toasts, removeToast, currentSurvey, workflow } = useAppStore();
  
  // Simple routing based on URL path
  const getCurrentPage = () => {
    const path = window.location.pathname;
    if (path === '/preview') {
      return 'preview';
    }
    if (path === '/rules') {
      return 'rules';
    }
    if (path === '/surveys') {
      return 'surveys';
    }
    return 'generator';
  };

  const currentPage = getCurrentPage();


  // Load survey from URL parameters when on preview page
  useEffect(() => {
    if (currentPage === 'preview') {
      const urlParams = new URLSearchParams(window.location.search);
      const surveyId = urlParams.get('surveyId');
      
      console.log('🔍 [App] Preview page loaded, survey ID from URL:', surveyId);
      
      if (surveyId && surveyId !== 'undefined' && surveyId !== 'null' && !currentSurvey) {
        console.log('📥 [App] Loading survey from URL parameter:', surveyId);
        useAppStore.getState().fetchSurvey(surveyId);
      } else if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
        console.log('⚠️ [App] No valid survey ID found in URL parameters');
      } else if (currentSurvey) {
        console.log('✅ [App] Survey already loaded, skipping fetch');
      }
    }
  }, [currentPage, currentSurvey]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Route to appropriate page */}
      {currentPage === 'preview' ? (
        <SurveyPreviewPage />
      ) : currentPage === 'rules' ? (
        <RulesPage />
      ) : currentPage === 'surveys' ? (
        <SurveysPage />
      ) : (
        <SurveyGeneratorPage />
      )}
    </div>
  );
}

export default App;