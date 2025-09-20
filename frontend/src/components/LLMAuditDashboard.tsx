import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  CurrencyDollarIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  EyeIcon,
  CogIcon
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
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<LLMAuditRecord | null>(null);
  const [filters, setFilters] = useState({
    purpose: '',
    model_name: '',
    success: '',
    page: 1,
    page_size: 20
  });

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

      // Fetch cost summary
      const costResponse = await fetch('/api/v1/llm-audit/cost-summary');
      const costData = await costResponse.json();
      setCostSummary(costData);
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPurposeColor = (purpose: string) => {
    const colors: Record<string, string> = {
      'survey_generation': 'bg-blue-100 text-blue-800',
      'evaluation': 'bg-green-100 text-green-800',
      'field_extraction': 'bg-purple-100 text-purple-800',
      'document_parsing': 'bg-orange-100 text-orange-800',
    };
    return colors[purpose] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
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
          {/* Sidebar - Cost Summary */}
          <div className="w-80 border-r border-gray-200 p-6 overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Summary</h3>
            
            {costSummary && (
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Total Cost</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {formatCurrency(costSummary.total_cost_usd)}
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Total Interactions</span>
                    <span className="text-xl font-semibold text-gray-900">
                      {costSummary.total_interactions}
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Success Rate</span>
                    <span className="text-xl font-semibold text-green-600">
                      {(costSummary.success_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Cost by Purpose */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Cost by Purpose</h4>
                  <div className="space-y-2">
                    {costSummary.cost_by_purpose.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-600">{item.purpose}</span>
                        <span className="font-medium">{formatCurrency(item.total_cost_usd)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cost by Model */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Cost by Model</h4>
                  <div className="space-y-2">
                    {costSummary.cost_by_model.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-600 truncate">{item.model_name}</span>
                        <span className="font-medium">{formatCurrency(item.total_cost_usd)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content - Audit Records */}
          <div className="flex-1 p-6 overflow-y-auto">
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
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Interaction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Purpose
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {auditRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {record.interaction_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(record.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{record.model_name}</div>
                        <div className="text-sm text-gray-500">{record.model_provider}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPurposeColor(record.purpose)}`}>
                          {record.purpose}
                        </span>
                        {record.sub_purpose && (
                          <div className="text-xs text-gray-500 mt-1">{record.sub_purpose}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
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
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.cost_usd ? formatCurrency(record.cost_usd) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.response_time_ms ? formatDuration(record.response_time_ms) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedRecord(record)}
                          className="text-blue-600 hover:text-blue-900 flex items-center"
                        >
                          <EyeIcon className="h-4 w-4 mr-1" />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
                <div className="grid grid-cols-2 gap-6">
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
                      <div><span className="font-medium">Cost:</span> {selectedRecord.cost_usd ? formatCurrency(selectedRecord.cost_usd) : 'N/A'}</div>
                      <div><span className="font-medium">Input Tokens:</span> {selectedRecord.input_tokens || 'N/A'}</div>
                      <div><span className="font-medium">Output Tokens:</span> {selectedRecord.output_tokens || 'N/A'}</div>
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <h4 className="font-semibold text-gray-900 mb-2">Hyperparameters</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><span className="font-medium">Temperature:</span> {selectedRecord.temperature || 'N/A'}</div>
                    <div><span className="font-medium">Top P:</span> {selectedRecord.top_p || 'N/A'}</div>
                    <div><span className="font-medium">Max Tokens:</span> {selectedRecord.max_tokens || 'N/A'}</div>
                  </div>
                </div>

                <div className="mt-6">
                  <h4 className="font-semibold text-gray-900 mb-2">Input Prompt</h4>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-40 overflow-y-auto">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                      {selectedRecord.input_prompt}
                    </pre>
                  </div>
                </div>

                {selectedRecord.output_content && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-2">Output Content</h4>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-40 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                        {selectedRecord.output_content}
                      </pre>
                    </div>
                  </div>
                )}

                {selectedRecord.interaction_metadata && Object.keys(selectedRecord.interaction_metadata).length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-2">Metadata</h4>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <pre className="text-sm text-gray-700">
                        {JSON.stringify(selectedRecord.interaction_metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LLMAuditDashboard;
