// Utility Functions
export const getQuestionCount = (survey: Survey): number => {
  // Check if we have sections (new format)
  if (survey.sections && survey.sections.length > 0) {
    return survey.sections.reduce((total, section) => total + (section.questions?.length || 0), 0);
  }
  // Fallback to legacy format
  return survey.questions?.length || 0;
};

// Enhanced RFQ Types
export interface RFQObjective {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  methodology_suggestions?: string[];
}

export interface RFQConstraint {
  id: string;
  type: 'budget' | 'timeline' | 'sample_size' | 'methodology' | 'custom';
  description: string;
  value?: string | number;
}

export interface RFQStakeholder {
  id: string;
  role: string;
  requirements: string;
  decision_influence: 'high' | 'medium' | 'low';
}

export interface RFQSuccess {
  id: string;
  metric: string;
  description: string;
  measurement: string;
}

export interface RFQTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  use_cases: string[];
  estimated_completion: number;
  complexity: 'simple' | 'moderate' | 'complex';
  template_data: Partial<EnhancedRFQRequest>;
}

export interface RFQQualityAssessment {
  overall_score: number;
  clarity_score: number;
  specificity_score: number;
  methodology_alignment: number;
  completeness_score: number;
  recommendations: string[];
  confidence_indicators: {
    objectives_clear: boolean;
    target_defined: boolean;
    methodology_appropriate: boolean;
    constraints_realistic: boolean;
  };
}

export interface EnhancedRFQRequest {
  // Basic Information
  title?: string;
  description: string;

  // Legacy fields for backward compatibility
  product_category?: string;
  target_segment?: string;
  research_goal?: string;

  // Enhanced Structure
  context?: {
    business_background?: string;
    market_situation?: string;
    decision_timeline?: string;
  };

  objectives?: RFQObjective[];

  target_audience?: {
    primary_segment?: string;
    secondary_segments?: string[];
    demographics?: Record<string, any>;
    size_estimate?: number;
    accessibility_notes?: string;
  };

  methodologies?: {
    preferred?: string[];
    excluded?: string[];
    requirements?: string[];
  };

  constraints?: RFQConstraint[];
  stakeholders?: RFQStakeholder[];
  success_metrics?: RFQSuccess[];

  // AI Configuration
  generation_config?: {
    creativity_level?: 'conservative' | 'balanced' | 'innovative';
    length_preference?: 'concise' | 'standard' | 'comprehensive';
    complexity_level?: 'basic' | 'intermediate' | 'advanced';
    include_validation_questions?: boolean;
    enable_adaptive_routing?: boolean;
  };

  // Meta Information
  estimated_budget?: string;
  expected_timeline?: string;
  approval_requirements?: string[];
  template_used?: string;
}

// Core API Types (Legacy compatibility)
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
  type: 'progress' | 'completed' | 'error' | 'human_review_required' | 'workflow_resuming';
  step?: string;
  percent?: number;
  message?: string;
  survey_id?: string;
  status?: string;
  workflow_paused?: boolean;
  review_id?: number;
  system_prompt?: string;
  pending_human_review?: boolean;
  prompt_approved?: boolean;
}

// UI State Types
export interface WorkflowState {
  status: 'idle' | 'started' | 'in_progress' | 'completed' | 'failed' | 'paused';
  workflow_id?: string;
  survey_id?: string;
  current_step?: string;
  progress?: number;
  message?: string;
  error?: string;
  workflow_paused?: boolean;
  pending_human_review?: boolean;
  review_id?: number;
  system_prompt?: string;
  prompt_approved?: boolean;
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
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
  duration?: number;
}

// Human Review Types
export interface PendingReview {
  id: number;
  workflow_id: string;
  survey_id?: string;
  review_status: 'pending' | 'in_progress' | 'in_review' | 'approved' | 'rejected' | 'expired';
  prompt_data: string;
  original_rfq: string;
  reviewer_id?: string;
  review_deadline?: string;
  reviewer_notes?: string;
  approval_reason?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
  is_expired?: boolean;
  time_remaining_hours?: number;
}

export interface ReviewDecision {
  decision: 'approve' | 'reject';
  notes?: string;
  reason?: string;
}

export interface PendingReviewsSummary {
  total_pending: number;
  total_in_progress: number;
  total_expired: number;
  oldest_pending?: string;
  reviews: PendingReview[];
}

// Store Types
export interface AppStore {
  // RFQ Input
  rfqInput: RFQRequest;
  setRFQInput: (input: Partial<RFQRequest>) => void;

  // Enhanced RFQ State
  enhancedRfq: EnhancedRFQRequest;
  setEnhancedRfq: (input: Partial<EnhancedRFQRequest>) => void;

  // RFQ Templates
  rfqTemplates: RFQTemplate[];
  setRfqTemplates: (templates: RFQTemplate[]) => void;
  selectedTemplate?: RFQTemplate;
  setSelectedTemplate: (template?: RFQTemplate) => void;

  // RFQ Quality Assessment
  rfqAssessment?: RFQQualityAssessment;
  setRfqAssessment: (assessment?: RFQQualityAssessment) => void;
  
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
  submitEnhancedRFQ: (rfq: EnhancedRFQRequest) => Promise<void>;
  fetchSurvey: (surveyId: string) => Promise<void>;
  connectWebSocket: (workflowId: string) => void;
  disconnectWebSocket: () => void;

  // Enhanced RFQ Actions
  fetchRfqTemplates: () => Promise<void>;
  assessRfqQuality: (rfq: EnhancedRFQRequest) => Promise<void>;
  generateRfqSuggestions: (partialRfq: Partial<EnhancedRFQRequest>) => Promise<string[]>;
  
  // Golden Examples Actions
  fetchGoldenExamples: () => Promise<void>;
  createGoldenExample: (example: GoldenExampleRequest) => Promise<void>;
  updateGoldenExample: (id: string, example: GoldenExampleRequest) => Promise<void>;
  deleteGoldenExample: (id: string) => Promise<void>;
  
  // Annotation Actions
  saveAnnotations: (annotations: SurveyAnnotations) => Promise<void>;
  loadAnnotations: (surveyId: string) => Promise<void>;
  
  // Human Review State
  pendingReviews: PendingReview[];
  activeReview?: PendingReview;
  setPendingReviews: (reviews: PendingReview[]) => void;
  setActiveReview: (review?: PendingReview) => void;
  
  // Human Review Actions
  checkPendingReviews: () => Promise<void>;
  fetchReviewByWorkflow: (workflowId: string) => Promise<PendingReview | null>;
  submitReviewDecision: (reviewId: number, decision: ReviewDecision) => Promise<void>;
  resumeReview: (reviewId: number) => Promise<void>;
  persistWorkflowState: (workflowId: string, state: any) => void;
  recoverWorkflowState: () => Promise<void>;
  resetWorkflow: () => void;
}