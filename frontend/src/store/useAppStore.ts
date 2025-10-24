import { create } from 'zustand';
import { AppStore, RFQRequest, EnhancedRFQRequest, WorkflowState, ProgressMessage, GoldenExampleRequest, GoldenExampleFormState, ToastMessage, SurveyAnnotations, getQuestionCount, PendingReview, ReviewDecision, RFQFieldMapping, DocumentAnalysisResponse, Survey, SurveyTextContent, TextComplianceReport, AiRATextLabel, METHODOLOGY_TEXT_REQUIREMENTS, AIRA_LABEL_TO_TYPE_MAP, GoldenSection, GoldenQuestion } from '../types';
import { ErrorClassifier } from '../types/errors';
import { apiService } from '../services/api';
import { rfqTemplateService } from '../services/RFQTemplateService';

// Utility function to generate unique IDs
const generateId = () => Math.random().toString(36).substr(2, 9);

export const useAppStore = create<AppStore>((set, get) => ({
  // Model Loading State
  modelLoading: {
    loading: false,
    ready: false,
    progress: 0,
    estimatedSeconds: 0,
    phase: 'connecting' as 'connecting' | 'loading' | 'finalizing' | 'ready' | 'error',
    message: 'Initializing...'
  },

  setModelLoading: (state) => set((prev) => ({
    modelLoading: { ...prev.modelLoading, ...state }
  })),

  // RFQ Input State
  rfqInput: {
    title: '',
    description: '',
    product_category: '',
    target_segment: '',
    research_goal: ''
  },

  setRFQInput: (input) => set((state) => ({
    rfqInput: { ...state.rfqInput, ...input }
  })),

  // Enhanced RFQ State
  enhancedRfq: {
    title: '',
    description: '',
    business_context: {
      company_product_background: '',
      business_problem: '',
      business_objective: '',
      // Enhanced fields with defaults
      stakeholder_requirements: '',
      decision_criteria: '',
      budget_range: '25k_50k',
      timeline_constraints: 'standard_4_weeks'
    },
    research_objectives: {
      research_audience: '',
      success_criteria: '',
      key_research_questions: [],
      // Enhanced fields with defaults
      success_metrics: '',
      validation_requirements: '',
      measurement_approach: 'mixed_methods'
    },
    methodology: {
      primary_method: 'basic_survey',
      stimuli_details: '',
      methodology_requirements: '',
      // Enhanced fields with defaults
      complexity_level: 'intermediate',
      required_methodologies: [],
      sample_size_target: '400-600 respondents'
    },
    survey_requirements: {
      sample_plan: '',
      required_sections: [],
      must_have_questions: [],
      screener_requirements: '',
      // Enhanced fields with defaults
      completion_time_target: '15_20min',
      device_compatibility: 'all_devices',
      accessibility_requirements: 'basic',
      data_quality_requirements: 'standard'
    },
    advanced_classification: {
      industry_classification: '',
      respondent_classification: '',
      methodology_tags: [],
      compliance_requirements: ['Standard Data Protection']
    },
    // Smart defaults for survey structure
    survey_structure: {
      qnr_sections: [
        'sample_plan',
        'screener',
        'brand_awareness',
        'concept_exposure',
        'methodology_section',
        'additional_questions',
        'programmer_instructions'
      ],
      text_requirements: [
        'study_intro',
        'concept_intro',
        'product_usage',
        'confidentiality_agreement',
        'methodology_instructions',
        'closing_thank_you'
      ]
    },
    // Smart defaults for survey logic
    survey_logic: {
      requires_piping_logic: false,
      requires_sampling_logic: false,
      requires_screener_logic: true,
      custom_logic_requirements: ''
    },
    // Smart defaults for brand usage requirements
    brand_usage_requirements: {
      brand_recall_required: false,
      brand_awareness_funnel: false,
      brand_product_satisfaction: false,
      usage_frequency_tracking: false
    }
  },

  setEnhancedRfq: (input) => set((state) => {
    console.log('🔍 [Store] setEnhancedRfq called', { 
      input, 
      currentState: state.enhancedRfq,
      stackTrace: new Error().stack?.split('\n').slice(0, 5)
    });
    // Use spread operator to create completely new object without mutations
    const newEnhancedRfq = {
      ...state.enhancedRfq,
      ...input,
      // Handle nested objects specifically to prevent mutations
      ...(input.business_context && {
        business_context: {
          ...state.enhancedRfq.business_context,
          ...input.business_context
        }
      }),
      ...(input.research_objectives && {
        research_objectives: {
          ...state.enhancedRfq.research_objectives,
          ...input.research_objectives
        }
      }),
      ...(input.methodology && {
        methodology: {
          ...state.enhancedRfq.methodology,
          ...input.methodology
        }
      }),
      ...(input.survey_requirements && {
        survey_requirements: {
          ...state.enhancedRfq.survey_requirements,
          ...input.survey_requirements
        }
      }),
      ...(input.advanced_classification && {
        advanced_classification: {
          ...state.enhancedRfq.advanced_classification,
          ...input.advanced_classification
        }
      }),
      ...(input.survey_structure && {
        survey_structure: {
          ...state.enhancedRfq.survey_structure,
          ...input.survey_structure
        }
      }),
      ...(input.survey_logic && {
        survey_logic: {
          ...state.enhancedRfq.survey_logic,
          ...input.survey_logic
        }
      }),
      ...(input.brand_usage_requirements && {
        brand_usage_requirements: {
          ...state.enhancedRfq.brand_usage_requirements,
          ...input.brand_usage_requirements
        }
      })
    };

    // Auto-save to localStorage whenever Enhanced RFQ is updated
    get().persistEnhancedRfqState(newEnhancedRfq);

    return {
      enhancedRfq: newEnhancedRfq
    };
  }),

  // RFQ Templates State
  rfqTemplates: [],
  setRfqTemplates: (templates) => set({ rfqTemplates: templates }),
  selectedTemplate: undefined,
  setSelectedTemplate: (template) => set({ selectedTemplate: template }),

  // RFQ Quality Assessment State
  rfqAssessment: undefined,
  setRfqAssessment: (assessment) => set({ rfqAssessment: assessment }),

  // Workflow State
  workflow: {
    status: 'idle'
  } as WorkflowState,

  workflowTimeoutId: undefined as NodeJS.Timeout | undefined,

  setWorkflowState: (workflowState) => {
    const currentState = get();
    const currentProgress = currentState.workflow.progress || 0;
    const newProgress = workflowState.progress;
    

    // Apply smooth progress transition to prevent jarring jumps
    let smoothedProgress = newProgress;
    if (newProgress !== undefined && newProgress !== currentProgress) {
      // Only allow forward progress or legitimate resets
      if (newProgress >= currentProgress) {
        smoothedProgress = newProgress;
      } else if (newProgress === 0) {
        // Allow 0% reset (legitimate restart)
        smoothedProgress = newProgress;
      } else {
        // Keep current progress if new progress is backward
        console.log('🚫 [Store] Preventing backward progress jump from', currentProgress, 'to', newProgress);
        smoothedProgress = currentProgress;
      }
    }

    
    set((state) => ({
      workflow: {
        ...state.workflow,
        ...workflowState,
        ...(smoothedProgress !== undefined && { progress: smoothedProgress })
      }
    }));

    // Persist workflow state for recovery
    const updatedWorkflow = get().workflow;
    if (updatedWorkflow.workflow_id && (updatedWorkflow.status === 'started' || updatedWorkflow.status === 'in_progress' || updatedWorkflow.status === 'paused' || updatedWorkflow.status === 'completed')) {
      get().persistWorkflowState(updatedWorkflow.workflow_id, updatedWorkflow);
      console.log('💾 [Store] Workflow state persisted after setWorkflowState');
    }

    // Set up completion timeout protection
    const { workflowTimeoutId } = get();

    // Clear existing timeout
    if (workflowTimeoutId) {
      clearTimeout(workflowTimeoutId);
    }

    // Only set timeout for in-progress workflows
    if (workflowState.status === 'in_progress' || workflowState.status === 'started') {
      console.log('⏰ [Store] Setting workflow completion timeout (5 minutes)');
      const newTimeoutId = setTimeout(() => {
        const currentState = get().workflow;

        // Only force completion if still in progress
        if (currentState.status === 'in_progress' || currentState.status === 'started') {
          console.log('🚨 [Store] Workflow timeout reached - forcing completion to prevent hanging');

          // Try to fetch survey data to see if generation actually completed
          const surveyId = currentState.survey_id;
          if (surveyId) {
            get().fetchSurvey(surveyId).then(() => {
              console.log('✅ [Store] Survey data found - marking workflow as completed');
              get().setWorkflowState({ status: 'completed' });
            }).catch(() => {
              console.log('❌ [Store] No survey data found - marking workflow as failed');
              get().setWorkflowState({
                status: 'failed',
                error: 'Workflow timed out after 5 minutes. Please try again.'
              });
            });
          } else {
            console.log('❌ [Store] No survey ID - marking workflow as failed');
            get().setWorkflowState({
              status: 'failed',
              error: 'Workflow timed out after 5 minutes. Please try again.'
            });
          }

          // Show timeout notification
          get().addToast({
            type: 'warning',
            title: 'Workflow Timeout',
            message: 'The survey generation took longer than expected. Checking for completion...',
            duration: 8000
          });
        }
      }, 5 * 60 * 1000); // 5 minutes

      set({ workflowTimeoutId: newTimeoutId });
    } else if (workflowState.status === 'completed' || workflowState.status === 'failed') {
      // Clear timeout when workflow completes
      set({ workflowTimeoutId: undefined });
    }
  },

  // Survey State
  currentSurvey: undefined,
  setSurvey: (survey) => {
    console.log('🔧 [Store] setSurvey called with:', survey);
    set({ currentSurvey: survey });
    console.log('🔧 [Store] currentSurvey updated in store');
  },

  // Golden Examples State
  goldenExamples: [],
  setGoldenExamples: (examples) => set({ goldenExamples: examples }),

  // Golden Content State
  goldenSections: [],
  goldenQuestions: [],
  goldenContentAnalytics: null,

  // UI State
  selectedQuestionId: undefined,
  setSelectedQuestion: (id) => set({ selectedQuestionId: id }),

  // Annotation State
  isAnnotationMode: false,
  setAnnotationMode: (enabled) => set({ isAnnotationMode: enabled }),
  currentAnnotations: undefined,
  setCurrentAnnotations: (annotations) => set({ currentAnnotations: annotations }),

  // Toast State
  toasts: [],
  addToast: (toast) => {
    // Check for existing toasts with the same title and type to prevent duplicates
    const existingToast = get().toasts.find(t => 
      t.title === toast.title && 
      t.type === toast.type && 
      t.message === toast.message
    );
    
    if (existingToast) {
      console.log('🔄 [Store] Toast already exists, skipping duplicate:', toast.title);
      return;
    }
    
    const newToast: ToastMessage = {
      ...toast,
      id: generateId()
    };
    set((state) => ({
      toasts: [...state.toasts, newToast]
    }));
  },
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter(toast => toast.id !== id)
  })),

  // Human Review State
  pendingReviews: [],
  activeReview: undefined,
  setPendingReviews: (reviews) => set({ pendingReviews: reviews }),
  setActiveReview: (review) => set({ activeReview: review }),

  // Document Upload State
  documentContent: undefined,
  documentAnalysis: undefined,
  fieldMappings: [],
  isDocumentProcessing: false,
  documentUploadError: undefined,

  // Edit Tracking State
  editedFields: new Set<string>(),
  originalFieldValues: {},

  // WebSocket connection
  websocket: undefined as WebSocket | undefined,


  // Actions

  fetchSurvey: async (surveyId: string) => {
    // Validate survey ID before making request
    if (!surveyId || surveyId === 'undefined' || surveyId === 'null' || surveyId.trim() === '') {
      console.error('❌ [Store] Invalid survey ID provided:', surveyId);
      return;
    }

    try {
      console.log('🔍 [Store] Fetching survey:', surveyId);
      const survey = await apiService.fetchSurvey(surveyId);
      console.log('✅ [Store] Survey fetched successfully:', {
        surveyId: survey.survey_id,
        title: survey.title,
        questionsCount: getQuestionCount(survey)
      });
      
      
      set({ currentSurvey: survey });
      console.log('✅ [Store] Survey state updated, should trigger re-render and redirect');
    } catch (error) {
      console.error('❌ [Store] Failed to fetch survey:', error);
    }
  },


  loadPillarScoresAsync: async (surveyId: string) => {
    try {
      console.log('🏛️ [Store] Loading pillar scores asynchronously:', surveyId);
      console.log('🏛️ [Store] Current survey state:', {
        hasCurrentSurvey: !!get().currentSurvey,
        currentSurveyId: get().currentSurvey?.survey_id,
        targetSurveyId: surveyId
      });
      
      const pillarScores = await apiService.fetchPillarScores(surveyId);
      console.log('🏛️ [Store] Pillar scores received from API:', pillarScores);

      // Update the current survey with pillar scores
      const currentState = get();
      if (currentState.currentSurvey && currentState.currentSurvey.survey_id === surveyId) {
        console.log('🏛️ [Store] Updating current survey with pillar scores');
        set({
          currentSurvey: {
            ...currentState.currentSurvey,
            pillar_scores: pillarScores
          }
        });
        console.log('✅ [Store] Pillar scores loaded and updated in survey');
      } else {
        console.warn('⚠️ [Store] Current survey mismatch or not found:', {
          hasCurrentSurvey: !!currentState.currentSurvey,
          currentSurveyId: currentState.currentSurvey?.survey_id,
          targetSurveyId: surveyId
        });
      }

      return pillarScores;
    } catch (error) {
      console.error('❌ [Store] Failed to load pillar scores (non-blocking):', error);
      console.error('❌ [Store] Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      return null;
    }
  },

  connectWebSocket: (workflowId: string) => {
    // Connect to backend WebSocket server (port 8000)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = process.env.NODE_ENV === 'production' 
      ? window.location.host 
      : 'localhost:8000';
    const wsUrl = `${protocol}//${backendHost}/ws/survey/${workflowId}`;
    
    let retryCount = 0;
    const maxRetries = 10; // Increased retries for workflow timeouts
    const retryDelay = 2000; // Reduced delay for faster reconnection
    let keepAliveInterval: NodeJS.Timeout | null = null;
    
    const connect = () => {
      console.log(`Connecting to WebSocket (attempt ${retryCount + 1}/${maxRetries + 1}):`, wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        retryCount = 0; // Reset retry count on successful connection
        
        // Set up keep-alive ping every 30 seconds
        keepAliveInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        const message: ProgressMessage = JSON.parse(event.data);
        console.log('🔔 [Frontend] WebSocket message received:', message);
        console.log('🔍 [Frontend] Message type:', message.type);
        console.log('🔍 [Frontend] Message step:', message.step);
        console.log('🔍 [Frontend] Message percent:', message.percent);
        console.log('🔍 [Frontend] Message workflow_paused:', message.workflow_paused);
        console.log('🔍 [Frontend] Message pending_human_review:', message.pending_human_review);
        
        if (message.type === 'progress') {
          console.log('📊 [Frontend] Progress update received:', {
            step: message.step,
            percent: message.percent,
            message: message.message
          });

          // Check if this is actually a completion message disguised as progress
          if (message.step === 'completed' && message.percent === 100) {
            console.log('🎉 [WebSocket] Progress completion detected, updating workflow status to completed');

            // Show success toast for progress-based completion
            get().addToast({
              type: 'success',
              title: '🎉 Survey Complete!',
              message: 'Ready to collect insights!',
              duration: 8000
            });

            set((state) => ({
              workflow: {
                ...state.workflow,
                status: 'completed',
                current_step: message.step,
                progress: message.percent,
                message: message.message
              }
            }));

            // Clear persisted workflow state since completion is successful
            localStorage.removeItem('survey_workflow_state');

            // Try to fetch survey if we have a survey_id
            const currentWorkflow = get().workflow;
            if (currentWorkflow.survey_id) {
              console.log('📥 [WebSocket] Fetching survey after progress completion');
              get().fetchSurvey(currentWorkflow.survey_id).then(() => {
                // After successfully fetching the survey, load pillar scores with a small delay
                console.log('🏛️ [WebSocket] Survey fetched after progress completion, loading pillar scores');
                if (currentWorkflow.survey_id) {
                  // Add a small delay to prevent API call conflicts
                  setTimeout(() => {
                    if (currentWorkflow.survey_id) {
                      get().loadPillarScoresAsync(currentWorkflow.survey_id).catch((error) => {
                        console.warn('⚠️ [WebSocket] Failed to load pillar scores after progress completion:', error);
                      });
                    }
                  }, 2000); // Increased delay to 2 seconds to prevent overwhelming backend
                }
              }).catch((error) => {
                console.warn('⚠️ [WebSocket] Failed to fetch survey after progress completion:', error);
              });
            }

            console.log('✅ [Frontend] Workflow marked as completed via progress message');
          } else {
          // Normal progress update
          console.log('🔍 [Frontend] Updating workflow state with step:', message.step, 'progress:', message.percent);
          const newWorkflowState = {
            current_step: message.step,
            progress: message.percent,
            message: message.message
          };
          
          // Use setWorkflowState to get progress smoothing
          get().setWorkflowState(newWorkflowState);
          console.log('✅ [Frontend] Workflow state updated with step:', message.step, 'progress:', message.percent);
          }

          console.log('✅ [Frontend] Progress state updated');
        } else if (message.type === 'llm_content_update') {
          console.log('📝 [Frontend] Streaming content update received:', {
            step: message.step,
            percent: message.percent,
            data: message.data
          });

          // Update streaming stats in workflow state
          set((state) => ({
            workflow: {
              ...state.workflow,
              current_step: message.step,
              progress: message.percent,
              message: message.message,
              streamingStats: {
                questionCount: message.data?.questionCount || 0,
                sectionCount: message.data?.sectionCount || 0,
                currentActivity: message.data?.currentActivity || '',
                latestQuestions: message.data?.latestQuestions || [],
                currentSections: message.data?.currentSections || [],
                estimatedProgress: message.data?.estimatedProgress || 0,
                surveyTitle: message.data?.surveyTitle,
                elapsedTime: message.data?.elapsedTime
              }
            }
          }));

          console.log('✅ [Frontend] Streaming stats updated');
        } else if (message.type === 'human_review_required') {
          console.log('🛑 [WebSocket] Human review required:', message);
          
          // Check if we already have a human review in progress to prevent duplicates
          const currentState = get();
          if (currentState.workflow.status === 'paused' && currentState.workflow.pending_human_review) {
            console.log('🔄 [Frontend] Human review already in progress, skipping duplicate message');
            return;
          }
          
          console.log('🔍 [Frontend] Setting workflow status to paused');

          // Update workflow state to show human review is needed
          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'paused',
              current_step: message.step,
              progress: message.percent,
              message: message.message,
              workflow_paused: message.workflow_paused || true,
              pending_human_review: true,
              review_id: message.review_id,
              system_prompt: message.system_prompt,
              prompt_approved: false
            }
          }));
          
          // Show notification that human review is needed (only once)
          get().addToast({
            type: 'warning',
            title: '🛑 Human Review Required',
            message: 'Please review the AI-generated prompt before survey generation continues.',
            duration: 10000
          });
          
          console.log('✅ [Frontend] Human review state updated');
          console.log('🔍 [Frontend] Current workflow state after update:', get().workflow);
        } else if (message.type === 'workflow_resuming') {
          console.log('🔄 [WebSocket] Workflow resuming:', message);
          
          // Update workflow state to show it's resuming
          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'in_progress',
              current_step: message.step,
              progress: message.percent,
              message: message.message,
              workflow_paused: message.workflow_paused || false,
              pending_human_review: message.pending_human_review || false,
              prompt_approved: true
            }
          }));
          
          console.log('✅ [Frontend] Workflow resuming state updated');
        } else if (message.type === 'completed') {
          console.log('🎉 [WebSocket] Workflow completed:', message);

          // Validate completion message
          if (!message.survey_id) {
            console.error('❌ [WebSocket] Invalid completion message - missing survey_id');
            // Try to recover by checking current workflow for survey_id
            const currentWorkflow = get().workflow;
            if (currentWorkflow.survey_id) {
              console.log('🔄 [WebSocket] Using survey_id from current workflow state');
              message.survey_id = currentWorkflow.survey_id;
            } else {
              console.error('❌ [WebSocket] Cannot complete workflow - no survey_id available');
              return;
            }
          }

          // Handle completion with resilience
          console.log('✅ [WebSocket] Processing workflow completion with survey_id:', message.survey_id);

          // Show success toast notification
          get().addToast({
            type: 'success',
            title: '🎉 Survey Complete!',
            message: 'Your professional survey is ready to collect insights!',
            duration: 8000
          });

          // Update workflow status first
          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'completed',
              survey_id: message.survey_id
            }
          }));

          // Clear persisted workflow state since completion is successful
          localStorage.removeItem('survey_workflow_state');

          // Fetch the completed survey with retry mechanism
          const fetchWithRetry = async (surveyId: string, retries = 3) => {
            for (let i = 0; i < retries; i++) {
              try {
                await get().fetchSurvey(surveyId);
                console.log('✅ [WebSocket] Survey fetched successfully after', i + 1, 'attempts');
                return;
              } catch (error) {
                console.warn(`⚠️ [WebSocket] Survey fetch attempt ${i + 1} failed:`, error);
                if (i === retries - 1) {
                  throw error;
                }
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
              }
            }
          };

          fetchWithRetry(message.survey_id).then(() => {
            // After successfully fetching the survey, load pillar scores with a small delay
            console.log('🏛️ [WebSocket] Survey fetched, loading pillar scores');
            if (message.survey_id) {
              // Add a small delay to prevent API call conflicts
              setTimeout(() => {
                if (message.survey_id) {
                  get().loadPillarScoresAsync(message.survey_id).catch((error) => {
                    console.warn('⚠️ [WebSocket] Failed to load pillar scores after survey completion:', error);
                  });
                }
              }, 2000); // Increased delay to 2 seconds to prevent overwhelming backend
            }
          }).catch((error) => {
            console.error('❌ [WebSocket] Failed to fetch survey after retries:', error);
            get().addToast({
              type: 'error',
              title: 'Survey Error',
              message: 'Survey was generated but failed to load. Please try refreshing.',
              duration: 6000
            });
          });
          
          // Don't close WebSocket immediately - let it stay open for a bit
          // This prevents the frontend from going blank
          console.log('🔌 [WebSocket] Workflow completed successfully, keeping WebSocket open for a moment');
          
          // Close WebSocket after a delay to ensure user sees completion
          setTimeout(() => {
            if (keepAliveInterval) {
              clearInterval(keepAliveInterval);
            }
            console.log('🔌 [WebSocket] Closing WebSocket after delay');
            ws.close(1000, 'Workflow completed');
          }, 1000); // Reduced to 1 second delay to prevent blocking
        } else if (message.type === 'error') {
          console.error('Workflow error:', message);

          // Classify the error using our error classification system
          const detailedError = ErrorClassifier.classifyError(
            message.message || 'Survey generation failed',
            {
              component: 'WebSocket',
              action: 'survey_generation',
              step: get().workflow.current_step,
              additionalData: {
                workflowId: get().workflow.workflow_id,
                message: message
              }
            }
          );

          // Enhanced error toast with debug information
          get().addToast({
            type: 'error',
            title: detailedError.severity === 'critical' ? 'Critical Error' : 'Generation Failed',
            message: `${detailedError.userMessage}\n\nDebug Code: ${ErrorClassifier.generateDebugHandle(detailedError.code, new Date())}`,
            duration: detailedError.severity === 'critical' ? 10000 : 6000
          });

          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'failed',
              error: message.message,
              detailedError: detailedError
            }
          }));

          // Close WebSocket on error
          if (keepAliveInterval) {
            clearInterval(keepAliveInterval);
          }
          ws.close(1000, 'Workflow failed');
        } else if (message.type === 'pong') {
          // Keep-alive response, do nothing
          console.log('Keep-alive pong received');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('🔌 [WebSocket] WebSocket closed:', event.code, event.reason);
        
        // Clear keep-alive interval
        if (keepAliveInterval) {
          clearInterval(keepAliveInterval);
        }
        
        // If workflow is completed, don't retry - just preserve the state
        const currentStatus = get().workflow.status;
        const currentSurvey = get().currentSurvey;
        console.log('🔍 [WebSocket] Close handler state check:', { 
          currentStatus, 
          hasSurvey: !!currentSurvey,
          surveyId: currentSurvey?.survey_id 
        });
        
        if (currentStatus === 'completed') {
          console.log('✅ [WebSocket] Workflow completed, WebSocket closed gracefully - preserving survey data');
          return; // Don't retry or change state
        }
        
        // Only retry if it's not a normal closure and we haven't exceeded max retries
        // Also retry if the workflow is still in progress
        const shouldRetry = (event.code !== 1000 && retryCount < maxRetries) || 
                           (currentStatus === 'in_progress' && retryCount < maxRetries);
        
        if (shouldRetry) {
          retryCount++;
          console.log(`WebSocket connection lost. Retrying in ${retryDelay}ms... (${retryCount}/${maxRetries})`);
          
          setTimeout(() => {
            connect();
          }, retryDelay);
        } else if (retryCount >= maxRetries) {
          console.error('WebSocket connection failed after maximum retries');

          // Classify the connection failure error
          const detailedError = ErrorClassifier.classifyError(
            'WebSocket connection failed after multiple attempts',
            {
              component: 'WebSocket',
              action: 'connection_retry',
              additionalData: { retryCount, maxRetries }
            }
          );

          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'failed',
              error: 'WebSocket connection failed after multiple attempts',
              detailedError: detailedError
            }
          }));

          // Show enhanced error notification
          get().addToast({
            type: 'error',
            title: 'Connection Failed',
            message: `${detailedError.userMessage}\n\nDebug Code: ${ErrorClassifier.generateDebugHandle(detailedError.code, new Date())}`,
            duration: 10000
          });
        }
      };

      set({ websocket: ws });
    };

    connect();
  },

  disconnectWebSocket: () => {
    const { websocket } = get();
    if (websocket) {
      websocket.close();
      set({ websocket: undefined });
    }
  },

  // Golden Examples Actions
  fetchGoldenExamples: async () => {
    try {
      const response = await fetch('/api/v1/golden-pairs/');
      if (!response.ok) throw new Error('Failed to fetch golden examples');
      const backendData = await response.json();
      
      // Map backend response to frontend format
      const goldenExamples = backendData.map((item: any) => ({
        id: item.id,
        rfq_text: item.rfq_text,
        survey_json: item.survey_json as any, // Keep as-is for now
        methodology_tags: item.methodology_tags || [],
        industry_category: item.industry_category || 'General',
        research_goal: item.research_goal || 'Market Research',
        quality_score: item.quality_score || undefined,
        usage_count: item.usage_count || 0,
        created_at: new Date().toISOString() // Backend doesn't provide this
      }));
      
      get().setGoldenExamples(goldenExamples);
    } catch (error) {
      console.error('Failed to fetch golden examples:', error);
    }
  },

  createGoldenExample: async (example: GoldenExampleRequest) => {
    console.log('🏆 [Store] Starting golden example creation');
    console.log('📝 [Store] Example data:', {
      rfq_text_length: example.rfq_text?.length || 0,
      survey_json_keys: Object.keys(example.survey_json || {}),
      methodology_tags: example.methodology_tags,
      industry_category: example.industry_category,
      research_goal: example.research_goal,
      quality_score: example.quality_score
    });
    console.log('📊 [Store] Survey JSON:', example.survey_json);
    
    try {
      console.log('🚀 [Store] Sending POST request to /api/v1/golden-pairs/');
      const response = await fetch('/api/v1/golden-pairs/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(example),
      });
      
      console.log('📡 [Store] Response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ [Store] API error response:', errorText);
        throw new Error(`Failed to create golden example: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('✅ [Store] Golden example created successfully:', result);
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Success',
        message: 'Golden example created successfully',
        duration: 2000
      });
      
      console.log('🎉 [Store] Golden example creation completed successfully');
    } catch (error) {
      console.error('❌ [Store] Failed to create golden example:', error);
      console.error('❌ [Store] Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to create golden example. Please try again.',
        duration: 5000
      });
      
      throw error;
    }
  },

  updateGoldenExample: async (id: string, example: GoldenExampleRequest) => {
    try {
      const response = await fetch(`/api/v1/golden-pairs/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(example),
      });
      if (!response.ok) throw new Error('Failed to update golden example');
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Updated',
        message: 'Golden example updated successfully',
        duration: 2000
      });
    } catch (error) {
      console.error('Failed to update golden example:', error);
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to update golden example. Please try again.',
        duration: 5000
      });
      
      throw error;
    }
  },

  deleteGoldenExample: async (id: string) => {
    try {
      const response = await fetch(`/api/v1/golden-pairs/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete golden example');
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Deleted',
        message: 'Golden example deleted successfully',
        duration: 2000
      });
    } catch (error) {
      console.error('Failed to delete golden example:', error);
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to delete golden example. Please try again.',
        duration: 5000
      });
      
      throw error;
    }
  },

  // Annotation Actions
  saveAnnotations: async (annotations: SurveyAnnotations) => {
    try {
      // Transform frontend format to backend format
      const transformedRequest = {
        survey_id: annotations.surveyId,
        question_annotations: annotations.questionAnnotations.map(qa => {
          const questionIdToUse = qa.originalQuestionId || qa.questionId;
          console.log('🔍 [saveAnnotations] Question ID mapping:', { 
            questionId: qa.questionId, 
            originalQuestionId: qa.originalQuestionId, 
            questionIdToUse 
          });
          return {
            question_id: questionIdToUse, // Use original question ID with prefix if available
            required: qa.required,
            quality: qa.quality,
            relevant: qa.relevant,
            methodological_rigor: qa.pillars.methodologicalRigor,
            content_validity: qa.pillars.contentValidity,
            respondent_experience: qa.pillars.respondentExperience,
            analytical_value: qa.pillars.analyticalValue,
            business_impact: qa.pillars.businessImpact,
            comment: qa.comment,
            labels: Array.isArray(qa.labels) ? qa.labels : [],
            removed_labels: Array.isArray(qa.removedLabels) ? qa.removedLabels : [],
            annotator_id: qa.annotatorId || "current-user"
          };
        }),
        section_annotations: annotations.sectionAnnotations.map(sa => ({
          section_id: parseInt(sa.sectionId),
          quality: sa.quality,
          relevant: sa.relevant,
          methodological_rigor: sa.pillars.methodologicalRigor,
          content_validity: sa.pillars.contentValidity,
          respondent_experience: sa.pillars.respondentExperience,
          analytical_value: sa.pillars.analyticalValue,
          business_impact: sa.pillars.businessImpact,
          comment: sa.comment,
          labels: Array.isArray(sa.labels) ? sa.labels : [],
          annotator_id: sa.annotatorId || "current-user",
          // Advanced labeling fields
          section_classification: sa.section_classification,
          mandatory_elements: sa.mandatory_elements,
          compliance_score: sa.compliance_score
        })),
        overall_comment: annotations.overallComment,
        annotator_id: annotations.annotatorId || "current-user",
        // Advanced labeling fields for survey-level
        detected_labels: annotations.detected_labels,
        compliance_report: annotations.compliance_report,
        advanced_metadata: annotations.advanced_metadata
      };

      const response = await fetch(`/api/v1/annotations/survey/${annotations.surveyId}/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transformedRequest),
      });
      
      console.log('🔍 [saveAnnotations] Request payload:', transformedRequest);
      
      // Detailed logging for q1 changes
      const q1Annotation = transformedRequest.question_annotations.find(qa => qa.question_id === 'q1');
      if (q1Annotation) {
        console.log('🎯 [saveAnnotations] Q1 CHANGES BEING SENT TO SERVER:', {
          question_id: q1Annotation.question_id,
          required: q1Annotation.required,
          quality: q1Annotation.quality,
          relevant: q1Annotation.relevant,
          pillars: {
            methodological_rigor: q1Annotation.methodological_rigor,
            content_validity: q1Annotation.content_validity,
            respondent_experience: q1Annotation.respondent_experience,
            analytical_value: q1Annotation.analytical_value,
            business_impact: q1Annotation.business_impact
          },
          comment: q1Annotation.comment,
          labels: q1Annotation.labels,
          annotator_id: q1Annotation.annotator_id
        });
      }
      
      console.log('🔍 [saveAnnotations] Question annotations details:', transformedRequest.question_annotations.map(qa => ({
        question_id: qa.question_id,
        labels: qa.labels,
        removed_labels: qa.removed_labels,
        methodological_rigor: qa.methodological_rigor,
        content_validity: qa.content_validity,
        respondent_experience: qa.respondent_experience,
        analytical_value: qa.analytical_value,
        business_impact: qa.business_impact
      })));
      
      // Debug: Check if removed_labels is present in the request
      const hasRemovedLabels = transformedRequest.question_annotations.some(qa => 
        qa.hasOwnProperty('removed_labels')
      );
      console.log('🔍 [saveAnnotations] Has removed_labels field:', hasRemovedLabels);
      
      if (!hasRemovedLabels) {
        console.log('❌ [saveAnnotations] WARNING: No removed_labels field found in request!');
      }
      console.log('🔍 [saveAnnotations] Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ [saveAnnotations] API error:', errorText);
        throw new Error(`Failed to save annotations: ${response.status} ${errorText}`);
      }
      
      const result = await response.json();
      
      // Update current annotations
      set({ currentAnnotations: { ...annotations, ...result } });
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Annotations Saved',
        message: 'Survey annotations saved successfully',
        duration: 2000
      });
      
    } catch (error) {
      console.error('Failed to save annotations:', error);
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Save Error',
        message: 'Failed to save annotations. Please try again.',
        duration: 5000
      });
      
      throw error;
    }
  },

  loadAnnotations: async (surveyId: string) => {
    console.log('🔍 [Store] loadAnnotations called with surveyId:', surveyId);
    try {
      const response = await fetch(`/api/v1/surveys/${surveyId}/annotations`);
      
      if (response.status === 404) {
        console.log('🔍 [Store] No annotations found, creating empty structure');
        // No annotations exist yet, create empty structure
        const emptyAnnotations: SurveyAnnotations = {
          surveyId,
          questionAnnotations: [],
          sectionAnnotations: [],
          overallComment: '',
        };
        set({ currentAnnotations: emptyAnnotations });
        return;
      }
      
      if (!response.ok) throw new Error('Failed to load annotations');
      
      const backendAnnotations = await response.json();
      console.log('🔍 [Store] Loaded annotations from backend:', backendAnnotations);
      console.log('🔍 [Store] First question annotation:', backendAnnotations.question_annotations?.[0]);
      console.log('🔍 [Store] AI generated field:', backendAnnotations.question_annotations?.[0]?.ai_generated);
      
      // Transform backend format to frontend format
      const frontendAnnotations: SurveyAnnotations = {
        surveyId: backendAnnotations.survey_id,
        questionAnnotations: (() => {
          // Create a map to handle duplicate question IDs (prefer AI-generated annotations)
          const annotationMap = new Map();
          
          (backendAnnotations.question_annotations || []).forEach((qa: any) => {
            const originalQuestionId = qa.question_id;
            const mappedQuestionId = qa.question_id?.replace(`${surveyId}_`, '') || qa.question_id;
            console.log('🔍 [Store] Mapping question ID:', { originalQuestionId, mappedQuestionId, surveyId });
            
            const transformedAnnotation = {
              id: qa.id, // Database ID for API operations
              questionId: mappedQuestionId,
              originalQuestionId: originalQuestionId, // Store original question ID with prefix for API operations
              required: qa.required,
              quality: qa.quality,
              relevant: qa.relevant,
              pillars: {
                methodologicalRigor: qa.methodological_rigor,
                contentValidity: qa.content_validity,
                respondentExperience: qa.respondent_experience,
                analyticalValue: qa.analytical_value,
                businessImpact: qa.business_impact,
              },
              comment: qa.comment,
              labels: qa.labels || [], // Include labels field
              removedLabels: qa.removed_labels || [], // Include removed labels field
              annotatorId: qa.annotator_id,
              timestamp: qa.created_at,
              // AI annotation fields
              aiGenerated: qa.ai_generated,
              aiConfidence: qa.ai_confidence,
              humanVerified: qa.human_verified,
              generationTimestamp: qa.generation_timestamp,
              // Human override tracking fields
              humanOverridden: qa.human_overridden,
              overrideTimestamp: qa.override_timestamp,
              originalAiQuality: qa.original_ai_quality,
              originalAiRelevant: qa.original_ai_relevant,
              originalAiComment: qa.original_ai_comment
            };
            
            // If we already have an annotation for this question ID, prefer human annotations over AI-generated ones
            if (!annotationMap.has(mappedQuestionId) || (!qa.ai_generated && annotationMap.get(mappedQuestionId)?.aiGenerated)) {
              annotationMap.set(mappedQuestionId, transformedAnnotation);
              console.log('🔍 [Store] Stored annotation for:', mappedQuestionId, 'AI generated:', qa.ai_generated, 'originalQuestionId:', originalQuestionId);
            }
          });
          
          const annotations = Array.from(annotationMap.values());
          console.log('🔍 [Store] Final annotations count:', annotations.length);
          return annotations;
        })(),
        sectionAnnotations: (backendAnnotations.section_annotations || []).map((sa: any, index: number) => {
          // Use the actual section_id from the backend
          const mappedSectionId = String(sa.section_id);
          console.log('🔍 [Store] Mapping section ID from backend:', { backendSectionId: sa.section_id, mappedSectionId, index });
          return {
            id: sa.id, // Database ID for API operations
            sectionId: mappedSectionId,
            quality: sa.quality,
            relevant: sa.relevant,
            pillars: {
              methodologicalRigor: sa.methodological_rigor,
              contentValidity: sa.content_validity,
              respondentExperience: sa.respondent_experience,
              analyticalValue: sa.analytical_value,
              businessImpact: sa.business_impact,
            },
            comment: sa.comment,
            labels: sa.labels || [], // Include labels field
            annotatorId: sa.annotator_id,
            timestamp: sa.created_at,
            // Advanced labeling fields
            section_classification: sa.section_classification,
            mandatory_elements: sa.mandatory_elements,
            compliance_score: sa.compliance_score,
            // AI annotation fields
            aiGenerated: sa.ai_generated,
            aiConfidence: sa.ai_confidence,
            humanVerified: sa.human_verified,
            generationTimestamp: sa.generation_timestamp,
            // Human override tracking fields
            humanOverridden: sa.human_overridden,
            overrideTimestamp: sa.override_timestamp,
            originalAiQuality: sa.original_ai_quality,
            originalAiRelevant: sa.original_ai_relevant,
            originalAiComment: sa.original_ai_comment
          };
        }),
        overallComment: backendAnnotations.overall_comment || '',
        annotatorId: backendAnnotations.annotator_id,
        createdAt: backendAnnotations.created_at,
        updatedAt: backendAnnotations.updated_at,
        // Advanced labeling fields
        detected_labels: backendAnnotations.detected_labels,
        compliance_report: backendAnnotations.compliance_report,
        advanced_metadata: backendAnnotations.advanced_metadata
      };
      
      console.log('🔍 [Store] Setting currentAnnotations:', frontendAnnotations);
      set({ currentAnnotations: frontendAnnotations });
      
    } catch (error) {
      console.error('Failed to load annotations:', error);
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Load Error',
        message: 'Failed to load annotations.',
        duration: 5000
      });
    }
  },

  verifyAIAnnotation: async (surveyId: string, annotationId: number, annotationType: 'question' | 'section') => {
    console.log('🔍 [Store] verifyAIAnnotation called:', { surveyId, annotationId, annotationType });
    try {
      const response = await fetch(`/api/v1/pillar-scores/${surveyId}/verify-annotation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          annotation_id: annotationId,
          annotation_type: annotationType
        }),
      });
      
      if (!response.ok) throw new Error('Failed to verify annotation');
      
      const result = await response.json();
      console.log('✅ [Store] Annotation verified:', result);
      
      // Update the annotation in current annotations
      const { currentAnnotations } = get();
      if (currentAnnotations) {
        if (annotationType === 'question') {
          const updatedAnnotations = {
            ...currentAnnotations,
            questionAnnotations: currentAnnotations.questionAnnotations.map(qa => 
              qa.id === annotationId 
                ? { ...qa, humanVerified: true }
                : qa
            )
          };
          set({ currentAnnotations: updatedAnnotations });
        } else {
          const updatedAnnotations = {
            ...currentAnnotations,
            sectionAnnotations: currentAnnotations.sectionAnnotations.map(sa => 
              sa.id === annotationId 
                ? { ...sa, humanVerified: true }
                : sa
            )
          };
          set({ currentAnnotations: updatedAnnotations });
        }
      }
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Annotation Verified',
        message: `${annotationType} annotation verified successfully`,
        duration: 1500
      });
      
    } catch (error) {
      console.error('Failed to verify annotation:', error);
      
      // Show error toast
      get().addToast({
        type: 'error',
        title: 'Verification Error',
        message: 'Failed to verify annotation. Please try again.',
        duration: 5000
      });
      
      throw error;
    }
  },



  // Advanced Labeling Actions
  applyAdvancedLabeling: async (surveyId: string) => {
    try {
      const response = await fetch(`/api/annotations/survey/${surveyId}/advanced-labeling`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to apply advanced labeling: ${response.statusText}`);
      }

      const data = await response.json();

      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Advanced Labeling Applied',
        message: `Processed ${data.results.processed_questions} questions and ${data.results.processed_sections} sections`,
        duration: 3000
      });

      // Reload annotations to get the new data
      await get().loadAnnotations(surveyId);

      return data.results;
    } catch (error) {
      console.error('Failed to apply advanced labeling:', error);

      get().addToast({
        type: 'error',
        title: 'Advanced Labeling Failed',
        message: error instanceof Error ? error.message : 'Failed to apply advanced labeling',
        duration: 5000
      });

      throw error;
    }
  },

  fetchComplianceReport: async (surveyId: string) => {
    try {
      const response = await fetch(`/api/annotations/survey/${surveyId}/compliance-report`);

      if (response.status === 404) {
        return null; // No compliance report available
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch compliance report: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch compliance report:', error);
      throw error;
    }
  },

  fetchDetectedLabels: async (surveyId: string) => {
    try {
      const response = await fetch(`/api/annotations/survey/${surveyId}/detected-labels`);

      if (response.status === 404) {
        return null; // No detected labels available
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch detected labels: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch detected labels:', error);
      throw error;
    }
  },

  // Human Review Actions
  checkPendingReviews: async () => {
    try {
      const response = await fetch('/api/v1/reviews/pending');
      if (!response.ok) throw new Error('Failed to fetch pending reviews');
      
      const data = await response.json();
      get().setPendingReviews(data.reviews);
      
      return data;
    } catch (error) {
      console.error('Failed to check pending reviews:', error);
      // Silently fail - don't show error toast for review checks
      // This prevents annoying error messages when the review system is not available
    }
  },

  fetchReviewByWorkflow: async (workflowId: string): Promise<PendingReview | null> => {
    try {
      console.log('🔍 [Store] Fetching review for workflow:', workflowId);
      const response = await fetch(`/api/v1/reviews/workflow/${workflowId}`);
      console.log('📡 [Store] Review API response status:', response.status);
      
      if (response.status === 404) {
        console.log('⚠️ [Store] No review found for workflow:', workflowId);
        return null; // No review found
      }
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ [Store] Review API error:', response.status, errorText);
        throw new Error(`Failed to fetch review: ${response.status} ${errorText}`);
      }
      
      const review = await response.json();
      console.log('✅ [Store] Review data received:', review);
      return review;
    } catch (error) {
      console.error('❌ [Store] Failed to fetch review by workflow:', error);
      return null;
    }
  },

  submitReviewDecision: async (reviewId: number, decision: ReviewDecision) => {
    try {
      const response = await fetch(`/api/v1/reviews/${reviewId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
      });
      
      if (!response.ok) throw new Error('Failed to submit review decision');
      
      const result = await response.json();
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: `Review ${decision.decision}d`,
        message: result.message,
        duration: 4000
      });
      
      // If approved, handle workflow resumption
      if (decision.decision === 'approve') {
        const currentWorkflow = get().workflow;
        const currentReview = get().activeReview;
        
        if (currentWorkflow.workflow_id && currentReview) {
          console.log('🔄 [Frontend] Review approved, resuming workflow...');
          
          // Update workflow state to show it's resuming
          get().setWorkflowState({
            status: 'in_progress',
            current_step: 'resuming_generation',
            progress: 60,
            message: 'Human review approved - resuming survey generation...',
            workflow_paused: false,
            pending_human_review: false,
            prompt_approved: true,
            system_prompt: undefined  // Clear the prompt since it's approved
          });
          
          // The backend will send a workflow_resuming message when it actually resumes
          // No need to manually reconnect WebSocket
          
          // Show info toast about resumption
          get().addToast({
            type: 'info',
            title: '🔄 Workflow Resuming',
            message: 'Survey generation will continue automatically...',
            duration: 6000
          });
        }
      }
      
      // Update local state
      get().setActiveReview(undefined);
      get().checkPendingReviews(); // Refresh pending reviews
      
      return result;
    } catch (error) {
      console.error('Failed to submit review decision:', error);
      get().addToast({
        type: 'error',
        title: 'Review Error',
        message: 'Failed to submit review decision. Please try again.',
        duration: 5000
      });
      throw error;
    }
  },

  resumeReview: async (reviewId: number) => {
    try {
      // Update review status to in_progress
      const response = await fetch(`/api/v1/reviews/${reviewId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_status: 'in_progress' })
      });
      
      if (!response.ok) throw new Error('Failed to resume review');
      
      const review = await response.json();
      get().setActiveReview(review);
      
      // Navigate to review interface
      window.history.pushState({}, '', `/review/${reviewId}`);
      
    } catch (error) {
      console.error('Failed to resume review:', error);
      get().addToast({
        type: 'error',
        title: 'Resume Error',
        message: 'Failed to resume review. Please try again.',
        duration: 5000
      });
    }
  },

  persistWorkflowState: (workflowId: string, state: any) => {
    // Persist critical workflow state to localStorage for recovery
    const persistState = {
      workflow_id: workflowId,
      survey_id: state.survey_id,
      status: state.status,
      current_step: state.current_step,
      progress: state.progress,
      timestamp: Date.now()
    };
    
    try {
      localStorage.setItem('survey_workflow_state', JSON.stringify(persistState));
      console.log('💾 [Store] Workflow state persisted to localStorage');
    } catch (error) {
      console.error('Failed to persist workflow state:', error);
    }
  },

  resetWorkflow: async () => {
    console.log('🔄 [Store] Resetting workflow to idle state');

    // Clear any pending timeout
    const { workflowTimeoutId, workflow } = get();
    if (workflowTimeoutId) {
      clearTimeout(workflowTimeoutId);
    }

    // If there's an active survey, delete it from the database
    if (workflow.survey_id) {
      try {
        console.log('🗑️ [Store] Deleting cancelled survey from database:', workflow.survey_id);
        const response = await fetch(`/api/v1/survey/${workflow.survey_id}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          console.log('✅ [Store] Survey deleted successfully');
        } else {
          console.warn('⚠️ [Store] Failed to delete survey, but continuing with reset');
        }
      } catch (error) {
        console.error('❌ [Store] Error deleting survey:', error);
        // Continue with reset even if deletion fails
      }
    }

    // Clean up progress tracker if workflow_id exists
    if (workflow.workflow_id) {
      try {
        console.log('🧹 [Store] Cleaning up progress tracker for workflow:', workflow.workflow_id);
        await fetch(`/api/v1/survey/workflow/${workflow.workflow_id}/cleanup`, {
          method: 'POST'
        });
      } catch (error) {
        console.warn('⚠️ [Store] Failed to cleanup progress tracker:', error);
        // Continue with reset even if cleanup fails
      }
    }

    // Clear workflow state
    set((state) => ({
      workflow: { status: 'idle' },
      workflowTimeoutId: undefined,
      currentSurvey: undefined,
      rfqInput: {
        title: '',
        description: '',
        product_category: '',
        target_segment: '',
        research_goal: ''
      },
      // Also clear Enhanced RFQ state
      enhancedRfq: {
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
          required_sections: [],
          must_have_questions: []
        }
      },
      // Clear document-related state
      documentContent: undefined,
      documentAnalysis: undefined,
      fieldMappings: [],
      isDocumentProcessing: false,
      documentUploadError: undefined
    }));

    // Clear persisted state
    localStorage.removeItem('survey_workflow_state');

    // Disconnect any active WebSocket
    get().disconnectWebSocket();

    console.log('✅ [Store] Workflow reset completed');
  },

  recoverWorkflowState: async () => {
    try {
      console.log('🔄 [Store] Starting workflow state recovery...');
      
      // Check localStorage for interrupted workflows
      const persistedState = localStorage.getItem('survey_workflow_state');
      console.log('🔍 [Store] Persisted state found:', !!persistedState);
      
      if (persistedState) {
        const state = JSON.parse(persistedState);
        const hoursSinceUpdate = (Date.now() - state.timestamp) / (1000 * 60 * 60);

        console.log('🔍 [Store] Parsed persisted state:', {
          status: state.status,
          workflowId: state.workflow_id,
          surveyId: state.survey_id,
          progress: state.progress,
          hoursSinceUpdate: hoursSinceUpdate.toFixed(2)
        });

        // Only recover if less than 24 hours old
        if (hoursSinceUpdate < 24) {
          console.log('🔄 [Store] Recovering workflow state (less than 24 hours old):', state);

          // Check if there's a pending review for this workflow
          try {
            const review = await get().fetchReviewByWorkflow(state.workflow_id);
            if (review && review.review_status === 'pending') {
              console.log('🔍 [Store] Found pending review:', review);
              get().setActiveReview(review);

              // Show recovery notification
              get().addToast({
                type: 'info',
                title: '⏳ Review Found',
                message: 'You have a pending survey prompt review. Click to resume.',
                duration: 8000
              });
            }
          } catch (reviewError) {
            console.log('🔍 [Store] No pending review found for workflow:', state.workflow_id);
          }

          // Only restore workflow state if it's not completed or if we're on a page that should show it
          const currentPath = window.location.pathname;
          const shouldRestoreWorkflow = 
            state.status === 'in_progress' || 
            state.status === 'started' ||
            (state.status === 'completed' && currentPath === '/');

          console.log('🔍 [Store] Restoration decision:', {
            currentPath,
            stateStatus: state.status,
            shouldRestoreWorkflow,
            isInProgress: state.status === 'in_progress',
            isStarted: state.status === 'started',
            isCompletedOnRoot: state.status === 'completed' && currentPath === '/'
          });

          if (shouldRestoreWorkflow) {
            console.log('✅ [Store] Restoring workflow state:', state);
            get().setWorkflowState(state);

            // Try to reconnect WebSocket if workflow was in progress
            if (state.status === 'in_progress' && state.workflow_id) {
              get().connectWebSocket(state.workflow_id);
            }
          } else {
            // Clean up completed workflows that shouldn't be restored
            console.log('🧹 [Store] Not restoring workflow state:', {
              reason: 'shouldRestoreWorkflow is false',
              currentPath,
              stateStatus: state.status
            });
            console.log('🧹 [Store] Cleaning up completed workflow state for non-generator page');
            localStorage.removeItem('survey_workflow_state');
          }
        } else {
          // Clean up old state
          console.log('🧹 [Store] Cleaning up old workflow state (older than 24 hours)');
          localStorage.removeItem('survey_workflow_state');
        }
      } else {
        console.log('ℹ️ [Store] No persisted workflow state found');
      }
      
      console.log('✅ [Store] Workflow state recovery completed');

      // Check for pending reviews
      await get().checkPendingReviews();

    } catch (error) {
      console.error('Failed to recover workflow state:', error);
    }
  },

  // Helper function to convert basic RFQ to Enhanced RFQ with smart defaults
  createEnhancedRfqFromBasic: (basicRfq: RFQRequest): EnhancedRFQRequest => {
    // Auto-map product_category to industry_classification
    const industryMapping: Record<string, string> = {
      'technology': 'technology',
      'healthcare': 'healthcare',
      'financial': 'financial',
      'retail': 'retail',
      'education': 'education',
      'automotive': 'automotive',
      'real_estate': 'real_estate',
      'food': 'food_beverage',
      'travel': 'travel',
      'entertainment': 'entertainment'
    };

    // Auto-map target_segment to respondent_classification
    const respondentMapping: Record<string, string> = {
      'b2c': 'B2C',
      'b2b': 'B2B',
      'consumer': 'B2C',
      'business': 'B2B',
      'professional': 'healthcare_professional',
      'expert': 'expert',
      'student': 'student',
      'employee': 'employee'
    };

    // Auto-detect methodology tags from research_goal and description
    const detectMethodologyTags = (goal: string = '', description: string = ''): string[] => {
      const text = `${goal} ${description}`.toLowerCase();
      const tags: string[] = [];

      if (text.includes('price') || text.includes('pricing') || text.includes('cost')) tags.push('van_westendorp');
      if (text.includes('quantitative') || text.includes('statistical')) tags.push('quantitative');
      if (text.includes('qualitative') || text.includes('interview')) tags.push('qualitative');
      if (text.includes('demographic') || text.includes('age') || text.includes('gender')) tags.push('demographic');
      if (text.includes('behavior') || text.includes('usage')) tags.push('behavioral');
      if (text.includes('attitude') || text.includes('opinion')) tags.push('attitudinal');
      if (text.includes('nps') || text.includes('recommend')) tags.push('net_promoter');

      return tags.length > 0 ? tags : ['quantitative', 'attitudinal'];
    };

    const enhancedRfq: EnhancedRFQRequest = {
      title: basicRfq.title || 'Research Project',
      description: basicRfq.description,

      business_context: {
        company_product_background: `Research project for ${basicRfq.product_category || 'product/service'} targeting ${basicRfq.target_segment || 'target audience'}.`,
        business_problem: 'Business challenge requiring market research insights.',
        business_objective: basicRfq.research_goal || 'Generate actionable insights for business decisions.',
        // Smart defaults
        stakeholder_requirements: 'Standard business stakeholders require actionable insights.',
        decision_criteria: 'Clear, actionable insights with statistical significance.',
        budget_range: '25k_50k',
        timeline_constraints: 'standard_4_weeks'
      },

      research_objectives: {
        research_audience: basicRfq.target_segment || 'General consumer population',
        success_criteria: 'Generate statistically significant insights that inform business decisions.',
        key_research_questions: basicRfq.research_goal ? [basicRfq.research_goal] : ['What are the key insights for this research?'],
        // Smart defaults
        success_metrics: 'Statistical significance, actionable insights, clear recommendations.',
        validation_requirements: 'Standard validation checks for data quality and reliability.',
        measurement_approach: 'mixed_methods'
      },

      methodology: {
        primary_method: 'basic_survey',
        stimuli_details: 'To be determined based on research objectives.',
        methodology_requirements: 'Standard market research methodology.',
        // Smart defaults
        complexity_level: 'intermediate',
        required_methodologies: [],
        sample_size_target: '400-600 respondents'
      },

      survey_requirements: {
        sample_plan: 'Nationally representative sample with standard demographic quotas.',
        required_sections: ['Screener', 'Demographics', 'Awareness', 'Usage', 'Satisfaction'],
        must_have_questions: [],
        screener_requirements: 'Standard screener to ensure qualified respondents.',
        // Smart defaults
        completion_time_target: '15_20min',
        device_compatibility: 'all_devices',
        accessibility_requirements: 'basic',
        data_quality_requirements: 'standard'
      },

      advanced_classification: {
        industry_classification: industryMapping[basicRfq.product_category?.toLowerCase() || ''] || '',
        respondent_classification: respondentMapping[basicRfq.target_segment?.toLowerCase() || ''] || 'B2C',
        methodology_tags: detectMethodologyTags(basicRfq.research_goal, basicRfq.description),
        compliance_requirements: ['Standard Data Protection']
      },

      // Smart defaults for survey structure
      survey_structure: {
        qnr_sections: [
          'sample_plan',
          'screener',
          'brand_awareness',
          'concept_exposure',
          'methodology_section',
          'additional_questions',
          'programmer_instructions'
        ],
        text_requirements: [
          'study_intro',
          'concept_intro',
          'product_usage',
          'confidentiality_agreement',
          'methodology_instructions',
          'closing_thank_you'
        ]
      },

      // Smart defaults for survey logic
      survey_logic: {
        requires_piping_logic: false,
        requires_sampling_logic: false,
        requires_screener_logic: true,
        custom_logic_requirements: ''
      },

      // Smart defaults for brand usage requirements
      brand_usage_requirements: {
        brand_recall_required: false,
        brand_awareness_funnel: false,
        brand_product_satisfaction: false,
        usage_frequency_tracking: false
      },

      rules_and_definitions: 'Standard market research terminology and definitions apply.'
    };

    return enhancedRfq;
  },

  // Enhanced RFQ Actions
  submitEnhancedRFQ: async (rfq: EnhancedRFQRequest) => {
    try {
      // Prevent multiple simultaneous workflows
      const currentWorkflow = get().workflow;
      if (currentWorkflow.status === 'started' || currentWorkflow.status === 'in_progress') {
        console.warn('⚠️ [Store] Enhanced RFQ workflow already in progress, ignoring duplicate submission');
        get().addToast({
          type: 'warning',
          title: 'Generation in Progress',
          message: 'A survey is already being generated. Please wait for it to complete.',
          duration: 5000
        });
        return;
      }

      // Clear any existing survey data and stale workflow state
      set({
        currentSurvey: undefined,
        workflow: {
          status: 'idle'
        }
      });

      // Clear any persisted workflow state to prevent conflicts
      localStorage.removeItem('survey_workflow_state');

      console.log('🚀 [Store] Starting enhanced RFQ workflow submission');

      // Import the enhanced text converter
      const { createEnhancedDescription } = await import('../utils/enhancedRfqConverter');

      // Create enriched description that combines original text with structured data
      const enhancedDescription = createEnhancedDescription(rfq);

      // Get edited fields summary for generation context
      const editedFieldsSummary = get().getEditedFieldsSummary();
      
      // Convert enhanced RFQ to format that includes both enriched text and structured data
      const enhancedRfqPayload = {
        title: rfq.title,
        description: enhancedDescription, // 🎯 Key change: Use enriched description instead of basic description
        target_segment: rfq.research_objectives?.research_audience || '',
        enhanced_rfq_data: rfq, // 🎯 Send the full structured data for storage and analytics
        edited_fields: editedFieldsSummary // 🎯 Send edited fields for generation context
      };

      console.log('🚀 [Enhanced RFQ] Submitting with enriched description and structured data:', {
        originalLength: rfq.description?.length || 0,
        enhancedLength: enhancedDescription.length,
        hasObjectives: (rfq.research_objectives?.key_research_questions?.length || 0) > 0,
        hasConstraints: false, // constraints field not in EnhancedRFQRequest interface
        hasStakeholders: false, // stakeholders field not in EnhancedRFQRequest interface
        structuredDataSize: JSON.stringify(rfq).length,
        editedFieldsCount: editedFieldsSummary.length,
        editedFields: editedFieldsSummary.map(f => f.field)
      });

      // Send enhanced payload directly to API to bypass legacy submitRFQ conversion
      const response = await fetch('/api/v1/rfq/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(enhancedRfqPayload),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit enhanced RFQ: ${response.statusText}`);
      }

      const responseData = await response.json();

      // Update workflow state with response
      set((state) => ({
        workflow: {
          ...state.workflow,
          workflow_id: responseData.workflow_id,
          survey_id: responseData.survey_id,
          status: 'in_progress',
          progress: 0,
          current_step: 'initializing_workflow',
          message: 'Starting enhanced survey generation workflow...'
        }
      }));

      // Persist workflow state immediately for recovery
      const currentState = get().workflow;
      get().persistWorkflowState(responseData.workflow_id, currentState);
      console.log('💾 [Store] Enhanced RFQ workflow state persisted after submission');

      // Show info toast that enhanced generation has started
      get().addToast({
        type: 'info',
        title: 'Enhanced Survey Generation Started',
        message: 'Your enhanced survey is being generated with your objectives, constraints, and stakeholder requirements!',
        duration: 5000
      });

      // Connect to WebSocket for progress updates
      get().connectWebSocket(responseData.workflow_id);

      // Store enhanced RFQ data for future reference and analytics
      localStorage.setItem('enhanced_rfq_data', JSON.stringify({
        ...rfq,
        enhanced_description: enhancedDescription,
        submission_timestamp: new Date().toISOString()
      }));

    } catch (error) {
      console.error('Failed to submit enhanced RFQ:', error);
      throw error;
    }
  },

  fetchRfqTemplates: async () => {
    try {
      const templates = await rfqTemplateService.getTemplates();
      get().setRfqTemplates(templates);
    } catch (error) {
      console.error('Failed to fetch RFQ templates:', error);
      get().addToast({
        type: 'error',
        title: 'Template Error',
        message: 'Failed to load RFQ templates',
        duration: 5000
      });
    }
  },

  assessRfqQuality: async (rfq: EnhancedRFQRequest) => {
    try {
      const assessment = await rfqTemplateService.assessQuality(rfq);
      get().setRfqAssessment(assessment);
    } catch (error) {
      console.error('Failed to assess RFQ quality:', error);
    }
  },

  generateRfqSuggestions: async (partialRfq: Partial<EnhancedRFQRequest>): Promise<string[]> => {
    try {
      const suggestions = await rfqTemplateService.generateSuggestions(partialRfq);
      return suggestions;
    } catch (error) {
      console.error('Failed to generate RFQ suggestions:', error);
      return [];
    }
  },

  // Edit Tracking Actions
  trackFieldEdit: (fieldPath: string, newValue: any) => {
    const state = get();
    
    // Get the current value using the field path
    const getNestedValue = (obj: any, path: string) => {
      return path.split('.').reduce((current, key) => current?.[key], obj);
    };
    
    const currentFieldValue = getNestedValue(state.enhancedRfq, fieldPath);
    
    // If this is the first time we're tracking this field, store the original value
    if (!state.originalFieldValues[fieldPath]) {
      state.originalFieldValues[fieldPath] = currentFieldValue;
    }
    
    // Check if the new value is different from the original
    const originalValue = state.originalFieldValues[fieldPath];
    const hasChanged = JSON.stringify(newValue) !== JSON.stringify(originalValue);
    
    if (hasChanged) {
      state.editedFields.add(fieldPath);
    } else {
      state.editedFields.delete(fieldPath);
    }
    
    console.log(`🔍 [Edit Tracking] Field ${fieldPath}: ${hasChanged ? 'edited' : 'reverted'}`, {
      original: originalValue,
      newValue: newValue,
      editedFields: Array.from(state.editedFields)
    });
  },

  getEditedFieldsSummary: () => {
    const state = get();
    const editedFields = Array.from(state.editedFields);
    const summary = editedFields.map(fieldPath => ({
      field: fieldPath,
      originalValue: state.originalFieldValues[fieldPath],
      currentValue: (() => {
        const getNestedValue = (obj: any, path: string) => {
          return path.split('.').reduce((current, key) => current?.[key], obj);
        };
        return getNestedValue(state.enhancedRfq, fieldPath);
      })()
    }));
    
    console.log('📝 [Edit Tracking] Edited fields summary:', summary);
    return summary;
  },

  clearEditTracking: () => {
    set({
      editedFields: new Set<string>(),
      originalFieldValues: {}
    });
  },

  // Document Upload Actions
  uploadDocument: async (file: File, sessionId?: string): Promise<DocumentAnalysisResponse> => {
    set({ isDocumentProcessing: true, documentUploadError: undefined });
    get().persistDocumentProcessingState(true, sessionId);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (sessionId) {
        formData.append('session_id', sessionId);
      }

      // Add timeout to prevent hanging indefinitely
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 900000); // 15 minute timeout for LLM processing

      const response = await fetch('/api/v1/rfq/upload-document', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const result: DocumentAnalysisResponse = await response.json();

      // Accept all field mappings regardless of confidence
      const incomingMappings = result.rfq_analysis.field_mappings || [];
      const autoAccepted = incomingMappings.map(m => ({
        ...m,
        user_action: 'accepted' as const
      }));

      // Update store with analysis results and auto-accepted mappings
      set({
        documentContent: result.document_content,
        documentAnalysis: result.rfq_analysis,
        fieldMappings: autoAccepted,
        isDocumentProcessing: false
      });

      // Auto-apply accepted mappings immediately
      const acceptedCount = autoAccepted.filter(m => m.user_action === 'accepted').length;
      console.log('🔍 [Document Upload] Field mappings received:', autoAccepted.length, 'mappings');
      console.log('🔍 [Document Upload] Accepted count:', acceptedCount);
      console.log('🔍 [Document Upload] Field mappings details:', autoAccepted);
      
      if (acceptedCount > 0) {
        // Apply mappings immediately using the accepted mappings
        let rfqUpdates = get().buildRFQUpdatesFromMappings(autoAccepted.filter(m => m.user_action === 'accepted'));
        console.log('🔍 [Document Upload] RFQ updates generated for', Object.keys(rfqUpdates).length, 'sections');
        console.log('🔍 [Document Upload] RFQ updates details:', rfqUpdates);

        // Apply methodology-based intelligence
        rfqUpdates = get().applyMethodologyIntelligence(rfqUpdates);

        get().setEnhancedRfq(rfqUpdates);
        console.log('🔍 [Document Upload] Enhanced RFQ updated in store');

        get().addToast({
          type: 'success',
          title: 'Auto-filled from Document',
          message: `Applied ${acceptedCount} extracted fields. Review in the sections below. Click "Reset Form" to start fresh with a new RFQ.`,
          duration: 8000
        });
      }

      // IMPORTANT: Persist state AFTER auto-fill logic completes
      // This ensures the enhancedRfq has the auto-filled data
      get().persistDocumentProcessingState(false);

      return result;
    } catch (error) {
      let errorMessage = error instanceof Error ? error.message : 'Document upload failed';

      // Handle timeout errors
      if (error instanceof Error && error.name === 'AbortError') {
        errorMessage = 'Document processing timed out after 15 minutes. The document may be too complex. Please try again or contact support.';
      }

      // Enhance error messages with user guidance
      if (errorMessage.includes('AI service not configured')) {
        errorMessage = 'AI service is not configured. Please contact support to enable document processing.';
      } else if (errorMessage.includes('timeout')) {
        errorMessage = 'Document processing timed out. Try uploading a smaller document or try again later.';
      } else if (errorMessage.includes('Network error') || errorMessage.includes('fetch')) {
        errorMessage = 'Network error. Please check your internet connection and try again.';
      } else if (errorMessage.includes('413') || errorMessage.includes('too large')) {
        errorMessage = 'File is too large. Please upload a document smaller than 10MB.';
      } else if (errorMessage.includes('400') || errorMessage.includes('Bad Request')) {
        errorMessage = 'Invalid file format. Please upload a valid DOCX document.';
      } else if (errorMessage.includes('500') || errorMessage.includes('Internal Server Error')) {
        errorMessage = 'Server error. The service is temporarily unavailable. Please try again in a few minutes.';
      }

      set({
        documentUploadError: errorMessage,
        isDocumentProcessing: false
      });
      get().persistDocumentProcessingState(false);
      
      throw new Error(errorMessage);
    }
  },

  analyzeText: async (text: string, filename = 'text_input.txt'): Promise<DocumentAnalysisResponse> => {
    set({ isDocumentProcessing: true, documentUploadError: undefined });
    get().persistDocumentProcessingState(true);

    try {
      const response = await fetch('/api/v1/rfq/analyze-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, filename }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Text analysis failed: ${response.statusText}`);
      }

      const result: DocumentAnalysisResponse = await response.json();

      // Accept all field mappings regardless of confidence
      const incomingMappings = result.rfq_analysis.field_mappings || [];
      const autoAccepted = incomingMappings.map(m => ({
        ...m,
        user_action: 'accepted' as const
      }));

      // Update store with analysis results and auto-accepted mappings
      set({
        documentContent: result.document_content,
        documentAnalysis: result.rfq_analysis,
        fieldMappings: autoAccepted,
        isDocumentProcessing: false
      });
      get().persistDocumentProcessingState(false);

      // Auto-apply if we have accepted mappings
      if (autoAccepted.some(m => m.user_action === 'accepted')) {
        get().applyDocumentMappings();
        get().addToast({
          type: 'success',
          title: 'Auto-filled from Text',
          message: `Applied ${autoAccepted.filter(m => m.user_action === 'accepted').length} extracted fields. Click "Reset Form" to start fresh with a new RFQ.`,
          duration: 8000
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Text analysis failed';
      set({
        documentUploadError: errorMessage,
        isDocumentProcessing: false
      });
      get().persistDocumentProcessingState(false);
      
      throw error;
    }
  },

  acceptFieldMapping: (field: string, value: any) => {
    set((state) => ({
      fieldMappings: state.fieldMappings.map(mapping =>
        mapping.field === field
          ? { ...mapping, user_action: 'accepted' as const }
          : mapping
      )
    }));
    get().persistDocumentProcessingState(false); // Persist after user interaction
  },

  rejectFieldMapping: (field: string) => {
    set((state) => ({
      fieldMappings: state.fieldMappings.map(mapping =>
        mapping.field === field
          ? { ...mapping, user_action: 'rejected' as const }
          : mapping
      )
    }));
    get().persistDocumentProcessingState(false); // Persist after user interaction
  },

  editFieldMapping: (field: string, value: any) => {
    set((state) => ({
      fieldMappings: state.fieldMappings.map(mapping =>
        mapping.field === field
          ? { ...mapping, value, user_action: 'edited' as const }
          : mapping
      )
    }));
    get().persistDocumentProcessingState(false); // Persist after user interaction
  },

  clearDocumentData: () => {
    set({
      documentContent: undefined,
      documentAnalysis: undefined,
      fieldMappings: [],
      documentUploadError: undefined
    });
    // Clear persisted state when clearing document data
    localStorage.removeItem('document_processing_state');
  },

  // Helper function to build RFQ updates from field mappings (simplified schema)
  buildRFQUpdatesFromMappings: (mappings: RFQFieldMapping[]): Partial<EnhancedRFQRequest> => {
    const rfqUpdates: Partial<EnhancedRFQRequest> = {};
    const validationErrors: string[] = [];

    // Helper function to validate and map enum values
    const validateAndMapEnum = (value: any, fieldName: string, validValues: string[], defaultValue?: string): string => {
      if (!value) return defaultValue || validValues[0];
      
      const stringValue = String(value).toLowerCase();
      
      // Try exact match first
      if (validValues.includes(stringValue)) {
        return stringValue;
      }
      
      // Try partial matches for common variations
      const partialMatches: Record<string, string> = {
        'standard': 'intermediate',
        '10k_50k': '25k_50k',
        '15_25_min': '15_20min',
        'both': 'all_devices',
        'rush': 'urgent_1_week',
        'flexible': 'flexible',
        'simple': 'simple',
        'advanced': 'complex',
        'expert': 'expert_level'
      };
      
      if (partialMatches[stringValue]) {
        return partialMatches[stringValue];
      }
      
      // Try to find closest match
      const closestMatch = validValues.find(valid => 
        valid.includes(stringValue) || stringValue.includes(valid)
      );
      
      if (closestMatch) {
        validationErrors.push(`Mapped '${value}' to '${closestMatch}' for ${fieldName}`);
        return closestMatch;
      }
      
      // Use default or first valid value
      const fallback = defaultValue || validValues[0];
      validationErrors.push(`Invalid value '${value}' for ${fieldName}, using fallback '${fallback}'`);
      return fallback;
    };

    mappings.forEach(mapping => {
      const value = mapping.value;
      
      // Extract field name from dot notation (e.g., 'business_context.company_product_background' -> 'company_product_background')
      const fieldName = mapping.field.includes('.') ? mapping.field.split('.').pop() : mapping.field;

      switch (fieldName) {
        // Basic Info
        case 'title':
          rfqUpdates.title = value;
          break;
        case 'description':
          rfqUpdates.description = value;
          break;
        
        // Direct Enhanced RFQ field mappings (from document parser)
        case 'company_product_background':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.company_product_background = value;
          break;
        case 'business_problem':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.business_problem = value;
          break;
        case 'business_objective':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.business_objective = value;
          break;
        case 'research_audience':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.research_audience = value;
          break;
        case 'success_criteria':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_criteria = value;
          break;
        case 'key_research_questions':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.key_research_questions = Array.isArray(value) ? value : (value || '').split('\n').filter((q: string) => q.trim());
          break;
        case 'stimuli_details':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey', stimuli_details: '', methodology_requirements: '' };
          rfqUpdates.methodology.stimuli_details = value;
          break;
        case 'methodology_requirements':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey', stimuli_details: '', methodology_requirements: '' };
          rfqUpdates.methodology.methodology_requirements = value;
          break;
        case 'sample_plan':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.sample_plan = value;
          break;
        case 'must_have_questions':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.must_have_questions = Array.isArray(value) ? value : (value || '').split('\n').filter((q: string) => q.trim());
          break;
        
        // Legacy Basic RFQ fields that map to Enhanced RFQ
        case 'research_goal':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_criteria = value;
          break;
        case 'target_segment':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.research_audience = value;
          break;
        case 'product_category':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.company_product_background = value;
          break;
        case 'objectives':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          // Convert objectives string to array of questions
          const objectives = Array.isArray(value) ? value : (value || '').split('\n').filter((obj: string) => obj.trim());
          rfqUpdates.research_objectives.key_research_questions = objectives;
          break;

        // Advanced Business Context fields
        case 'stakeholder_requirements':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.stakeholder_requirements = value;
          break;
        case 'decision_criteria':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.decision_criteria = value;
          break;
        case 'budget_range':
        case 'budget':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.budget_range = validateAndMapEnum(
            value, 
            'budget_range', 
            ['under_10k', '10k_25k', '25k_50k', '50k_100k', 'over_100k'],
            '25k_50k'
          ) as 'under_10k' | '10k_25k' | '25k_50k' | '50k_100k' | 'over_100k';
          break;
        case 'timeline_constraints':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.timeline_constraints = validateAndMapEnum(
            value, 
            'timeline_constraints', 
            ['urgent_1_week', 'fast_2_weeks', 'standard_4_weeks', 'extended_8_weeks', 'flexible'],
            'standard_4_weeks'
          ) as 'urgent_1_week' | 'fast_2_weeks' | 'standard_4_weeks' | 'extended_8_weeks' | 'flexible';
          break;

        // Advanced Research Objectives fields
        case 'success_metrics':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_metrics = value;
          break;
        case 'validation_requirements':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.validation_requirements = value;
          break;
        case 'measurement_approach':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          // Map measurement approach text to options
          const approachText = (value || '').toString().toLowerCase();
          if (approachText.includes('quantitative')) {
            rfqUpdates.research_objectives.measurement_approach = 'quantitative';
          } else if (approachText.includes('qualitative')) {
            rfqUpdates.research_objectives.measurement_approach = 'qualitative';
          } else if (approachText.includes('mixed')) {
            rfqUpdates.research_objectives.measurement_approach = 'mixed_methods';
          } else {
            rfqUpdates.research_objectives.measurement_approach = 'mixed_methods';
          }
          break;

        // Advanced Methodology fields
        case 'complexity_level':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey', stimuli_details: '', methodology_requirements: '' };
          rfqUpdates.methodology.complexity_level = validateAndMapEnum(
            value, 
            'complexity_level', 
            ['simple', 'intermediate', 'complex', 'expert_level'],
            'intermediate'
          ) as 'simple' | 'intermediate' | 'complex' | 'expert_level';
          break;
        case 'required_methodologies':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey', stimuli_details: '', methodology_requirements: '' };
          // Convert methodologies to array if needed
          const methodologies = Array.isArray(value) ? value : (value || '').split(',').map((m: string) => m.trim());
          rfqUpdates.methodology.required_methodologies = methodologies;
          break;
        case 'sample_size_target':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey', stimuli_details: '', methodology_requirements: '' };
          rfqUpdates.methodology.sample_size_target = value;
          break;

        // Advanced Survey Requirements fields
        case 'completion_time_target':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.completion_time_target = validateAndMapEnum(
            value, 
            'completion_time_target', 
            ['under_5min', '5_10min', '10_15min', '15_20min', '20_30min', 'over_30min'],
            '15_20min'
          ) as 'under_5min' | '5_10min' | '10_15min' | '15_20min' | '20_30min' | 'over_30min';
          break;
        case 'device_compatibility':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.device_compatibility = validateAndMapEnum(
            value, 
            'device_compatibility', 
            ['mobile_only', 'desktop_only', 'mobile_first', 'desktop_first', 'all_devices'],
            'all_devices'
          ) as 'mobile_only' | 'desktop_only' | 'mobile_first' | 'desktop_first' | 'all_devices';
          break;
        case 'accessibility_requirements':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.accessibility_requirements = validateAndMapEnum(
            value, 
            'accessibility_requirements', 
            ['basic', 'wcag_aa', 'wcag_aaa', 'custom'],
            'basic'
          ) as 'basic' | 'wcag_aa' | 'wcag_aaa' | 'custom';
          break;
        case 'data_quality_requirements':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          // Map data quality text to options
          const qualityText = (value || '').toString().toLowerCase();
          if (qualityText.includes('premium')) {
            rfqUpdates.survey_requirements.data_quality_requirements = 'premium';
          } else if (qualityText.includes('basic')) {
            rfqUpdates.survey_requirements.data_quality_requirements = 'basic';
          } else {
            rfqUpdates.survey_requirements.data_quality_requirements = 'standard';
          }
          break;
        case 'screener_requirements':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', must_have_questions: [] };
          rfqUpdates.survey_requirements.screener_requirements = value;
          break;

        // Survey Structure fields
        case 'qnr_sections_detected':
          if (!rfqUpdates.survey_structure) rfqUpdates.survey_structure = { qnr_sections: [], text_requirements: [] };
          // Convert QNR sections to array if needed
          const qnrSections = Array.isArray(value) ? value : (value || '').split(',').map((s: string) => s.trim());
          rfqUpdates.survey_structure.qnr_sections = qnrSections;
          break;
        case 'text_requirements_detected':
          if (!rfqUpdates.survey_structure) rfqUpdates.survey_structure = { qnr_sections: [], text_requirements: [] };
          // Convert text requirements to array if needed
          const textRequirements = Array.isArray(value) ? value : (value || '').split(',').map((t: string) => t.trim());
          rfqUpdates.survey_structure.text_requirements = textRequirements;
          break;
        case 'requires_piping_logic':
          if (!rfqUpdates.survey_logic) rfqUpdates.survey_logic = { requires_piping_logic: false, requires_sampling_logic: false, requires_screener_logic: false, custom_logic_requirements: '' };
          rfqUpdates.survey_logic.requires_piping_logic = Boolean(value);
          break;
        case 'requires_sampling_logic':
          if (!rfqUpdates.survey_logic) rfqUpdates.survey_logic = { requires_piping_logic: false, requires_sampling_logic: false, requires_screener_logic: false, custom_logic_requirements: '' };
          rfqUpdates.survey_logic.requires_sampling_logic = Boolean(value);
          break;
        case 'requires_screener_logic':
          if (!rfqUpdates.survey_logic) rfqUpdates.survey_logic = { requires_piping_logic: false, requires_sampling_logic: false, requires_screener_logic: false, custom_logic_requirements: '' };
          rfqUpdates.survey_logic.requires_screener_logic = Boolean(value);
          break;
        case 'custom_logic_requirements':
          if (!rfqUpdates.survey_logic) rfqUpdates.survey_logic = { requires_piping_logic: false, requires_sampling_logic: false, requires_screener_logic: false, custom_logic_requirements: '' };
          rfqUpdates.survey_logic.custom_logic_requirements = value;
          break;

        // Brand Usage Requirements fields
        case 'brand_recall_required':
          if (!rfqUpdates.brand_usage_requirements) rfqUpdates.brand_usage_requirements = { brand_recall_required: false, brand_awareness_funnel: false, brand_product_satisfaction: false, usage_frequency_tracking: false };
          rfqUpdates.brand_usage_requirements.brand_recall_required = Boolean(value);
          break;
        case 'brand_awareness_funnel':
          if (!rfqUpdates.brand_usage_requirements) rfqUpdates.brand_usage_requirements = { brand_recall_required: false, brand_awareness_funnel: false, brand_product_satisfaction: false, usage_frequency_tracking: false };
          rfqUpdates.brand_usage_requirements.brand_awareness_funnel = Boolean(value);
          break;
        case 'brand_product_satisfaction':
          if (!rfqUpdates.brand_usage_requirements) rfqUpdates.brand_usage_requirements = { brand_recall_required: false, brand_awareness_funnel: false, brand_product_satisfaction: false, usage_frequency_tracking: false };
          rfqUpdates.brand_usage_requirements.brand_product_satisfaction = Boolean(value);
          break;
        case 'usage_frequency_tracking':
          if (!rfqUpdates.brand_usage_requirements) rfqUpdates.brand_usage_requirements = { brand_recall_required: false, brand_awareness_funnel: false, brand_product_satisfaction: false, usage_frequency_tracking: false };
          rfqUpdates.brand_usage_requirements.usage_frequency_tracking = Boolean(value);
          break;

        // Advanced Classification fields
        case 'industry_classification':
          if (!rfqUpdates.advanced_classification) rfqUpdates.advanced_classification = { industry_classification: '', respondent_classification: '', methodology_tags: [], compliance_requirements: [] };
          rfqUpdates.advanced_classification.industry_classification = value;
          break;
        case 'respondent_classification':
          if (!rfqUpdates.advanced_classification) rfqUpdates.advanced_classification = { industry_classification: '', respondent_classification: '', methodology_tags: [], compliance_requirements: [] };
          rfqUpdates.advanced_classification.respondent_classification = value;
          break;
        case 'methodology_tags':
          if (!rfqUpdates.advanced_classification) rfqUpdates.advanced_classification = { industry_classification: '', respondent_classification: '', methodology_tags: [], compliance_requirements: [] };
          // Handle both string and array values
          if (Array.isArray(value)) {
            rfqUpdates.advanced_classification.methodology_tags = value;
          } else if (typeof value === 'string') {
            // Split by comma and clean up
            rfqUpdates.advanced_classification.methodology_tags = value.split(',').map(tag => tag.trim()).filter(tag => tag);
          }
          break;

        // Rules and Definitions field
        case 'rules_and_definitions':
          rfqUpdates.rules_and_definitions = value;
          break;

        // Legacy field mapping for backward compatibility
        default:
          console.warn(`Unknown field mapping: ${mapping.field}`);
          break;
      }
    });

    // Add document source information if we have document content
    const state = get();
    if (state.documentContent) {
      rfqUpdates.document_source = {
        type: 'upload',
        filename: state.documentContent.filename,
        upload_id: state.documentContent.filename
      };
    }

    // Log validation errors for debugging
    if (validationErrors.length > 0) {
      console.warn('⚠️ [Field Mapping] Validation errors detected:', validationErrors);
    }

    return rfqUpdates;
  },

  // Apply methodology-based intelligence to auto-configure survey structure
  applyMethodologyIntelligence: (rfqUpdates: Partial<EnhancedRFQRequest>): Partial<EnhancedRFQRequest> => {
    const enhancedUpdates = { ...rfqUpdates };

    // Extract detected methodologies
    const methodologies: string[] = [];
    if (enhancedUpdates.methodology?.primary_method) {
      methodologies.push(enhancedUpdates.methodology.primary_method);
    }
    if (enhancedUpdates.methodology?.required_methodologies) {
      methodologies.push(...enhancedUpdates.methodology.required_methodologies);
    }

    if (methodologies.length === 0) {
      return enhancedUpdates;
    }

    // Initialize survey_structure if not exists
    if (!enhancedUpdates.survey_structure) {
      enhancedUpdates.survey_structure = {};
    }

    // Auto-configure QNR sections based on methodology
    if (!enhancedUpdates.survey_structure.qnr_sections || enhancedUpdates.survey_structure.qnr_sections.length === 0) {
      const qnrSections = new Set<string>();

      // Always include core sections
      qnrSections.add('sample_plan');
      qnrSections.add('screener');
      qnrSections.add('additional_questions');
      qnrSections.add('programmer_instructions');

      // Add methodology-specific sections
      methodologies.forEach(methodology => {
        switch (methodology.toLowerCase()) {
          case 'concept_test':
          case 'ad_test':
          case 'package_test':
            qnrSections.add('brand_awareness');
            qnrSections.add('concept_exposure');
            qnrSections.add('methodology_section');
            break;
          case 'conjoint':
            qnrSections.add('concept_exposure');
            qnrSections.add('methodology_section');
            break;
          case 'van_westendorp':
          case 'gabor_granger':
          case 'pricing':
            qnrSections.add('brand_awareness');
            qnrSections.add('methodology_section');
            break;
          case 'brand_tracker':
          case 'u_and_a':
            qnrSections.add('brand_awareness');
            break;
          case 'max_diff':
            qnrSections.add('methodology_section');
            break;
          default:
            // For unknown methodologies, include all sections
            qnrSections.add('brand_awareness');
            qnrSections.add('concept_exposure');
            qnrSections.add('methodology_section');
        }
      });

      enhancedUpdates.survey_structure.qnr_sections = Array.from(qnrSections);
    }

    // Auto-configure text requirements based on methodology
    if (!enhancedUpdates.survey_structure.text_requirements || enhancedUpdates.survey_structure.text_requirements.length === 0) {
      const textRequirements = new Set<string>();

      // Always include Study_Intro (mandatory)
      textRequirements.add('Study_Intro');

      // Add methodology-specific text requirements
      methodologies.forEach(methodology => {
        switch (methodology.toLowerCase()) {
          case 'concept_test':
          case 'ad_test':
          case 'monadic':
          case 'sequential':
            textRequirements.add('Concept_Intro');
            break;
          case 'conjoint':
          case 'segmentation':
            textRequirements.add('Confidentiality_Agreement');
            break;
          case 'product_test':
          case 'package_test':
          case 'brand_tracker':
          case 'u_and_a':
          case 'pricing':
          case 'van_westendorp':
          case 'gabor_granger':
          case 'competitive':
            textRequirements.add('Product_Usage');
            break;
        }
      });

      enhancedUpdates.survey_structure.text_requirements = Array.from(textRequirements);
    }

    // Auto-configure survey logic based on methodology complexity
    if (!enhancedUpdates.survey_logic) {
      enhancedUpdates.survey_logic = {};
    }

    // Piping logic for complex methodologies
    if (enhancedUpdates.survey_logic.requires_piping_logic === undefined) {
      const complexMethodologies = ['conjoint', 'max_diff', 'concept_test', 'ad_test'];
      enhancedUpdates.survey_logic.requires_piping_logic = methodologies.some(m =>
        complexMethodologies.includes(m.toLowerCase())
      );
    }

    // Sampling logic for quota-based studies
    if (enhancedUpdates.survey_logic.requires_sampling_logic === undefined) {
      const quotaMethodologies = ['segmentation', 'brand_tracker', 'u_and_a'];
      enhancedUpdates.survey_logic.requires_sampling_logic = methodologies.some(m =>
        quotaMethodologies.includes(m.toLowerCase())
      );
    }

    // Screener logic for most methodologies
    if (enhancedUpdates.survey_logic.requires_screener_logic === undefined) {
      enhancedUpdates.survey_logic.requires_screener_logic = methodologies.length > 0;
    }

    // Auto-configure brand usage requirements
    if (!enhancedUpdates.brand_usage_requirements) {
      enhancedUpdates.brand_usage_requirements = {};
    }

    // Brand recall for brand-focused studies
    if (enhancedUpdates.brand_usage_requirements.brand_recall_required === undefined) {
      const brandMethodologies = ['brand_tracker', 'u_and_a', 'competitive'];
      enhancedUpdates.brand_usage_requirements.brand_recall_required = methodologies.some(m =>
        brandMethodologies.includes(m.toLowerCase())
      );
    }

    // Brand awareness funnel for comprehensive brand studies
    if (enhancedUpdates.brand_usage_requirements.brand_awareness_funnel === undefined) {
      const funnelMethodologies = ['brand_tracker', 'u_and_a'];
      enhancedUpdates.brand_usage_requirements.brand_awareness_funnel = methodologies.some(m =>
        funnelMethodologies.includes(m.toLowerCase())
      );
    }

    // Product satisfaction for product studies
    if (enhancedUpdates.brand_usage_requirements.brand_product_satisfaction === undefined) {
      const satisfactionMethodologies = ['product_test', 'u_and_a', 'brand_tracker'];
      enhancedUpdates.brand_usage_requirements.brand_product_satisfaction = methodologies.some(m =>
        satisfactionMethodologies.includes(m.toLowerCase())
      );
    }

    // Usage frequency tracking for usage studies
    if (enhancedUpdates.brand_usage_requirements.usage_frequency_tracking === undefined) {
      const usageMethodologies = ['u_and_a', 'brand_tracker', 'product_test', 'package_test'];
      enhancedUpdates.brand_usage_requirements.usage_frequency_tracking = methodologies.some(m =>
        usageMethodologies.includes(m.toLowerCase())
      );
    }

    return enhancedUpdates;
  },

  applyDocumentMappings: () => {
    const state = get();
    const acceptedMappings = state.fieldMappings.filter(
      mapping => mapping.user_action === 'accepted' || mapping.user_action === 'edited'
    );

    if (acceptedMappings.length === 0) {
      get().addToast({
        type: 'warning',
        title: 'No Mappings Selected',
        message: 'Please accept or edit at least one field mapping before applying.',
        duration: 4000
      });
      return;
    }

    // Use the helper function to build updates
    let rfqUpdates = get().buildRFQUpdatesFromMappings(acceptedMappings);

    // Apply methodology-based intelligence
    rfqUpdates = get().applyMethodologyIntelligence(rfqUpdates);

    // Apply updates to Enhanced RFQ
    get().setEnhancedRfq(rfqUpdates);

    console.log('Applied document mappings:', rfqUpdates);
  },

  // Enhanced RFQ State Persistence (simplified - no separate localStorage needed)
  persistEnhancedRfqState: (enhancedRfq: EnhancedRFQRequest) => {
    // Persist enhancedRfq to localStorage so it survives navigation
    try {
      localStorage.setItem('enhanced_rfq_data', JSON.stringify(enhancedRfq));
      console.log('💾 [Store] Enhanced RFQ state persisted to localStorage', {
        hasBusinessContext: !!enhancedRfq.business_context?.company_product_background,
        hasResearchObjectives: !!enhancedRfq.research_objectives?.research_audience
      });
    } catch (error) {
      console.error('Failed to persist enhancedRfq state:', error);
    }
  },

  // Document Processing State Persistence
  persistDocumentProcessingState: (isProcessing: boolean, sessionId?: string) => {
    try {
      const state = get();
      
      // Always persist the document data AND the auto-filled enhancedRfq
      // This ensures data is available through all 6 steps until explicit reset
      const existingState = localStorage.getItem('document_processing_state');
      let existingSessionId: string | undefined;
      
      if (existingState) {
        try {
          const parsed = JSON.parse(existingState);
          existingSessionId = parsed.sessionId;
        } catch (e) {
          // Ignore parse errors
        }
      }
      
      const stateToSave = {
        isProcessing,
        sessionId: sessionId || existingSessionId,
        documentContent: state.documentContent,
        documentAnalysis: state.documentAnalysis,
        fieldMappings: state.fieldMappings,
        enhancedRfq: state.enhancedRfq,  // CRITICAL: Save auto-filled form data!
        timestamp: Date.now()
      };
      
      localStorage.setItem('document_processing_state', JSON.stringify(stateToSave));
      
      if (isProcessing) {
        console.log('💾 [Store] Document processing state persisted (processing)', { sessionId });
      } else {
        console.log('💾 [Store] Document processing state persisted (complete, with auto-filled data)', { 
          sessionId: stateToSave.sessionId,
          hasEnhancedRfqData: !!stateToSave.enhancedRfq.business_context?.company_product_background
        });
      }
    } catch (error) {
      console.error('Failed to persist document processing state:', error);
    }
  },

  restoreDocumentProcessingState: () => {
    try {
      console.log('🔍 [Store] restoreDocumentProcessingState called');
      const persistedState = localStorage.getItem('document_processing_state');
      console.log('🔍 [Store] Persisted document processing state:', persistedState);

      if (persistedState) {
        const state = JSON.parse(persistedState);

        console.log('🔍 [Store] Restoring document processing state from localStorage', {
          isProcessing: state.isProcessing,
          sessionId: state.sessionId,
          hasDocumentContent: !!state.documentContent,
          hasDocumentAnalysis: !!state.documentAnalysis,
          fieldMappingsCount: state.fieldMappings?.length || 0,
          hasEnhancedRfq: !!state.enhancedRfq,
          enhancedRfqHasBusinessContext: !!state.enhancedRfq?.business_context?.company_product_background
        });

        // CRITICAL: Only restore enhancedRfq if it has meaningful data
        // Don't overwrite current enhancedRfq if the persisted one is empty
        const shouldRestoreEnhancedRfq = state.enhancedRfq && (
          state.enhancedRfq.business_context?.company_product_background ||
          state.enhancedRfq.business_context?.business_problem ||
          state.enhancedRfq.research_objectives?.research_audience ||
          (state.enhancedRfq.research_objectives?.key_research_questions?.length > 0)
        );
        
        console.log('🔍 [Store] Should restore enhancedRfq?', shouldRestoreEnhancedRfq);
        
        set({
          isDocumentProcessing: state.isProcessing || false,
          documentContent: state.documentContent,
          documentAnalysis: state.documentAnalysis,
          fieldMappings: state.fieldMappings || [],
          ...(shouldRestoreEnhancedRfq ? { enhancedRfq: state.enhancedRfq } : {})  // Only restore if has data
        });

        return true;
      } else {
        console.log('🔍 [Store] No persisted document processing state found');
      }
      return false;
    } catch (error) {
      console.error('Failed to restore document processing state:', error);
      return false;
    }
  },

  restoreEnhancedRfqState: (showToast: boolean = true) => {
    // Restore enhancedRfq from localStorage
    try {
      const savedRfq = localStorage.getItem('enhanced_rfq_data');
      
      if (savedRfq) {
        const parsed = JSON.parse(savedRfq);
        
        // Only restore if it has meaningful data
        const hasData = parsed.business_context?.company_product_background ||
                       parsed.business_context?.business_problem ||
                       parsed.research_objectives?.research_audience ||
                       (parsed.research_objectives?.key_research_questions?.length > 0);
        
        if (hasData) {
          console.log('🔍 [Store] Restoring enhancedRfq from localStorage', {
            hasBusinessContext: !!parsed.business_context?.company_product_background,
            hasResearchObjectives: !!parsed.research_objectives?.research_audience
          });
          
          set({ enhancedRfq: parsed });
          return true;
        } else {
          console.log('🔍 [Store] Enhanced RFQ in localStorage is empty, skipping restore');
        }
      } else {
        console.log('🔍 [Store] No enhanced RFQ found in localStorage');
      }
      return false;
    } catch (error) {
      console.error('Failed to restore enhancedRfq state:', error);
      return false;
    }
  },

  clearEnhancedRfqState: () => {
    console.log('🧹 [Store] clearEnhancedRfqState called - clearing Enhanced RFQ state');
    // Reset Enhanced RFQ to default state
    set({
      enhancedRfq: {
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
      }
    });
    // Clear all localStorage keys
    localStorage.removeItem('enhanced_rfq_initialized');
    localStorage.removeItem('enhanced_rfq_data');  // Clear persisted enhancedRfq
    console.log('🧹 [Store] Enhanced RFQ state cleared from Zustand store and localStorage');
  },

  resetDocumentProcessingState: () => {
    set({
      isDocumentProcessing: false,
      documentContent: undefined,
      documentAnalysis: undefined,
      fieldMappings: [],
      documentUploadError: undefined
    });
    
    // Clear localStorage when explicitly resetting
    localStorage.removeItem('document_processing_state');
    
    console.log('🔄 [Store] Document processing state reset and localStorage cleared');
  },

  // Pillar Evaluation Polling
  startPillarEvaluationPolling: (surveyId: string) => {
    console.log('🔍 [Store] Starting pillar evaluation polling for survey:', surveyId);
    // This would typically start a polling mechanism to check for pillar evaluation results
    // For now, we'll just log that it was called
    console.log('Pillar evaluation polling started (implementation pending)');
  },

  // Text Content Validation Functions
  getRequiredTextForMethodology: (methodology: string[]): AiRATextLabel[] => {
    const requiredLabels = new Set<AiRATextLabel>();

    methodology.forEach(method => {
      const methodRequirements = METHODOLOGY_TEXT_REQUIREMENTS[method] || [];
      methodRequirements.forEach(label => requiredLabels.add(label as AiRATextLabel));
    });

    return Array.from(requiredLabels);
  },

  validateSurveyTextCompliance: (survey: Survey): TextComplianceReport => {
    const methodology = survey.methodologies || [];
    const requiredLabels = get().getRequiredTextForMethodology(methodology);

    const textComplianceChecks = requiredLabels.map(label => {
      const found = survey.sections?.some(section =>
        section.introText?.label === label ||
        section.textBlocks?.some(text => text.label === label)
      ) || false;

      const foundText = survey.sections?.reduce((acc, section) => {
        if (section.introText?.label === label) return section.introText;
        const blockText = section.textBlocks?.find(text => text.label === label);
        return blockText || acc;
      }, undefined as SurveyTextContent | undefined);

      return {
        label,
        type: AIRA_LABEL_TO_TYPE_MAP[label] as any,
        required: true,
        found,
        content: foundText,
        section: foundText?.section_id?.toString()
      };
    });

    const missingElements = textComplianceChecks
      .filter(check => !check.found)
      .map(check => check.label);

    const complianceScore = textComplianceChecks.length > 0
      ? Math.round((textComplianceChecks.filter(c => c.found).length / textComplianceChecks.length) * 100)
      : 100;

    const complianceLevel = complianceScore >= 90 ? 'full' :
                           complianceScore >= 60 ? 'partial' : 'poor';

    const recommendations = missingElements.map(label =>
      `Add mandatory ${(label as string).replace('_', ' ')} text introduction`
    );

    return {
      survey_id: survey.survey_id,
      methodology,
      required_text_elements: textComplianceChecks,
      missing_elements: missingElements,
      compliance_score: complianceScore,
      compliance_level: complianceLevel,
      recommendations,
      analysis_timestamp: new Date().toISOString()
    };
  },

  // Golden Example State Management
  goldenExampleSessionId: null,
  goldenExampleState: null,

  persistGoldenExampleState: async (sessionId: string, state: GoldenExampleFormState) => {
    try {
      console.log('💾 [Store] Persisting golden example state for session:', sessionId);
      console.log('💾 [Store] State data:', state);
      
      // Save to database
      const response = await fetch('/api/v1/golden-pairs/state/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, state_data: state })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Also save to localStorage for faster restoration
      localStorage.setItem('golden_example_session_id', sessionId);
      localStorage.setItem('golden_example_state', JSON.stringify(state));
      
      set({ goldenExampleSessionId: sessionId, goldenExampleState: state });
      console.log('✅ [Store] Golden example state persisted successfully');
    } catch (error) {
      console.error('❌ [Store] Failed to persist golden example state:', error);
    }
  },

  restoreGoldenExampleState: async () => {
    try {
      console.log('📂 [Store] Attempting to restore golden example state...');
      
      // Try localStorage first (faster)
      const sessionId = localStorage.getItem('golden_example_session_id');
      console.log('📂 [Store] Session ID from localStorage:', sessionId);
      
      if (!sessionId) {
        console.log('⚠️ [Store] No session ID found in localStorage');
        return false;
      }
      
      // Then fetch from database (more reliable)
      console.log('📂 [Store] Fetching state from database...');
      const response = await fetch(`/api/v1/golden-pairs/state/${sessionId}`);
      console.log('📂 [Store] Database response status:', response.status);
      
      if (!response.ok) {
        console.log('⚠️ [Store] Database fetch failed:', response.status, response.statusText);
        return false;
      }
      
      const data = await response.json();
      console.log('📂 [Store] Database response data:', data);
      
      set({ 
        goldenExampleSessionId: sessionId, 
        goldenExampleState: data.state_data 
      });
      console.log('✅ [Store] Golden example state restored successfully');
      return true;
    } catch (error) {
      console.error('❌ [Store] Failed to restore golden example state:', error);
      return false;
    }
  },

  clearGoldenExampleState: async (sessionId?: string) => {
    const sid = sessionId || get().goldenExampleSessionId;
    if (sid) {
      try {
        await fetch(`/api/v1/golden-pairs/state/${sid}`, { method: 'DELETE' });
      } catch (error) {
        console.warn('⚠️ Failed to clear state from database:', error);
      }
    }
    localStorage.removeItem('golden_example_session_id');
    localStorage.removeItem('golden_example_state');
    set({ goldenExampleSessionId: null, goldenExampleState: null });
  },

  generateMissingTextContent: (missing: AiRATextLabel[], methodology: string[], rfq?: EnhancedRFQRequest): SurveyTextContent[] => {
    return missing.map((label, index) => {
      const type = AIRA_LABEL_TO_TYPE_MAP[label] as any;
      let content = '';

      // Generate appropriate content based on label type and RFQ context
      switch (label) {
        case 'Study_Intro':
          content = rfq ?
            `Thank you for agreeing to participate in this ${rfq.methodology?.primary_method || 'research'} study. Your responses will help us understand ${rfq.business_context?.business_objective || 'market preferences'}. This survey should take approximately ${rfq.survey_requirements?.completion_time_target?.replace('_', '-').replace('min', ' minutes') || '10-15 minutes'} to complete.` :
            'Thank you for agreeing to participate in this research study. Your responses are valuable and will help us understand important market insights.';
          break;
        case 'Concept_Intro':
          content = rfq?.methodology?.stimuli_details ?
            `Please review the following concept carefully: ${rfq.methodology.stimuli_details}. We will ask for your opinions and reactions to this concept.` :
            'Please review the following concept carefully. We will ask for your opinions and reactions to this concept.';
          break;
        case 'Confidentiality_Agreement':
          content = 'All responses in this survey are confidential and will only be used for research purposes. Your individual responses will not be shared with third parties.';
          break;
        case 'Product_Usage':
          content = rfq?.business_context?.company_product_background ?
            `Before we begin, please tell us about your experience with ${rfq.business_context.company_product_background}.` :
            'Before we begin, please tell us about your experience with products in this category.';
          break;
        default:
          content = `${(label as string).replace('_', ' ')} content will be provided here.`;
      }

      return {
        id: `text_${label.toLowerCase()}_${index}`,
        type,
        content,
        mandatory: true,
        label,
        order: index
      };
    });
  },

  // Golden Content Actions
  fetchGoldenSections: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      
      const response = await fetch(`/api/v1/golden-content/sections?${params}`);
      if (!response.ok) throw new Error('Failed to fetch golden sections');
      const sections = await response.json();
      set({ goldenSections: sections });
    } catch (error) {
      console.error('Failed to fetch golden sections:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load golden sections',
        duration: 5000
      });
    }
  },

  fetchGoldenQuestions: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      
      const response = await fetch(`/api/v1/golden-content/questions?${params}`);
      if (!response.ok) throw new Error('Failed to fetch golden questions');
      const questions = await response.json();
      set({ goldenQuestions: questions });
    } catch (error) {
      console.error('Failed to fetch golden questions:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load golden questions',
        duration: 5000
      });
    }
  },

  updateGoldenSection: async (id: string, updates: Partial<GoldenSection>) => {
    try {
      const response = await fetch(`/api/v1/golden-content/sections/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      if (!response.ok) throw new Error('Failed to update golden section');
      
      // Refresh list
      await get().fetchGoldenSections();
      
      get().addToast({
        type: 'success',
        title: 'Updated',
        message: 'Golden section updated successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to update golden section:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to update golden section',
        duration: 5000
      });
    }
  },

  updateGoldenQuestion: async (id: string, updates: Partial<GoldenQuestion>) => {
    try {
      const response = await fetch(`/api/v1/golden-content/questions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      if (!response.ok) throw new Error('Failed to update golden question');
      
      // Refresh list
      await get().fetchGoldenQuestions();
      
      get().addToast({
        type: 'success',
        title: 'Updated',
        message: 'Golden question updated successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to update golden question:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to update golden question',
        duration: 5000
      });
    }
  },

  deleteGoldenSection: async (id: string) => {
    try {
      const response = await fetch(`/api/v1/golden-content/sections/${id}`, { 
        method: 'DELETE' 
      });
      
      if (!response.ok) throw new Error('Failed to delete golden section');
      
      // Refresh list
      await get().fetchGoldenSections();
      
      get().addToast({
        type: 'success',
        title: 'Deleted',
        message: 'Golden section deleted successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to delete golden section:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to delete golden section',
        duration: 5000
      });
    }
  },

  deleteGoldenQuestion: async (id: string) => {
    try {
      const response = await fetch(`/api/v1/golden-content/questions/${id}`, { 
        method: 'DELETE' 
      });
      
      if (!response.ok) throw new Error('Failed to delete golden question');
      
      // Refresh list
      await get().fetchGoldenQuestions();
      
      get().addToast({
        type: 'success',
        title: 'Deleted',
        message: 'Golden question deleted successfully',
        duration: 3000
      });
    } catch (error) {
      console.error('Failed to delete golden question:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to delete golden question',
        duration: 5000
      });
    }
  },

  fetchGoldenContentAnalytics: async () => {
    try {
      const response = await fetch('/api/v1/golden-content/analytics');
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const analytics = await response.json();
      set({ goldenContentAnalytics: analytics });
    } catch (error) {
      console.error('Failed to fetch golden content analytics:', error);
      get().addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load analytics',
        duration: 5000
      });
    }
  }
}));