// Core API Types
export interface RFQRequest {
  title?: string;
  description: string;
  product_category?: string;
  target_segment?: string;
  research_goal?: string;
}

export interface RFQSubmissionResponse {
  workflow_id: string;
  survey_id: string;
  status: string;
}

export interface Survey {
  survey_id: string;
  title: string;
  description: string;
  estimated_time: number;
  confidence_score: number;
  methodologies: string[];
  golden_examples: GoldenExample[];
  questions: Question[];
  metadata: SurveyMetadata;
}

export interface Question {
  id: string;
  text: string;
  type: 'multiple_choice' | 'scale' | 'text' | 'ranking';
  options?: string[];
  scale_labels?: Record<string, string>;
  required: boolean;
  category: string;
  methodology?: string;
  ai_rationale?: string;
}

// Removed duplicate interface - using the full definition below

export interface SurveyMetadata {
  target_responses: number;
  methodology: string[];
  [key: string]: any;
}

// WebSocket Progress Types
export interface ProgressMessage {
  type: 'progress' | 'completed' | 'error';
  step?: string;
  percent?: number;
  message?: string;
  survey_id?: string;
  status?: string;
}

// UI State Types
export interface WorkflowState {
  status: 'idle' | 'started' | 'in_progress' | 'completed' | 'failed';
  workflow_id?: string;
  survey_id?: string;
  current_step?: string;
  progress?: number;
  message?: string;
  error?: string;
}

// Golden Examples Types
export interface GoldenExample {
  id: string;
  rfq_text: string;
  survey_json: Survey;
  methodology_tags: string[];
  industry_category: string;
  research_goal: string;
  quality_score: number;
  usage_count: number;
  created_at: string;
}

export interface GoldenExampleRequest {
  title?: string;
  rfq_text: string;
  survey_json: Survey;
  methodology_tags: string[];
  industry_category: string;
  research_goal: string;
  quality_score?: number;
}

export interface GoldenExamplesResponse {
  examples: GoldenExample[];
  count: number;
}

// Toast Types
export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

// Store Types
export interface AppStore {
  // RFQ Input
  rfqInput: RFQRequest;
  setRFQInput: (input: Partial<RFQRequest>) => void;
  
  // Workflow State
  workflow: WorkflowState;
  setWorkflowState: (state: Partial<WorkflowState>) => void;
  
  // Survey Data
  currentSurvey?: Survey;
  setSurvey: (survey: Survey) => void;
  
  // Golden Examples
  goldenExamples: GoldenExample[];
  setGoldenExamples: (examples: GoldenExample[]) => void;
  
  // UI State
  selectedQuestionId?: string;
  setSelectedQuestion: (id?: string) => void;
  
  // Toast Notifications
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
  
  // WebSocket
  websocket?: WebSocket;
  
  
  // Actions
  submitRFQ: (rfq: RFQRequest) => Promise<void>;
  fetchSurvey: (surveyId: string) => Promise<void>;
  connectWebSocket: (workflowId: string) => void;
  disconnectWebSocket: () => void;
  
  // Golden Examples Actions
  fetchGoldenExamples: () => Promise<void>;
  createGoldenExample: (example: GoldenExampleRequest) => Promise<void>;
  updateGoldenExample: (id: string, example: GoldenExampleRequest) => Promise<void>;
  deleteGoldenExample: (id: string) => Promise<void>;
}