import { create } from 'zustand';
import { AppStore, RFQRequest, EnhancedRFQRequest, RFQTemplate, RFQQualityAssessment, WorkflowState, ProgressMessage, GoldenExampleRequest, ToastMessage, SurveyAnnotations, getQuestionCount, PendingReview, ReviewDecision, DocumentContent, DocumentAnalysis, RFQFieldMapping, DocumentAnalysisResponse, DetailedError, ErrorCode, StreamingStats } from '../types';
import { ErrorClassifier } from '../types/errors';
import { apiService } from '../services/api';
import { rfqTemplateService } from '../services/RFQTemplateService';

// Utility function to generate unique IDs
const generateId = () => Math.random().toString(36).substr(2, 9);

export const useAppStore = create<AppStore>((set, get) => ({
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
      business_objective: ''
    },
    research_objectives: {
      research_audience: '',
      success_criteria: '',
      key_research_questions: []
    },
    methodology: {
      primary_method: 'basic_survey',
      stimuli_details: '',
      methodology_requirements: ''
    },
    survey_requirements: {
      sample_plan: '',
      required_sections: [],
      must_have_questions: [],
      screener_requirements: ''
    }
  },

  setEnhancedRfq: (input) => set((state) => {
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
      // Only allow forward progress or resets (to prevent backward jumps)
      if (newProgress >= currentProgress || newProgress === 0) {
        smoothedProgress = newProgress;
      } else {
        // Keep current progress if new progress is backward (unless it's a reset)
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

  // WebSocket connection
  websocket: undefined as WebSocket | undefined,


  // Actions
  submitRFQ: async (rfq: RFQRequest) => {
    try {
      // Prevent multiple simultaneous workflows
      const currentWorkflow = get().workflow;
      if (currentWorkflow.status === 'started' || currentWorkflow.status === 'in_progress') {
        console.warn('⚠️ [Store] Workflow already in progress, ignoring duplicate submission');
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

      // Set initial progress state
      set((state) => ({
        workflow: {
          ...state.workflow,
          status: 'started',
          progress: 0,
          current_step: 'initializing',
          message: 'Submitting request and preparing workflow...'
        }
      }));

      console.log('🚀 [Store] Starting new workflow submission');

      const response = await apiService.submitRFQ(rfq);
      
      set((state) => ({
        workflow: {
          ...state.workflow,
          workflow_id: response.workflow_id,
          survey_id: response.survey_id,
          status: 'in_progress',
          progress: 5,
          current_step: 'initializing_workflow',
          message: 'Starting survey generation workflow...'
        }
      }));

      // Show info toast that generation has started
      get().addToast({
        type: 'info',
        title: 'Survey Generation Started',
        message: 'Your survey is being generated. You can step away and we\'ll notify you when it\'s ready!',
        duration: 5000
      });

      // Connect to WebSocket for progress updates
      get().connectWebSocket(response.workflow_id);

    } catch (error) {
      // Classify the error for better handling
      const detailedError = ErrorClassifier.classifyError(
        error,
        { component: 'RFQSubmission', action: 'submit_rfq' }
      );

      set((state) => ({
        workflow: {
          ...state.workflow,
          status: 'failed',
          error: error instanceof Error ? error.message : 'Unknown error',
          detailedError: detailedError
        }
      }));

      // Show enhanced error toast
      get().addToast({
        type: 'error',
        title: 'Submission Failed',
        message: `${detailedError.userMessage}\n\nDebug Code: ${ErrorClassifier.generateDebugHandle(detailedError.code, new Date())}`,
        duration: 8000
      });
    }
  },

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
            const newWorkflowState = {
              current_step: message.step,
              progress: message.percent,
              message: message.message
            };
            set((state) => ({
              workflow: {
                ...state.workflow,
                ...newWorkflowState
              }
            }));
          }

          // Persist workflow state for recovery
          const currentState = get().workflow;
          if (currentState.workflow_id) {
            get().persistWorkflowState(currentState.workflow_id, currentState);
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
        quality_score: item.quality_score || 0.8,
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
        duration: 4000
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
        duration: 4000
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
        duration: 4000
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
        question_annotations: annotations.questionAnnotations.map(qa => ({
          question_id: qa.questionId,
          required: qa.required,
          quality: qa.quality,
          relevant: qa.relevant,
          methodological_rigor: qa.pillars.methodologicalRigor,
          content_validity: qa.pillars.contentValidity,
          respondent_experience: qa.pillars.respondentExperience,
          analytical_value: qa.pillars.analyticalValue,
          business_impact: qa.pillars.businessImpact,
          comment: qa.comment,
          annotator_id: qa.annotatorId || "current-user"
        })),
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
          annotator_id: sa.annotatorId || "current-user"
        })),
        overall_comment: annotations.overallComment,
        annotator_id: annotations.annotatorId || "current-user"
      };

      const response = await fetch(`/api/v1/annotations/survey/${annotations.surveyId}/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transformedRequest),
      });
      
      if (!response.ok) throw new Error('Failed to save annotations');
      
      const result = await response.json();
      
      // Update current annotations
      set({ currentAnnotations: { ...annotations, ...result } });
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Annotations Saved',
        message: 'Survey annotations saved successfully',
        duration: 4000
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
      
      // Transform backend format to frontend format
      const frontendAnnotations: SurveyAnnotations = {
        surveyId: backendAnnotations.survey_id,
        questionAnnotations: (backendAnnotations.question_annotations || []).map((qa: any) => ({
          questionId: qa.question_id,
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
          annotatorId: qa.annotator_id,
          timestamp: qa.created_at
        })),
        sectionAnnotations: (backendAnnotations.section_annotations || []).map((sa: any) => ({
          sectionId: sa.section_id.toString(),
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
          annotatorId: sa.annotator_id,
          timestamp: sa.created_at
        })),
        overallComment: backendAnnotations.overall_comment || '',
        annotatorId: backendAnnotations.annotator_id,
        createdAt: backendAnnotations.created_at,
        updatedAt: backendAnnotations.updated_at
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
      get().addToast({
        type: 'error',
        title: 'Review Error',
        message: 'Failed to check for pending reviews',
        duration: 5000
      });
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

  resetWorkflow: () => {
    console.log('🔄 [Store] Resetting workflow to idle state');

    // Clear any pending timeout
    const { workflowTimeoutId } = get();
    if (workflowTimeoutId) {
      clearTimeout(workflowTimeoutId);
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
    localStorage.removeItem('enhanced_rfq_state');

    // Disconnect any active WebSocket
    get().disconnectWebSocket();

    console.log('✅ [Store] Workflow reset completed');
  },

  recoverWorkflowState: async () => {
    try {
      // Check localStorage for interrupted workflows
      const persistedState = localStorage.getItem('survey_workflow_state');
      if (persistedState) {
        const state = JSON.parse(persistedState);
        const hoursSinceUpdate = (Date.now() - state.timestamp) / (1000 * 60 * 60);

        // Only recover if less than 24 hours old
        if (hoursSinceUpdate < 24) {
          console.log('🔄 [Store] Recovering workflow state:', state);

          // Check if there's a pending review for this workflow
          try {
            const review = await get().fetchReviewByWorkflow(state.workflow_id);
            if (review && review.review_status === 'pending') {
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

          if (shouldRestoreWorkflow) {
            get().setWorkflowState(state);

            // Try to reconnect WebSocket if workflow was in progress
            if (state.status === 'in_progress' && state.workflow_id) {
              get().connectWebSocket(state.workflow_id);
            }
          } else {
            // Clean up completed workflows that shouldn't be restored
            console.log('🧹 [Store] Cleaning up completed workflow state for non-generator page');
            localStorage.removeItem('survey_workflow_state');
          }
        } else {
          // Clean up old state
          localStorage.removeItem('survey_workflow_state');
        }
      }

      // Check for pending reviews
      await get().checkPendingReviews();

    } catch (error) {
      console.error('Failed to recover workflow state:', error);
    }
  },

  // Enhanced RFQ Actions
  submitEnhancedRFQ: async (rfq: EnhancedRFQRequest) => {
    try {
      // Import the enhanced text converter
      const { createEnhancedDescription } = await import('../utils/enhancedRfqConverter');

      // Create enriched description that combines original text with structured data
      const enhancedDescription = createEnhancedDescription(rfq);

      // Convert enhanced RFQ to format that includes both enriched text and structured data
      const enhancedRfqPayload = {
        title: rfq.title,
        description: enhancedDescription, // 🎯 Key change: Use enriched description instead of basic description
        target_segment: rfq.research_objectives?.research_audience || '',
        enhanced_rfq_data: rfq // 🎯 Send the full structured data for storage and analytics
      };

      console.log('🚀 [Enhanced RFQ] Submitting with enriched description and structured data:', {
        originalLength: rfq.description?.length || 0,
        enhancedLength: enhancedDescription.length,
        hasObjectives: (rfq.research_objectives?.key_research_questions?.length || 0) > 0,
        hasConstraints: false, // constraints field not in EnhancedRFQRequest interface
        hasStakeholders: false, // stakeholders field not in EnhancedRFQRequest interface
        structuredDataSize: JSON.stringify(rfq).length
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
          progress: 5,
          current_step: 'initializing_workflow',
          message: 'Starting enhanced survey generation workflow...'
        }
      }));

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

  // Document Upload Actions
  uploadDocument: async (file: File, sessionId?: string): Promise<DocumentAnalysisResponse> => {
    set({ isDocumentProcessing: true, documentUploadError: undefined });

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (sessionId) {
        formData.append('session_id', sessionId);
      }

      const response = await fetch('/api/v1/rfq/upload-document', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const result: DocumentAnalysisResponse = await response.json();

      // Dynamic confidence thresholds per field type for simplified schema
      const fieldConfidenceThresholds: Record<string, number> = {
        // Critical fields - must be very accurate
        title: 0.95,
        description: 0.85,
        company_product_background: 0.80,

        // High priority fields - important but editable
        business_problem: 0.75,
        business_objective: 0.75,
        primary_method: 0.90,  // Methodology must be accurate

        // Medium priority fields - helpful but not critical
        research_audience: 0.70,
        success_criteria: 0.70,
        key_research_questions: 0.65,
        stimuli_details: 0.65,
        methodology_requirements: 0.60,
        sample_plan: 0.70,
        required_sections: 0.60,
        must_have_questions: 0.60,
        screener_requirements: 0.60,
        rules_and_definitions: 0.55
      };

      const incomingMappings = result.rfq_analysis.field_mappings || [];
      const autoAccepted = incomingMappings.map(m => {
        const threshold = fieldConfidenceThresholds[m.field] || 0.80; // Default fallback
        return m.confidence >= threshold ? { ...m, user_action: 'accepted' as const } : m;
      });

      // Update store with analysis results and auto-accepted mappings
      set({
        documentContent: result.document_content,
        documentAnalysis: result.rfq_analysis,
        fieldMappings: autoAccepted,
        isDocumentProcessing: false
      });

      // Auto-apply accepted mappings immediately
      const acceptedCount = autoAccepted.filter(m => m.user_action === 'accepted').length;
      if (acceptedCount > 0) {
        // Apply mappings immediately using the accepted mappings
        const rfqUpdates = get().buildRFQUpdatesFromMappings(autoAccepted.filter(m => m.user_action === 'accepted'));
        get().setEnhancedRfq(rfqUpdates);

        get().addToast({
          type: 'success',
          title: 'Auto-filled from Document',
          message: `Applied ${acceptedCount} high-confidence fields (dynamic thresholds). Review in the sections below.`,
          duration: 6000
        });
      }

      return result;
    } catch (error) {
      let errorMessage = error instanceof Error ? error.message : 'Document upload failed';

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
      throw new Error(errorMessage);
    }
  },

  analyzeText: async (text: string, filename = 'text_input.txt'): Promise<DocumentAnalysisResponse> => {
    set({ isDocumentProcessing: true, documentUploadError: undefined });

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

      // Dynamic confidence thresholds per field type for simplified schema
      const fieldConfidenceThresholds: Record<string, number> = {
        // Critical fields - must be very accurate
        title: 0.95,
        description: 0.85,
        company_product_background: 0.80,

        // High priority fields - important but editable
        business_problem: 0.75,
        business_objective: 0.75,
        primary_method: 0.90,  // Methodology must be accurate

        // Medium priority fields - helpful but not critical
        research_audience: 0.70,
        success_criteria: 0.70,
        key_research_questions: 0.65,
        stimuli_details: 0.65,
        methodology_requirements: 0.60,
        sample_plan: 0.70,
        required_sections: 0.60,
        must_have_questions: 0.60,
        screener_requirements: 0.60,
        rules_and_definitions: 0.55
      };

      const incomingMappings = result.rfq_analysis.field_mappings || [];
      const autoAccepted = incomingMappings.map(m => {
        const threshold = fieldConfidenceThresholds[m.field] || 0.80; // Default fallback
        return m.confidence >= threshold ? { ...m, user_action: 'accepted' as const } : m;
      });

      // Update store with analysis results and auto-accepted mappings
      set({
        documentContent: result.document_content,
        documentAnalysis: result.rfq_analysis,
        fieldMappings: autoAccepted,
        isDocumentProcessing: false
      });

      // Auto-apply if we have accepted mappings
      if (autoAccepted.some(m => m.user_action === 'accepted')) {
        get().applyDocumentMappings();
        get().addToast({
          type: 'success',
          title: 'Auto-filled from Text',
          message: `Applied ${autoAccepted.filter(m => m.user_action === 'accepted').length} high-confidence fields (dynamic thresholds).`,
          duration: 5000
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Text analysis failed';
      set({
        documentUploadError: errorMessage,
        isDocumentProcessing: false
      });
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
  },

  rejectFieldMapping: (field: string) => {
    set((state) => ({
      fieldMappings: state.fieldMappings.map(mapping =>
        mapping.field === field
          ? { ...mapping, user_action: 'rejected' as const }
          : mapping
      )
    }));
  },

  editFieldMapping: (field: string, value: any) => {
    set((state) => ({
      fieldMappings: state.fieldMappings.map(mapping =>
        mapping.field === field
          ? { ...mapping, value, user_action: 'edited' as const }
          : mapping
      )
    }));
  },

  clearDocumentData: () => {
    set({
      documentContent: undefined,
      documentAnalysis: undefined,
      fieldMappings: [],
      documentUploadError: undefined
    });
  },

  // Helper function to build RFQ updates from field mappings (simplified schema)
  buildRFQUpdatesFromMappings: (mappings: RFQFieldMapping[]): Partial<EnhancedRFQRequest> => {
    const rfqUpdates: Partial<EnhancedRFQRequest> = {};

    mappings.forEach(mapping => {
      const value = mapping.value;

      switch (mapping.field) {
        // Basic Info
        case 'title':
          rfqUpdates.title = value;
          break;
        case 'description':
          rfqUpdates.description = value;
          break;

        // Business Context
        case 'company_product_background':
        case 'business_background':
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

        // Research Objectives
        case 'research_audience':
        case 'target_audience':
        case 'target_segment':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.research_audience = value;
          break;
        case 'success_criteria':
        case 'desired_outcome':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_criteria = value;
          break;
        case 'key_research_questions':
        case 'research_questions':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          if (Array.isArray(value)) {
            rfqUpdates.research_objectives.key_research_questions = value;
          } else if (typeof value === 'string') {
            rfqUpdates.research_objectives.key_research_questions = [value];
          }
          break;

        // Methodology
        case 'primary_method':
        case 'methodology':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey' };
          if (['van_westendorp', 'gabor_granger', 'conjoint', 'basic_survey'].includes(value)) {
            rfqUpdates.methodology.primary_method = value;
          }
          break;
        case 'stimuli_details':
        case 'concept_details':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey' };
          rfqUpdates.methodology.stimuli_details = value;
          break;
        case 'methodology_requirements':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey' };
          rfqUpdates.methodology.methodology_requirements = value;
          break;

        // Survey Requirements
        case 'sample_plan':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', required_sections: [], must_have_questions: [] };
          rfqUpdates.survey_requirements.sample_plan = value;
          break;
        case 'required_sections':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', required_sections: [], must_have_questions: [] };
          if (Array.isArray(value)) {
            rfqUpdates.survey_requirements.required_sections = value;
          } else if (typeof value === 'string') {
            rfqUpdates.survey_requirements.required_sections = [value];
          }
          break;
        case 'must_have_questions':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', required_sections: [], must_have_questions: [] };
          if (Array.isArray(value)) {
            rfqUpdates.survey_requirements.must_have_questions = value;
          } else if (typeof value === 'string') {
            rfqUpdates.survey_requirements.must_have_questions = [value];
          }
          break;
        case 'screener_requirements':
          if (!rfqUpdates.survey_requirements) rfqUpdates.survey_requirements = { sample_plan: '', required_sections: [], must_have_questions: [] };
          rfqUpdates.survey_requirements.screener_requirements = value;
          break;

        // Meta
        case 'rules_and_definitions':
          rfqUpdates.rules_and_definitions = value;
          break;

        // Additional field mappings from document parsing
        case 'objectives':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          if (Array.isArray(value)) {
            rfqUpdates.research_objectives.key_research_questions = value;
          } else if (typeof value === 'string') {
            rfqUpdates.research_objectives.key_research_questions = [value];
          }
          break;
        case 'research_goal':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_criteria = value;
          break;
        case 'methodology_details':
          if (!rfqUpdates.methodology) rfqUpdates.methodology = { primary_method: 'basic_survey' };
          rfqUpdates.methodology.methodology_requirements = value;
          break;
        case 'product_category':
          if (!rfqUpdates.business_context) rfqUpdates.business_context = { company_product_background: '', business_problem: '', business_objective: '' };
          rfqUpdates.business_context.company_product_background = value;
          break;
        case 'deliverables':
          if (!rfqUpdates.research_objectives) rfqUpdates.research_objectives = { research_audience: '', success_criteria: '', key_research_questions: [] };
          rfqUpdates.research_objectives.success_criteria = value;
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

    return rfqUpdates;
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
    const rfqUpdates = get().buildRFQUpdatesFromMappings(acceptedMappings);

    // Apply updates to Enhanced RFQ
    get().setEnhancedRfq(rfqUpdates);

    // Show success toast
    get().addToast({
      type: 'success',
      title: 'Document Data Applied',
      message: `Applied ${acceptedMappings.length} field mappings to your RFQ.`,
      duration: 5000
    });

    console.log('Applied document mappings:', rfqUpdates);
  },

  // Enhanced RFQ State Persistence
  persistEnhancedRfqState: (enhancedRfq: EnhancedRFQRequest) => {
    try {
      const stateToPersist = {
        ...enhancedRfq,
        lastSaved: Date.now()
      };
      localStorage.setItem('enhanced_rfq_state', JSON.stringify(stateToPersist));
      console.log('💾 [Store] Enhanced RFQ state persisted to localStorage');
    } catch (error) {
      console.error('Failed to persist Enhanced RFQ state:', error);
    }
  },

  restoreEnhancedRfqState: () => {
    try {
      const persistedState = localStorage.getItem('enhanced_rfq_state');
      if (persistedState) {
        const state = JSON.parse(persistedState);
        const hoursSinceUpdate = (Date.now() - (state.lastSaved || 0)) / (1000 * 60 * 60);

        // Only restore if less than 24 hours old
        if (hoursSinceUpdate < 24) {
          console.log('🔄 [Store] Restoring Enhanced RFQ state from localStorage');
          
          // Remove the lastSaved field before setting state
          const { lastSaved, ...enhancedRfqState } = state;
          
          set({ enhancedRfq: enhancedRfqState });
          
          get().addToast({
            type: 'info',
            title: '📝 Form Restored',
            message: 'Your Enhanced RFQ form has been restored from your last session.',
            duration: 5000
          });
          
          return true;
        } else {
          // Clean up old state
          localStorage.removeItem('enhanced_rfq_state');
          console.log('🧹 [Store] Cleaned up old Enhanced RFQ state');
        }
      }
      return false;
    } catch (error) {
      console.error('Failed to restore Enhanced RFQ state:', error);
      return false;
    }
  },

  clearEnhancedRfqState: () => {
    try {
      localStorage.removeItem('enhanced_rfq_state');
      console.log('🧹 [Store] Enhanced RFQ state cleared from localStorage');
    } catch (error) {
      console.error('Failed to clear Enhanced RFQ state:', error);
    }
  },

  // Pillar Evaluation Polling
  startPillarEvaluationPolling: (surveyId: string) => {
    console.log('🔍 [Store] Starting pillar evaluation polling for survey:', surveyId);
    // This would typically start a polling mechanism to check for pillar evaluation results
    // For now, we'll just log that it was called
    console.log('Pillar evaluation polling started (implementation pending)');
  }
}));