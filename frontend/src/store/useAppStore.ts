import { create } from 'zustand';
import { AppStore, RFQRequest, Survey, WorkflowState, ProgressMessage, GoldenExample, GoldenExampleRequest, ToastMessage } from '../types';
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
  },
  
  setWorkflowState: (workflowState) => set((state) => ({
    workflow: { ...state.workflow, ...workflowState }
  })),

  // Survey State
  currentSurvey: undefined,
  setSurvey: (survey) => set({ currentSurvey: survey }),

  // Golden Examples State
  goldenExamples: [],
  setGoldenExamples: (examples) => set({ goldenExamples: examples }),

  // UI State
  selectedQuestionId: undefined,
  setSelectedQuestion: (id) => set({ selectedQuestionId: id }),

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
      set((state) => ({
        workflow: { ...state.workflow, status: 'started' }
      }));

      const response = await apiService.submitRFQ(rfq);
      
      set((state) => ({
        workflow: {
          ...state.workflow,
          workflow_id: response.workflow_id,
          survey_id: response.survey_id,
          status: 'in_progress'
        }
      }));

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
    try {
      const survey = await apiService.fetchSurvey(surveyId);
      set({ currentSurvey: survey });
    } catch (error) {
      console.error('Failed to fetch survey:', error);
    }
  },

  connectWebSocket: (workflowId: string) => {
    const wsUrl = `ws://localhost:8001/ws/survey/${workflowId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const message: ProgressMessage = JSON.parse(event.data);
      
      if (message.type === 'progress') {
        set((state) => ({
          workflow: {
            ...state.workflow,
            current_step: message.step,
            progress: message.percent,
            message: message.message
          }
        }));
      } else if (message.type === 'completed') {
        set((state) => ({
          workflow: {
            ...state.workflow,
            status: 'completed',
            survey_id: message.survey_id
          }
        }));
        
        // Fetch the completed survey
        if (message.survey_id) {
          get().fetchSurvey(message.survey_id);
        }
      } else if (message.type === 'error') {
        set((state) => ({
          workflow: {
            ...state.workflow,
            status: 'failed',
            error: message.message
          }
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      set((state) => ({
        workflow: {
          ...state.workflow,
          status: 'failed',
          error: 'Connection failed'
        }
      }));
    };

    set({ websocket: ws });
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
      const response = await fetch('http://localhost:8001/api/v1/golden-examples');
      if (!response.ok) throw new Error('Failed to fetch golden examples');
      const data = await response.json();
      get().setGoldenExamples(data.examples);
    } catch (error) {
      console.error('Failed to fetch golden examples:', error);
    }
  },

  createGoldenExample: async (example: GoldenExampleRequest) => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/golden-examples', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(example),
      });
      if (!response.ok) throw new Error('Failed to create golden example');
      
      // Show success toast
      get().addToast({
        type: 'success',
        title: 'Success',
        message: 'Golden example created successfully',
        duration: 4000
      });
    } catch (error) {
      console.error('Failed to create golden example:', error);
      
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
      const response = await fetch(`http://localhost:8001/api/v1/golden-examples/${id}`, {
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
      const response = await fetch(`http://localhost:8001/api/v1/golden-examples/${id}`, {
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
  }
}));