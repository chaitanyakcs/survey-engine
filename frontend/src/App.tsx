import React, { useEffect } from 'react';
import { useAppStore } from './store/useAppStore';
import { SurveyGeneratorPage, SurveyPreviewPage, GoldenExamplesPage } from './pages';
import { RulesPage } from './pages/RulesPage';
import { SettingsPage } from './pages/SettingsPage';
import { SurveysPage } from './pages/SurveysPage';
import { GoldenExampleEditPage } from './pages/GoldenExampleEditPage';
import { GoldenExampleCreatePage } from './pages/GoldenExampleCreatePage';
import AnnotationPage from './pages/AnnotationPage';
import { LLMAuditViewer } from './components/LLMAuditViewer';
import { AnnotationInsightsDashboard } from './components/AnnotationInsightsDashboard';
import { ToastContainer } from './components/Toast';
import { SidebarProvider } from './contexts/SidebarContext';

function App() {
  const { toasts, removeToast, currentSurvey, recoverWorkflowState, restoreDocumentProcessingState, restoreEnhancedRfqState, restoreGoldenExampleState } = useAppStore();
  
  // Simple routing based on URL path
  const getCurrentPage = () => {
    const path = window.location.pathname;
    if (path === '/preview') {
      return 'preview';
    }
    if (path === '/rules') {
      return 'rules';
    }
    if (path === '/settings') {
      return 'settings';
    }
    if (path === '/surveys') {
      return 'surveys';
    }
    if (path === '/golden-examples') {
      return 'golden-examples';
    }
    if (path.startsWith('/golden-examples/') && path.includes('/edit')) {
      return 'golden-edit';
    }
    if (path === '/golden-examples/new') {
      return 'golden-create';
    }
    if (path === '/llm-audit') {
      return 'llm-audit';
    }
    if (path.startsWith('/llm-audit/survey/')) {
      return 'llm-audit-survey';
    }
    if (path === '/annotation-insights') {
      return 'annotation-insights';
    }
    if (path.startsWith('/annotations/')) {
      return 'annotations';
    }
    return 'generator';
  };

  const currentPage = getCurrentPage();


  // Initialize app and recover any pending workflows/reviews and document state
  useEffect(() => {
    recoverWorkflowState();
    restoreDocumentProcessingState();
    restoreEnhancedRfqState(false); // Restore without showing toast on app load
    restoreGoldenExampleState(); // Add this
  }, [recoverWorkflowState, restoreDocumentProcessingState, restoreEnhancedRfqState, restoreGoldenExampleState]);

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
    <SidebarProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Toast Container */}
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        
        {/* Route to appropriate page */}
        {currentPage === 'preview' ? (
          <SurveyPreviewPage />
        ) : currentPage === 'rules' ? (
          <RulesPage />
        ) : currentPage === 'settings' ? (
          <SettingsPage />
        ) : currentPage === 'surveys' ? (
          <SurveysPage />
        ) : currentPage === 'golden-examples' ? (
          <GoldenExamplesPage />
        ) : currentPage === 'golden-edit' ? (
          <GoldenExampleEditPage />
        ) : currentPage === 'golden-create' ? (
          <GoldenExampleCreatePage />
        ) : currentPage === 'llm-audit' ? (
          <LLMAuditViewer 
            title="LLM Audit Dashboard"
            showSummary={true}
            onClose={() => window.history.back()}
          />
        ) : currentPage === 'llm-audit-survey' ? (
          <LLMAuditViewer 
            surveyId={window.location.pathname.split('/')[3]}
            title="Survey LLM Audit"
            showSummary={true}
            onClose={() => window.history.back()}
          />
        ) : currentPage === 'annotation-insights' ? (
          <AnnotationInsightsDashboard />
        ) : currentPage === 'annotations' ? (
          <AnnotationPage />
        ) : (
          <SurveyGeneratorPage />
        )}
      </div>
    </SidebarProvider>
  );
}

export default App;