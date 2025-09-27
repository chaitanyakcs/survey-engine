// Define error types locally to avoid import issues
export enum ErrorCode {
  // ========== GENERATION ERRORS ==========
  LLM_API_FAILURE = 'GEN_001',
  JSON_PARSING_FAILED = 'GEN_002',
  EVALUATION_FAILED = 'GEN_003',
  INSUFFICIENT_QUESTIONS = 'GEN_004',
  PROMPT_TOO_LONG = 'GEN_005',
  RATE_LIMIT_EXCEEDED = 'GEN_006',
  CONTENT_POLICY_VIOLATION = 'GEN_007',

  // ========== SYSTEM ERRORS ==========
  DATABASE_ERROR = 'SYS_001',
  TIMEOUT_ERROR = 'SYS_002',
  NETWORK_ERROR = 'SYS_003',
  SERVICE_UNAVAILABLE = 'SYS_004',
  AUTHENTICATION_ERROR = 'SYS_005',
  PERMISSION_DENIED = 'SYS_006',

  // ========== VALIDATION ERRORS ==========
  INVALID_RFQ = 'VAL_001',
  MISSING_REQUIRED_FIELDS = 'VAL_002',
  INVALID_METHODOLOGY = 'VAL_003',
  CONFLICTING_REQUIREMENTS = 'VAL_004',

  // ========== WORKFLOW ERRORS ==========
  HUMAN_REVIEW_TIMEOUT = 'WF_001',
  HUMAN_REVIEW_REJECTED = 'WF_002',
  WORKFLOW_INTERRUPTED = 'WF_003',
  STATE_CORRUPTION = 'WF_004',

  // ========== UNKNOWN/FALLBACK ==========
  UNKNOWN_ERROR = 'UNK_001'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum RecoveryAction {
  RETRY = 'retry',
  WAIT_AND_RETRY = 'wait_retry',
  RETURN_TO_FORM = 'return_to_form',
  CONTACT_SUPPORT = 'contact_support',
  RETRY_WITH_DIFFERENT_PARAMS = 'retry_modified',
  REFRESH_PAGE = 'refresh_page',
  CHECK_NETWORK = 'check_network'
}

export interface DebugInfo {
  timestamp: string;
  component?: string;
  action?: string;
  step?: string;
  additionalData?: Record<string, any>;
  stackTrace?: string;
  requestId?: string;
  userId?: string;
  sessionId?: string;
  workflowId?: string;
  userAgent?: string;
  context?: Record<string, any>;
  errorCode?: string;
}

export interface DetailedError {
  code: ErrorCode;
  severity: ErrorSeverity;
  message: string;
  userMessage: string;
  technicalDetails?: string;
  debugInfo: DebugInfo;
  retryable: boolean;
  suggestedActions: RecoveryAction[];
  estimatedRecoveryTime?: number; // minutes
  helpUrl?: string;
  relatedErrors?: ErrorCode[];
}

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
  // ========== BASIC INFO ==========
  title: string;
  description: string;

  // ========== BUSINESS CONTEXT ==========
  business_context: {
    company_product_background: string;    // Background on company, product & research
    business_problem: string;              // What business wants to achieve
    business_objective: string;            // Business objective from research
  };

  // ========== RESEARCH OBJECTIVES ==========
  research_objectives: {
    research_audience: string;             // Respondent type, demographics, segments
    success_criteria: string;              // Desired outcome / success criteria
    key_research_questions: string[];     // Key research questions & considerations
  };

  // ========== METHODOLOGY ==========
  methodology: {
    primary_method: 'van_westendorp' | 'gabor_granger' | 'conjoint' | 'basic_survey';
    stimuli_details?: string;             // Concept details, price ranges
    methodology_requirements?: string;     // Additional methodology notes
  };

  // ========== SURVEY REQUIREMENTS ==========
  survey_requirements: {
    sample_plan: string;                  // Sample structure, LOI, recruiting criteria
    required_sections: string[];          // QNR structure sections
    must_have_questions: string[];        // Must-have Qs per respondent type
    screener_requirements?: string;       // Screener & respondent tagging rules
  };

  // ========== SIMPLE META ==========
  rules_and_definitions?: string;        // Rules, definitions, jargon feed

  // Document Integration
  document_source?: DocumentSource;
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
  type: 'progress' | 'completed' | 'error' | 'human_review_required' | 'workflow_resuming' | 'llm_content_update';
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
  data?: {
    questionCount?: number;
    sectionCount?: number;
    currentActivity?: string;
    latestQuestions?: Array<{
      text: string;
      type?: string;
      hasOptions?: boolean;
    }>;
    currentSections?: Array<{
      title: string;
      questionCount: number;
    }>;
    estimatedProgress?: number;
    surveyTitle?: string;
    elapsedTime?: number;
  };
}

// UI State Types
export interface WorkflowState {
  status: 'idle' | 'started' | 'in_progress' | 'completed' | 'failed' | 'paused' | 'degraded';
  workflow_id?: string;
  survey_id?: string;
  current_step?: string;
  progress?: number;
  message?: string;
  error?: string;
  detailedError?: DetailedError; // Enhanced error information
  degradationReason?: string; // When survey generated but with issues
  workflow_paused?: boolean;
  pending_human_review?: boolean;
  review_id?: number;
  system_prompt?: string;
  prompt_approved?: boolean;
  survey_fetch_failed?: boolean; // When survey fetch fails after completion
  survey_fetch_error?: string; // Error message from failed survey fetch
  streamingStats?: StreamingStats; // Real-time generation progress
}

export interface StreamingStats {
  questionCount: number;
  sectionCount: number;
  currentActivity: string;
  latestQuestions: Array<{
    text: string;
    type?: string;
    hasOptions?: boolean;
  }>;
  currentSections: Array<{
    title: string;
    questionCount: number;
  }>;
  estimatedProgress: number;
  surveyTitle?: string;
  elapsedTime?: number;
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

  // Prompt editing fields
  edited_prompt_data?: string;
  original_prompt_data?: string;
  prompt_edited: boolean;
  prompt_edit_timestamp?: string;
  edited_by?: string;
  edit_reason?: string;
}

export interface EditPromptRequest {
  edited_prompt: string;
  edit_reason?: string;
}

export interface ReviewDecision {
  decision: 'approve' | 'reject' | 'approve_with_edits';
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

// Document Integration Types
export interface DocumentContent {
  raw_text: string;
  filename: string;
  word_count: number;
  extraction_timestamp: string;
  file_size?: number;
  content_type?: string;
}

export interface DocumentSource {
  type: 'upload' | 'paste';
  filename: string;
  upload_id?: string;
}

export interface DocumentAnalysis {
  confidence: number;
  identified_sections: {
    objectives?: SectionMatch;
    business_context?: SectionMatch;
    target_audience?: SectionMatch;
    constraints?: SectionMatch;
    methodologies?: SectionMatch;
    stakeholders?: SectionMatch;
    success_metrics?: SectionMatch;
  };
  extracted_entities: {
    stakeholders: string[];
    industries: string[];
    research_types: string[];
    methodologies: string[];
  };
  field_mappings: RFQFieldMapping[];
  processing_error?: string;
  extraction_error?: string;
}

export interface SectionMatch {
  confidence: number;
  source_text: string;
  source_section: string;
  extracted_data: any;
  reasoning: string;
}

export interface RFQFieldMapping {
  field: keyof EnhancedRFQRequest | string;
  value: any;
  confidence: number;
  source: string;
  reasoning: string;
  needs_review: boolean;
  suggestions?: string[];
  user_action?: 'accepted' | 'rejected' | 'edited';
  original_value?: any;
}

export interface DocumentAnalysisResponse {
  document_content: DocumentContent;
  rfq_analysis: DocumentAnalysis;
  processing_status: 'completed' | 'error' | 'processing';
  errors: string[];
}

export interface DocumentUploadProgress {
  stage: 'uploading' | 'parsing' | 'analyzing' | 'mapping' | 'completed' | 'error';
  progress: number;
  message: string;
  error?: string;
}

// Error Handling Types
export * from './errors';

// Explicitly export ErrorClassifier to ensure it's available
export { ErrorClassifier } from './errors';

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
  workflowTimeoutId?: NodeJS.Timeout;
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
  loadPillarScoresAsync: (surveyId: string) => Promise<any>;
  startPillarEvaluationPolling: (surveyId: string) => void;
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

  // Document Upload State
  documentContent?: DocumentContent;
  documentAnalysis?: DocumentAnalysis;
  fieldMappings: RFQFieldMapping[];
  isDocumentProcessing: boolean;
  documentUploadError?: string;

  // Document Upload Actions
  uploadDocument: (file: File, sessionId?: string) => Promise<DocumentAnalysisResponse>;
  analyzeText: (text: string, filename?: string) => Promise<DocumentAnalysisResponse>;
  acceptFieldMapping: (field: string, value: any) => void;
  rejectFieldMapping: (field: string) => void;
  editFieldMapping: (field: string, value: any) => void;
  clearDocumentData: () => void;
  applyDocumentMappings: () => void;
  buildRFQUpdatesFromMappings: (mappings: RFQFieldMapping[]) => Partial<EnhancedRFQRequest>;

  // Enhanced RFQ State Persistence
  persistEnhancedRfqState: (enhancedRfq: EnhancedRFQRequest) => void;
  restoreEnhancedRfqState: () => boolean;
  clearEnhancedRfqState: () => void;
}