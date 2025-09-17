// Utility Functions
export const getQuestionCount = (survey: Survey): number => {
  // Check if we have sections (new format)
  if (survey.sections && survey.sections.length > 0) {
    return survey.sections.reduce((total, section) => total + (section.questions?.length || 0), 0);
  }
  // Fallback to legacy format
  return survey.questions?.length || 0;
};

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

export interface SurveySection {
  id: number;
  title: string;
  description: string;
  questions: Question[];
}

export interface Survey {
  survey_id: string;
  title: string;
  description: string;
  estimated_time: number;
  confidence_score: number;
  methodologies: string[];
  golden_examples: GoldenExample[];
  // Support both legacy and new formats
  questions?: Question[];
  sections?: SurveySection[];
  metadata: SurveyMetadata;
  raw_output?: {
    document_text?: string;
    extraction_timestamp?: string;
    source_file?: string;
    error?: string;
  };
  // For golden examples that have nested structure
  final_output?: Survey;
  settings?: any;
  pillar_scores?: {
    overall_grade: string;
    weighted_score: number;
    total_score: number;
    summary: string;
    pillar_breakdown: Array<{
      pillar_name: string;
      display_name: string;
      score: number;
      weighted_score: number;
      weight: number;
      criteria_met: number;
      total_criteria: number;
      grade: string;
    }>;
    recommendations: string[];
  };
}

export interface SurveyListItem {
  id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
  methodology_tags: string[];
  quality_score?: number;
  estimated_time?: number;
  question_count: number;
  annotation?: Record<string, any>;
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
  sections_count?: number;
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

// Annotation Types
export type LikertScale = 1 | 2 | 3 | 4 | 5;

export interface QuestionAnnotation {
  questionId: string;
  required: boolean;
  quality: LikertScale;
  relevant: LikertScale;
  pillars: {
    methodologicalRigor: LikertScale;
    contentValidity: LikertScale;
    respondentExperience: LikertScale;
    analyticalValue: LikertScale;
    businessImpact: LikertScale;
  };
  comment?: string;
  annotatorId?: string;
  timestamp?: string;
}

export interface SectionAnnotation {
  sectionId: string;
  quality: LikertScale;
  relevant: LikertScale;
  pillars: {
    methodologicalRigor: LikertScale;
    contentValidity: LikertScale;
    respondentExperience: LikertScale;
    analyticalValue: LikertScale;
    businessImpact: LikertScale;
  };
  comment?: string;
  annotatorId?: string;
  timestamp?: string;
}

export interface SurveyAnnotations {
  surveyId: string;
  questionAnnotations: QuestionAnnotation[];
  sectionAnnotations: SectionAnnotation[];
  overallComment?: string;
  annotatorId?: string;
  createdAt?: string;
  updatedAt?: string;
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
  
  // Annotation State
  isAnnotationMode: boolean;
  setAnnotationMode: (enabled: boolean) => void;
  currentAnnotations?: SurveyAnnotations;
  setCurrentAnnotations: (annotations: SurveyAnnotations) => void;
  
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
  
  // Annotation Actions
  saveAnnotations: (annotations: SurveyAnnotations) => Promise<void>;
  loadAnnotations: (surveyId: string) => Promise<void>;
}