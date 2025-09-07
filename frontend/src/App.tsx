import React, { useEffect } from 'react';
import { useAppStore } from './store/useAppStore';
import { SurveyGeneratorPage, SurveyPreviewPage } from './pages';
import { ToastContainer } from './components/Toast';

function App() {
  const { toasts, removeToast, currentSurvey, workflow, getStoredSurveyId, clearStoredSurveyId } = useAppStore();
  
  // Simple routing based on URL path
  const getCurrentPage = () => {
    const path = window.location.pathname;
    if (path === '/preview') {
      return 'preview';
    }
    return 'generator';
  };

  const currentPage = getCurrentPage();

  // Clear localStorage on app load if we're on the generator page (fresh start)
  useEffect(() => {
    if (currentPage === 'generator' && !workflow.status) {
      console.log('🧹 [App] Clearing localStorage on fresh generator page load');
      clearStoredSurveyId();
    }
  }, [currentPage, workflow.status, clearStoredSurveyId]);

  // Auto-redirect to preview when survey is completed AND loaded
  useEffect(() => {
    console.log('🔍 [App] State check:', { 
      workflowStatus: workflow.status, 
      hasSurvey: !!currentSurvey, 
      surveyId: currentSurvey?.survey_id,
      currentPath: window.location.pathname 
    });
    
    // Only redirect if:
    // 1. Workflow is completed
    // 2. We have a survey with a valid ID (from state or localStorage)
    // 3. We're not already on the preview page
    if (workflow.status === 'completed' && window.location.pathname !== '/preview') {
      let surveyId = currentSurvey?.survey_id;
      
      // If no survey in state, try localStorage
      if (!surveyId || surveyId === 'undefined') {
        surveyId = getStoredSurveyId() || undefined;
        console.log('🔄 [App] Using survey ID from localStorage:', surveyId);
      }
      
      if (surveyId && surveyId !== 'undefined' && surveyId !== 'null') {
        console.log('🚀 [App] Auto-redirecting to preview page with survey ID:', surveyId);
        window.location.href = `/preview?surveyId=${surveyId}`;
      } else if (!currentSurvey) {
        console.log('⏳ [App] Workflow completed but no survey ID available, waiting...');
      } else {
        console.log('⚠️ [App] Workflow completed but survey ID is invalid:', surveyId);
      }
    }
  }, [workflow.status, currentSurvey, getStoredSurveyId]);

  // Load survey from URL parameters or localStorage when on preview page
  useEffect(() => {
    if (currentPage === 'preview') {
      // Debug URL parsing
      const currentUrl = window.location.href;
      const search = window.location.search;
      const urlParams = new URLSearchParams(search);
      const surveyIdFromUrl = urlParams.get('surveyId');
      
      // Get survey ID from URL or localStorage
      let surveyId: string | null = surveyIdFromUrl;
      if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
        surveyId = getStoredSurveyId();
        console.log('🔄 [App] Using survey ID from localStorage:', surveyId);
      }
      
      console.log('🔍 [App] Preview page loaded, checking for survey ID:', {
        currentUrl: currentUrl,
        search: search,
        surveyIdFromUrl: surveyIdFromUrl,
        surveyIdFromStorage: getStoredSurveyId(),
        finalSurveyId: surveyId,
        hasCurrentSurvey: !!currentSurvey,
        urlParamsEntries: Array.from(urlParams.entries())
      });
      
      if (surveyId && surveyId !== 'undefined' && surveyId !== 'null' && !currentSurvey) {
        console.log('📥 [App] Loading survey from ID:', surveyId);
        useAppStore.getState().fetchSurvey(surveyId);
      } else if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
        console.log('⚠️ [App] No valid survey ID found in URL parameters or localStorage');
      } else if (currentSurvey) {
        console.log('✅ [App] Survey already loaded, skipping fetch');
      }
    }
  }, [currentPage, currentSurvey, getStoredSurveyId]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Route to appropriate page */}
      {currentPage === 'preview' ? (
        <SurveyPreviewPage />
      ) : (
        <SurveyGeneratorPage />
      )}
    </div>
  );
}

export default App;