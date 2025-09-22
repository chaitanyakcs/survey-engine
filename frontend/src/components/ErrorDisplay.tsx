/**
 * Rich Error Display Components
 *
 * Provides structured error display with debug information,
 * recovery actions, and engineering support features.
 */

import React, { useState } from 'react';
import { DetailedError, ErrorSeverity, RecoveryAction } from '../types';

interface ErrorDisplayProps {
  error: DetailedError;
  onRecoveryAction?: (action: RecoveryAction) => void;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRecoveryAction,
  onRetry,
  onDismiss,
  className = ''
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [debugInfoCopied, setDebugInfoCopied] = useState(false);

  const getSeverityColor = (severity: ErrorSeverity) => {
    switch (severity) {
      case 'low': return 'border-yellow-200 bg-yellow-50';
      case 'medium': return 'border-orange-200 bg-orange-50';
      case 'high': return 'border-red-200 bg-red-50';
      case 'critical': return 'border-red-500 bg-red-100';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getSeverityIcon = (severity: ErrorSeverity) => {
    switch (severity) {
      case 'low':
        return (
          <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      case 'medium':
        return (
          <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'high':
      case 'critical':
        return (
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getActionIcon = (action: RecoveryAction) => {
    switch (action) {
      case 'retry':
        return (
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'return_to_form':
        return (
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        );
      case 'contact_support':
        return (
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'refresh_page':
        return (
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getActionText = (action: RecoveryAction) => {
    switch (action) {
      case 'retry': return 'Try Again';
      case 'retry_modified': return 'Try with Different Settings';
      case 'return_to_form': return 'Return to Form';
      case 'contact_support': return 'Contact Support';
      case 'refresh_page': return 'Refresh Page';
      case 'check_network': return 'Check Network';
      case 'wait_retry': return `Wait ${error.estimatedRecoveryTime || 2} min & Retry`;
      default: return action;
    }
  };

  const copyDebugInfo = async () => {
    const debugInfo = {
      errorCode: error.code,
      debugHandle: `DBG-${new Date().getFullYear()}-${Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24)).toString().padStart(3, '0')}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      timestamp: error.debugInfo.timestamp,
      userAgent: error.debugInfo.userAgent,
      sessionId: error.debugInfo.sessionId,
      workflowId: error.debugInfo.workflowId,
      context: error.debugInfo.context,
      message: error.message,
      technicalDetails: error.technicalDetails
    };

    try {
      await navigator.clipboard.writeText(JSON.stringify(debugInfo, null, 2));
      setDebugInfoCopied(true);
      setTimeout(() => setDebugInfoCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy debug info:', err);
    }
  };

  return (
    <div className={`border rounded-lg p-6 ${getSeverityColor(error.severity)} ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          {getSeverityIcon(error.severity)}
          <div className="ml-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {error.severity === 'critical' ? 'Critical Error' :
               error.severity === 'high' ? 'Error' :
               error.severity === 'medium' ? 'Issue Detected' : 'Warning'}
            </h3>
            <p className="text-sm text-gray-600">
              Error Code: <span className="font-mono font-semibold">{error.code}</span>
            </p>
          </div>
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* User Message */}
      <div className="mb-4">
        <p className="text-gray-800 leading-relaxed">{error.userMessage}</p>
      </div>

      {/* Recovery Actions */}
      {error.suggestedActions.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Suggested Actions:</h4>
          <div className="flex flex-wrap gap-2">
            {error.suggestedActions.map((action, index) => (
              <button
                key={index}
                onClick={() => {
                  if (action === 'retry' && onRetry) {
                    onRetry();
                  } else if (onRecoveryAction) {
                    onRecoveryAction(action);
                  }
                }}
                className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {getActionIcon(action)}
                {getActionText(action)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Debug Information Section */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            {showTechnicalDetails ? 'Hide' : 'Show'} Technical Details
          </button>

          <button
            onClick={copyDebugInfo}
            className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded transition-colors ${
              debugInfoCopied
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {debugInfoCopied ? (
              <>
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy Debug Info
              </>
            )}
          </button>
        </div>

        {showTechnicalDetails && (
          <div className="mt-3 p-3 bg-gray-100 rounded-md">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-semibold">Session ID:</span>{' '}
                <span className="font-mono">{error.debugInfo.sessionId}</span>
              </div>
              {error.debugInfo.workflowId && (
                <div>
                  <span className="font-semibold">Workflow ID:</span>{' '}
                  <span className="font-mono">{error.debugInfo.workflowId}</span>
                </div>
              )}
              <div>
                <span className="font-semibold">Timestamp:</span>{' '}
                <span className="font-mono">{new Date(error.debugInfo.timestamp).toLocaleString()}</span>
              </div>
              {error.debugInfo.context && (
                <div>
                  <span className="font-semibold">Context:</span>{' '}
                  <span className="font-mono">{JSON.stringify(error.debugInfo.context)}</span>
                </div>
              )}
              {error.technicalDetails && (
                <div>
                  <span className="font-semibold">Technical Details:</span>
                  <pre className="mt-1 text-xs bg-white p-2 rounded border overflow-x-auto">
                    {error.technicalDetails}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Help Link */}
      {error.helpUrl && (
        <div className="mt-3 pt-3 border-t">
          <a
            href={error.helpUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            View Troubleshooting Guide
          </a>
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;