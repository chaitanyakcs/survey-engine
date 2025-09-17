import { create } from 'zustand';
import { AppStore, RFQRequest, WorkflowState, ProgressMessage, GoldenExampleRequest, ToastMessage, SurveyAnnotations, getQuestionCount } from '../types';
import { apiService } from '../services/api';

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

  // WebSocket connection  
  websocket: undefined as WebSocket | undefined,


  // Actions
  submitRFQ: async (rfq: RFQRequest) => {
    try {
      // Clear any existing survey data when starting new RFQ
      set({ currentSurvey: undefined });
      
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
        
        if (message.type === 'progress') {
          console.log('📊 [Frontend] Progress update received:', {
            step: message.step,
            percent: message.percent,
            message: message.message
          });
          set((state) => ({
            workflow: {
              ...state.workflow,
              current_step: message.step,
              progress: message.percent,
              message: message.message
            }
          }));
          console.log('✅ [Frontend] Progress state updated');
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
  }
}));