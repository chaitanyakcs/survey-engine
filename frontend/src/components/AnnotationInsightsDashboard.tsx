import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ArrowTrendingUpIcon, 
  UsersIcon, 
  ChartBarIcon 
} from '@heroicons/react/24/outline';
import { Sidebar } from './Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from './Toast';
import { useAppStore } from '../store/useAppStore';

interface AnnotationStats {
  total_annotations: number;
  high_quality_count: number;
  low_quality_count: number;
  average_score: number;
  improvement_trend: number;
  improvement_trend_metadata?: {
    status: string;
    message: string;
    baseline_period: string;
    recent_period: string;
    baseline_count: number;
    recent_count: number;
    baseline_avg?: number;
    recent_avg?: number;
  };
}

interface HumanVsAIStats {
  total_ai_annotations: number;
  total_human_annotations: number;
  ai_question_annotations: number;
  ai_section_annotations: number;
  human_question_annotations: number;
  human_section_annotations: number;
  overridden_annotations: number;
  verified_annotations: number;
  average_ai_confidence: number;
  ai_annotations_with_confidence: number;
}

interface QualityPattern {
  type: string;
  example: string;
  score: number;
}

interface CommonIssue {
  issue: string;
  frequency: number;
  examples: string[];
}

interface AnnotationInsights {
  high_quality_patterns: QualityPattern[];
  common_issues: CommonIssue[];
  summary: AnnotationStats;
  human_vs_ai_stats: HumanVsAIStats;
}

export function AnnotationInsightsDashboard() {
  const { toasts, removeToast } = useAppStore();
  const { mainContentClasses } = useSidebarLayout();
  const [insights, setInsights] = useState<AnnotationInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'settings') {
      window.location.href = '/settings';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
    }
  };

  useEffect(() => {
    fetchAnnotationInsights();
  }, []);

  const fetchAnnotationInsights = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/annotation-insights');
      if (!response.ok) {
        throw new Error('Failed to fetch annotation insights');
      }
      const data = await response.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="annotation-insights" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading annotation insights...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="annotation-insights" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
              <span className="text-red-800">
                Error loading annotation insights: {error}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="min-h-screen bg-gray-50">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="annotation-insights" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <span className="text-blue-800">
              No annotation data available yet. Start annotating surveys to see insights!
            </span>
          </div>
        </div>
      </div>
    );
  }

  const { summary, high_quality_patterns, common_issues, human_vs_ai_stats } = insights;
  const highQualityPercentage = summary.total_annotations > 0 
    ? (summary.high_quality_count / summary.total_annotations) * 100 
    : 0;
  
  const aiPercentage = summary.total_annotations > 0 
    ? (human_vs_ai_stats.total_ai_annotations / summary.total_annotations) * 100 
    : 0;
  
  const humanPercentage = summary.total_annotations > 0 
    ? (human_vs_ai_stats.total_human_annotations / summary.total_annotations) * 100 
    : 0;
  
  const verificationRate = human_vs_ai_stats.total_ai_annotations > 0 
    ? (human_vs_ai_stats.verified_annotations / human_vs_ai_stats.total_ai_annotations) * 100 
    : 0;
  
  const overrideRate = human_vs_ai_stats.total_ai_annotations > 0 
    ? (human_vs_ai_stats.overridden_annotations / human_vs_ai_stats.total_ai_annotations) * 100 
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <Sidebar currentView="annotation-insights" onViewChange={handleViewChange} />
      <div className={mainContentClasses}>
        <div className="space-y-6 p-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">📊 Annotation Insights Dashboard</h1>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-600">Total Annotations</h3>
                <UsersIcon className="h-5 w-5 text-gray-400" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-gray-900">{summary.total_annotations}</div>
                <p className="text-xs text-gray-500">
                  Questions & sections reviewed
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-600">High Quality</h3>
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-green-600">{summary.high_quality_count}</div>
                <p className="text-xs text-gray-500">
                  Score ≥ 4.0 ({highQualityPercentage.toFixed(1)}%)
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-600">Average Score</h3>
                <ChartBarIcon className="h-5 w-5 text-gray-400" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-bold text-gray-900">{summary.average_score.toFixed(1)}</div>
                <p className="text-xs text-gray-500">
                  Out of 5.0
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-600">Improvement Trend</h3>
                <ArrowTrendingUpIcon className={`h-5 w-5 ${
                  summary.improvement_trend > 0 ? 'text-green-600' : 
                  summary.improvement_trend < 0 ? 'text-red-600' : 
                  'text-gray-400'
                }`} />
              </div>
              <div className="mt-2">
                {summary.improvement_trend_metadata?.status === 'success' ? (
                  <>
                    <div className={`text-2xl font-bold ${
                      summary.improvement_trend > 0 ? 'text-green-600' : 
                      summary.improvement_trend < 0 ? 'text-red-600' : 
                      'text-gray-600'
                    }`}>
                      {summary.improvement_trend > 0 ? '+' : ''}{summary.improvement_trend.toFixed(1)}%
                    </div>
                    <p className="text-xs text-gray-500">
                      Yesterday vs {summary.improvement_trend_metadata.baseline_period}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {summary.improvement_trend_metadata.recent_count} recent, {summary.improvement_trend_metadata.baseline_count} baseline
                    </p>
                  </>
                ) : (
                  <>
                    <div className="text-2xl font-bold text-gray-400">
                      {summary.improvement_trend.toFixed(1)}%
                    </div>
                    <p className="text-xs text-gray-500">
                      {summary.improvement_trend_metadata?.message || 'Calculating...'}
                    </p>
                    {summary.improvement_trend_metadata?.status === 'establishing_baseline' && (
                      <p className="text-xs text-blue-500 mt-1">
                        Need 7+ days of history
                      </p>
                    )}
                    {summary.improvement_trend_metadata?.status === 'insufficient_data' && (
                      <p className="text-xs text-orange-500 mt-1">
                        Need at least 10 annotations
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Human vs AI Statistics */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <UsersIcon className="h-6 w-6 text-blue-600 mr-2" />
              Human vs AI Annotation Statistics
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-blue-800">AI Annotations</h3>
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-blue-900">{human_vs_ai_stats.total_ai_annotations}</div>
                  <p className="text-xs text-blue-600">
                    {aiPercentage.toFixed(1)}% of total
                  </p>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-green-800">Human Annotations</h3>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-green-900">{human_vs_ai_stats.total_human_annotations}</div>
                  <p className="text-xs text-green-600">
                    {humanPercentage.toFixed(1)}% of total
                  </p>
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-purple-800">Verified AI</h3>
                  <CheckCircleIcon className="h-5 w-5 text-purple-600" />
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-purple-900">{human_vs_ai_stats.verified_annotations}</div>
                  <p className="text-xs text-purple-600">
                    {verificationRate.toFixed(1)}% verification rate
                  </p>
                </div>
              </div>

              <div className="bg-orange-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-orange-800">Overridden AI</h3>
                  <XCircleIcon className="h-5 w-5 text-orange-600" />
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-orange-900">{human_vs_ai_stats.overridden_annotations}</div>
                  <p className="text-xs text-orange-600">
                    {overrideRate.toFixed(1)}% override rate
                  </p>
                </div>
              </div>
            </div>

            {/* Detailed Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">AI Annotation Breakdown</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Questions:</span>
                    <span className="font-medium">{human_vs_ai_stats.ai_question_annotations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Sections:</span>
                    <span className="font-medium">{human_vs_ai_stats.ai_section_annotations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">With Confidence:</span>
                    <span className="font-medium">{human_vs_ai_stats.ai_annotations_with_confidence}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Avg Confidence:</span>
                    <span className="font-medium">{(human_vs_ai_stats.average_ai_confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Human Annotation Breakdown</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Questions:</span>
                    <span className="font-medium">{human_vs_ai_stats.human_question_annotations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Sections:</span>
                    <span className="font-medium">{human_vs_ai_stats.human_section_annotations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total:</span>
                    <span className="font-medium">{human_vs_ai_stats.total_human_annotations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">AI Overrides:</span>
                    <span className="font-medium">{human_vs_ai_stats.overridden_annotations}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quality Progress */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Distribution</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">High Quality (4.0-5.0)</span>
                  <span className="text-gray-900">{summary.high_quality_count} items</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${highQualityPercentage}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Low Quality (1.0-3.0)</span>
                  <span className="text-gray-900">{summary.low_quality_count} items</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-red-600 h-2 rounded-full" 
                    style={{ width: `${(summary.low_quality_count / summary.total_annotations) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* High Quality Patterns */}
          {high_quality_patterns.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                High-Quality Patterns (Score 4-5)
              </h3>
              <div className="space-y-4">
                {high_quality_patterns.slice(0, 3).map((pattern, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-full">
                        {pattern.type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium text-gray-600 bg-blue-100 rounded-full">
                        Score: {pattern.score.toFixed(1)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 italic">
                      "{pattern.example}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common Issues */}
          {common_issues.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <XCircleIcon className="h-5 w-5 text-red-600" />
                Common Issues to Avoid
              </h3>
              <div className="space-y-4">
                {common_issues.slice(0, 5).map((issue, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-1 text-xs font-medium text-red-600 bg-red-100 rounded-full">
                        {issue.issue.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-full">
                        {issue.frequency} mentions
                      </span>
                    </div>
                    {issue.examples.length > 0 && (
                      <p className="text-sm text-gray-600 italic">
                        Example: "{issue.examples[0]}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}