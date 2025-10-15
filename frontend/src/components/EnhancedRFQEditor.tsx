import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { DocumentUpload } from './DocumentUpload';

// Animated sprinkle component
const AnimatedSprinkle: React.FC<{ className?: string }> = ({ className = "" }) => (
  <span 
    className={`inline-block text-primary-500 text-lg font-bold animate-pulse hover:animate-bounce drop-shadow-sm ${className}`} 
    title="Auto-filled from document"
    style={{ 
      filter: 'drop-shadow(0 0 3px rgba(234, 179, 8, 0.6))',
      textShadow: '0 0 4px rgba(234, 179, 8, 0.8)'
    }}
  >
    ✨
  </span>
);

// Helper component for form fields with auto-fill indicators
const FormField: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'textarea' | 'select';
  rows?: number;
  isAutoFilled?: boolean;
  isEdited?: boolean;
  options?: { value: string; label: string; }[];
}> = ({ label, value, onChange, placeholder = '', type = 'text', rows = 4, isAutoFilled = false, isEdited = false, options = [] }) => {
  const inputClasses = `${
    isAutoFilled ? 'input-highlighted' : 
    isEdited ? 'w-full px-4 py-4 bg-secondary-50 border border-secondary-200 rounded-2xl focus:ring-4 focus:ring-secondary-500/20 focus:border-secondary-500 transition-all duration-300' :
    'input-default'
  } ${type === 'textarea' ? 'resize-none' : ''}`;

  return (
    <div>
      <label className="label-default mb-3 flex items-center space-x-2">
        <span>{label}</span>
        {isAutoFilled && <AnimatedSprinkle />}
        {isEdited && !isAutoFilled && (
          <span 
            className="inline-block text-secondary-500 text-lg font-bold animate-pulse hover:animate-bounce drop-shadow-sm" 
            title="Manually edited"
            style={{ 
              filter: 'drop-shadow(0 0 3px rgba(37, 99, 235, 0.6))',
              textShadow: '0 0 4px rgba(37, 99, 235, 0.8)'
            }}
          >
            ✏️
          </span>
        )}
      </label>
      <div className="relative">
        {type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={rows}
            className={inputClasses}
          />
        ) : type === 'select' ? (
          <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={inputClasses}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className={inputClasses}
          />
        )}
      </div>
    </div>
  );
};

interface EnhancedRFQEditorProps {
  onPreview?: () => void;
  mode?: 'create' | 'edit';
}

export const EnhancedRFQEditor: React.FC<EnhancedRFQEditorProps> = ({
  onPreview,
  mode = 'create'
}) => {
  console.log('🔍 [EnhancedRFQEditor] Component mounted/rendered', { mode });
  const {
    enhancedRfq,
    setEnhancedRfq,
    workflow,
    // Document upload state and actions
    fieldMappings,
    addToast,
    isDocumentProcessing,
    // State persistence
    restoreEnhancedRfqState,
    clearEnhancedRfqState,
    resetDocumentProcessingState,
    // Edit tracking
    trackFieldEdit
  } = useAppStore();

  console.log('🔍 [EnhancedRFQEditor] Current state:', { 
    enhancedRfq, 
    fieldMappings: fieldMappings.length, 
    isDocumentProcessing 
  });
  console.log('🔍 [EnhancedRFQEditor] Field mappings details:', fieldMappings);

  // Helper functions for document processing
  const setDocumentContent = (content: any) => {
    useAppStore.setState({ documentContent: content });
  };

  const setRfqAnalysis = (analysis: any) => {
    useAppStore.setState({ documentAnalysis: analysis });
  };

  const setFieldMappings = (mappings: any[]) => {
    useAppStore.setState({ fieldMappings: mappings });
  };

  // Helper function to check if a field was actually auto-filled from document
  const isFieldAutoFilled = (fieldPath: string): boolean => {
    const isAutoFilled = fieldMappings.some(mapping => {
      // Handle both dot notation and direct field names
      const mappingField = mapping.field.includes('.') ? mapping.field.split('.').pop() : mapping.field;
      const checkField = fieldPath.includes('.') ? fieldPath.split('.').pop() : fieldPath;
      return mappingField === checkField && mapping.user_action === 'accepted';
    });
    return isAutoFilled;
  };

  // Helper function to check if a field has been manually edited
  const isFieldEdited = (fieldPath: string): boolean => {
    const { editedFields } = useAppStore.getState();
    return editedFields.has(fieldPath);
  };

  // Helper function to update field with edit tracking
  const updateField = (fieldPath: string, value: any, updateFn: (value: any) => void) => {
    // Update the field value
    updateFn(value);
    
    // Track the edit
    trackFieldEdit(fieldPath, value);
  };

  const [currentSection, setCurrentSection] = useState<string>(() => {
    // Resilient section restoration with fallback
    try {
      const savedSection = localStorage.getItem('enhanced_rfq_current_section');
      const validSections = ['document', 'business_context', 'research_objectives', 'methodology', 'survey_requirements'];
      const isValidSection = savedSection && validSections.includes(savedSection);
      
      const finalSection = isValidSection ? savedSection : 'document';
      
      console.log('🔍 [EnhancedRFQEditor] Restoring current section:', finalSection);
      return finalSection;
    } catch (error) {
      console.warn('⚠️ [EnhancedRFQEditor] Error restoring section, defaulting to document:', error);
      return 'document';
    }
  });

  // Reset confirmation modal state
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  // Survey structure tab state
  const [surveyStructureTab, setSurveyStructureTab] = useState<string>('sections');

  // Resilient setCurrentSection that safely persists to localStorage
  const setCurrentSectionWithPersistence = useCallback((section: string) => {
    console.log('🔍 [EnhancedRFQEditor] Setting current section with persistence', 'section:', section);
    setCurrentSection(section);
    
    try {
      localStorage.setItem('enhanced_rfq_current_section', section);
    } catch (error) {
      console.warn('⚠️ [EnhancedRFQEditor] Failed to persist section to localStorage:', error);
      // Continue without persistence - UI still works
    }
  }, []);

  // Initialize enhanced RFQ with defaults
  const hasInitialized = useRef(false);
  const hasUserData = useRef(false);

  // Check if component has been initialized before (persist across remounts)
  const hasBeenInitialized = localStorage.getItem('enhanced_rfq_initialized') === 'true';
  
  // Check if there's existing user data that should be preserved
  const hasExistingUserData = enhancedRfq.title || 
                            enhancedRfq.description || 
                            enhancedRfq.business_context?.company_product_background ||
                            enhancedRfq.business_context?.business_problem ||
                            enhancedRfq.business_context?.business_objective ||
                            enhancedRfq.research_objectives?.research_audience ||
                            enhancedRfq.research_objectives?.success_criteria ||
                            (enhancedRfq.research_objectives?.key_research_questions && enhancedRfq.research_objectives.key_research_questions.length > 0) ||
                            enhancedRfq.methodology?.stimuli_details ||
                            enhancedRfq.methodology?.methodology_requirements ||
                            enhancedRfq.survey_requirements?.sample_plan ||
                            (enhancedRfq.survey_requirements?.must_have_questions && enhancedRfq.survey_requirements.must_have_questions.length > 0);

  // Track if field mappings have been applied to prevent loops
  const fieldMappingsAppliedRef = React.useRef(false);

  // Separate useEffect for field mappings to avoid infinite loops
  React.useEffect(() => {
    if (fieldMappings.length > 0 && !fieldMappingsAppliedRef.current) {
      console.log('🎯 [EnhancedRFQEditor] Field mappings detected, applying to form:', fieldMappings.length);
      fieldMappingsAppliedRef.current = true; // Prevent multiple applications
      
      // Apply field mappings immediately with error handling
      try {
        const { applyDocumentMappings } = useAppStore.getState();
        applyDocumentMappings();
        console.log('✅ [EnhancedRFQEditor] Field mappings applied successfully');
      } catch (error) {
        console.error('❌ [EnhancedRFQEditor] Failed to apply field mappings:', error);
        addToast({
          type: 'warning',
          title: 'Field Mapping Warning',
          message: 'Some fields could not be automatically applied. Please review the form manually.',
          duration: 6000
        });
      }
    }
  }, [fieldMappings, addToast]);

  // Initialize the component once
  React.useEffect(() => {
    // Skip initialization if already initialized or has user data
    if (hasInitialized.current || hasBeenInitialized || hasExistingUserData) {
      console.log('🔍 [EnhancedRFQEditor] Skipping initialization - already initialized or has user data',
        'hasInitialized:', hasInitialized.current,
        'hasBeenInitialized:', hasBeenInitialized,
        'hasExistingUserData:', hasExistingUserData,
        'fieldMappings:', fieldMappings.length
      );
      return;
    }
    
    hasInitialized.current = true;
    localStorage.setItem('enhanced_rfq_initialized', 'true');
    
    console.log('🔍 [EnhancedRFQEditor] useEffect triggered', {
      hasInitialized: hasInitialized.current,
      enhancedRfqTitle: enhancedRfq.title,
      enhancedRfqDescription: enhancedRfq.description,
      currentSection,
      fieldMappingsCount: fieldMappings.length
    });
    
    // Check if this is a page refresh vs navigation
    const isPageRefresh = performance.navigation?.type === 1; // 1 = reload
    console.log('🔍 [EnhancedRFQEditor] Initializing component', {
      isPageRefresh,
      navigationType: performance.navigation?.type
    });
    
    // Try to restore state from localStorage first, but don't show toast on page refresh
    const wasRestored = restoreEnhancedRfqState(!isPageRefresh);
    console.log('🔍 [EnhancedRFQEditor] State restoration result', { wasRestored });
    
    // Check if there's any user data in the form
    const hasAnyUserData = enhancedRfq.title || 
                          enhancedRfq.description || 
                          enhancedRfq.business_context?.company_product_background ||
                          enhancedRfq.business_context?.business_problem ||
                          enhancedRfq.business_context?.business_objective ||
                          enhancedRfq.research_objectives?.research_audience ||
                          enhancedRfq.research_objectives?.success_criteria ||
                          (enhancedRfq.research_objectives?.key_research_questions && enhancedRfq.research_objectives.key_research_questions.length > 0) ||
                          enhancedRfq.methodology?.stimuli_details ||
                          enhancedRfq.methodology?.methodology_requirements ||
                          enhancedRfq.survey_requirements?.sample_plan ||
                          (enhancedRfq.survey_requirements?.must_have_questions && enhancedRfq.survey_requirements.must_have_questions.length > 0);

    // Update the hasUserData flag
    if (hasAnyUserData) {
      hasUserData.current = true;
    }

    // Only initialize with defaults if this is truly a fresh start (no existing data and no user data flag)
    if (!wasRestored && !hasAnyUserData && !hasUserData.current) {
      console.log('🔍 [EnhancedRFQEditor] Initializing with default values - form is completely empty');
      setEnhancedRfq({
        title: '',
        description: '',
        business_context: {
          company_product_background: '',
          business_problem: '',
          business_objective: ''
        },
        research_objectives: {
          research_audience: '',
          success_criteria: '',
          key_research_questions: []
        },
        methodology: {
          primary_method: 'basic_survey'
        },
        survey_requirements: {
          sample_plan: '',
          must_have_questions: []
        }
      });
    } else {
      console.log('🔍 [EnhancedRFQEditor] Skipping initialization - state already exists or was restored', {
        wasRestored,
        hasAnyUserData,
        hasUserDataFlag: hasUserData.current,
        hasTitle: !!enhancedRfq.title,
        hasDescription: !!enhancedRfq.description,
        hasBusinessContext: !!enhancedRfq.business_context?.company_product_background,
        hasResearchObjectives: !!enhancedRfq.research_objectives?.research_audience
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasBeenInitialized, hasExistingUserData, restoreEnhancedRfqState, addToast]);

  // Persist current section to localStorage whenever it changes (except initial mount)
  const isInitialMount = useRef(true);
  
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      console.log('🔍 [EnhancedRFQEditor] Skipping section persistence on initial mount', 'currentSection:', currentSection);
      return;
    }
    
    console.log('🔍 [EnhancedRFQEditor] Persisting current section to localStorage', 'currentSection:', currentSection);
    
    try {
      localStorage.setItem('enhanced_rfq_current_section', currentSection);
    } catch (error) {
      console.warn('⚠️ [EnhancedRFQEditor] Failed to persist section to localStorage:', error);
      // Continue without persistence - UI still works
    }
  }, [currentSection]);

  // Status polling for when user returns while processing is still active
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const startStatusPolling = useCallback((sessionId: string) => {
    // Clear any existing polling interval
    if (pollingIntervalRef.current) {
      console.log('🔄 [EnhancedRFQEditor] Clearing existing polling interval');
      clearInterval(pollingIntervalRef.current);
    }
    
    console.log('🔄 [EnhancedRFQEditor] Starting status polling for sessionId:', sessionId);
    
    // Poll every 10 seconds
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/rfq/status/${sessionId}`);
        if (response.ok) {
          const status = await response.json();
          console.log('📊 [EnhancedRFQEditor] Polling status:', status.status);
          
          if (status.status === 'completed') {
            console.log('✅ [EnhancedRFQEditor] Processing completed, fetching results');
            // Stop polling
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            
            // Fetch the completed document analysis and apply to form
            if (status.has_results) {
              console.log('📥 [EnhancedRFQEditor] Fetching completed analysis results');
              try {
                // Fetch the analysis results from the backend
                const resultsResponse = await fetch(`/api/v1/rfq/status/${sessionId}/results`);
                if (resultsResponse.ok) {
                  const results = await resultsResponse.json();
                  console.log('📊 [EnhancedRFQEditor] Retrieved analysis results:', results);

                  // Apply the results to the form
                  if (results.document_content) {
                    setDocumentContent(results.document_content);
                  }
                  
                  if (results.rfq_analysis) {
                    setRfqAnalysis(results.rfq_analysis);
                  }
                  
                  if (results.field_mappings && results.field_mappings.length > 0) {
                    setFieldMappings(results.field_mappings);
                    console.log('🎯 [EnhancedRFQEditor] Applied field mappings:', results.field_mappings);
                    
                    // Reset the applied flag for new field mappings
                    fieldMappingsAppliedRef.current = false;
                  }

                  // Mark as completed and navigate to business context
                  resetDocumentProcessingState();
                  setCurrentSectionWithPersistence('business_context');
                  
                  // Show success message with field mapping count
                  const mappingCount = results.field_mappings?.length || 0;
                  addToast({
                    type: 'success',
                    title: 'Document Analysis Complete',
                    message: `Document analyzed successfully. ${mappingCount > 0 ? `${mappingCount} fields extracted and applied to form.` : 'No fields could be extracted from the document.'}`,
                    duration: 8000
                  });
                } else {
                  console.error('❌ [EnhancedRFQEditor] Failed to fetch analysis results');
                  addToast({
                    type: 'error',
                    title: 'Analysis Results Error',
                    message: 'Failed to fetch completed analysis results.',
                    duration: 5000
                  });
                }
              } catch (error) {
                console.error('❌ [EnhancedRFQEditor] Error fetching analysis results:', error);
                addToast({
                  type: 'error',
                  title: 'Analysis Results Error',
                  message: 'Error fetching completed analysis results.',
                  duration: 5000
                });
              }
            }
          } else if (status.status === 'cancelled') {
            console.log('🛑 [EnhancedRFQEditor] Processing was cancelled, stopping polling');
            // Stop polling
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            // Reset form state
            clearEnhancedRfqState();
            resetDocumentProcessingState();
            setCurrentSectionWithPersistence('document');
            addToast({
              type: 'info',
              title: 'Processing Cancelled',
              message: 'Document processing was cancelled.',
              duration: 3000
            });
            return; // Exit polling function
          } else if (status.status === 'failed') {
            console.log('❌ [EnhancedRFQEditor] Processing failed');
            // Stop polling
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            
            resetDocumentProcessingState();
            addToast({
              type: 'error',
              title: 'Document Processing Failed',
              message: status.error_message || 'Failed to process document.',
              duration: 5000
            });
          }
          // If still in_progress, continue polling
        }
      } catch (error) {
        console.warn('⚠️ [EnhancedRFQEditor] Polling error:', error);
        // Continue polling despite errors
      }
    }, 10000); // Poll every 10 seconds
  }, [addToast, resetDocumentProcessingState, setCurrentSectionWithPersistence, clearEnhancedRfqState]);
  
  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        console.log('🧹 [EnhancedRFQEditor] Cleaning up polling interval on unmount');
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  // Simple section change tracking - just log and handle document processing
  useEffect(() => {
    console.log('🔍 [EnhancedRFQEditor] Current section:', currentSection);
    
    // If document is processing, stay on document section
    if (isDocumentProcessing && currentSection !== 'document') {
      console.log('🔍 [EnhancedRFQEditor] Document processing active - staying on document section');
      setCurrentSectionWithPersistence('document');
    }
  }, [currentSection, isDocumentProcessing, setCurrentSectionWithPersistence]);

  // Resilient component lifecycle with backend status verification (runs once on mount)
  useEffect(() => {
    console.log('🔍 [EnhancedRFQEditor] Component mounted');
    
    // Check if we need to verify backend status (simple resilience check)
    const verifyBackendStatus = async () => {
      const persistedState = localStorage.getItem('document_processing_state');
      if (persistedState) {
        try {
          const state = JSON.parse(persistedState);
          if (state.sessionId) {
            console.log('🔍 [EnhancedRFQEditor] Verifying backend status for resilience...', {
              sessionId: state.sessionId,
              isProcessing: state.isProcessing
            });
            
            try {
              // Simple timeout for resilience
              const controller = new AbortController();
              const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
              
              const response = await fetch(`/api/v1/rfq/status/${state.sessionId}`, {
                signal: controller.signal
              });
              
              clearTimeout(timeoutId);
              
              if (response.ok) {
                const backendStatus = await response.json();
                console.log('🔍 [EnhancedRFQEditor] Backend status:', backendStatus.status);
                
                // Handle different backend statuses
                if (backendStatus.status === 'failed') {
                  console.log('❌ [EnhancedRFQEditor] Backend confirmed processing failed, clearing state');
                  resetDocumentProcessingState();
                  addToast({
                    type: 'error',
                    title: 'Document Processing Failed',
                    message: backendStatus.error_message || 'Failed to process document. Please try again.',
                    duration: 5000
                  });
                } else if (backendStatus.status === 'in_progress') {
                  console.log('⏳ [EnhancedRFQEditor] Document still processing, starting polling');
                  // Update Zustand store to reflect processing state if needed
                  const currentProcessingState = useAppStore.getState().isDocumentProcessing;
                  if (!currentProcessingState) {
                    console.log('⚠️ [EnhancedRFQEditor] Frontend state out of sync, updating isDocumentProcessing to true');
                    useAppStore.setState({ isDocumentProcessing: true });
                  }
                  // Start polling to check when processing completes
                  startStatusPolling(state.sessionId);
                } else if (backendStatus.status === 'completed') {
                  console.log('✅ [EnhancedRFQEditor] Document processing complete, fetching results');
                  // Ensure isDocumentProcessing is false
                  const currentProcessingState = useAppStore.getState().isDocumentProcessing;
                  if (currentProcessingState) {
                    console.log('⚠️ [EnhancedRFQEditor] Frontend state out of sync, updating isDocumentProcessing to false');
                    useAppStore.setState({ isDocumentProcessing: false });
                  }
                  
                  // Fetch the completed analysis results and apply them
                  if (backendStatus.has_results) {
                    console.log('📥 [EnhancedRFQEditor] Fetching completed analysis results on mount');
                    try {
                      // Fetch the analysis results from the backend
                      const resultsResponse = await fetch(`/api/v1/rfq/status/${state.sessionId}/results`);
                      if (resultsResponse.ok) {
                        const results = await resultsResponse.json();
                        console.log('📊 [EnhancedRFQEditor] Retrieved analysis results on mount:', results);
                        
                        // Apply the analysis results directly to the store
                        const { addToast } = useAppStore.getState();
                        
                        // Accept all field mappings regardless of confidence
                        const incomingMappings = results.rfq_analysis?.field_mappings || [];
                        const autoAccepted = incomingMappings.map((m: any) => ({
                          ...m,
                          user_action: 'accepted' as const
                        }));

                        // Update store with analysis results and auto-accepted mappings
                        useAppStore.setState({
                          documentContent: results.document_content,
                          documentAnalysis: results.rfq_analysis,
                          fieldMappings: autoAccepted,
                          isDocumentProcessing: false
                        });

                        // Auto-apply accepted mappings immediately
                        const acceptedCount = autoAccepted.filter((m: any) => m.user_action === 'accepted').length;
                        if (acceptedCount > 0) {
                          // Apply mappings immediately using the accepted mappings
                          let rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(autoAccepted.filter((m: any) => m.user_action === 'accepted'));

                          // Apply methodology-based intelligence
                          rfqUpdates = useAppStore.getState().applyMethodologyIntelligence(rfqUpdates);

                          useAppStore.getState().setEnhancedRfq(rfqUpdates);

                          addToast({
                            type: 'success',
                            title: 'Auto-filled from Document',
                            message: `Applied ${acceptedCount} extracted fields. Review in the sections below. Click "Reset Form" to start fresh with a new RFQ.`,
                            duration: 8000
                          });
                          
                          // Automatically advance to Business Context section to show auto-filled content
                          setTimeout(() => {
                            setCurrentSectionWithPersistence('business_context');
                          }, 1000); // Small delay to let user see the success message
                        } else {
                          addToast({
                            type: 'info',
                            title: 'Document Processing Complete',
                            message: 'Document analysis completed, but no fields were extracted for auto-fill.',
                            duration: 5000
                          });
                        }
                      } else {
                        console.warn('⚠️ [EnhancedRFQEditor] Failed to fetch analysis results on mount');
                        addToast({
                          type: 'warning',
                          title: 'Document Processing Complete',
                          message: 'Document analysis completed, but results could not be retrieved. Please refresh the page.',
                          duration: 5000
                        });
                      }
                    } catch (error) {
                      console.error('❌ [EnhancedRFQEditor] Error fetching analysis results on mount:', error);
                      addToast({
                        type: 'error',
                        title: 'Error Retrieving Results',
                        message: 'Document analysis completed, but there was an error retrieving the results. Please refresh the page.',
                        duration: 5000
                      });
                    }
                  } else {
                    console.log('⚠️ [EnhancedRFQEditor] Processing completed but no results available');
                    addToast({
                      type: 'info',
                      title: 'Document Processing Complete',
                      message: 'Document analysis completed, but no results are available.',
                      duration: 5000
                    });
                  }
                } else if (backendStatus.status === 'not_found') {
                  console.log('🔍 [EnhancedRFQEditor] No backend record found, keeping local data if exists');
                  // Ensure isDocumentProcessing is false
                  const currentProcessingState = useAppStore.getState().isDocumentProcessing;
                  if (currentProcessingState) {
                    console.log('⚠️ [EnhancedRFQEditor] Frontend state out of sync, updating isDocumentProcessing to false');
                    useAppStore.setState({ isDocumentProcessing: false });
                  }
                  // Keep the data and let user continue
                }
              } else {
                console.log('⚠️ [EnhancedRFQEditor] Backend status check failed, keeping current state');
              }
            } catch (error) {
              if (error instanceof Error && error.name === 'AbortError') {
                console.log('⏰ [EnhancedRFQEditor] Backend status check timed out, keeping current state');
              } else {
                console.log('⚠️ [EnhancedRFQEditor] Backend status check error, keeping current state:', error instanceof Error ? error.message : String(error));
              }
              // On any error, keep current state (fail-safe)
            }
          } else {
            console.log('🔍 [EnhancedRFQEditor] No sessionId found in persisted state, skipping backend check');
          }
        } catch (error) {
          console.log('⚠️ [EnhancedRFQEditor] Error parsing persisted state:', error instanceof Error ? error.message : String(error));
        }
      } else {
        console.log('🔍 [EnhancedRFQEditor] No persisted document processing state found, skipping backend check');
      }
    };
    
    // Run verification in background (non-blocking)
    verifyBackendStatus();
    
    // Clean up WebSocket connection if it exists
    return () => {
      console.log('🔍 [EnhancedRFQEditor] Component unmounting');
      if ((window as any).rfqProcessingWebSocket) {
        console.log('🔌 [EnhancedRFQEditor] Cleaning up WebSocket connection');
        (window as any).rfqProcessingWebSocket.close();
        delete (window as any).rfqProcessingWebSocket;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount - dependencies are accessed via closures

  const sections = [
    { id: 'document', title: 'Document Upload', icon: '📄', description: 'Upload RFQ document for auto-extraction' },
    { id: 'business_context', title: 'Business Context', icon: '🏢', description: 'Company background, business problem & objective' },
    { id: 'research_objectives', title: 'Research Objectives', icon: '🎯', description: 'Research audience, success criteria & key questions' },
    { id: 'methodology', title: 'Methodology', icon: '🔬', description: 'Van Westendorp, Conjoint, Gabor Granger or other approach' },
    { id: 'survey_requirements', title: 'Survey Requirements', icon: '📋', description: 'Sample plan, sections, must-have questions' },
    { id: 'survey_structure', title: 'Survey Structure', icon: '🏗️', description: 'QNR section preferences and text introduction requirements' },
    { id: 'advanced_classification', title: 'Advanced Classification', icon: '🏷️', description: 'Industry, respondent classification & compliance requirements' }
  ];

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  const addResearchQuestion = () => {
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: [...(enhancedRfq.research_objectives?.key_research_questions || []), '']
      }
    });
  };

  const updateResearchQuestion = (index: number, value: string) => {
    const questions = [...(enhancedRfq.research_objectives?.key_research_questions || [])];
    questions[index] = value;
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: questions
      }
    });
  };

  const removeResearchQuestion = (index: number) => {
    const questions = [...(enhancedRfq.research_objectives?.key_research_questions || [])];
    questions.splice(index, 1);
    setEnhancedRfq({
      ...enhancedRfq,
      research_objectives: {
        ...enhancedRfq.research_objectives,
        key_research_questions: questions
      }
    });
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced RFQ Builder</h1>
              <p className="text-gray-600">Create comprehensive research requirements with AI assistance</p>
            </div>
            <div className="flex items-center space-x-3">
              {/* Reset Button - always visible */}
              <button
                onClick={() => setShowResetConfirm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-red-50 text-red-700 border border-red-200 rounded-lg hover:bg-red-100 transition-colors font-medium"
                title="Reset entire form to original state"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Reset Form</span>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="bg-gray-100 rounded-2xl p-4 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-800">
                {isDocumentProcessing ? 'Document Processing...' : 'Progress'}
              </span>
              <span className="text-sm text-gray-600">
                {isDocumentProcessing ? 'Processing' : `${sections.findIndex(s => s.id === currentSection) + 1} of ${sections.length}`}
              </span>
            </div>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  isDocumentProcessing ? 'bg-blue-500 animate-pulse' : 'bg-yellow-500'
                }`}
                style={{ 
                  width: isDocumentProcessing 
                    ? '25%' // Show 25% progress during document processing
                    : `${((sections.findIndex(s => s.id === currentSection) + 1) / sections.length) * 100}%`
                }}
              ></div>
            </div>
            <div className="flex justify-between mt-2">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => !isDocumentProcessing && setCurrentSectionWithPersistence(section.id)}
                  disabled={isDocumentProcessing && section.id !== 'document'}
                  className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-all duration-200 ${
                    currentSection === section.id
                      ? 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                      : isDocumentProcessing && section.id !== 'document'
                      ? 'text-gray-400 cursor-not-allowed opacity-50'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-lg">{section.icon}</span>
                  <span className="text-xs font-medium">{section.title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="w-full">
          {/* Main Content */}
          <div className="w-full">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">

                {/* Document Upload Section */}
                {currentSection === 'document' && !isDocumentProcessing && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">📄</span>
                      Document Upload
                    </h2>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                      <div className="flex items-start space-x-3">
                        <div className="text-yellow-600 text-2xl">💡</div>
                        <div>
                          <h3 className="font-semibold text-yellow-900 mb-2">Smart Auto-fill</h3>
                          <p className="text-yellow-800 text-sm">
                            Upload your RFQ document to automatically extract business context, research objectives,
                            methodology requirements, and survey specifications using AI-powered analysis.
                          </p>
                        </div>
                      </div>
                    </div>

                    <DocumentUpload
                      onDocumentAnalyzed={(result) => {
                        console.log('Document upload successful:', result);
                        addToast({
                          type: 'success',
                          title: 'Document Uploaded',
                          message: 'Document processed successfully. Check the sections below for auto-filled content.',
                          duration: 5000
                        });
                        
                        // Automatically advance to Business Context section to show auto-filled content
                        setTimeout(() => {
                          setCurrentSectionWithPersistence('business_context');
                        }, 1000); // Small delay to let user see the success message
                      }}
                    />
                  </div>
                )}

                {/* Document Processing State */}
                {isDocumentProcessing && (
                  <div className="space-y-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-8">
                      <div className="flex items-center space-x-3 mb-6">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-medium text-blue-900">Analyzing Your Document</h3>
                          <p className="text-blue-700 mt-1">
                            Our AI is extracting key information from your RFQ document...
                          </p>
                        </div>
                      </div>
                      
                      {/* Progress Steps */}
                      <div className="space-y-4 mb-6">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <span className="text-blue-800 font-medium">Document uploaded successfully</span>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                          </div>
                          <span className="text-blue-800 font-medium">Extracting text and structure</span>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                          </div>
                          <span className="text-gray-600">Analyzing content with AI</span>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                          </div>
                          <span className="text-gray-600">Mapping fields to survey requirements</span>
                        </div>
                      </div>
                      
                      <div className="text-sm text-blue-600 mb-6">
                        This usually takes 5-10 minutes depending on document complexity.
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-center space-x-4">
                        <button
                          onClick={async () => {
                            try {
                              // Get current session ID from localStorage
                              const persistedState = localStorage.getItem('document_processing_state');
                              const currentSessionId = persistedState ? JSON.parse(persistedState).sessionId : null;
                              
                              if (currentSessionId) {
                                // Call backend cancellation API
                                console.log('🛑 [EnhancedRFQEditor] Cancelling processing for session:', currentSessionId);
                                const response = await fetch(`/api/v1/rfq/cancel/${currentSessionId}`, {
                                  method: 'POST'
                                });
                                
                                if (response.ok) {
                                  console.log('✅ [EnhancedRFQEditor] Backend processing cancelled successfully');
                                } else {
                                  console.warn('⚠️ [EnhancedRFQEditor] Failed to cancel backend processing, but continuing with frontend cleanup');
                                }
                              }
                              
                              // Stop frontend polling
                              if (pollingIntervalRef.current) {
                                clearInterval(pollingIntervalRef.current);
                                pollingIntervalRef.current = null;
                                console.log('🔄 [EnhancedRFQEditor] Stopped frontend polling');
                              }
                              
                              // Clear document processing state
                              clearEnhancedRfqState();
                              resetDocumentProcessingState();
                              // Reset processing state to show document upload
                              setCurrentSectionWithPersistence('document');
                              // Clear localStorage
                              localStorage.removeItem('enhanced_rfq_initialized');
                              // Reset user data flag
                              hasUserData.current = false;
                              addToast({
                                type: 'info',
                                title: 'Processing Cancelled',
                                message: 'Document processing has been cancelled and form reset.',
                                duration: 3000
                              });
                            } catch (error) {
                              console.error('❌ [EnhancedRFQEditor] Error cancelling processing:', error);
                              addToast({
                                type: 'error',
                                title: 'Cancellation Error',
                                message: 'Failed to cancel processing, but form has been reset.',
                                duration: 5000
                              });
                            }
                          }}
                          className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                        >
                          Cancel Processing
                        </button>
                        
                        <button
                          onClick={() => {
                            // Clear document processing state and navigate to business context
                            clearEnhancedRfqState();
                            resetDocumentProcessingState();
                            setCurrentSection('business_context');
                            // Clear localStorage
                            localStorage.removeItem('enhanced_rfq_initialized');
                            // Reset user data flag
                            hasUserData.current = false;
                            addToast({
                              type: 'info',
                              title: 'Manual Entry Mode',
                              message: 'Switched to manual entry. You can now fill out the form manually.',
                              duration: 3000
                            });
                          }}
                          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                        >
                          Enter Manually
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Business Context Section */}
                {currentSection === 'business_context' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                        <span className="text-3xl mr-3">🏢</span>
                        Business Context
                      </h2>
                      {enhancedRfq.document_source && !isDocumentProcessing && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 flex items-center space-x-2">
                          <AnimatedSprinkle className="text-lg" />
                          <span className="text-sm text-yellow-800 font-medium">Auto-filled from document</span>
                        </div>
                      )}
                    </div>


                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Project Title"
                        value={enhancedRfq.title || ''}
                        onChange={(value) => updateField('title', value, (val) => setEnhancedRfq({ ...enhancedRfq, title: val }))}
                        placeholder="Enter your research project title"
                        type="text"
                        isAutoFilled={isFieldAutoFilled('title')}
                        isEdited={isFieldEdited('title')}
                      />

                      <FormField
                        label="Project Description"
                        value={enhancedRfq.description}
                        onChange={(value) => updateField('description', value, (val) => setEnhancedRfq({ ...enhancedRfq, description: val }))}
                        placeholder="Brief overview of the research project..."
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('description')}
                        isEdited={isFieldEdited('description')}
                      />
                    </div>

                    <FormField
                      label="Company & Product Background"
                      value={enhancedRfq.business_context?.company_product_background || ''}
                      onChange={(value) => updateField('business_context.company_product_background', value, (val) => setEnhancedRfq({
                        ...enhancedRfq,
                        business_context: {
                          ...enhancedRfq.business_context,
                          company_product_background: val,
                          business_problem: enhancedRfq.business_context?.business_problem || '',
                          business_objective: enhancedRfq.business_context?.business_objective || ''
                        }
                      }))}
                      placeholder="Provide background on your company, product, and any relevant research history that influences this study design..."
                      type="textarea"
                      rows={6}
                      isAutoFilled={isFieldAutoFilled('business_context.company_product_background')}
                    />

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Business Problem"
                        value={enhancedRfq.business_context?.business_problem || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: value,
                            business_objective: enhancedRfq.business_context?.business_objective || ''
                          }
                        })}
                        placeholder="What business challenge or question needs to be addressed?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('business_context.business_problem')}
                      />

                      <FormField
                        label="Business Objective"
                        value={enhancedRfq.business_context?.business_objective || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: value
                          }
                        })}
                        placeholder="What does the business want to achieve from this research?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('business_context.business_objective')}
                      />
                    </div>

                    {/* Enhanced Business Context Fields */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Stakeholder Requirements"
                        value={enhancedRfq.business_context?.stakeholder_requirements || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: enhancedRfq.business_context?.business_objective || '',
                            stakeholder_requirements: value
                          }
                        })}
                        placeholder="Key stakeholder needs and requirements..."
                        type="textarea"
                        rows={3}
                        isAutoFilled={isFieldAutoFilled('business_context.stakeholder_requirements')}
                      />

                      <FormField
                        label="Decision Criteria"
                        value={enhancedRfq.business_context?.decision_criteria || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: enhancedRfq.business_context?.business_objective || '',
                            decision_criteria: value
                          }
                        })}
                        placeholder="What defines success for this research..."
                        type="textarea"
                        rows={3}
                        isAutoFilled={isFieldAutoFilled('business_context.decision_criteria')}
                      />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Budget Range"
                        value={enhancedRfq.business_context?.budget_range || '10k_50k'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: enhancedRfq.business_context?.business_objective || '',
                            budget_range: value as 'under_10k' | '10k_25k' | '25k_50k' | '50k_100k' | 'over_100k'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'under_10k', label: 'Under $10k' },
                          { value: '10k_25k', label: '$10k - $25k' },
                          { value: '25k_50k', label: '$25k - $50k' },
                          { value: '50k_100k', label: '$50k - $100k' },
                          { value: 'over_100k', label: 'Over $100k' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('business_context.budget_range')}
                      />

                      <FormField
                        label="Timeline Constraints"
                        value={enhancedRfq.business_context?.timeline_constraints || 'standard'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          business_context: {
                            ...enhancedRfq.business_context,
                            company_product_background: enhancedRfq.business_context?.company_product_background || '',
                            business_problem: enhancedRfq.business_context?.business_problem || '',
                            business_objective: enhancedRfq.business_context?.business_objective || '',
                            timeline_constraints: value as 'urgent_1_week' | 'fast_2_weeks' | 'standard_4_weeks' | 'extended_8_weeks' | 'flexible'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'urgent_1_week', label: 'Urgent (1 week)' },
                          { value: 'fast_2_weeks', label: 'Fast (2 weeks)' },
                          { value: 'standard_4_weeks', label: 'Standard (4 weeks)' },
                          { value: 'extended_8_weeks', label: 'Extended (8 weeks)' },
                          { value: 'flexible', label: 'Flexible' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('business_context.timeline_constraints')}
                      />
                    </div>
                  </div>
                )}

                {/* Research Objectives Section */}
                {currentSection === 'research_objectives' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🎯</span>
                      Research Objectives
                    </h2>

                    <div className="grid grid-cols-1 gap-6">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FormField
                          label="Research Audience"
                          value={enhancedRfq.research_objectives?.research_audience || ''}
                          onChange={(value) => setEnhancedRfq({
                            ...enhancedRfq,
                            research_objectives: {
                              ...enhancedRfq.research_objectives,
                              research_audience: value,
                              success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                              key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                            }
                          })}
                          placeholder="Describe respondent type, demographics, targeted segments..."
                          type="textarea"
                          rows={4}
                          isAutoFilled={isFieldAutoFilled('research_objectives.research_audience')}
                        />

                        <FormField
                          label="Success Criteria"
                        value={enhancedRfq.research_objectives?.success_criteria || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          research_objectives: {
                            ...enhancedRfq.research_objectives,
                            research_audience: enhancedRfq.research_objectives?.research_audience || '',
                            success_criteria: value,
                            key_research_questions: enhancedRfq.research_objectives?.key_research_questions || []
                          }
                        })}
                        placeholder="What defines success for this research? What decisions will flow from this?"
                        type="textarea"
                        rows={4}
                        isAutoFilled={isFieldAutoFilled('research_objectives.success_criteria')}
                        />
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <label className="block text-sm font-semibold text-gray-800">
                            Key Research Questions
                          </label>
                          <button
                            onClick={addResearchQuestion}
                            className="px-3 py-1 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
                          >
                            + Add Question
                          </button>
                        </div>
                      <div className="space-y-3">
                        {(enhancedRfq.research_objectives?.key_research_questions || []).map((question, index) => (
                          <div key={index} className="flex items-center space-x-3">
                            <div className="flex-1">
                              <input
                                type="text"
                                value={question}
                                onChange={(e) => updateResearchQuestion(index, e.target.value)}
                                placeholder={`Research question ${index + 1}...`}
                                className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300"
                              />
                            </div>
                            <button
                              onClick={() => removeResearchQuestion(index)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                        {(enhancedRfq.research_objectives?.key_research_questions || []).length === 0 && (
                          <div className="text-center py-8 text-gray-500">
                            <p>No research questions added yet.</p>
                            <p className="text-sm">Click "Add Question" to get started.</p>
                          </div>
                        )}
                      </div>
                      </div>

                      {/* Enhanced Research Objectives Fields */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FormField
                          label="Success Metrics"
                          value={enhancedRfq.research_objectives?.success_metrics || ''}
                          onChange={(value) => setEnhancedRfq({
                            ...enhancedRfq,
                            research_objectives: {
                              ...enhancedRfq.research_objectives,
                              research_audience: enhancedRfq.research_objectives?.research_audience || '',
                              success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                              key_research_questions: enhancedRfq.research_objectives?.key_research_questions || [],
                              success_metrics: value
                            }
                          })}
                          placeholder="How research success will be measured..."
                          type="textarea"
                          rows={3}
                          isAutoFilled={isFieldAutoFilled('research_objectives.success_metrics')}
                        />

                        <FormField
                          label="Validation Requirements"
                          value={enhancedRfq.research_objectives?.validation_requirements || ''}
                          onChange={(value) => setEnhancedRfq({
                            ...enhancedRfq,
                            research_objectives: {
                              ...enhancedRfq.research_objectives,
                              research_audience: enhancedRfq.research_objectives?.research_audience || '',
                              success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                              key_research_questions: enhancedRfq.research_objectives?.key_research_questions || [],
                              validation_requirements: value
                            }
                          })}
                          placeholder="What validation is needed..."
                          type="textarea"
                          rows={3}
                          isAutoFilled={isFieldAutoFilled('research_objectives.validation_requirements')}
                        />
                      </div>

                      <FormField
                        label="Measurement Approach"
                        value={enhancedRfq.research_objectives?.measurement_approach || 'mixed_methods'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          research_objectives: {
                            ...enhancedRfq.research_objectives,
                            research_audience: enhancedRfq.research_objectives?.research_audience || '',
                            success_criteria: enhancedRfq.research_objectives?.success_criteria || '',
                            key_research_questions: enhancedRfq.research_objectives?.key_research_questions || [],
                            measurement_approach: value as 'quantitative' | 'qualitative' | 'mixed_methods'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'quantitative', label: 'Quantitative' },
                          { value: 'qualitative', label: 'Qualitative' },
                          { value: 'mixed_methods', label: 'Mixed Methods' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('research_objectives.measurement_approach')}
                      />
                    </div>
                  </div>
                )}

                {/* Methodology Section */}
                {currentSection === 'methodology' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🔬</span>
                      Research Methodology
                    </h2>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Primary Methodology
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        {(['basic_survey', 'van_westendorp', 'gabor_granger', 'conjoint'] as const).map((method) => (
                          <button
                            key={method}
                            onClick={() => setEnhancedRfq({
                              ...enhancedRfq,
                              methodology: {
                                ...enhancedRfq.methodology,
                                primary_method: method
                              }
                            })}
                            className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                              enhancedRfq.methodology?.primary_method === method
                                ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                                : 'border-gray-200 hover:border-gray-300 text-gray-700'
                            }`}
                          >
                            <div className="font-medium capitalize">
                              {method.replace('_', ' ')}
                            </div>
                            <div className="text-xs mt-1 text-gray-500">
                              {method === 'basic_survey' && 'Standard survey'}
                              {method === 'van_westendorp' && 'Price sensitivity'}
                              {method === 'gabor_granger' && 'Price acceptance'}
                              {method === 'conjoint' && 'Trade-off analysis'}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <FormField
                      label="Stimuli Details"
                      value={enhancedRfq.methodology?.stimuli_details || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        methodology: {
                          ...enhancedRfq.methodology,
                          primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                          stimuli_details: value
                        }
                      })}
                      placeholder="Describe concepts, price ranges, features to test, or other stimuli details..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('methodology.stimuli_details')}
                    />

                    <FormField
                      label="Methodology Requirements"
                      value={enhancedRfq.methodology?.methodology_requirements || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        methodology: {
                          ...enhancedRfq.methodology,
                          primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                          methodology_requirements: value
                        }
                      })}
                      placeholder="Any specific methodology requirements, constraints, or considerations..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('methodology.methodology_requirements')}
                    />

                    {/* Enhanced Methodology Fields */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Complexity Level"
                        value={enhancedRfq.methodology?.complexity_level || 'standard'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          methodology: {
                            ...enhancedRfq.methodology,
                            primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                            stimuli_details: enhancedRfq.methodology?.stimuli_details || '',
                            methodology_requirements: enhancedRfq.methodology?.methodology_requirements || '',
                            complexity_level: value as 'simple' | 'intermediate' | 'complex' | 'expert_level'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'simple', label: 'Simple' },
                          { value: 'intermediate', label: 'Intermediate' },
                          { value: 'complex', label: 'Complex' },
                          { value: 'expert_level', label: 'Expert Level' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('methodology.complexity_level')}
                      />

                      <FormField
                        label="Sample Size Target"
                        value={enhancedRfq.methodology?.sample_size_target || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          methodology: {
                            ...enhancedRfq.methodology,
                            primary_method: enhancedRfq.methodology?.primary_method || 'basic_survey',
                            stimuli_details: enhancedRfq.methodology?.stimuli_details || '',
                            methodology_requirements: enhancedRfq.methodology?.methodology_requirements || '',
                            sample_size_target: value
                          }
                        })}
                        placeholder="e.g., 400-600 respondents"
                        type="text"
                        isAutoFilled={isFieldAutoFilled('methodology.sample_size_target')}
                      />
                    </div>
                  </div>
                )}

                {/* Survey Requirements Section */}
                {currentSection === 'survey_requirements' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">📋</span>
                      Survey Requirements
                    </h2>

                    <FormField
                      label="Sample Plan"
                      value={enhancedRfq.survey_requirements?.sample_plan || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: value,
                          must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || []
                        }
                      })}
                      placeholder="Include sample structure, LOI, recruiting criteria, target sample size..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.sample_plan')}
                    />


                    <FormField
                      label="Must-Have Questions"
                      value={(enhancedRfq.survey_requirements?.must_have_questions || []).join('\n')}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                          must_have_questions: value.split('\n').filter(q => q.trim())
                        }
                      })}
                      placeholder="List must-have questions (one per line)..."
                      type="textarea"
                      rows={4}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.must_have_questions')}
                    />

                    <FormField
                      label="Screener Requirements"
                      value={enhancedRfq.survey_requirements?.screener_requirements || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        survey_requirements: {
                          ...enhancedRfq.survey_requirements,
                          sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                          must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                          screener_requirements: value
                        }
                      })}
                      placeholder="Screener and respondent tagging rules, piping logic..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('survey_requirements.screener_requirements')}
                    />

                    <FormField
                      label="Rules & Definitions"
                      value={enhancedRfq.rules_and_definitions || ''}
                      onChange={(value) => setEnhancedRfq({
                        ...enhancedRfq,
                        rules_and_definitions: value
                      })}
                      placeholder="Rules, definitions, jargon feed, special terms..."
                      type="textarea"
                      rows={3}
                      isAutoFilled={isFieldAutoFilled('rules_and_definitions')}
                    />

                    {/* Enhanced Survey Requirements Fields */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Completion Time Target"
                        value={enhancedRfq.survey_requirements?.completion_time_target || '15_25_min'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          survey_requirements: {
                            ...enhancedRfq.survey_requirements,
                            sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                            must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                            completion_time_target: value as 'under_5min' | '5_10min' | '10_15min' | '15_20min' | '20_30min' | 'over_30min'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'under_5min', label: 'Under 5 minutes' },
                          { value: '5_10min', label: '5-10 minutes' },
                          { value: '10_15min', label: '10-15 minutes' },
                          { value: '15_20min', label: '15-20 minutes' },
                          { value: '20_30min', label: '20-30 minutes' },
                          { value: 'over_30min', label: 'Over 30 minutes' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('survey_requirements.completion_time_target')}
                      />

                      <FormField
                        label="Device Compatibility"
                        value={enhancedRfq.survey_requirements?.device_compatibility || 'all_devices'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          survey_requirements: {
                            ...enhancedRfq.survey_requirements,
                            sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                            must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                            device_compatibility: value as 'mobile_only' | 'desktop_only' | 'mobile_first' | 'desktop_first' | 'all_devices'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'mobile_only', label: 'Mobile Only' },
                          { value: 'desktop_only', label: 'Desktop Only' },
                          { value: 'mobile_first', label: 'Mobile First' },
                          { value: 'desktop_first', label: 'Desktop First' },
                          { value: 'all_devices', label: 'All Devices' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('survey_requirements.device_compatibility')}
                      />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Accessibility Requirements"
                        value={enhancedRfq.survey_requirements?.accessibility_requirements || 'basic'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          survey_requirements: {
                            ...enhancedRfq.survey_requirements,
                            sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                            must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                            accessibility_requirements: value as 'basic' | 'wcag_aa' | 'wcag_aaa' | 'custom'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'basic', label: 'Basic' },
                          { value: 'wcag_aa', label: 'WCAG AA' },
                          { value: 'wcag_aaa', label: 'WCAG AAA' },
                          { value: 'custom', label: 'Custom' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('survey_requirements.accessibility_requirements')}
                      />

                      <FormField
                        label="Data Quality Requirements"
                        value={enhancedRfq.survey_requirements?.data_quality_requirements || 'standard'}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          survey_requirements: {
                            ...enhancedRfq.survey_requirements,
                            sample_plan: enhancedRfq.survey_requirements?.sample_plan || '',
                            must_have_questions: enhancedRfq.survey_requirements?.must_have_questions || [],
                            data_quality_requirements: value as 'basic' | 'standard' | 'premium'
                          }
                        })}
                        type="select"
                        options={[
                          { value: 'basic', label: 'Basic' },
                          { value: 'standard', label: 'Standard' },
                          { value: 'premium', label: 'Premium' }
                        ]}
                        isAutoFilled={isFieldAutoFilled('survey_requirements.data_quality_requirements')}
                      />
                    </div>
                  </div>
                )}

                {/* Survey Structure Section */}
                {currentSection === 'survey_structure' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🏗️</span>
                      Survey Structure
                    </h2>

                    {/* Tab Navigation */}
                    <div className="border-b border-gray-200">
                      <nav className="-mb-px flex space-x-8">
                        {[
                          { id: 'sections', name: 'Sections', icon: '📋' },
                          { id: 'quality', name: 'Quality Preview', icon: '🎯' },
                          { id: 'text', name: 'Text Blocks', icon: '📝' },
                          { id: 'logic', name: 'Logic & Brand', icon: '⚙️' }
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setSurveyStructureTab(tab.id)}
                            className={`py-2 px-1 border-b-2 font-medium text-sm ${
                              surveyStructureTab === tab.id
                                ? 'border-yellow-500 text-yellow-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                          >
                            <span className="mr-2">{tab.icon}</span>
                            {tab.name}
                          </button>
                        ))}
                      </nav>
                    </div>

                    {/* Tab Content */}
                    {surveyStructureTab === 'sections' && (
                      <div className="space-y-4">
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <div className="text-blue-600 text-lg">ℹ️</div>
                            <div>
                              <h3 className="font-semibold text-blue-900 mb-1">QNR Section Structure</h3>
                              <p className="text-blue-800 text-sm">
                                Select which sections to include in your survey. All sections follow industry best practices.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 gap-3">
                          {[
                            { id: 'sample_plan', name: 'Sample Plan', description: 'Participant qualification criteria and quotas', required: true },
                            { id: 'screener', name: 'Screener', description: 'Initial qualification and demographics', required: true },
                            { id: 'brand_awareness', name: 'Brand/Product Awareness', description: 'Brand recall and awareness funnel', required: false },
                            { id: 'concept_exposure', name: 'Concept Exposure', description: 'Product concept introduction and reaction', required: false },
                            { id: 'methodology_section', name: 'Methodology', description: 'Research-specific questions (Pricing, Conjoint)', required: false },
                            { id: 'additional_questions', name: 'Additional Questions', description: 'Supplementary research questions', required: false },
                            { id: 'programmer_instructions', name: 'Programmer Instructions', description: 'Technical implementation notes', required: false }
                          ].map((section) => (
                            <div key={section.id} className={`flex items-center justify-between p-3 border rounded-lg ${
                              section.required ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
                            }`}>
                              <div className="flex items-center space-x-3">
                                <input
                                  type="checkbox"
                                  checked={section.required || (enhancedRfq.survey_structure?.qnr_sections || []).includes(section.id)}
                                  disabled={section.required}
                                  onChange={(e) => {
                                    if (!section.required) {
                                      const sections = [...(enhancedRfq.survey_structure?.qnr_sections || [])];
                                      if (e.target.checked) {
                                        sections.push(section.id);
                                      } else {
                                        const index = sections.indexOf(section.id);
                                        if (index > -1) sections.splice(index, 1);
                                      }
                                      setEnhancedRfq({
                                        ...enhancedRfq,
                                        survey_structure: {
                                          ...enhancedRfq.survey_structure,
                                          qnr_sections: sections
                                        }
                                      });
                                    }
                                  }}
                                  className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                                />
                                <div>
                                  <div className="font-medium text-gray-900 flex items-center">
                                    {section.name}
                                    {section.required && <span className="ml-2 text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Required</span>}
                                  </div>
                                  <div className="text-sm text-gray-600">{section.description}</div>
                                </div>
                              </div>
                              <div className="text-xs text-gray-500 font-mono">
                                #{['sample_plan', 'screener', 'brand_awareness', 'concept_exposure', 'methodology_section', 'additional_questions', 'programmer_instructions'].indexOf(section.id) + 1}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Quality Preview Tab */}
                    {surveyStructureTab === 'quality' && (
                      <div className="space-y-4">
                        {/* Compact Quality Overview */}
                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="text-blue-600 text-2xl">🎯</div>
                              <div>
                                <h4 className="font-semibold text-blue-900">Structure Validation Preview</h4>
                                <p className="text-blue-800 text-sm">AI will validate your survey against QNR best practices</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl font-bold text-blue-900">85%+</div>
                              <div className="text-xs text-blue-700">Target Quality</div>
                            </div>
                          </div>
                        </div>

                        {/* Compact Requirements Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          
                          {/* Essential Requirements - Always shown */}
                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex items-center mb-3">
                              <span className="text-green-600 text-lg mr-2">✅</span>
                              <h5 className="font-semibold text-green-900">Essential Requirements</h5>
                            </div>
                            <div className="space-y-2">
                              {[
                                {
                                  name: 'Recent participation check',
                                  tooltip: 'Prevents respondents from participating in multiple similar studies, ensuring data quality and preventing bias from professional survey takers.'
                                },
                                {
                                  name: 'Conflict of interest screening', 
                                  tooltip: 'Identifies respondents who work for competitors or have financial interests that could bias their responses.'
                                },
                                {
                                  name: 'Basic demographics',
                                  tooltip: 'Essential demographic questions (age, gender, location) for sample representativeness and quota management.'
                                },
                                {
                                  name: 'Category usage qualification',
                                  tooltip: 'Ensures respondents have relevant experience with the product category being researched.'
                                }
                              ].map((req, index) => (
                                <div key={index} className="flex items-center text-sm text-green-800 group">
                                  <span className="text-green-600 mr-2">•</span>
                                  <span className="flex-1">{req.name}</span>
                                  <div className="relative">
                                    <span className="text-green-600 cursor-help">ℹ️</span>
                                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                                      {req.tooltip}
                                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Conditional Requirements - Dynamic */}
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex items-center mb-3">
                              <span className="text-blue-600 text-lg mr-2">⚠️</span>
                              <h5 className="font-semibold text-blue-900">Smart Requirements</h5>
                              <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Auto-detected</span>
                            </div>
                            <div className="space-y-2">
                              {/* Brand Study Requirements */}
                              {(enhancedRfq.research_objectives?.key_research_questions?.some((obj: string) => 
                                obj.toLowerCase().includes('brand') || 
                                obj.toLowerCase().includes('awareness') ||
                                obj.toLowerCase().includes('recall')
                              ) || enhancedRfq.business_context?.company_product_background?.toLowerCase().includes('consumer')) && (
                                <>
                                  <div className="text-xs font-medium text-blue-700 mb-1 flex items-center group">
                                    Brand Study:
                                    <span className="ml-1 text-blue-600 cursor-help">ℹ️</span>
                                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                                      Brand studies require specific question sequences to measure awareness, consideration, and purchase intent.
                                      <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                  <div className="text-sm text-blue-800">• Unaided brand recall • Awareness funnel • Product satisfaction</div>
                                </>
                              )}

                              {/* Concept Testing Requirements */}
                              {enhancedRfq.research_objectives?.key_research_questions?.some((obj: string) => 
                                obj.toLowerCase().includes('concept') || 
                                obj.toLowerCase().includes('testing') ||
                                obj.toLowerCase().includes('evaluation')
                              ) && (
                                <>
                                  <div className="text-xs font-medium text-blue-700 mb-1 flex items-center group">
                                    Concept Testing:
                                    <span className="ml-1 text-blue-600 cursor-help">ℹ️</span>
                                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                                      Concept testing requires structured introduction, evaluation questions, and purchase intent measurement.
                                      <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                  <div className="text-sm text-blue-800">• Concept introduction • Overall impression • Purchase likelihood</div>
                                </>
                              )}

                              {/* Van Westendorp Requirements */}
                              {(enhancedRfq.methodology?.primary_method === 'van_westendorp' || 
                                enhancedRfq.methodology?.required_methodologies?.some((tag: string) => 
                                  tag.toLowerCase().includes('van westendorp') || 
                                  tag.toLowerCase().includes('pricing')
                                )) && (
                                <>
                                  <div className="text-xs font-medium text-orange-700 mb-1 flex items-center group">
                                    Van Westendorp Pricing:
                                    <span className="ml-1 text-orange-600 cursor-help">ℹ️</span>
                                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                                      Van Westendorp requires exactly 4 price questions: too cheap, bargain, getting expensive, too expensive. Missing any will fail validation.
                                      <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                  <div className="text-sm text-orange-800">• 4 price sensitivity questions (critical)</div>
                                </>
                              )}

                              {/* Gabor Granger Requirements */}
                              {(enhancedRfq.methodology?.primary_method === 'gabor_granger' || 
                                enhancedRfq.methodology?.required_methodologies?.some((tag: string) => 
                                  tag.toLowerCase().includes('gabor granger') || 
                                  tag.toLowerCase().includes('sequential')
                                )) && (
                                <>
                                  <div className="text-xs font-medium text-purple-700 mb-1 flex items-center group">
                                    Gabor Granger Pricing:
                                    <span className="ml-1 text-purple-600 cursor-help">ℹ️</span>
                                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                                      Gabor Granger uses sequential price testing where respondents see increasing prices until they reject. Requires proper price sequence logic.
                                      <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                  <div className="text-sm text-purple-800">• Sequential price acceptance questions</div>
                                </>
                              )}

                              {/* Default message if no conditional requirements */}
                              {!enhancedRfq.research_objectives?.key_research_questions?.some((obj: string) => 
                                obj.toLowerCase().includes('brand') || 
                                obj.toLowerCase().includes('awareness') ||
                                obj.toLowerCase().includes('recall') ||
                                obj.toLowerCase().includes('concept') || 
                                obj.toLowerCase().includes('testing') ||
                                obj.toLowerCase().includes('evaluation')
                              ) && !enhancedRfq.business_context?.company_product_background?.toLowerCase().includes('consumer') &&
                              enhancedRfq.methodology?.primary_method !== 'van_westendorp' &&
                              enhancedRfq.methodology?.primary_method !== 'gabor_granger' &&
                              !enhancedRfq.methodology?.required_methodologies?.some((tag: string) => 
                                tag.toLowerCase().includes('van westendorp') || 
                                tag.toLowerCase().includes('pricing') ||
                                tag.toLowerCase().includes('gabor granger') || 
                                tag.toLowerCase().includes('sequential')
                              ) && (
                                <div className="text-sm text-gray-600 italic">No additional requirements detected</div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Quality Assurance Note */}
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                          <div className="flex items-start space-x-2">
                            <div className="text-gray-500 text-sm">ℹ️</div>
                            <div className="text-sm text-gray-700">
                              <span className="font-medium">Quality Assurance:</span> Missing requirements will be flagged but won't block generation. 
                              Aim for 85%+ compliance for optimal survey quality.
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Text Blocks Tab */}
                    {surveyStructureTab === 'text' && (
                      <div className="space-y-4">
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <div className="text-yellow-600 text-lg">⚠️</div>
                            <div>
                              <h4 className="font-semibold text-yellow-900 mb-1">Text Introduction Requirements</h4>
                              <p className="text-yellow-800 text-sm">
                                Select text blocks to include in your survey for compliance and best practices.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                          {[
                            { id: 'study_intro', name: 'Study Introduction', description: 'Participant welcome and study overview', mandatory: true },
                            { id: 'concept_intro', name: 'Concept Introduction', description: 'Before concept evaluation sections', mandatory: false },
                            { id: 'product_usage', name: 'Product Usage Introduction', description: 'Before brand/usage awareness questions', mandatory: false },
                            { id: 'confidentiality_agreement', name: 'Confidentiality Agreement', description: 'For sensitive research topics', mandatory: false },
                            { id: 'methodology_instructions', name: 'Methodology Instructions', description: 'Method-specific instructions', mandatory: false },
                            { id: 'closing_thank_you', name: 'Closing Thank You', description: 'Final section thank you and next steps', mandatory: false }
                          ].map((textBlock) => (
                            <label key={textBlock.id} className={`flex items-start space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                              textBlock.mandatory
                                ? 'border-green-200 bg-green-50 cursor-not-allowed'
                                : 'border-gray-200 hover:bg-gray-50'
                            }`}>
                              <input
                                type="checkbox"
                                checked={textBlock.mandatory || (enhancedRfq.survey_structure?.text_requirements || []).includes(textBlock.id)}
                                disabled={textBlock.mandatory}
                                onChange={(e) => {
                                  if (!textBlock.mandatory) {
                                    const requirements = [...(enhancedRfq.survey_structure?.text_requirements || [])];
                                    if (e.target.checked) {
                                      requirements.push(textBlock.id);
                                    } else {
                                      const index = requirements.indexOf(textBlock.id);
                                      if (index > -1) requirements.splice(index, 1);
                                    }
                                    setEnhancedRfq({
                                      ...enhancedRfq,
                                      survey_structure: {
                                        ...enhancedRfq.survey_structure,
                                        text_requirements: requirements
                                      }
                                    });
                                  }
                                }}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500 mt-1"
                              />
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <span className="font-medium text-gray-900">{textBlock.name}</span>
                                  {textBlock.mandatory && (
                                    <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                                      Required
                                    </span>
                                  )}
                                </div>
                                <div className="text-sm text-gray-600 mt-1">{textBlock.description}</div>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Logic & Brand Tab */}
                    {surveyStructureTab === 'logic' && (
                      <div className="space-y-6">
                        {/* Survey Logic Section */}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <span className="text-blue-600 mr-2">⚙️</span>
                            Survey Logic Requirements
                          </h3>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.survey_logic?.requires_piping_logic || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  survey_logic: {
                                    ...enhancedRfq.survey_logic,
                                    requires_piping_logic: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Piping Logic</div>
                                <div className="text-sm text-gray-600">Carry forward responses between questions</div>
                              </div>
                            </label>

                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.survey_logic?.requires_sampling_logic || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  survey_logic: {
                                    ...enhancedRfq.survey_logic,
                                    requires_sampling_logic: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Sampling Logic</div>
                                <div className="text-sm text-gray-600">Randomization and quota controls</div>
                              </div>
                            </label>

                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.survey_logic?.requires_screener_logic || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  survey_logic: {
                                    ...enhancedRfq.survey_logic,
                                    requires_screener_logic: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Screener Logic</div>
                                <div className="text-sm text-gray-600">Advanced qualification routing</div>
                              </div>
                            </label>

                            <div className="lg:col-span-2">
                              <FormField
                                label="Custom Logic Requirements"
                                value={enhancedRfq.survey_logic?.custom_logic_requirements || ''}
                                onChange={(value) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  survey_logic: {
                                    ...enhancedRfq.survey_logic,
                                    custom_logic_requirements: value
                                  }
                                })}
                                placeholder="Describe any custom logic, skip patterns, or complex routing requirements..."
                                type="textarea"
                                rows={3}
                                isAutoFilled={isFieldAutoFilled('survey_logic.custom_logic_requirements')}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Brand & Usage Section */}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <span className="text-purple-600 mr-2">🏷️</span>
                            Brand & Usage Requirements
                          </h3>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.brand_usage_requirements?.brand_recall_required || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  brand_usage_requirements: {
                                    ...enhancedRfq.brand_usage_requirements,
                                    brand_recall_required: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Brand Recall Questions</div>
                                <div className="text-sm text-gray-600">Unaided and aided brand awareness</div>
                              </div>
                            </label>

                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.brand_usage_requirements?.brand_awareness_funnel || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  brand_usage_requirements: {
                                    ...enhancedRfq.brand_usage_requirements,
                                    brand_awareness_funnel: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Brand Awareness Funnel</div>
                                <div className="text-sm text-gray-600">Awareness → Consideration → Trial → Purchase</div>
                              </div>
                            </label>

                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.brand_usage_requirements?.brand_product_satisfaction || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  brand_usage_requirements: {
                                    ...enhancedRfq.brand_usage_requirements,
                                    brand_product_satisfaction: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Brand/Product Satisfaction</div>
                                <div className="text-sm text-gray-600">Satisfaction and loyalty metrics</div>
                              </div>
                            </label>

                            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={enhancedRfq.brand_usage_requirements?.usage_frequency_tracking || false}
                                onChange={(e) => setEnhancedRfq({
                                  ...enhancedRfq,
                                  brand_usage_requirements: {
                                    ...enhancedRfq.brand_usage_requirements,
                                    usage_frequency_tracking: e.target.checked
                                  }
                                })}
                                className="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                              />
                              <div>
                                <div className="font-medium text-gray-900">Usage Frequency Tracking</div>
                                <div className="text-sm text-gray-600">Frequency, occasion, and context tracking</div>
                              </div>
                            </label>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Advanced Classification Section */}
                {currentSection === 'advanced_classification' && (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🏷️</span>
                      Advanced Classification
                    </h2>

                    <div className="bg-purple-50 border border-purple-200 rounded-xl p-6">
                      <div className="flex items-start space-x-3">
                        <div className="text-purple-600 text-2xl">🎯</div>
                        <div>
                          <h3 className="font-semibold text-purple-900 mb-2">Research Classification</h3>
                          <p className="text-purple-800 text-sm">
                            Classify your research project to ensure proper methodology selection, compliance requirements,
                            and quality standards are applied.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <FormField
                        label="Industry Classification"
                        value={enhancedRfq.advanced_classification?.industry_classification || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          advanced_classification: {
                            ...enhancedRfq.advanced_classification,
                            industry_classification: value
                          }
                        })}
                        type="text"
                        placeholder="e.g., Technology, Healthcare, Financial Services, Retail, Automotive, Education"
                        isAutoFilled={isFieldAutoFilled('advanced_classification.industry_classification')}
                      />

                      <FormField
                        label="Respondent Classification"
                        value={enhancedRfq.advanced_classification?.respondent_classification || ''}
                        onChange={(value) => setEnhancedRfq({
                          ...enhancedRfq,
                          advanced_classification: {
                            ...enhancedRfq.advanced_classification,
                            respondent_classification: value
                          }
                        })}
                        type="text"
                        placeholder="e.g., B2C Consumers, B2B Professionals, Healthcare Workers, Students, General Public"
                        isAutoFilled={isFieldAutoFilled('advanced_classification.respondent_classification')}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Methodology Tags
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {[
                          'quantitative', 'qualitative', 'mixed_methods', 'attitudinal', 'behavioral',
                          'concept_testing', 'brand_tracking', 'pricing_research', 'segmentation',
                          'customer_satisfaction', 'market_sizing', 'competitive_analysis'
                        ].map((tag) => (
                          <label key={tag} className="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={(enhancedRfq.advanced_classification?.methodology_tags || []).includes(tag)}
                              onChange={(e) => {
                                const tags = [...(enhancedRfq.advanced_classification?.methodology_tags || [])];
                                if (e.target.checked) {
                                  tags.push(tag);
                                } else {
                                  const index = tags.indexOf(tag);
                                  if (index > -1) tags.splice(index, 1);
                                }
                                setEnhancedRfq({
                                  ...enhancedRfq,
                                  advanced_classification: {
                                    ...enhancedRfq.advanced_classification,
                                    methodology_tags: tags
                                  }
                                });
                              }}
                              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm font-medium text-gray-700 capitalize">
                              {tag.replace('_', ' ')}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Compliance Requirements
                      </label>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        {[
                          'Standard Data Protection', 'GDPR Compliance', 'HIPAA Compliance',
                          'SOC 2 Compliance', 'ISO 27001', 'Custom Compliance'
                        ].map((requirement) => (
                          <label key={requirement} className="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={(enhancedRfq.advanced_classification?.compliance_requirements || []).includes(requirement)}
                              onChange={(e) => {
                                const requirements = [...(enhancedRfq.advanced_classification?.compliance_requirements || [])];
                                if (e.target.checked) {
                                  requirements.push(requirement);
                                } else {
                                  const index = requirements.indexOf(requirement);
                                  if (index > -1) requirements.splice(index, 1);
                                }
                                setEnhancedRfq({
                                  ...enhancedRfq,
                                  advanced_classification: {
                                    ...enhancedRfq.advanced_classification,
                                    compliance_requirements: requirements
                                  }
                                });
                              }}
                              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm font-medium text-gray-700">{requirement}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Section */}
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    {/* Left side - Navigation buttons */}
                    <div className="flex items-center space-x-3">
                      {/* Previous Button */}
                      {sections.findIndex(s => s.id === currentSection) > 0 && !isDocumentProcessing && (
                        <button
                          onClick={() => {
                            const currentIndex = sections.findIndex(s => s.id === currentSection);
                            setCurrentSectionWithPersistence(sections[currentIndex - 1].id);
                          }}
                          className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                          </svg>
                          <span>Previous</span>
                        </button>
                      )}

                      {/* Next Button */}
                      {sections.findIndex(s => s.id === currentSection) < sections.length - 1 && !isDocumentProcessing && (
                        <button
                          onClick={() => {
                            const currentIndex = sections.findIndex(s => s.id === currentSection);
                            setCurrentSectionWithPersistence(sections[currentIndex + 1].id);
                          }}
                          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
                        >
                          <span>Next</span>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Right side - Preview & Generate */}
                    <div className="flex items-center space-x-3">

                      {/* Preview & Generate - only show on last section */}
                      {sections.findIndex(s => s.id === currentSection) === sections.length - 1 && (
                        <>
                          <div className="text-right mr-4">
                            <h3 className="text-lg font-semibold text-gray-900">Ready to Generate Your Survey?</h3>
                            <p className="text-gray-600 text-sm">
                              Review your requirements and generate a professional survey
                            </p>
                          </div>
                          <button
                            onClick={onPreview}
                            disabled={isLoading}
                            className="px-8 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl hover:from-yellow-600 hover:to-orange-600 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                          >
                            {isLoading ? (
                              <>
                                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span>Generating...</span>
                              </>
                            ) : (
                              <>
                                <span>Preview & Generate</span>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                                </svg>
                              </>
                            )}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">Reset Form</h3>
                <p className="text-sm text-gray-500">This action cannot be undone</p>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-700">
                Are you sure you want to reset the entire form? This will clear all data and return to the document upload section.
              </p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  clearEnhancedRfqState();
                  resetDocumentProcessingState();
                  setCurrentSectionWithPersistence('document');
                  // Clear localStorage
                  localStorage.removeItem('enhanced_rfq_current_section');
                  localStorage.removeItem('enhanced_rfq_initialized');
                  // Reset user data flag
                  hasUserData.current = false;
                  setShowResetConfirm(false);
                  addToast({
                    type: 'info',
                    title: 'Form Reset',
                    message: 'All form data has been cleared. You can start fresh.',
                    duration: 4000
                  });
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition-colors"
              >
                Reset Form
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};