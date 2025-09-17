import React, { useState, useEffect, useCallback } from 'react';
import { XMarkIcon, DocumentTextIcon, ClockIcon, CpuChipIcon } from '@heroicons/react/24/outline';

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

interface SystemPromptViewerProps {
  surveyId: string;
  onClose: () => void;
}

export const SystemPromptViewer: React.FC<SystemPromptViewerProps> = ({ surveyId, onClose }) => {
  const [prompts, setPrompts] = useState<SystemPromptAudit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<SystemPromptAudit | null>(null);

  const fetchSystemPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/v1/system-prompt-audit/survey/${surveyId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch system prompts: ${response.statusText}`);
      }
      
      const data = await response.json();
      setPrompts(data.prompts || []);
      
      // Select the most recent prompt by default
      if (data.prompts && data.prompts.length > 0) {
        setSelectedPrompt(data.prompts[0]);
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
      console.log('System prompt copied to clipboard');
    });
  };

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

  if (prompts.length === 0) {
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
            <h2 className="text-xl font-semibold text-gray-900">System Prompt Viewer</h2>
            <p className="text-sm text-gray-600 mt-1">
              View the AI prompts used to generate this survey
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="flex h-[calc(90vh-120px)]">
          {/* Sidebar - Prompt List */}
          <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Generation History</h3>
              <div className="space-y-2">
                {prompts.map((prompt) => (
                  <button
                    key={prompt.id}
                    onClick={() => setSelectedPrompt(prompt)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedPrompt?.id === prompt.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        {prompt.prompt_type === 'generation' ? 'Survey Generation' : 
                         prompt.prompt_type === 'content_validity_objective_extraction' ? 'Content Validity - Objective Extraction' :
                         prompt.prompt_type === 'methodological_rigor_bias_detection' ? 'Methodological Rigor - Bias Detection' :
                         prompt.prompt_type === 'evaluation' ? 'Pillar Evaluation' :
                         prompt.prompt_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(prompt.created_at)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      {prompt.model_version && (
                        <div className="flex items-center space-x-1">
                          <CpuChipIcon className="w-3 h-3" />
                          <span>{prompt.model_version}</span>
                        </div>
                      )}
                      {prompt.generation_context?.golden_examples_count !== undefined && (
                        <span>{prompt.generation_context.golden_examples_count} examples</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content - Selected Prompt */}
          <div className="flex-1 flex flex-col">
            {selectedPrompt ? (
              <>
                {/* Prompt Header */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {selectedPrompt.prompt_type === 'generation' ? 'Survey Generation Prompt' : 
                         selectedPrompt.prompt_type === 'content_validity_objective_extraction' ? 'Content Validity - Objective Extraction Prompt' :
                         selectedPrompt.prompt_type === 'methodological_rigor_bias_detection' ? 'Methodological Rigor - Bias Detection Prompt' :
                         selectedPrompt.prompt_type === 'evaluation' ? 'Pillar Evaluation Prompt' :
                         selectedPrompt.prompt_type}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                        <div className="flex items-center space-x-1">
                          <ClockIcon className="w-4 h-4" />
                          <span>{formatDate(selectedPrompt.created_at)}</span>
                        </div>
                        {selectedPrompt.model_version && (
                          <div className="flex items-center space-x-1">
                            <CpuChipIcon className="w-4 h-4" />
                            <span>{selectedPrompt.model_version}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(selectedPrompt.system_prompt)}
                      className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Copy
                    </button>
                  </div>
                  
                  {/* Generation Context */}
                  {selectedPrompt.generation_context && (
                    <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Generation Context</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                        {selectedPrompt.generation_context.golden_examples_count !== undefined && (
                          <div>Golden Examples: {selectedPrompt.generation_context.golden_examples_count}</div>
                        )}
                        {selectedPrompt.generation_context.methodology_blocks_count !== undefined && (
                          <div>Methodology Blocks: {selectedPrompt.generation_context.methodology_blocks_count}</div>
                        )}
                        {selectedPrompt.generation_context.custom_rules_count !== undefined && (
                          <div>Custom Rules: {selectedPrompt.generation_context.custom_rules_count}</div>
                        )}
                        {selectedPrompt.generation_context.context_keys && (
                          <div className="col-span-2">
                            Context Keys: {selectedPrompt.generation_context.context_keys.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Prompt Content */}
                <div className="flex-1 p-4 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
                    {selectedPrompt.system_prompt}
                  </pre>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Select a prompt to view
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
