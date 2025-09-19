import { create } from 'zustand';
import { AppStore, RFQRequest, EnhancedRFQRequest, RFQTemplate, RFQQualityAssessment, WorkflowState, ProgressMessage, GoldenExampleRequest, ToastMessage, SurveyAnnotations, getQuestionCount, PendingReview, ReviewDecision } from '../types';
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
    objectives: [],
    constraints: [],
    stakeholders: [],
    success_metrics: [],
    generation_config: {
      creativity_level: 'balanced',
      length_preference: 'standard',
      complexity_level: 'intermediate',
      include_validation_questions: true,
      enable_adaptive_routing: false
    }
  },

  setEnhancedRfq: (input) => set((state) => {
    // Use spread operator to create completely new object without mutations
    return {
      enhancedRfq: {
        ...state.enhancedRfq,
        ...input,
        // Handle nested objects specifically to prevent mutations
        ...(input.context && {
          context: {
            ...state.enhancedRfq.context,
            ...input.context
          }
        }),
        ...(input.target_audience && {
          target_audience: {
            ...state.enhancedRfq.target_audience,
            ...input.target_audience
          }
        }),
        ...(input.methodologies && {
          methodologies: {
            ...state.enhancedRfq.methodologies,
            ...input.methodologies
          }
        }),
        ...(input.generation_config && {
          generation_config: {
            ...state.enhancedRfq.generation_config,
            ...input.generation_config
          }
        })
      }
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
  
  setWorkflowState: (workflowState) => set((state) => ({
    workflow: { ...state.workflow, ...workflowState }
  })),

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
      set((state) => ({
        workflow: {
          ...state.workflow,
          status: 'failed',
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }));
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

  connectWebSocket: (workflowId: string) => {
    // Use relative URL so it works in both local and production environments
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/survey/${workflowId}`;
    
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

            // Show success toast for progress-based completion
            get().addToast({
              type: 'success',
              title: '🎉 Survey Complete!',
              message: 'Your professional survey is ready to collect insights!',
              duration: 8000
            });

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
          
          console.log('🔄 [WebSocket] Workflow status updated to completed, survey_id:', message.survey_id);
          
          // Fetch the completed survey
          if (message.survey_id) {
            console.log('📥 [WebSocket] Fetching completed survey:', message.survey_id);
            get().fetchSurvey(message.survey_id).then(() => {
              console.log('✅ [WebSocket] Survey fetched successfully, state should trigger redirect');
              // Log the current state after fetch
              const currentState = get();
              console.log('🔍 [WebSocket] Current state after fetch:', {
                workflowStatus: currentState.workflow.status,
                hasSurvey: !!currentState.currentSurvey,
                surveyId: currentState.currentSurvey?.survey_id
              });
            }).catch((error) => {
              console.error('❌ [WebSocket] Failed to fetch survey:', error);
              // Show error toast if survey fetch fails
              get().addToast({
                type: 'error',
                title: 'Survey Error',
                message: 'Survey was generated but failed to load. Please try refreshing.',
                duration: 6000
              });
            });
          } else {
            console.error('❌ [WebSocket] No survey_id in completion message:', message);
            // Show error toast if no survey ID
            get().addToast({
              type: 'error',
              title: 'Generation Error',
              message: 'Survey generation completed but no survey ID was provided.',
              duration: 6000
            });
          }
          
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
          }, 3000); // 3 second delay
        } else if (message.type === 'error') {
          console.error('Workflow error:', message);
          
          // Show error toast notification
          get().addToast({
            type: 'error',
            title: 'Generation Failed',
            message: message.message || 'Survey generation failed. Please try again.',
            duration: 6000
          });
          
          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'failed',
              error: message.message
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
          set((state) => ({
            workflow: {
              ...state.workflow,
              status: 'failed',
              error: 'WebSocket connection failed after multiple attempts'
            }
          }));
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

    // Clear workflow state
    set((state) => ({
      workflow: { status: 'idle' },
      currentSurvey: undefined,
      rfqInput: {
        title: '',
        description: '',
        product_category: '',
        target_segment: '',
        research_goal: ''
      }
    }));

    // Clear persisted state
    localStorage.removeItem('survey_workflow_state');

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
            (state.status === 'completed' && (currentPath === '/' || currentPath.startsWith('/summary/')));

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
        product_category: rfq.product_category,
        target_segment: rfq.target_audience?.primary_segment || rfq.target_segment,
        research_goal: rfq.research_goal,
        enhanced_rfq_data: rfq // 🎯 Send the full structured data for storage and analytics
      };

      console.log('🚀 [Enhanced RFQ] Submitting with enriched description and structured data:', {
        originalLength: rfq.description?.length || 0,
        enhancedLength: enhancedDescription.length,
        hasObjectives: (rfq.objectives?.length || 0) > 0,
        hasConstraints: (rfq.constraints?.length || 0) > 0,
        hasStakeholders: (rfq.stakeholders?.length || 0) > 0,
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
  }
}));