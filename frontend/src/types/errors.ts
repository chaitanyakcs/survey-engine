/**
 * Comprehensive Error Classification System
 *
 * Provides structured error handling with specific error codes,
 * debug information, and recovery suggestions for the survey engine.
 */

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
  LOW = 'low',        // Minor issues, degraded functionality
  MEDIUM = 'medium',  // Important issues, workarounds available
  HIGH = 'high',      // Major issues, significant impact
  CRITICAL = 'critical' // System breaking, immediate attention needed
}

export enum RecoveryAction {
  RETRY = 'retry',
  RETRY_WITH_DIFFERENT_PARAMS = 'retry_modified',
  RETURN_TO_FORM = 'return_to_form',
  CONTACT_SUPPORT = 'contact_support',
  REFRESH_PAGE = 'refresh_page',
  CHECK_NETWORK = 'check_network',
  WAIT_AND_RETRY = 'wait_retry'
}

export interface DebugInfo {
  sessionId: string;
  workflowId?: string;
  timestamp: string;
  errorCode: ErrorCode;
  stackTrace?: string;
  userAgent: string;
  rfqHash?: string; // Anonymized RFQ for reproduction
  context?: Record<string, any>;
  breadcrumbs?: string[]; // User action trail
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

export interface ErrorContext {
  component?: string;
  action?: string;
  step?: string;
  additionalData?: Record<string, any>;
}

/**
 * Error classification and enhancement utilities
 */
export class ErrorClassifier {

  /**
   * Generate a unique debug handle for engineering support
   */
  static generateDebugHandle(errorCode: ErrorCode, timestamp: Date): string {
    const year = timestamp.getFullYear();
    const dayOfYear = Math.floor((timestamp.getTime() - new Date(year, 0, 0).getTime()) / (1000 * 60 * 60 * 24));
    const sequence = Math.random().toString(36).substring(2, 8).toUpperCase();

    return `DBG-${year}-${dayOfYear.toString().padStart(3, '0')}-${sequence}`;
  }

  /**
   * Create anonymized hash of RFQ for debugging (without exposing sensitive data)
   */
  static createRfqHash(rfq: any): string {
    const rfqString = JSON.stringify(rfq);
    let hash = 0;
    for (let i = 0; i < rfqString.length; i++) {
      const char = rfqString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16).padStart(8, '0');
  }

  /**
   * Classify raw error into structured DetailedError
   */
  static classifyError(
    rawError: Error | string | any,
    context?: ErrorContext
  ): DetailedError {
    const timestamp = new Date();
    const errorString = rawError instanceof Error ? rawError.message : String(rawError);

    // Determine error code based on error content
    let code = ErrorCode.UNKNOWN_ERROR;
    let severity = ErrorSeverity.MEDIUM;
    let retryable = true;
    let suggestedActions: RecoveryAction[] = [RecoveryAction.RETRY];
    let userMessage = 'An unexpected error occurred. Please try again.';

    // Classification logic
    if (errorString.includes('timeout') || errorString.includes('TIMEOUT')) {
      code = ErrorCode.TIMEOUT_ERROR;
      severity = ErrorSeverity.MEDIUM;
      suggestedActions = [RecoveryAction.RETRY, RecoveryAction.CHECK_NETWORK];
      userMessage = 'The request timed out. Please check your connection and try again.';
    } else if (errorString.includes('network') || errorString.includes('fetch')) {
      code = ErrorCode.NETWORK_ERROR;
      severity = ErrorSeverity.HIGH;
      suggestedActions = [RecoveryAction.CHECK_NETWORK, RecoveryAction.RETRY];
      userMessage = 'Network connection issue. Please check your internet and try again.';
    } else if (errorString.includes('JSON') || errorString.includes('parsing')) {
      code = ErrorCode.JSON_PARSING_FAILED;
      severity = ErrorSeverity.HIGH;
      suggestedActions = [RecoveryAction.RETRY, RecoveryAction.CONTACT_SUPPORT];
      userMessage = 'Survey generation completed but response format was invalid. Please try again.';
    } else if (errorString.includes('401') || errorString.includes('unauthorized')) {
      code = ErrorCode.AUTHENTICATION_ERROR;
      severity = ErrorSeverity.HIGH;
      retryable = false;
      suggestedActions = [RecoveryAction.REFRESH_PAGE, RecoveryAction.CONTACT_SUPPORT];
      userMessage = 'Authentication failed. Please refresh the page and try again.';
    } else if (errorString.includes('403') || errorString.includes('forbidden')) {
      code = ErrorCode.PERMISSION_DENIED;
      severity = ErrorSeverity.HIGH;
      retryable = false;
      suggestedActions = [RecoveryAction.CONTACT_SUPPORT];
      userMessage = 'Access denied. Please contact support for assistance.';
    } else if (errorString.includes('500') || errorString.includes('internal server')) {
      code = ErrorCode.SERVICE_UNAVAILABLE;
      severity = ErrorSeverity.CRITICAL;
      suggestedActions = [RecoveryAction.WAIT_AND_RETRY, RecoveryAction.CONTACT_SUPPORT];
      userMessage = 'Server error occurred. Please wait a moment and try again.';
    } else if (errorString.includes('rate limit') || errorString.includes('too many requests')) {
      code = ErrorCode.RATE_LIMIT_EXCEEDED;
      severity = ErrorSeverity.MEDIUM;
      suggestedActions = [RecoveryAction.WAIT_AND_RETRY];
      userMessage = 'Too many requests. Please wait a moment before trying again.';
    } else if (errorString.includes('evaluation') || errorString.includes('scoring')) {
      code = ErrorCode.EVALUATION_FAILED;
      severity = ErrorSeverity.LOW; // Should be non-critical now with graceful degradation
      suggestedActions = [RecoveryAction.RETRY];
      userMessage = 'Survey quality scoring unavailable, but generation will continue normally.';
    }

    const debugHandle = this.generateDebugHandle(code, timestamp);

    const debugInfo: DebugInfo = {
      sessionId: this.generateSessionId(),
      timestamp: timestamp.toISOString(),
      errorCode: code,
      stackTrace: rawError instanceof Error ? rawError.stack : undefined,
      userAgent: navigator.userAgent,
      context: context ? { ...context } : undefined,
      breadcrumbs: this.getBreadcrumbs()
    };

    return {
      code,
      severity,
      message: errorString,
      userMessage,
      technicalDetails: rawError instanceof Error ? rawError.stack : undefined,
      debugInfo,
      retryable,
      suggestedActions,
      estimatedRecoveryTime: this.getEstimatedRecoveryTime(code),
      helpUrl: this.getHelpUrl(code)
    };
  }

  /**
   * Generate or retrieve session ID
   */
  private static generateSessionId(): string {
    let sessionId = localStorage.getItem('survey_engine_session_id');
    if (!sessionId) {
      sessionId = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2);
      localStorage.setItem('survey_engine_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Get user action breadcrumbs for debugging
   */
  private static getBreadcrumbs(): string[] {
    // In a real implementation, this would track user actions
    // For now, return a simple breadcrumb based on current URL
    return [window.location.pathname];
  }

  /**
   * Get estimated recovery time for different error types
   */
  private static getEstimatedRecoveryTime(code: ErrorCode): number {
    switch (code) {
      case ErrorCode.TIMEOUT_ERROR:
        return 1; // 1 minute
      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return 5; // 5 minutes
      case ErrorCode.SERVICE_UNAVAILABLE:
        return 10; // 10 minutes
      case ErrorCode.NETWORK_ERROR:
        return 2; // 2 minutes
      default:
        return 0; // Immediate retry
    }
  }

  /**
   * Get help documentation URL for specific errors
   */
  private static getHelpUrl(code: ErrorCode): string | undefined {
    const baseUrl = '/docs/troubleshooting';

    switch (code) {
      case ErrorCode.NETWORK_ERROR:
        return `${baseUrl}#network-issues`;
      case ErrorCode.TIMEOUT_ERROR:
        return `${baseUrl}#timeout-issues`;
      case ErrorCode.AUTHENTICATION_ERROR:
        return `${baseUrl}#authentication`;
      case ErrorCode.INVALID_RFQ:
        return `${baseUrl}#rfq-validation`;
      default:
        return `${baseUrl}#general`;
    }
  }
}

/**
 * Pre-defined error configurations for common scenarios
 */
export const ERROR_CONFIGS = {
  [ErrorCode.LLM_API_FAILURE]: {
    userMessage: 'AI service is temporarily unavailable. Please try again in a few minutes.',
    severity: ErrorSeverity.HIGH,
    suggestedActions: [RecoveryAction.WAIT_AND_RETRY, RecoveryAction.CONTACT_SUPPORT]
  },
  [ErrorCode.INSUFFICIENT_QUESTIONS]: {
    userMessage: 'Unable to generate enough questions. Please provide more detailed requirements.',
    severity: ErrorSeverity.MEDIUM,
    suggestedActions: [RecoveryAction.RETURN_TO_FORM, RecoveryAction.RETRY_WITH_DIFFERENT_PARAMS]
  },
  [ErrorCode.HUMAN_REVIEW_REJECTED]: {
    userMessage: 'Survey generation was rejected during review. Please modify your requirements.',
    severity: ErrorSeverity.MEDIUM,
    suggestedActions: [RecoveryAction.RETURN_TO_FORM]
  }
} as const;