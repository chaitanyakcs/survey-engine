import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { SurveyGenerationIndicator } from '../components/SurveyGenerationIndicator';
import { useAppStore } from '../store/useAppStore';
import { SurveyListItem, Survey } from '../types';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

// Helper function to get sections count from survey
const getSectionsCount = (survey: Survey | null | undefined): number => {
  if (!survey) return 1;
  
  // Check if survey has sections
  if (survey.sections && survey.sections.length > 0) {
    return survey.sections.length;
  }
  
  // If no sections but has questions, treat as 1 section
  if (survey.questions && survey.questions.length > 0) {
    return 1;
  }
  
  // Default fallback
  return 1;
};

export const SurveysPage: React.FC = () => {
  const { setSurvey, setRFQInput, toasts, removeToast, addToast, workflow, currentSurvey } = useAppStore();
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [selectedSurvey, setSelectedSurvey] = useState<SurveyListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { mainContentClasses } = useSidebarLayout();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [selectedSurveys, setSelectedSurveys] = useState<Set<string>>(new Set());
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);
  const [currentUrl, setCurrentUrl] = useState(window.location.search);
  const [isRetrying, setIsRetrying] = useState(false);

  const fetchSurveys = useCallback(async (isRetry = false) => {
    try {
      if (isRetry) {
        setIsRetrying(true);
        addToast({
          type: 'info',
          title: 'Retrying...',
          message: 'Attempting to fetch surveys again. Please wait.',
          duration: 3000
        });
      } else {
        setLoading(true);
      }
      
      console.log('📡 [Fetch] Starting to fetch surveys from /api/v1/survey/list');
      const response = await fetch('/api/v1/survey/list');
      console.log('📡 [Fetch] Response status:', response.status);
      if (!response.ok) throw new Error('Failed to fetch surveys');
      
      const data = await response.json();
      console.log('📡 [Fetch] Survey list data:', data);
      console.log('📡 [Fetch] Number of surveys:', data.length);
      console.log('📡 [Fetch] First survey (if any):', data[0]);
      setSurveys(data);
      setError(null);
      
      if (isRetry) {
        addToast({
          type: 'success',
          title: 'Surveys Loaded Successfully',
          message: 'Surveys have been fetched and loaded successfully.',
          duration: 5000
        });
      }
    } catch (err) {
      console.error('❌ [Fetch] Error fetching surveys:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch surveys';
      setError(errorMessage);
      
      addToast({
        type: 'error',
        title: 'Failed to Load Surveys',
        message: errorMessage,
        duration: 7000
      });
    } finally {
      setLoading(false);
      setIsRetrying(false);
    }
  }, [addToast]);

  const handleViewSurvey = useCallback(async (survey: SurveyListItem) => {
    try {
      console.log('🔍 [Survey View] Starting to view survey:', survey.id);
      console.log('🔍 [Survey View] Survey object keys:', Object.keys(survey));
      console.log('🔍 [Survey View] Survey type:', typeof survey);
      console.log('🔍 [Survey View] Full survey object:', survey);

      // Fetch the full survey data
      console.log('🌐 [Survey View] Making API call to:', `/api/v1/survey/${survey.id}`);
      const response = await fetch(`/api/v1/survey/${survey.id}`);
      console.log('🌐 [Survey View] API response status:', response.status);
      console.log('🌐 [Survey View] API response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        console.error('❌ [Survey View] API response not OK:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('❌ [Survey View] Error response body:', errorText);
        throw new Error('Failed to fetch survey');
      }

      const surveyData = await response.json();
      console.log('📊 [Survey View] API response data:', surveyData);
      console.log('📊 [Survey View] Raw output questions:', surveyData.raw_output?.questions);
      console.log('📊 [Survey View] Final output questions:', surveyData.final_output?.questions);

      // Convert to the format expected by SurveyPreview
      // Handle both legacy questions format and new sections format
      let extractedQuestions = [];
      let sections = [];

      if (surveyData.final_output?.sections && surveyData.final_output.sections.length > 0) {
        // New sections format
        sections = surveyData.final_output.sections.map((section: any, index: number) => ({
          ...section,
          order: section.order || index + 1,
          questions: (section.questions || []).map((question: any) => ({
            ...question,
            // Preserve labels field from backend
            labels: question.labels || question.metadata?.labels || []
          })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
        })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0));
        extractedQuestions = sections.flatMap((section: any) => section.questions || []);
        console.log('📋 [Survey View] Using sections format - sections:', sections.length, 'questions:', extractedQuestions.length);
      } else if (surveyData.final_output?.questions && surveyData.final_output.questions.length > 0) {
        // Legacy questions format
        extractedQuestions = (surveyData.final_output.questions || []).map((question: any) => ({
          ...question,
          // Preserve labels field from backend
          labels: question.labels || question.metadata?.labels || []
        })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0));
        console.log('📋 [Survey View] Using legacy questions format - questions:', extractedQuestions.length);
      } else if (surveyData.raw_output?.sections && surveyData.raw_output.sections.length > 0) {
        // Fallback to raw_output sections
        sections = surveyData.raw_output.sections.map((section: any, index: number) => ({
          ...section,
          order: section.order || index + 1,
          questions: (section.questions || []).sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
        })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0));
        extractedQuestions = sections.flatMap((section: any) => section.questions || []);
        console.log('📋 [Survey View] Using raw_output sections format - sections:', sections.length, 'questions:', extractedQuestions.length);
      } else if (surveyData.raw_output?.questions && surveyData.raw_output.questions.length > 0) {
        // Fallback to raw_output questions
        extractedQuestions = (surveyData.raw_output.questions || []).sort((a: any, b: any) => (a.order || 0) - (b.order || 0));
        console.log('📋 [Survey View] Using raw_output questions format - questions:', extractedQuestions.length);
      }

      console.log('📋 [Survey View] Extracted questions:', extractedQuestions);
      console.log('📋 [Survey View] Questions count:', extractedQuestions.length);

      const surveyForPreview = {
        survey_id: survey.id,
        title: survey.title,
        description: survey.description,
        estimated_time: survey.estimated_time || 10,
        confidence_score: survey.quality_score || 0.8,
        methodologies: survey.methodology_tags || [],
        golden_examples: [], // Empty for now
        questions: extractedQuestions,
        sections: sections, // Include sections for new format
        metadata: {
          target_responses: 100,
          methodology: survey.methodology_tags || [],
          estimated_time: survey.estimated_time,
          quality_score: survey.quality_score,
          methodology_tags: survey.methodology_tags
        },
        pillar_scores: surveyData.pillar_scores, // Include pillar scores from API response
        rfq_id: surveyData.rfq_id // Include rfq_id for concept file loading
      };

      console.log('🎯 [Survey View] Converted survey for preview:', surveyForPreview);

      // Set the survey in the app store
      setSurvey(surveyForPreview);
      console.log('✅ [Survey View] Survey set in store');

      // Load existing annotations for this survey
      try {
        console.log('🔍 [Survey View] Loading annotations for survey:', survey.id);
        await useAppStore.getState().loadAnnotations(survey.id);
        console.log('✅ [Survey View] Annotations loaded successfully');
      } catch (error) {
        console.warn('⚠️ [Survey View] Failed to load annotations:', error);
        // Continue without annotations - they'll be created when needed
      }

      // Set a mock RFQ input for context
      setRFQInput({
        title: survey.title,
        description: survey.description,
        product_category: survey.methodology_tags?.[0] || 'General',
        target_segment: 'General',
        research_goal: 'Survey Analysis'
      });

      setSelectedSurvey(survey);
      console.log('🎉 [Survey View] Survey view setup complete');
    } catch (err) {
      console.error('Failed to load survey:', err);
    }
  }, [setSurvey, setRFQInput]);

  // Load surveys from URL parameter
  useEffect(() => {
    console.log('🔍 [Survey List] Component mounted/updated, fetching surveys');
    fetchSurveys();
  }, [fetchSurveys]);

  // Force refresh when component becomes visible (more reliable than popstate)
  useEffect(() => {
    let lastRefreshTime = 0;
    const REFRESH_COOLDOWN = 2000; // 2 seconds cooldown to prevent excessive refreshes
    
    const handlePageShow = () => {
      const now = Date.now();
      if (now - lastRefreshTime > REFRESH_COOLDOWN) {
        console.log('🔄 [Survey List] Page show event, refreshing surveys');
        lastRefreshTime = now;
        fetchSurveys();
      }
    };

    // Listen for page show event (when user navigates back to this page)
    window.addEventListener('pageshow', handlePageShow);
    
    // Also refresh immediately if we're on surveys page
    if (window.location.pathname === '/surveys') {
      console.log('🔄 [Survey List] On surveys page, refreshing to ensure latest data');
      fetchSurveys();
    }
    
    return () => {
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, [fetchSurveys]);

  // Refresh surveys when returning from individual survey view
  useEffect(() => {
    const handleVisibilityChange = () => {
      console.log('🔍 [Survey List] Visibility changed:', { hidden: document.hidden, pathname: window.location.pathname });
      if (!document.hidden && window.location.pathname === '/surveys') {
        console.log('🔄 [Survey List] Page became visible, refreshing survey list');
        fetchSurveys();
      }
    };

    const handleFocus = () => {
      console.log('🔍 [Survey List] Window focused:', { pathname: window.location.pathname });
      if (window.location.pathname === '/surveys') {
        console.log('🔄 [Survey List] Window focused, refreshing survey list');
        fetchSurveys();
      }
    };

    const handlePopState = () => {
      console.log('🔍 [Survey List] Popstate event:', { pathname: window.location.pathname });
      setCurrentUrl(window.location.search); // Update URL state
      if (window.location.pathname === '/surveys') {
        console.log('🔄 [Survey List] Navigated back to surveys page, refreshing survey list');
        fetchSurveys();
      }
    };

    // Listen for page visibility changes (when user navigates back)
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Listen for window focus (when user switches back to tab)
    window.addEventListener('focus', handleFocus);
    
    // Listen for browser back/forward navigation
    window.addEventListener('popstate', handlePopState);
    
    // Cleanup
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [fetchSurveys]);

  // Handle URL parameter after surveys are loaded
  useEffect(() => {
    const urlParams = new URLSearchParams(currentUrl);
    const surveyId = urlParams.get('id');
    
    if (surveyId && surveys.length > 0) {
      console.log('🔍 [URL] Looking for survey with ID:', surveyId);
      console.log('🔍 [URL] Available surveys:', surveys.length);
      const survey = surveys.find(s => s.id === surveyId);
      console.log('🔍 [URL] Found survey:', survey);
      if (survey) {
        console.log('🔍 [URL] Setting selected survey:', survey.title);
        setSelectedSurvey(survey);
        // Also fetch the full survey data for preview
        handleViewSurvey(survey);
      } else {
        console.log('❌ [URL] Survey not found with ID:', surveyId);
      }
    }
  }, [surveys, currentUrl, handleViewSurvey]);


  // Update URL when survey is selected
  useEffect(() => {
    if (selectedSurvey) {
      const url = new URL(window.location.href);
      url.searchParams.set('id', selectedSurvey.id);
      window.history.replaceState({}, '', url.toString());
      setCurrentUrl(url.search);
    }
  }, [selectedSurvey]);

  const handleDeleteSurvey = async (surveyId: string) => {
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete survey');
      
      setSurveys(surveys.filter(s => s.id !== surveyId));
      if (selectedSurvey?.id === surveyId) {
        setSelectedSurvey(null);
      }
      setShowDeleteConfirm(null);
    } catch (err) {
      console.error('Failed to delete survey:', err);
    }
  };

  const handleMultiSelectToggle = () => {
    setIsMultiSelectMode(!isMultiSelectMode);
    setSelectedSurveys(new Set());
  };

  const handleSurveySelect = (surveyId: string) => {
    if (isMultiSelectMode) {
      // Prevent selection of reference surveys
      const survey = surveys.find(s => s.id === surveyId);
      if (survey && survey.status === 'reference') {
        return;
      }
      
      setSelectedSurveys(prev => {
        const newSet = new Set(prev);
        if (newSet.has(surveyId)) {
          newSet.delete(surveyId);
        } else {
          newSet.add(surveyId);
        }
        return newSet;
      });
    } else {
      // Navigate to read-only view instead of edit mode
      console.log('🖱️ [Click] Survey clicked, navigating to read-only view:', surveyId);
      window.location.href = `/surveys/${surveyId}`;
    }
  };

  const handleBulkDelete = async () => {
    if (selectedSurveys.size === 0) return;
    
    // Filter out reference surveys from deletion
    const surveysToDelete = Array.from(selectedSurveys).filter(surveyId => {
      const survey = surveys.find(s => s.id === surveyId);
      return survey && survey.status !== 'reference';
    });
    
    if (surveysToDelete.length === 0) {
      addToast({
        type: 'warning',
        title: 'No Surveys to Delete',
        message: 'No surveys can be deleted. Reference surveys are automatically managed.',
        duration: 5000
      });
      return;
    }
    
    console.log('🗑️ [SurveysPage] Starting bulk delete for surveys:', surveysToDelete);
    
    try {
      const deletePromises = surveysToDelete.map(async (surveyId) => {
        console.log(`🗑️ [SurveysPage] Deleting survey: ${surveyId}`);
        const response = await fetch(`/api/v1/survey/${surveyId}`, { method: 'DELETE' });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`❌ [SurveysPage] Failed to delete survey ${surveyId}:`, response.status, errorText);
          throw new Error(`Failed to delete survey ${surveyId}: ${response.status} ${errorText}`);
        }
        
        console.log(`✅ [SurveysPage] Successfully deleted survey: ${surveyId}`);
        return response;
      });
      
      await Promise.all(deletePromises);
      
      console.log('✅ [SurveysPage] All surveys deleted successfully');
      
      setSurveys(prev => prev.filter(s => !surveysToDelete.includes(s.id)));
      if (selectedSurvey && surveysToDelete.includes(selectedSurvey.id)) {
        setSelectedSurvey(null);
      }
      setSelectedSurveys(new Set());
      setIsMultiSelectMode(false);
      
      // Show success message
      addToast({
        type: 'success',
        title: 'Surveys Deleted',
        message: `Successfully deleted ${surveysToDelete.length} survey(s)`,
        duration: 3000
      });
      
    } catch (err) {
      console.error('❌ [SurveysPage] Bulk delete failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete surveys');
    }
  };

  const handleSelectAll = () => {
    // Filter out reference surveys from selection
    const selectableSurveys = filteredSurveys.filter(({ survey }) => survey.status !== 'reference');
    
    if (selectedSurveys.size === selectableSurveys.length) {
      setSelectedSurveys(new Set());
    } else {
      setSelectedSurveys(new Set(selectableSurveys.map(({ survey, currentVersionId }) => currentVersionId || survey.id)));
    }
  };

  // Helper function to check if a survey is currently being generated
  const isSurveyGenerating = (surveyId: string) => {
    return workflow.survey_id === surveyId && 
           (workflow.status === 'started' || workflow.status === 'in_progress' || workflow.status === 'paused');
  };

  // Helper function to get generation status for a survey
  const getGenerationStatus = (surveyId: string) => {
    if (!isSurveyGenerating(surveyId)) return null;
    
    return {
      isGenerating: true,
      progress: workflow.progress || 0,
      status: workflow.status as 'started' | 'in_progress' | 'completed' | 'failed' | 'paused',
      message: workflow.message
    };
  };

  const handleBack = () => {
    setSelectedSurvey(null);
    // Remove ID from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('id');
    window.history.replaceState({}, '', url.toString());
  };

  // Group surveys by rfq_id (surveys with the same rfq_id are versions of each other)
  const groupedSurveys = React.useMemo(() => {
    const groups = new Map<string, {
      survey: SurveyListItem;
      versionCount: number;
      currentVersionId: string | null;
    }>();

    // First pass: collect all surveys by their rfq_id
    const surveysByGroup = new Map<string, SurveyListItem[]>();
    
    surveys.forEach(survey => {
      // Group by rfq_id if available, otherwise fall back to parent_survey_id chain or id
      // For reference surveys (no rfq_id), use id as group key
      let groupKey: string;
      
      if (survey.rfq_id) {
        // Group by rfq_id - all surveys for the same RFQ are versions
        groupKey = survey.rfq_id;
      } else if (survey.parent_survey_id) {
        // If no rfq_id but has parent, trace back to find root (for reference surveys)
        // For now, use parent_survey_id as group key
        groupKey = survey.parent_survey_id;
      } else {
        // No rfq_id and no parent - standalone survey (reference or original)
        groupKey = survey.id;
      }
      
      if (!surveysByGroup.has(groupKey)) {
        surveysByGroup.set(groupKey, []);
      }
      surveysByGroup.get(groupKey)!.push(survey);
    });

    // Second pass: for each group, find the current version and create the grouped entry
    surveysByGroup.forEach((groupSurveys, groupKey) => {
      // Find the current version for this group, or use the latest one
      const currentVersion = groupSurveys.find(s => s.is_current) || 
                            groupSurveys.sort((a, b) => 
                              new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                            )[0];
      
      groups.set(groupKey, {
        survey: currentVersion,
        versionCount: groupSurveys.length,
        currentVersionId: currentVersion?.id || null
      });
    });

    return Array.from(groups.values());
  }, [surveys]);

  const filteredSurveys = groupedSurveys.filter(({ survey }) => {
    const matchesSearch = survey.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         survey.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || survey.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  
  console.log('🔍 [Render] Surveys count:', surveys.length);
  console.log('🔍 [Render] Grouped surveys count:', groupedSurveys.length);
  console.log('🔍 [Render] Filtered surveys count:', filteredSurveys.length);
  console.log('🔍 [Render] First filtered survey (if any):', filteredSurveys[0]);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'surveys' | 'rules' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/?view=golden-examples';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
    }
  };

  return (
    <div className="min-h-screen bg-white flex">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Sidebar */}
      <Sidebar currentView="surveys" onViewChange={handleViewChange} />

      {/* Main Content */}
      <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>
        {selectedSurvey ? (
          <div className="h-full flex flex-col">
            {/* Survey Header with Title and Metadata */}
            <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 px-6 py-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleBack}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 group"
                  >
                    <svg className="h-5 w-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  
                  <div className="flex-1">
                    <h1 className="text-xl font-bold text-gray-900 mb-1">
                      {selectedSurvey.title}
                    </h1>
                    <p className="text-sm text-gray-600 mb-2">
                      {selectedSurvey.description}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>⏱️ ~{selectedSurvey.estimated_time || 18} minutes</span>
                      <span>📊 {selectedSurvey.question_count || 0} questions</span>
                      <span>📋 {getSectionsCount(currentSurvey)} sections</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                      {selectedSurvey.status}
                    </span>
                    {selectedSurvey.quality_score && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                        {selectedSurvey.quality_score.toFixed(1)}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setShowDeleteConfirm(selectedSurvey.id)}
                    className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-all duration-200 font-medium hover:shadow-md"
                    title="Delete survey"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            {/* Survey Preview - Removed, now using separate edit route */}
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
              <div className="px-6 py-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Surveys</h1>
                      <p className="text-gray-600 mt-1">Manage and preview your generated surveys</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => fetchSurveys()}
                      className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200 font-medium"
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                      <span>Refresh</span>
                    </button>
                    
                    {isMultiSelectMode && (
                      <>
                        <button
                          onClick={handleSelectAll}
                          className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200 font-medium"
                        >
                          <CheckIcon className="h-4 w-4" />
                          <span>{selectedSurveys.size === filteredSurveys.length ? 'Deselect All' : 'Select All'}</span>
                        </button>
                        
                        {selectedSurveys.size > 0 && (
                          <button
                            onClick={handleBulkDelete}
                            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-xl transition-all duration-200 font-medium"
                          >
                            <TrashIcon className="h-4 w-4" />
                            <span>Delete ({selectedSurveys.size})</span>
                          </button>
                        )}
                      </>
                    )}
                    
                    <button
                      onClick={handleMultiSelectToggle}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 font-medium ${
                        isMultiSelectMode 
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <CheckIcon className="h-4 w-4" />
                      <span>{isMultiSelectMode ? 'Exit Select' : 'Select'}</span>
                    </button>
                    
                    <button
                      onClick={() => window.location.href = '/'}
                      className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-600 to-amber-600 text-white hover:from-yellow-700 hover:to-amber-700 rounded-xl transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      <PlusIcon className="h-5 w-5" />
                      <span>New Survey</span>
                    </button>
                  </div>
                </div>

                {/* Search and Filters */}
                <div className="flex items-center space-x-4">
                  <div className="relative flex-1 max-w-md">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search surveys..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                    />
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <FunnelIcon className="h-5 w-5 text-gray-400" />
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
                    >
                      <option value="all">All Status</option>
                      <option value="completed">Completed</option>
                      <option value="in_progress">In Progress</option>
                      <option value="failed">Failed</option>
                    </select>
                  </div>
                </div>
              </div>
            </header>

            {/* Content */}
            <main className="flex-1 overflow-y-auto p-6">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="flex flex-col items-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-200 border-t-amber-600"></div>
                    <p className="text-gray-600 text-lg">Loading surveys...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                      <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Error loading surveys</h3>
                    <p className="text-red-600 mb-6">{error}</p>
                    <button
                      onClick={() => fetchSurveys(true)}
                      disabled={isRetrying}
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-yellow-600 to-amber-600 text-white rounded-xl hover:from-yellow-700 hover:to-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      {isRetrying ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Retrying...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Try Again
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : filteredSurveys.length === 0 ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-amber-200 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                      <PlusIcon className="h-12 w-12 text-gray-400" />
                    </div>
                    <h3 className="text-2xl font-semibold text-gray-900 mb-3">No surveys found</h3>
                    <p className="text-gray-600 mb-8 text-lg">
                      {searchQuery || statusFilter !== 'all' 
                        ? 'Try adjusting your search or filters'
                        : 'Get started by creating your first survey'
                      }
                    </p>
                    <button
                      onClick={() => window.location.href = '/'}
                      className="px-8 py-4 bg-gradient-to-r from-yellow-600 to-amber-600 text-white rounded-xl hover:from-yellow-700 hover:to-amber-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      <PlusIcon className="h-5 w-5 mr-2 inline" />
                      Create Survey
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Error Display */}
                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
                          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-red-900">Error</p>
                          <p className="text-sm text-red-800">{error}</p>
                        </div>
                        <button
                          onClick={() => setError(null)}
                          className="ml-auto text-red-400 hover:text-red-600"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {filteredSurveys.map(({ survey, versionCount, currentVersionId }) => (
                    <div
                      key={survey.id}
                      className={`bg-white rounded-xl border-2 transition-all duration-200 cursor-pointer ${
                        selectedSurveys.has(currentVersionId || survey.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                      }`}
                      onClick={() => handleSurveySelect(currentVersionId || survey.id)}
                    >
                      <div className="p-6">
                        <div className="flex items-center space-x-4">
                          {/* Checkbox for multi-select */}
                          {isMultiSelectMode && (
                            <div className="flex-shrink-0">
                              {survey.status === 'reference' ? (
                                <div className="relative group">
                                  <div className="w-5 h-5 rounded border-2 border-gray-200 bg-gray-100 flex items-center justify-center cursor-not-allowed">
                                    <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
                                    </svg>
                                  </div>
                                  {/* Tooltip */}
                                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                                    Reference surveys cannot be selected for deletion
                                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                                  </div>
                                </div>
                              ) : (
                                <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                                  selectedSurveys.has(currentVersionId || survey.id)
                                    ? 'bg-blue-600 border-blue-600'
                                    : 'border-gray-300'
                                }`}>
                                  {selectedSurveys.has(currentVersionId || survey.id) && (
                                    <CheckIcon className="w-3 h-3 text-white" />
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Survey Icon */}
                          <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                          </div>
                          
                          {/* Survey Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <h3 className="text-lg font-semibold text-gray-900 truncate">
                                  {survey.title}
                                </h3>
                                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                  {survey.description}
                                </p>
                                <div className="flex items-center space-x-4 mt-3">
                                  <div className="flex items-center space-x-2">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      survey.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                                      survey.status === 'validated' ? 'bg-green-100 text-green-800' :
                                      survey.status === 'edited' ? 'bg-blue-100 text-blue-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {survey.status}
                                    </span>
                                    
                                    {/* Version Count Badge */}
                                    {versionCount > 1 && (
                                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                                        {versionCount} {versionCount === 1 ? 'version' : 'versions'}
                                      </span>
                                    )}
                                    
                                    {/* Generation Indicator */}
                                    {(() => {
                                      const generationStatus = getGenerationStatus(survey.id);
                                      return generationStatus ? (
                                        <SurveyGenerationIndicator
                                          isGenerating={generationStatus.isGenerating}
                                          progress={generationStatus.progress}
                                          status={generationStatus.status}
                                          message={generationStatus.message}
                                          className="text-xs"
                                        />
                                      ) : null;
                                    })()}
                                  </div>
                                  <span className="text-sm text-gray-500">
                                    {survey.question_count} {survey.question_count === 1 ? 'question' : 'questions'}
                                    {survey.instruction_count > 0 && (
                                      <> • {survey.instruction_count} {survey.instruction_count === 1 ? 'instruction' : 'instructions'}</>
                                    )}
                                  </span>
                                  {survey.estimated_time && (
                                    <span className="text-sm text-gray-500">
                                      ~{survey.estimated_time} min
                                    </span>
                                  )}
                                  <span className="text-sm text-gray-500">
                                    {new Date(survey.created_at).toLocaleString()}
                                  </span>
                                </div>
                              </div>
                              
                              {/* Actions */}
                              {!isMultiSelectMode && (
                                <div className="flex items-center space-x-2 ml-4">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      console.log('🖱️ [Click] View button clicked for survey:', survey);
                                      console.log('🖱️ [Click] Survey ID:', currentVersionId || survey?.id);
                                      window.location.href = `/surveys/${currentVersionId || survey.id}`;
                                    }}
                                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                    title="View Survey"
                                  >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                    </svg>
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      console.log('🖱️ [Click] Edit button clicked for survey:', survey);
                                      console.log('🖱️ [Click] Survey ID:', currentVersionId || survey?.id);
                                      window.location.href = `/surveys/${currentVersionId || survey.id}/edit`;
                                    }}
                                    className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                    title="Edit Survey"
                                  >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                  </button>
                                  {survey.status === 'reference' ? (
                                    <div className="relative group">
                                      <button
                                        disabled
                                        className="p-2 text-gray-300 cursor-not-allowed rounded-lg transition-colors"
                                        title="Reference surveys cannot be deleted directly. They are automatically removed when their corresponding golden example is deleted."
                                      >
                                        <TrashIcon className="w-5 h-5" />
                                      </button>
                                      {/* Tooltip */}
                                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                                        Reference surveys cannot be deleted directly. They are automatically removed when their corresponding golden example is deleted.
                                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                                      </div>
                                    </div>
                                  ) : (
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setShowDeleteConfirm(survey.id);
                                      }}
                                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                      title="Delete Survey"
                                    >
                                      <TrashIcon className="w-5 h-5" />
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </main>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Survey</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this survey? This action cannot be undone.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteSurvey(showDeleteConfirm)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
