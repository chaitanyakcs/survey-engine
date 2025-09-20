import React, { useState, useEffect, useCallback } from 'react';
import { XMarkIcon, DocumentTextIcon, ClockIcon, CpuChipIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

interface SystemPromptAudit {
  id: string;
  survey_id: string;
  rfq_id?: string;
  system_prompt: string;
  prompt_type: string;
  model_version?: string;
  generation_context?: {
    golden_examples_count?: number;
    methodology_blocks_count?: number;
    custom_rules_count?: number;
    context_keys?: string[];
  };
  created_at: string;
}

interface LLMInteraction {
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
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stop_sequences?: string[];
  response_time_ms?: number;
  success: boolean;
  error_message?: string;
  interaction_metadata?: Record<string, any>;
  tags?: string[];
  created_at: string;
}

type AuditItem = SystemPromptAudit | LLMInteraction;

function isSystemPromptAudit(item: AuditItem): item is SystemPromptAudit {
  return 'system_prompt' in item;
}

function isLLMInteraction(item: AuditItem): item is LLMInteraction {
  return 'interaction_id' in item;
}

interface SystemPromptViewerProps {
  surveyId: string;
  onClose: () => void;
}

export const SystemPromptViewer: React.FC<SystemPromptViewerProps> = ({ surveyId, onClose }) => {
  const [allItems, setAllItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<AuditItem | null>(null);
  const [filter, setFilter] = useState<'all' | 'prompts' | 'llm'>('all');

  const fetchSystemPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/system-prompt-audit/survey/${surveyId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch system prompts: ${response.statusText}`);
      }

      const data = await response.json();

      // Combine system prompts and LLM interactions into one array
      const combined: AuditItem[] = [
        ...(data.prompts || []),
        ...(data.llm_interactions || [])
      ];

      // Sort by creation time (newest first)
      combined.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      setAllItems(combined);

      // Select the most recent item by default
      if (combined.length > 0) {
        setSelectedItem(combined[0]);
      }
    } catch (err) {
      console.error('Error fetching system prompts:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch system prompts');
    } finally {
      setLoading(false);
    }
  }, [surveyId]);

  useEffect(() => {
    fetchSystemPrompts();
  }, [fetchSystemPrompts]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // You could add a toast notification here
      console.log('Content copied to clipboard');
    });
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
      'generation': 'bg-blue-100 text-blue-800',
    };
    return colors[purpose] || 'bg-gray-100 text-gray-800';
  };

  const getItemTitle = (item: AuditItem) => {
    if (isSystemPromptAudit(item)) {
      if (item.prompt_type === 'generation') return 'Survey Generation';
      if (item.prompt_type === 'content_validity_objective_extraction') return 'Content Validity - Objective Extraction';
      if (item.prompt_type === 'methodological_rigor_bias_detection') return 'Methodological Rigor - Bias Detection';
      if (item.prompt_type === 'evaluation') return 'Pillar Evaluation';
      return item.prompt_type;
    } else {
      return `${item.purpose}${item.sub_purpose ? ` - ${item.sub_purpose}` : ''}`;
    }
  };

  const getItemContent = (item: AuditItem) => {
    if (isSystemPromptAudit(item)) {
      return item.system_prompt;
    } else {
      return item.input_prompt;
    }
  };

  const filteredItems = allItems.filter(item => {
    if (filter === 'prompts') return isSystemPromptAudit(item);
    if (filter === 'llm') return isLLMInteraction(item);
    return true;
  });

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-3 text-gray-600">Loading system prompts...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">System Prompt Viewer</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          <div className="text-center py-8">
            <div className="text-red-600 mb-2">Error loading system prompts</div>
            <div className="text-gray-600 text-sm">{error}</div>
            <button
              onClick={fetchSystemPrompts}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (allItems.length === 0) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">System Prompt Viewer</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          <div className="text-center py-8">
            <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <div className="text-gray-600 mb-2">No system prompts found</div>
            <div className="text-gray-500 text-sm">System prompts are only available for surveys generated after this feature was implemented.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">LLM Audit Viewer</h2>
            <p className="text-sm text-gray-600 mt-1">
              View all AI interactions and prompts used for this survey
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Filter buttons */}
        <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm rounded-lg font-medium ${
                filter === 'all'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              All ({allItems.length})
            </button>
            <button
              onClick={() => setFilter('prompts')}
              className={`px-3 py-1 text-sm rounded-lg font-medium ${
                filter === 'prompts'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              System Prompts ({allItems.filter(isSystemPromptAudit).length})
            </button>
            <button
              onClick={() => setFilter('llm')}
              className={`px-3 py-1 text-sm rounded-lg font-medium ${
                filter === 'llm'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              LLM Interactions ({allItems.filter(isLLMInteraction).length})
            </button>
          </div>
        </div>

        <div className="flex h-[calc(90vh-180px)]">
          {/* Sidebar - Item List */}
          <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                {filter === 'prompts' ? 'System Prompts' :
                 filter === 'llm' ? 'LLM Interactions' :
                 'All Interactions'}
              </h3>
              <div className="space-y-2">
                {filteredItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedItem?.id === item.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">
                          {getItemTitle(item)}
                        </span>
                        {isLLMInteraction(item) && (
                          <div className="flex items-center">
                            {item.success ? (
                              <CheckCircleIcon className="w-3 h-3 text-green-500" />
                            ) : (
                              <ExclamationCircleIcon className="w-3 h-3 text-red-500" />
                            )}
                          </div>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      {isSystemPromptAudit(item) ? (
                        <>
                          {item.model_version && (
                            <div className="flex items-center space-x-1">
                              <CpuChipIcon className="w-3 h-3" />
                              <span>{item.model_version}</span>
                            </div>
                          )}
                          {item.generation_context?.golden_examples_count !== undefined && (
                            <span>{item.generation_context.golden_examples_count} examples</span>
                          )}
                        </>
                      ) : (
                        <>
                          <div className="flex items-center space-x-1">
                            <CpuChipIcon className="w-3 h-3" />
                            <span>{item.model_name}</span>
                          </div>
                          {item.response_time_ms && (
                            <div className="flex items-center space-x-1">
                              <ClockIcon className="w-3 h-3" />
                              <span>{formatDuration(item.response_time_ms)}</span>
                            </div>
                          )}
                          <span className={`inline-flex px-1 py-0.5 text-xs font-semibold rounded ${getPurposeColor(item.purpose)}`}>
                            {item.purpose}
                          </span>
                        </>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content - Selected Item */}
          <div className="flex-1 flex flex-col">
            {selectedItem ? (
              <>
                {/* Header */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {getItemTitle(selectedItem)}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                        <div className="flex items-center space-x-1">
                          <ClockIcon className="w-4 h-4" />
                          <span>{formatDate(selectedItem.created_at)}</span>
                        </div>
                        {isSystemPromptAudit(selectedItem) ? (
                          selectedItem.model_version && (
                            <div className="flex items-center space-x-1">
                              <CpuChipIcon className="w-4 h-4" />
                              <span>{selectedItem.model_version}</span>
                            </div>
                          )
                        ) : (
                          <>
                            <div className="flex items-center space-x-1">
                              <CpuChipIcon className="w-4 h-4" />
                              <span>{selectedItem.model_name}</span>
                            </div>
                            {selectedItem.response_time_ms && (
                              <div className="flex items-center space-x-1">
                                <ClockIcon className="w-4 h-4" />
                                <span>{formatDuration(selectedItem.response_time_ms)}</span>
                              </div>
                            )}
                            <div className="flex items-center space-x-1">
                              {selectedItem.success ? (
                                <CheckCircleIcon className="w-4 h-4 text-green-500" />
                              ) : (
                                <ExclamationCircleIcon className="w-4 h-4 text-red-500" />
                              )}
                              <span>{selectedItem.success ? 'Success' : 'Failed'}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(getItemContent(selectedItem))}
                      className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Copy
                    </button>
                  </div>

                  {/* Context Information */}
                  {isSystemPromptAudit(selectedItem) ? (
                    selectedItem.generation_context && (
                      <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Generation Context</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                          {selectedItem.generation_context.golden_examples_count !== undefined && (
                            <div>Golden Examples: {selectedItem.generation_context.golden_examples_count}</div>
                          )}
                          {selectedItem.generation_context.methodology_blocks_count !== undefined && (
                            <div>Methodology Blocks: {selectedItem.generation_context.methodology_blocks_count}</div>
                          )}
                          {selectedItem.generation_context.custom_rules_count !== undefined && (
                            <div>Custom Rules: {selectedItem.generation_context.custom_rules_count}</div>
                          )}
                          {selectedItem.generation_context.context_keys && (
                            <div className="col-span-2">
                              Context Keys: {selectedItem.generation_context.context_keys.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Interaction Details</h4>
                      <div className="grid grid-cols-3 gap-4 text-xs text-gray-600">
                        <div><span className="font-medium">Model Provider:</span> {selectedItem.model_provider}</div>
                        <div><span className="font-medium">Purpose:</span> {selectedItem.purpose}</div>
                        {selectedItem.sub_purpose && (
                          <div><span className="font-medium">Sub-purpose:</span> {selectedItem.sub_purpose}</div>
                        )}
                        {selectedItem.input_tokens && (
                          <div><span className="font-medium">Input Tokens:</span> {selectedItem.input_tokens}</div>
                        )}
                        {selectedItem.output_tokens && (
                          <div><span className="font-medium">Output Tokens:</span> {selectedItem.output_tokens}</div>
                        )}
                        {selectedItem.temperature && (
                          <div><span className="font-medium">Temperature:</span> {selectedItem.temperature}</div>
                        )}
                        {selectedItem.top_p && (
                          <div><span className="font-medium">Top P:</span> {selectedItem.top_p}</div>
                        )}
                        {selectedItem.max_tokens && (
                          <div><span className="font-medium">Max Tokens:</span> {selectedItem.max_tokens}</div>
                        )}
                        {selectedItem.error_message && (
                          <div className="col-span-3"><span className="font-medium text-red-600">Error:</span> {selectedItem.error_message}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 p-4 overflow-y-auto">
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      {isSystemPromptAudit(selectedItem) ? 'System Prompt' : 'Input Prompt'}
                    </h4>
                    <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
                      {getItemContent(selectedItem)}
                    </pre>
                  </div>

                  {/* Output content for LLM interactions */}
                  {isLLMInteraction(selectedItem) && selectedItem.output_content && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Output Content</h4>
                      <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
                        {selectedItem.output_content}
                      </pre>
                    </div>
                  )}

                  {/* Metadata for LLM interactions */}
                  {isLLMInteraction(selectedItem) && selectedItem.interaction_metadata && Object.keys(selectedItem.interaction_metadata).length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Metadata</h4>
                      <pre className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
                        {JSON.stringify(selectedItem.interaction_metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Select an item to view
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
