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
    // Enhanced fields
    stakeholder_requirements?: string;     // Key stakeholder needs and requirements
    decision_criteria?: string;            // What defines success for this research
    budget_range?: 'under_10k' | '10k_25k' | '25k_50k' | '50k_100k' | 'over_100k';
    timeline_constraints?: 'urgent_1_week' | 'fast_2_weeks' | 'standard_4_weeks' | 'extended_8_weeks' | 'flexible';
  };

  // ========== RESEARCH OBJECTIVES ==========
  research_objectives: {
    research_audience: string;             // Respondent type, demographics, segments
    success_criteria: string;              // Desired outcome / success criteria
    key_research_questions: string[];     // Key research questions & considerations
    // Enhanced fields
    success_metrics?: string;              // How research success will be measured
    validation_requirements?: string;      // What validation is needed
    measurement_approach?: 'quantitative' | 'qualitative' | 'mixed_methods';
  };

  // ========== METHODOLOGY ==========
  methodology: {
    primary_method: 'van_westendorp' | 'gabor_granger' | 'conjoint' | 'basic_survey';
    stimuli_details?: string;             // Concept details, price ranges
    methodology_requirements?: string;     // Additional methodology notes
    // Enhanced fields
    complexity_level?: 'simple' | 'intermediate' | 'complex' | 'expert_level';
    required_methodologies?: string[];     // Specific methodologies required
    sample_size_target?: string;          // Target number of respondents
  };

  // ========== SURVEY REQUIREMENTS ==========
  survey_requirements: {
    sample_plan: string;                  // Sample structure, LOI, recruiting criteria
    required_sections?: string[];         // QNR structure sections (moved to survey_structure)
    must_have_questions: string[];        // Must-have Qs per respondent type
    screener_requirements?: string;       // Screener & respondent tagging rules
    // Enhanced fields
    completion_time_target?: 'under_5min' | '5_10min' | '10_15min' | '15_20min' | '20_30min' | 'over_30min';
    device_compatibility?: 'mobile_only' | 'desktop_only' | 'mobile_first' | 'desktop_first' | 'all_devices';
    accessibility_requirements?: 'basic' | 'wcag_aa' | 'wcag_aaa' | 'custom';
    data_quality_requirements?: 'basic' | 'standard' | 'premium';
  };

  // ========== ADVANCED CLASSIFICATION ==========
  advanced_classification?: {
    industry_classification?: string;      // From INDUSTRY_CLASSIFICATIONS
    respondent_classification?: string;    // From RESPONDENT_TYPES
    methodology_tags?: string[];          // From METHODOLOGY_TAGS
    compliance_requirements?: string[];   // GDPR, CCPA, Healthcare, Financial, etc.
    target_countries?: string[];          // Geographic targeting (QNR_Country)
    healthcare_specifics?: {              // Medical/Healthcare requirements
      medical_conditions_general?: boolean;
      medical_conditions_study?: boolean;
      patient_requirements?: string;
    };
  };

  // ========== SURVEY STRUCTURE PREFERENCES ==========
  survey_structure?: {
    qnr_sections?: string[];              // Selected QNR sections
    text_requirements?: string[];         // Required text introduction types
  };

  // ========== SURVEY LOGIC REQUIREMENTS ==========
  survey_logic?: {
    requires_piping_logic?: boolean;      // Piping requirements
    requires_sampling_logic?: boolean;    // Sampling logic rules
    requires_screener_logic?: boolean;    // Screener termination rules
    custom_logic_requirements?: string;   // Custom logic descriptions
    piping_logic?: string;                // Legacy field for backward compatibility
    sampling_logic?: string;             // Legacy field for backward compatibility
    screener_logic?: string;             // Legacy field for backward compatibility
    user_categorization?: string;        // User/Non-User categorization
  };

  // ========== BRAND & USAGE REQUIREMENTS ==========
  brand_usage_requirements?: {
    brand_recall_required?: boolean;      // Top of mind brand questions
    brand_awareness_funnel?: boolean;     // Awareness → Consideration → Purchase funnel
    brand_product_satisfaction?: boolean; // Current brand satisfaction
    usage_frequency_tracking?: boolean;   // Usage frequency questions
    brand_recall_needed?: boolean;        // Legacy field for backward compatibility
    brand_satisfaction?: boolean;         // Legacy field for backward compatibility
    purchase_decision_factors?: boolean;  // Purchase influence factors
    category_usage_frequency?: boolean;   // Legacy field for backward compatibility
    category_usage_financial?: boolean;   // Spend and financial patterns
    future_consideration?: boolean;       // Future purchase consideration
  };

  // ========== ADDITIONAL REQUIREMENTS ==========
  additional_requirements?: {
    detailed_demographics?: string[];    // Education, Employment, Salary, Ethnicity
    adoption_behavior?: boolean;         // Innovation adoption patterns
    media_consumption?: boolean;         // Media platform usage
    feature_awareness?: boolean;         // Technology and feature awareness
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

export interface SurveyTextContent {
  id: string;
  type: 'introduction' | 'transition' | 'instruction' | 'concept_intro' | 'study_intro' | 'confidentiality' | 'product_usage';
  content: string;
  mandatory: boolean;
  label?: string; // Maps to AiRA labeling (e.g., "Concept_Intro", "Study_Intro")
  section_id?: number; // Links to parent section
  order?: number; // Position within section content
}

export interface SurveySection {
  id: number;
  title: string;
  description: string;
  questions: Question[];
  order: number;

  // NEW: Optional text content before and after questions
  introText?: SurveyTextContent;
  closingText?: SurveyTextContent;

  // NEW: Additional text blocks for complex sections
  textBlocks?: SurveyTextContent[];
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
  // Comment metadata from DOCX extraction
  comment_metadata?: {
    total_comments: number;
    comment_categories: string[];
    extraction_timestamp: string;
  };
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
  rfq_data?: EnhancedRFQRequest;  // NEW
  rfq_id?: string;  // NEW
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
  type: 'multiple_choice' | 'single_choice' | 'yes_no' | 'dropdown' | 'scale' | 'text' | 'ranking' | 'instruction' | 'matrix' | 'numeric' | 'date' | 'boolean' | 'open_text' | 'multiple_select' | 'matrix_likert' | 'constant_sum' | 'numeric_grid' | 'numeric_open' | 'likert' | 'open_end' | 'display_only' | 'single_open' | 'multiple_open' | 'open_ended' | 'gabor_granger' | 'maxdiff' | 'van_westendorp' | 'conjoint' | 'unknown';
  options?: string[];
  features?: string[]; // For MaxDiff questions
  scale_labels?: Record<string, string>;
  required: boolean;
  category: string;
  methodology?: string;
  ai_rationale?: string;
  description?: string; // For additional context, especially useful for instructions
  label?: string; // For programming notes and other labels
  labels?: string[]; // Array of auto-detected labels for categorization
  order?: number; // Order within section or survey
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

// LLM Audit Types
export interface LLMAuditRecord {
  id: string;
  interaction_id: string;
  parent_workflow_id?: string;
  parent_survey_id?: string;
  parent_rfq_id?: string;
  model_name: string;
  model_provider: string;
  model_version?: string;
  purpose: string;
  sub_purpose?: string;
  context_type?: string;
  input_prompt: string;
  input_tokens?: number;
  output_content?: string;
  output_tokens?: number;
  raw_response?: any;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stop_sequences?: string[];
  response_time_ms?: number;
  cost_usd?: number;
  success: boolean;
  error_message?: string;
  interaction_metadata?: Record<string, any>;
  tags?: string[];
  created_at: string;
  updated_at: string;
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
  quality_score: number | null;
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
  quality_score?: number | null;
  auto_generate_rfq?: boolean;  // Flag to indicate if RFQ should be auto-generated
}

export interface GoldenExampleFormState {
  formData: GoldenExampleRequest;
  autoGenerateRfq: boolean;
  rfqInputMode: 'text' | 'upload';
  timestamp: number;
}

export interface GoldenExamplesResponse {
  examples: GoldenExample[];
  count: number;
}

// Annotation Types
export type LikertScale = 1 | 2 | 3 | 4 | 5;

// Advanced Labeling Constants
export const INDUSTRY_CLASSIFICATIONS = [
  'technology',
  'healthcare',
  'financial',
  'retail',
  'education',
  'automotive',
  'real_estate',
  'food_beverage',
  'travel',
  'entertainment'
] as const;

export const RESPONDENT_TYPES = [
  'B2C',
  'B2B',
  'healthcare_professional',
  'student',
  'expert',
  'employee'
] as const;

export const METHODOLOGY_TAGS = [
  'quantitative',
  'qualitative',
  'demographic',
  'behavioral',
  'attitudinal',
  'screening',
  'net_promoter',
  'van_westendorp'
] as const;

export const SECTION_CLASSIFICATIONS = [
  'introduction',
  'demographics',
  'screening',
  'content',
  'closing'
] as const;

export const COMPLIANCE_STATUS_OPTIONS = [
  'compliant',
  'needs_review',
  'non_compliant',
  'not_checked'
] as const;

// Enhanced RFQ Constants
export const BUDGET_RANGES = [
  'under_10k',
  '10k_50k',
  '50k_100k',
  '100k_plus'
] as const;

export const TIMELINE_CONSTRAINTS = [
  'rush',
  'standard',
  'flexible'
] as const;

export const MEASUREMENT_APPROACHES = [
  'quantitative',
  'qualitative',
  'mixed_methods'
] as const;

export const COMPLEXITY_LEVELS = [
  'simple',
  'standard',
  'advanced'
] as const;

export const COMPLETION_TIME_TARGETS = [
  '5_10_min',
  '10_15_min',
  '15_25_min',
  '25_plus_min'
] as const;

export const DEVICE_COMPATIBILITY_OPTIONS = [
  'mobile_first',
  'desktop_first',
  'both'
] as const;

export const ACCESSIBILITY_REQUIREMENTS = [
  'standard',
  'enhanced',
  'full_compliance'
] as const;

export const DATA_QUALITY_REQUIREMENTS = [
  'basic',
  'standard',
  'premium'
] as const;

export const COMPLIANCE_REQUIREMENTS = [
  'GDPR',
  'CCPA',
  'Healthcare',
  'Financial',
  'Standard Data Protection'
] as const;

export const REQUIRED_METHODOLOGIES = [
  'van_westendorp',
  'gabor_granger',
  'conjoint',
  'maxdiff',
  'monadic_testing',
  'concept_testing',
  'brand_tracking',
  'usage_attitudes'
] as const;

// AiRA Mandatory Text Requirements
export const AIRA_TEXT_LABELS = [
  'Study_Intro',
  'Concept_Intro',
  'Confidentiality_Agreement',
  'Product_Usage'
] as const;

export const TEXT_CONTENT_TYPES = [
  'introduction',
  'transition',
  'instruction',
  'concept_intro',
  'study_intro',
  'confidentiality',
  'product_usage'
] as const;

// Mapping of AiRA labels to content types
export const AIRA_LABEL_TO_TYPE_MAP: Record<string, string> = {
  'Study_Intro': 'study_intro',
  'Concept_Intro': 'concept_intro',
  'Confidentiality_Agreement': 'confidentiality',
  'Product_Usage': 'product_usage'
};

// Text requirements by methodology
export const METHODOLOGY_TEXT_REQUIREMENTS: Record<string, string[]> = {
  'van_westendorp': ['Study_Intro', 'Concept_Intro'],
  'gabor_granger': ['Study_Intro', 'Concept_Intro'],
  'conjoint': ['Study_Intro', 'Product_Usage'],
  'basic_survey': ['Study_Intro']
};

// QNR Country/Geographic Options (from QNR Tags)
export const QNR_COUNTRIES = [
  'Canada',
  'EU',
  'France',
  'India',
  'Japan',
  'UK',
  'US'
] as const;

// Additional Demographics Options
export const ADDITIONAL_DEMOGRAPHICS = [
  'Education',
  'Employment',
  'Salary',
  'Ethnicity',
  'Household_Income',
  'Marital_Status',
  'Children'
] as const;

// Survey Logic Types
export const SURVEY_LOGIC_TYPES = [
  'piping_logic',
  'sampling_logic',
  'screener_logic',
  'user_categorization'
] as const;

// Mandatory QNR Sections (from QNR labeling)
export const MANDATORY_QNR_SECTIONS = [
  'Additional Questions',
  'Brand/Product Awareness & Usage',
  'Concept exposure',
  'Methodology',
  'Programmer Instructions',
  'Sample Plan',
  'Screener'
] as const;

export type IndustryClassification = typeof INDUSTRY_CLASSIFICATIONS[number];
export type RespondentType = typeof RESPONDENT_TYPES[number];
export type MethodologyTag = typeof METHODOLOGY_TAGS[number];
export type SectionClassification = typeof SECTION_CLASSIFICATIONS[number];
export type ComplianceStatus = typeof COMPLIANCE_STATUS_OPTIONS[number];

// Enhanced RFQ Types
export type BudgetRange = typeof BUDGET_RANGES[number];
export type TimelineConstraint = typeof TIMELINE_CONSTRAINTS[number];
export type MeasurementApproach = typeof MEASUREMENT_APPROACHES[number];
export type ComplexityLevel = typeof COMPLEXITY_LEVELS[number];
export type CompletionTimeTarget = typeof COMPLETION_TIME_TARGETS[number];
export type DeviceCompatibility = typeof DEVICE_COMPATIBILITY_OPTIONS[number];
export type AccessibilityRequirement = typeof ACCESSIBILITY_REQUIREMENTS[number];
export type DataQualityRequirement = typeof DATA_QUALITY_REQUIREMENTS[number];
export type ComplianceRequirement = typeof COMPLIANCE_REQUIREMENTS[number];
export type RequiredMethodology = typeof REQUIRED_METHODOLOGIES[number];
export type AiRATextLabel = typeof AIRA_TEXT_LABELS[number];
export type TextContentType = typeof TEXT_CONTENT_TYPES[number];
export type QNRCountry = typeof QNR_COUNTRIES[number];
export type AdditionalDemographic = typeof ADDITIONAL_DEMOGRAPHICS[number];
export type SurveyLogicType = typeof SURVEY_LOGIC_TYPES[number];
export type MandatoryQNRSection = typeof MANDATORY_QNR_SECTIONS[number];

export interface QuestionAnnotation {
  id?: number; // Database ID for API operations
  questionId: string;
  originalQuestionId?: string; // Original question ID with survey prefix for API operations
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
  labels?: string[];
  removedLabels?: string[]; // Track auto-generated labels that user explicitly removed
  annotatorId?: string;
  timestamp?: string;
  
  // AI-generated annotation tracking
  aiGenerated?: boolean;
  aiConfidence?: number; // 0.0-1.0
  humanVerified?: boolean;
  generationTimestamp?: string;
  
  // Human override tracking
  humanOverridden?: boolean;
  overrideTimestamp?: string;
  originalAiQuality?: number;
  originalAiRelevant?: number;
  originalAiComment?: string;
}

export interface SectionAnnotation {
  id?: number; // Database ID for API operations
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
  labels?: string[];
  annotatorId?: string;
  timestamp?: string;

  // Advanced labeling fields
  section_classification?: string;
  mandatory_elements?: Record<string, any>;
  compliance_score?: number;
  
  // AI-generated annotation tracking
  aiGenerated?: boolean;
  aiConfidence?: number; // 0.0-1.0
  humanVerified?: boolean;
  generationTimestamp?: string;
  
  // Human override tracking
  humanOverridden?: boolean;
  overrideTimestamp?: string;
  originalAiQuality?: number;
  originalAiRelevant?: number;
  originalAiComment?: string;
}

export interface SurveyLevelAnnotation {
  surveyId: string;
  overallComment?: string;
  labels?: string[];
  annotatorId?: string;
  timestamp?: string;

  // Advanced labeling fields
  detectedLabels?: Record<string, any>;
  complianceReport?: Record<string, any>;
  advancedMetadata?: Record<string, any>;

  // Survey-level quality ratings
  overallQuality?: LikertScale;
  surveyRelevance?: LikertScale;
  methodologyScore?: LikertScale;
  respondentExperienceScore?: LikertScale;
  businessValueScore?: LikertScale;

  // Survey classification
  surveyType?: string;
  industryCategory?: string;
  researchMethodology?: string[];
  targetAudience?: string;
  surveyComplexity?: 'simple' | 'moderate' | 'complex';
  estimatedDuration?: number; // in minutes
  complianceStatus?: 'compliant' | 'non-compliant' | 'needs-review';
}

export interface SurveyAnnotations {
  surveyId: string;
  surveyLevelAnnotation?: SurveyLevelAnnotation;
  questionAnnotations: QuestionAnnotation[];
  sectionAnnotations: SectionAnnotation[];
  overallComment?: string;
  annotatorId?: string;
  createdAt?: string;
  updatedAt?: string;

  // Advanced labeling fields
  detected_labels?: Record<string, any>;
  compliance_report?: Record<string, any>;
  advanced_metadata?: Record<string, any>;
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

export interface DocumentParseResponse {
  survey_json: Survey;
  confidence_score?: number;
  extracted_text: string;
  product_category?: string;
  research_goal?: string;
  methodologies?: string[];
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
  details?: string;
  estimated_time?: number;
  content_preview?: string;
  error?: string;
}

// Error Handling Types
export * from './errors';

// Explicitly export ErrorClassifier to ensure it's available
export { ErrorClassifier } from './errors';

// Store Types
// Text Content Compliance Validation
export interface TextComplianceCheck {
  label: AiRATextLabel;
  type: TextContentType;
  required: boolean;
  found: boolean;
  content?: SurveyTextContent;
  section?: string;
}

export interface TextComplianceReport {
  survey_id: string;
  methodology: string[];
  required_text_elements: TextComplianceCheck[];
  missing_elements: AiRATextLabel[];
  compliance_score: number;
  compliance_level: 'full' | 'partial' | 'poor';
  recommendations: string[];
  analysis_timestamp: string;
}

// Helper functions for text validation
export interface TextValidationUtils {
  getRequiredTextForMethodology: (methodology: string[]) => AiRATextLabel[];
  validateSurveyTextCompliance: (survey: Survey) => TextComplianceReport;
  generateMissingTextContent: (missing: AiRATextLabel[], rfq: EnhancedRFQRequest) => SurveyTextContent[];
}

export interface AppStore {
  // Model Loading State
  modelLoading: {
    loading: boolean;
    ready: boolean;
    progress: number;
    estimatedSeconds: number;
    phase: 'connecting' | 'loading' | 'finalizing' | 'ready' | 'error';
    message: string;
  };
  setModelLoading: (state: Partial<AppStore['modelLoading']>) => void;

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
  verifyAIAnnotation: (surveyId: string, annotationId: number, annotationType: 'question' | 'section') => Promise<void>;

  // Advanced Labeling Actions
  applyAdvancedLabeling: (surveyId: string) => Promise<any>;
  fetchComplianceReport: (surveyId: string) => Promise<any>;
  fetchDetectedLabels: (surveyId: string) => Promise<any>;
  
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

  // Edit Tracking State
  editedFields: Set<string>;
  originalFieldValues: Record<string, any>;

  // Document Upload Actions
  uploadDocument: (file: File, sessionId?: string) => Promise<DocumentAnalysisResponse>;
  analyzeText: (text: string, filename?: string) => Promise<DocumentAnalysisResponse>;
  acceptFieldMapping: (field: string, value: any) => void;
  rejectFieldMapping: (field: string) => void;
  editFieldMapping: (field: string, value: any) => void;
  clearDocumentData: () => void;
  applyDocumentMappings: () => void;
  buildRFQUpdatesFromMappings: (mappings: RFQFieldMapping[]) => Partial<EnhancedRFQRequest>;

  // Edit Tracking Actions
  trackFieldEdit: (fieldPath: string, newValue: any) => void;
  getEditedFieldsSummary: () => Array<{ field: string; originalValue: any; currentValue: any }>;
  clearEditTracking: () => void;

  // Enhanced RFQ State Persistence
  persistEnhancedRfqState: (enhancedRfq: EnhancedRFQRequest) => void;
  restoreEnhancedRfqState: (showToast?: boolean) => boolean;
  clearEnhancedRfqState: () => void;
  resetDocumentProcessingState: () => void;

  // Document Processing State Persistence
  persistDocumentProcessingState: (isProcessing: boolean, sessionId?: string) => void;
  restoreDocumentProcessingState: () => boolean;

  // Golden Example State Management
  goldenExampleSessionId: string | null;
  goldenExampleState: GoldenExampleFormState | null;
  persistGoldenExampleState: (sessionId: string, state: GoldenExampleFormState) => Promise<void>;
  restoreGoldenExampleState: () => Promise<boolean>;
  clearGoldenExampleState: (sessionId?: string) => Promise<void>;

  // Enhanced RFQ Conversion
  createEnhancedRfqFromBasic: (basicRfq: RFQRequest) => EnhancedRFQRequest;

  // Methodology-based intelligence
  applyMethodologyIntelligence: (rfqUpdates: Partial<EnhancedRFQRequest>) => Partial<EnhancedRFQRequest>;

  // Text Content Validation Actions
  validateSurveyTextCompliance: (survey: Survey) => TextComplianceReport;
  generateMissingTextContent: (missing: AiRATextLabel[], methodology: string[], rfq?: EnhancedRFQRequest) => SurveyTextContent[];
  getRequiredTextForMethodology: (methodology: string[]) => AiRATextLabel[];

  // Golden Content Types
  goldenSections: GoldenSection[];
  goldenQuestions: GoldenQuestion[];
  goldenContentAnalytics: GoldenContentAnalytics | null;

  // Golden Content Actions
  fetchGoldenSections: (filters?: any) => Promise<void>;
  fetchGoldenQuestions: (filters?: any) => Promise<void>;
  updateGoldenSection: (id: string, updates: Partial<GoldenSection>) => Promise<void>;
  updateGoldenQuestion: (id: string, updates: Partial<GoldenQuestion>) => Promise<void>;
  deleteGoldenSection: (id: string) => Promise<void>;
  deleteGoldenQuestion: (id: string) => Promise<void>;
  fetchGoldenContentAnalytics: () => Promise<void>;
}

// Golden Content Types
export interface GoldenSection {
  id: string;
  section_id: string;
  golden_pair_id?: string;
  annotation_id?: number;
  section_title?: string;
  section_text: string;
  section_type?: string;
  methodology_tags: string[];
  industry_keywords: string[];
  question_patterns: string[];
  quality_score?: number;
  usage_count: number;
  human_verified: boolean;
  labels: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GoldenQuestion {
  id: string;
  question_id: string;
  golden_pair_id?: string;
  annotation_id?: number;
  question_text: string;
  question_type?: string;
  question_subtype?: string;
  methodology_tags: string[];
  industry_keywords: string[];
  question_patterns: string[];
  quality_score?: number;
  usage_count: number;
  human_verified: boolean;
  labels: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GoldenContentAnalytics {
  total_sections: number;
  total_questions: number;
  human_verified_sections: number;
  human_verified_questions: number;
  avg_section_quality: number;
  avg_question_quality: number;
  top_section_types: Array<{type: string; count: number}>;
  top_question_types: Array<{type: string; count: number}>;
  methodology_coverage: Record<string, number>;
  industry_coverage: Record<string, number>;
}