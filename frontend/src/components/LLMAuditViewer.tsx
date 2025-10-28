import React, { useState, useEffect, useCallback } from 'react';
import { 
  DocumentTextIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  ClipboardDocumentIcon, 
  CheckIcon,
  EyeIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { CreateGoldenPairModal } from './CreateGoldenPairModal';
import { LLMAuditRecord } from '../types';
import { Sidebar } from './Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';

interface LLMAuditSummary {
  total_interactions: number;
  successful_interactions: number;
  failed_interactions: number;
  success_rate: number;
  interactions_by_purpose: Array<{ purpose: string; count: number }>;
  interactions_by_model: Array<{ model_name: string; count: number }>;
  average_response_time_ms?: number;
  total_tokens_input?: number;
  total_tokens_output?: number;
}

interface LLMAuditViewerProps {
  surveyId?: string; // Optional - if provided, filters by survey
  title?: string; // Optional custom title
  showSummary?: boolean; // Whether to show the summary sidebar
  initialPurposeFilter?: string; // Initial purpose filter value (e.g., 'evaluation', 'generation')
  standalone?: boolean; // Whether to show as a standalone page with sidebar (default: true)
}

export const LLMAuditViewer: React.FC<LLMAuditViewerProps> = ({ 
  surveyId, 
  title = "LLM Audit Viewer",
  showSummary = true,
  initialPurposeFilter = '',
  standalone = true
}) => {
  const [auditRecords, setAuditRecords] = useState<LLMAuditRecord[]>([]);
  const [summary, setSummary] = useState<LLMAuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<LLMAuditRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'prompt' | 'output' | 'raw_response' | 'metadata'>('prompt');
  const [filters, setFilters] = useState({
    purpose: initialPurposeFilter,
    model_name: '',
    success: '',
    page: 1,
    page_size: 50
  });
  const [copiedTab, setCopiedTab] = useState<string | null>(null);
  const [showGoldenPairModal, setShowGoldenPairModal] = useState(false);
  const [selectedAuditForGolden, setSelectedAuditForGolden] = useState<LLMAuditRecord | null>(null);

  const { mainContentClasses } = useSidebarLayout();

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
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

  const fetchAuditData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build query parameters for both requests
      const params = new URLSearchParams();
      if (filters.purpose) params.append('purpose', filters.purpose);
      if (filters.model_name) params.append('model_name', filters.model_name);
      if (filters.success !== '') params.append('success', filters.success);
      if (surveyId) params.append('parent_survey_id', surveyId);
      params.append('page', filters.page.toString());
      params.append('page_size', filters.page_size.toString());

      // Fetch both audit records and summary in parallel
      const [recordsResponse, summaryResponse] = await Promise.all([
        fetch(`/api/v1/llm-audit/interactions?${params}`),
        showSummary ? fetch(`/api/v1/llm-audit/summary?${params}`) : Promise.resolve(null)
      ]);
      
      if (!recordsResponse.ok) {
        throw new Error(`Failed to fetch LLM interactions: ${recordsResponse.statusText}`);
      }

      const recordsData = await recordsResponse.json();
      setAuditRecords(recordsData.records || []);

      // Select the most recent record by default
      if (recordsData.records && recordsData.records.length > 0) {
        setSelectedRecord(recordsData.records[0]);
      }

      // Fetch summary if requested
      if (showSummary && summaryResponse) {
        if (!summaryResponse.ok) {
          console.warn(`Failed to fetch summary: ${summaryResponse.statusText}`);
        } else {
          const summaryData = await summaryResponse.json();
          setSummary(summaryData);
        }
      }
    } catch (err) {
      console.error('Error fetching audit data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch audit data');
    } finally {
      setLoading(false);
    }
  }, [filters, surveyId, showSummary]);

  useEffect(() => {
    fetchAuditData();
  }, [fetchAuditData]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPurposeDisplayName = (purpose: string, sub_purpose?: string) => {
    const purposeMap: Record<string, string> = {
      'survey_generation': 'Survey Creation',
      'evaluation': 'Quality Assessment',
      'field_extraction': 'Data Extraction',
      'document_parsing': 'Document Analysis',
      'rfq_parsing': 'RFQ Processing',
      'golden_example_creation': 'Golden Example Creation'
    };
    
    let displayName = purposeMap[purpose] || purpose;
    if (sub_purpose) {
      displayName += ` (${sub_purpose})`;
    }
    return displayName;
  };

  const copyToClipboard = async (text: string, tabName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTab(tabName);
      setTimeout(() => setCopiedTab(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const renderTabContent = () => {
    if (!selectedRecord) return null;

    const content = {
      prompt: selectedRecord.input_prompt,
      output: selectedRecord.output_content || 'No output available',
      raw_response: selectedRecord.raw_response || 'No raw response available',
      metadata: JSON.stringify({
        interaction_id: selectedRecord.interaction_id,
        model_name: selectedRecord.model_name,
        model_provider: selectedRecord.model_provider,
        model_version: selectedRecord.model_version,
        purpose: selectedRecord.purpose,
        sub_purpose: selectedRecord.sub_purpose,
        context_type: selectedRecord.context_type,
        input_tokens: selectedRecord.input_tokens,
        output_tokens: selectedRecord.output_tokens,
        temperature: selectedRecord.temperature,
        top_p: selectedRecord.top_p,
        max_tokens: selectedRecord.max_tokens,
        frequency_penalty: selectedRecord.frequency_penalty,
        presence_penalty: selectedRecord.presence_penalty,
        stop_sequences: selectedRecord.stop_sequences,
        response_time_ms: selectedRecord.response_time_ms,
        success: selectedRecord.success,
        error_message: selectedRecord.error_message,
        interaction_metadata: selectedRecord.interaction_metadata,
        tags: selectedRecord.tags,
        created_at: selectedRecord.created_at
      }, null, 2)
    };

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 capitalize">
            {activeTab.replace('_', ' ')}
          </h3>
          <button
            onClick={() => copyToClipboard(content[activeTab], activeTab)}
            className="flex items-center space-x-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ClipboardDocumentIcon className="w-4 h-4" />
            <span>{copiedTab === activeTab ? 'Copied!' : 'Copy'}</span>
            {copiedTab === activeTab && <CheckIcon className="w-4 h-4 text-green-600" />}
          </button>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
          <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
            {typeof content[activeTab] === 'string' 
              ? content[activeTab] 
              : JSON.stringify(content[activeTab], null, 2)
            }
          </pre>
        </div>
      </div>
    );
  };

  if (loading) {
    const content = (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
        <span className="ml-3 text-gray-600">Loading audit records...</span>
      </div>
    );

    if (!standalone) {
      return content;
    }

    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar currentView="llm-review" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          {content}
        </div>
      </div>
    );
  }

  if (error) {
    const content = (
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl mx-auto mt-8">
        <div className="text-center py-8">
          <div className="text-red-600 mb-2">Error loading audit records</div>
          <div className="text-gray-600 text-sm">{error}</div>
          <button
            onClick={fetchAuditData}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    );

    if (!standalone) {
      return content;
    }

    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar currentView="llm-review" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          {content}
        </div>
      </div>
    );
  }

  if (auditRecords.length === 0) {
    const content = (
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl mx-auto mt-8">
        <div className="text-center py-8">
          <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <div className="text-gray-600 mb-2">No audit records found</div>
          <div className="text-gray-500 text-sm">
            {surveyId 
              ? "No LLM interactions found for this survey."
              : "No LLM interactions found with the current filters."
            }
          </div>
        </div>
      </div>
    );

    if (!standalone) {
      return content;
    }

    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar currentView="llm-review" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          {content}
        </div>
      </div>
    );
  }

  const content = (
    <div className="bg-white w-full h-screen overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
              <p className="text-sm text-gray-600 mt-1">
                {surveyId 
                  ? "View all AI interactions and prompts used for this survey"
                  : "View all AI interactions and prompts across the system"
                }
              </p>
            </div>
          </div>

        <div className="flex h-[calc(100vh-120px)]">
          {/* Summary Sidebar */}
          {showSummary && (
            <div className="w-80 border-r border-gray-200 bg-gray-50 p-6 overflow-y-auto">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
              
              {summary ? (
                <>
                  {/* Stats */}
                  <div className="space-y-4 mb-6">
                    <div className="bg-white rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-600">Total Interactions</span>
                        <span className="text-xl font-semibold text-gray-900">{summary.total_interactions}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-600">Successful</span>
                        <span className="text-xl font-semibold text-green-600">
                          {summary.successful_interactions}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-600">Failed</span>
                        <span className="text-xl font-semibold text-red-600">
                          {summary.failed_interactions}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-600">Success Rate</span>
                        <span className="text-xl font-semibold text-blue-600">
                          {summary.success_rate}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Additional Stats */}
                  {(summary.average_response_time_ms || summary.total_tokens_input) && (
                    <div className="space-y-4 mb-6">
                      <div className="bg-white rounded-lg p-4">
                        {summary.average_response_time_ms && (
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-600">Avg Response Time</span>
                            <span className="text-sm font-semibold text-gray-900">
                              {formatDuration(summary.average_response_time_ms)}
                            </span>
                          </div>
                        )}
                        {summary.total_tokens_input && (
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-600">Total Input Tokens</span>
                            <span className="text-sm font-semibold text-gray-900">
                              {summary.total_tokens_input.toLocaleString()}
                            </span>
                          </div>
                        )}
                        {summary.total_tokens_output && (
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-600">Total Output Tokens</span>
                            <span className="text-sm font-semibold text-gray-900">
                              {summary.total_tokens_output.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Purposes */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">By Purpose</h4>
                    <div className="space-y-2">
                      {summary.interactions_by_purpose.map((item, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span className="text-gray-600">{getPurposeDisplayName(item.purpose)}</span>
                          <span className="font-medium">{item.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Models */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">By Model</h4>
                    <div className="space-y-2">
                      {summary.interactions_by_model.map((item, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span className="text-gray-600 truncate">{item.model_name}</span>
                          <span className="font-medium">{item.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center text-gray-500 py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400 mx-auto mb-2"></div>
                  <div className="text-sm">Loading summary...</div>
                </div>
              )}
            </div>
          )}

          {/* Main Content */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Filters */}
            <div className="p-6 border-b border-gray-200 bg-gray-50">
              <div className="flex gap-4 flex-wrap">
                <select
                  value={filters.purpose}
                  onChange={(e) => setFilters({ ...filters, purpose: e.target.value, page: 1 })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Purposes</option>
                  <option value="survey_generation">Survey Generation</option>
                  <option value="evaluation">Evaluation</option>
                  <option value="field_extraction">Field Extraction</option>
                  <option value="document_parsing">Document Parsing</option>
                </select>

                <select
                  value={filters.model_name}
                  onChange={(e) => setFilters({ ...filters, model_name: e.target.value, page: 1 })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Models</option>
                  {Array.from(new Set(auditRecords.map(r => r.model_name))).map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>

                <select
                  value={filters.success}
                  onChange={(e) => setFilters({ ...filters, success: e.target.value, page: 1 })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Status</option>
                  <option value="true">Success</option>
                  <option value="false">Failed</option>
                </select>
              </div>
            </div>

            <div className="flex-1 flex min-h-0">
              {/* Records List */}
              <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
                <div className="p-4 space-y-2">
                  {auditRecords.map((record) => (
                    <div
                      key={record.id}
                      onClick={() => setSelectedRecord(record)}
                      className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                        selectedRecord?.id === record.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {getPurposeDisplayName(record.purpose, record.sub_purpose)}
                            </span>
                            <div className="flex items-center">
                              {record.success ? (
                                <CheckCircleIcon className="w-4 h-4 text-green-500" />
                              ) : (
                                <XCircleIcon className="w-4 h-4 text-red-500" />
                              )}
                            </div>
                          </div>
                          <div className="text-xs text-gray-500 mb-2">
                            {record.model_name} • {new Date(record.created_at).toLocaleString()}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-2">
                          {record.response_time_ms && (
                            <div className="flex items-center space-x-1 text-xs text-gray-500">
                              <ClockIcon className="w-3 h-3" />
                              <span>{formatDuration(record.response_time_ms)}</span>
                            </div>
                          )}
                          <EyeIcon className="w-4 h-4 text-gray-400" />
                        </div>
                      </div>
                      {record.purpose === 'document_parsing' && record.sub_purpose === 'survey_conversion' && record.success && (
                        <div className="mt-3 flex justify-end">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedAuditForGolden(record);
                              setShowGoldenPairModal(true);
                            }}
                            className="px-3 py-1 text-sm font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md hover:bg-emerald-100 hover:border-emerald-300 transition-colors"
                          >
                            Create Golden Pair
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Detail View */}
              <div className="w-2/3 p-6 overflow-y-auto">
                {selectedRecord ? (
                  <div className="space-y-6">
                    {/* Record Header */}
                    <div className="border-b border-gray-200 pb-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {getPurposeDisplayName(selectedRecord.purpose, selectedRecord.sub_purpose)}
                        </h3>
                        <div className="flex items-center space-x-2">
                          {selectedRecord.success ? (
                            <CheckCircleIcon className="w-5 h-5 text-green-500" />
                          ) : (
                            <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
                          )}
                          <span className={`text-sm font-medium ${
                            selectedRecord.success ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {selectedRecord.success ? 'Success' : 'Failed'}
                          </span>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>Model: {selectedRecord.model_name} ({selectedRecord.model_provider})</div>
                        <div>Created: {new Date(selectedRecord.created_at).toLocaleString()}</div>
                        {selectedRecord.response_time_ms && (
                          <div>Duration: {formatDuration(selectedRecord.response_time_ms)}</div>
                        )}
                        {selectedRecord.input_tokens && (
                          <div>Tokens: {selectedRecord.input_tokens} in, {selectedRecord.output_tokens || 0} out</div>
                        )}
                      </div>
                    </div>

                    {/* Tabs */}
                    <div className="border-b border-gray-200">
                      <nav className="-mb-px flex space-x-8">
                        {['prompt', 'output', 'raw_response', 'metadata'].map((tab) => (
                          <button
                            key={tab}
                            onClick={() => setActiveTab(tab as any)}
                            className={`py-2 px-1 border-b-2 font-medium text-sm ${
                              activeTab === tab
                                ? 'border-indigo-500 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                          >
                            {tab.replace('_', ' ').toUpperCase()}
                          </button>
                        ))}
                      </nav>
                    </div>

                    {/* Tab Content */}
                    {renderTabContent()}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    Select a record to view details
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
  );

  if (!standalone) {
    return (
      <>
        {content}
        {/* Golden Pair Creation Modal */}
        <CreateGoldenPairModal
          isOpen={showGoldenPairModal}
          onClose={() => {
            setShowGoldenPairModal(false);
            setSelectedAuditForGolden(null);
          }}
          auditRecord={selectedAuditForGolden}
          onSuccess={() => {
            // Show success toast
            console.log('Golden pair created successfully!');
            // Could add a toast notification here
          }}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar currentView="llm-review" onViewChange={handleViewChange} />
      <div className={mainContentClasses}>
        {content}
      </div>
      
      {/* Golden Pair Creation Modal */}
      <CreateGoldenPairModal
        isOpen={showGoldenPairModal}
        onClose={() => {
          setShowGoldenPairModal(false);
          setSelectedAuditForGolden(null);
        }}
        auditRecord={selectedAuditForGolden}
        onSuccess={() => {
          // Show success toast
          console.log('Golden pair created successfully!');
          // Could add a toast notification here
        }}
      />
    </div>
  );
};
