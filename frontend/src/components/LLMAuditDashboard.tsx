import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  EyeIcon,
  CogIcon,
  ClipboardDocumentIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

interface LLMAuditRecord {
  id: string;
  interaction_id: string;
  parent_workflow_id?: string;
  parent_survey_id?: string;
  parent_rfq_id?: string;
  model_name: string;
  model_provider: string;
  purpose: string;
  sub_purpose?: string;
  context_type?: string;
  input_prompt: string;
  input_tokens?: number;
  output_content?: string;
  output_tokens?: number;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  response_time_ms?: number;
  cost_usd?: number;
  success: boolean;
  error_message?: string;
  interaction_metadata?: Record<string, any>;
  tags?: string[];
  created_at: string;
}

interface CostSummary {
  total_cost_usd: number;
  total_interactions: number;
  successful_interactions: number;
  success_rate: number;
  cost_by_purpose: Array<{
    purpose: string;
    total_cost_usd: number;
    interaction_count: number;
  }>;
  cost_by_model: Array<{
    model_name: string;
    total_cost_usd: number;
    interaction_count: number;
  }>;
}

interface LLMAuditDashboardProps {
  onClose: () => void;
}

const LLMAuditDashboard: React.FC<LLMAuditDashboardProps> = ({ onClose }) => {
  const [auditRecords, setAuditRecords] = useState<LLMAuditRecord[]>([]);
  // const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<LLMAuditRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'prompt' | 'output' | 'metadata'>('prompt');
  const [filters, setFilters] = useState({
    purpose: '',
    model_name: '',
    success: '',
    page: 1,
    page_size: 20
  });
  const [copiedTab, setCopiedTab] = useState<string | null>(null);

  useEffect(() => {
    fetchAuditData();
  }, [filters]);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      
      // Fetch audit records
      const params = new URLSearchParams();
      if (filters.purpose) params.append('purpose', filters.purpose);
      if (filters.model_name) params.append('model_name', filters.model_name);
      if (filters.success !== '') params.append('success', filters.success);
      params.append('page', filters.page.toString());
      params.append('page_size', filters.page_size.toString());

      const recordsResponse = await fetch(`/api/v1/llm-audit/interactions?${params}`);
      const recordsData = await recordsResponse.json();
      setAuditRecords(recordsData.records || []);

      // Fetch cost summary - disabled for now
      // const costResponse = await fetch('/api/v1/llm-audit/cost-summary');
      // const costData = await costResponse.json();
      // setCostSummary(costData);
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  };


  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPurposeColor = (purpose: string) => {
    const colors: Record<string, string> = {
      'survey_generation': 'bg-yellow-100 text-yellow-800',
      'evaluation': 'bg-green-100 text-green-800',
      'field_extraction': 'bg-amber-100 text-amber-800',
      'document_parsing': 'bg-orange-100 text-orange-800',
    };
    return colors[purpose] || 'bg-gray-100 text-gray-800';
  };

  const copyToClipboard = async (text: string, tabName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTab(tabName);
      setTimeout(() => setCopiedTab(null), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading audit data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">LLM Audit Dashboard</h2>
            <p className="text-gray-600">Monitor and analyze LLM interactions across the system</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XCircleIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="flex h-[calc(90vh-120px)]">
          {/* Sidebar - Summary (Cost hidden for now) */}
          <div className="w-80 border-r border-gray-200 p-6 overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
            
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Total Interactions</span>
                  <span className="text-xl font-semibold text-gray-900">
                    {auditRecords.length}
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Successful</span>
                  <span className="text-xl font-semibold text-green-600">
                    {auditRecords.filter(r => r.success).length}
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Failed</span>
                  <span className="text-xl font-semibold text-red-600">
                    {auditRecords.filter(r => !r.success).length}
                  </span>
                </div>
              </div>

              {/* Purposes */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">By Purpose</h4>
                <div className="space-y-2">
                  {Array.from(new Set(auditRecords.map(r => r.purpose))).map((purpose, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-gray-600">{purpose}</span>
                      <span className="font-medium">
                        {auditRecords.filter(r => r.purpose === purpose).length}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Models */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">By Model</h4>
                <div className="space-y-2">
                  {Array.from(new Set(auditRecords.map(r => r.model_name))).map((model, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-gray-600 truncate">{model}</span>
                      <span className="font-medium">
                        {auditRecords.filter(r => r.model_name === model).length}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content - Audit Records */}
          <div className="flex-1 p-6 overflow-y-auto min-w-0">
            {/* Filters */}
            <div className="mb-6 flex gap-4">
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

            {/* Audit Records Table */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto max-w-full relative">
                <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '800px' }}>
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                      Interaction
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40">
                      Model
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                      Purpose
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                      Duration
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {auditRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 w-48">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {record.interaction_id}
                        </div>
                        <div className="text-sm text-gray-500 truncate">
                          {new Date(record.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-4 py-4 w-40">
                        <div className="text-sm text-gray-900 truncate">{record.model_name}</div>
                        <div className="text-sm text-gray-500 truncate">{record.model_provider}</div>
                      </td>
                      <td className="px-4 py-4 w-32">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPurposeColor(record.purpose)}`}>
                          {record.purpose}
                        </span>
                        {record.sub_purpose && (
                          <div className="text-xs text-gray-500 mt-1 truncate">{record.sub_purpose}</div>
                        )}
                      </td>
                      <td className="px-4 py-4 w-24">
                        {record.success ? (
                          <div className="flex items-center text-green-600">
                            <CheckCircleIcon className="h-4 w-4 mr-1" />
                            <span className="text-sm">Success</span>
                          </div>
                        ) : (
                          <div className="flex items-center text-red-600">
                            <XCircleIcon className="h-4 w-4 mr-1" />
                            <span className="text-sm">Failed</span>
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4 w-20 text-sm text-gray-900">
                        {record.response_time_ms ? formatDuration(record.response_time_ms) : 'N/A'}
                      </td>
                      <td className="px-4 py-4 w-20 text-sm font-medium">
                        <button
                          onClick={() => {
                            setSelectedRecord(record);
                            setActiveTab('prompt');
                          }}
                          className="text-yellow-600 hover:text-yellow-900 flex items-center whitespace-nowrap"
                        >
                          <EyeIcon className="h-4 w-4 mr-1" />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                </table>
                {/* Scroll indicator */}
                <div className="absolute bottom-2 right-2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-75">
                  ← Scroll to see all columns →
                </div>
              </div>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {auditRecords.length} records
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
                  disabled={filters.page === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                  disabled={auditRecords.length < filters.page_size}
                  className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Record Detail Modal */}
        {selectedRecord && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  Interaction Details: {selectedRecord.interaction_id}
                </h3>
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                {/* Basic Info and Performance - Always visible */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Basic Info</h4>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Model:</span> {selectedRecord.model_name}</div>
                      <div><span className="font-medium">Provider:</span> {selectedRecord.model_provider}</div>
                      <div><span className="font-medium">Purpose:</span> {selectedRecord.purpose}</div>
                      {selectedRecord.sub_purpose && (
                        <div><span className="font-medium">Sub-purpose:</span> {selectedRecord.sub_purpose}</div>
                      )}
                      <div><span className="font-medium">Success:</span> {selectedRecord.success ? 'Yes' : 'No'}</div>
                      {selectedRecord.error_message && (
                        <div><span className="font-medium">Error:</span> {selectedRecord.error_message}</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Performance</h4>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Response Time:</span> {selectedRecord.response_time_ms ? formatDuration(selectedRecord.response_time_ms) : 'N/A'}</div>
                      <div><span className="font-medium">Input Tokens:</span> {selectedRecord.input_tokens || 'N/A'}</div>
                      <div><span className="font-medium">Output Tokens:</span> {selectedRecord.output_tokens || 'N/A'}</div>
                    </div>
                  </div>
                </div>

                {/* Hyperparameters - Always visible */}
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-2">Hyperparameters</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><span className="font-medium">Temperature:</span> {selectedRecord.temperature || 'N/A'}</div>
                    <div><span className="font-medium">Top P:</span> {selectedRecord.top_p || 'N/A'}</div>
                    <div><span className="font-medium">Max Tokens:</span> {selectedRecord.max_tokens || 'N/A'}</div>
                  </div>
                </div>

                {/* Tab Navigation */}
                <div className="border-b border-gray-200 mb-4">
                  <nav className="-mb-px flex space-x-8">
                    <button
                      onClick={() => setActiveTab('prompt')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'prompt'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      Input Prompt
                    </button>
                    {selectedRecord.output_content && (
                      <button
                        onClick={() => setActiveTab('output')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          activeTab === 'output'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        Output Content
                      </button>
                    )}
                    {selectedRecord.interaction_metadata && Object.keys(selectedRecord.interaction_metadata).length > 0 && (
                      <button
                        onClick={() => setActiveTab('metadata')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          activeTab === 'metadata'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        Metadata
                      </button>
                    )}
                  </nav>
                </div>

                {/* Tab Content */}
                <div className="min-h-[400px]">
                  {activeTab === 'prompt' && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">Input Prompt</h4>
                        <button
                          onClick={() => copyToClipboard(selectedRecord.input_prompt, 'prompt')}
                          className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                        >
                          {copiedTab === 'prompt' ? (
                            <>
                              <CheckIcon className="h-4 w-4 mr-1 text-green-600" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <ClipboardDocumentIcon className="h-4 w-4 mr-1" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {selectedRecord.input_prompt}
                        </pre>
                      </div>
                    </div>
                  )}

                  {activeTab === 'output' && selectedRecord.output_content && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">Output Content</h4>
                        <button
                          onClick={() => copyToClipboard(selectedRecord.output_content || '', 'output')}
                          className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                        >
                          {copiedTab === 'output' ? (
                            <>
                              <CheckIcon className="h-4 w-4 mr-1 text-green-600" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <ClipboardDocumentIcon className="h-4 w-4 mr-1" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {selectedRecord.output_content}
                        </pre>
                      </div>
                    </div>
                  )}

                  {activeTab === 'metadata' && selectedRecord.interaction_metadata && Object.keys(selectedRecord.interaction_metadata).length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">Metadata</h4>
                        <button
                          onClick={() => copyToClipboard(JSON.stringify(selectedRecord.interaction_metadata, null, 2), 'metadata')}
                          className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                        >
                          {copiedTab === 'metadata' ? (
                            <>
                              <CheckIcon className="h-4 w-4 mr-1 text-green-600" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <ClipboardDocumentIcon className="h-4 w-4 mr-1" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                        <pre className="text-sm text-gray-700">
                          {JSON.stringify(selectedRecord.interaction_metadata, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LLMAuditDashboard;
