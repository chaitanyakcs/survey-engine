/**
 * Error Banner Component
 *
 * A compact error display for inline use in pages and workflows.
 * Provides essential error information with expandable details.
 */

import React, { useState } from 'react';
import { DetailedError, ErrorSeverity } from '../types';

interface ErrorBannerProps {
  error: DetailedError;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  compact?: boolean;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  error,
  onRetry,
  onDismiss,
  className = '',
  compact = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSeverityStyles = (severity: ErrorSeverity) => {
    switch (severity) {
      case 'low':
        return {
          border: 'border-yellow-300',
          bg: 'bg-yellow-50',
          text: 'text-yellow-800',
          icon: 'text-yellow-600'
        };
      case 'medium':
        return {
          border: 'border-orange-300',
          bg: 'bg-orange-50',
          text: 'text-orange-800',
          icon: 'text-orange-600'
        };
      case 'high':
        return {
          border: 'border-red-300',
          bg: 'bg-red-50',
          text: 'text-red-800',
          icon: 'text-red-600'
        };
      case 'critical':
        return {
          border: 'border-red-500',
          bg: 'bg-red-100',
          text: 'text-red-900',
          icon: 'text-red-700'
        };
      default:
        return {
          border: 'border-gray-300',
          bg: 'bg-gray-50',
          text: 'text-gray-800',
          icon: 'text-gray-600'
        };
    }
  };

  const styles = getSeverityStyles(error.severity);

  const generateDebugHandle = () => {
    const year = new Date().getFullYear();
    const dayOfYear = Math.floor((Date.now() - new Date(year, 0, 0).getTime()) / (1000 * 60 * 60 * 24));
    const sequence = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `DBG-${year}-${dayOfYear.toString().padStart(3, '0')}-${sequence}`;
  };

  if (compact) {
    return (
      <div className={`flex items-center p-3 border rounded-md ${styles.border} ${styles.bg} ${className}`}>
        <svg className={`w-5 h-5 mr-3 ${styles.icon}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>

        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${styles.text}`}>
            {error.userMessage}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Code: {error.code} • Debug: {generateDebugHandle()}
          </p>
        </div>

        <div className="flex items-center ml-4 space-x-2">
          {error.retryable && onRetry && (
            <button
              onClick={onRetry}
              className="text-xs px-2 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className={`${styles.icon} hover:opacity-70 transition-opacity`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg ${styles.border} ${styles.bg} ${className}`}>
      {/* Main Banner */}
      <div className="flex items-start p-4">
        <svg className={`w-6 h-6 mr-3 mt-0.5 ${styles.icon}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className={`text-sm font-semibold ${styles.text}`}>
              {error.severity === 'critical' ? 'Critical Error' :
               error.severity === 'high' ? 'Error Occurred' :
               error.severity === 'medium' ? 'Issue Detected' : 'Warning'}
            </h4>
            <span className="text-xs font-mono text-gray-600 bg-white px-2 py-1 rounded">
              {error.code}
            </span>
          </div>

          <p className={`text-sm mt-1 ${styles.text}`}>
            {error.userMessage}
          </p>

          <div className="flex items-center mt-3 space-x-3">
            {error.retryable && onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center text-xs px-3 py-1 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Try Again
              </button>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-gray-600 hover:text-gray-800 transition-colors"
            >
              {isExpanded ? 'Hide Details' : 'Show Details'}
            </button>

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs text-gray-600 hover:text-gray-800 transition-colors ml-auto"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 bg-white bg-opacity-50">
          <div className="space-y-3">
            <div>
              <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Debug Information</h5>
              <div className="mt-1 text-xs text-gray-600 space-y-1">
                <div>Debug Handle: <span className="font-mono">{generateDebugHandle()}</span></div>
                <div>Session: <span className="font-mono">{error.debugInfo.sessionId}</span></div>
                <div>Time: <span className="font-mono">{new Date(error.debugInfo.timestamp).toLocaleString()}</span></div>
                {error.debugInfo.workflowId && (
                  <div>Workflow: <span className="font-mono">{error.debugInfo.workflowId}</span></div>
                )}
              </div>
            </div>

            {error.suggestedActions.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Suggested Actions</h5>
                <ul className="mt-1 text-xs text-gray-600 space-y-1">
                  {error.suggestedActions.map((action, index) => (
                    <li key={index} className="flex items-center">
                      <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                      {action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {error.helpUrl && (
              <div>
                <a
                  href={error.helpUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  View Help
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ErrorBanner;