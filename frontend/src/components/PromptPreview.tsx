import React, { useState, useEffect, useCallback } from 'react';
import { EnhancedRFQRequest } from '../types';

interface PromptPreviewProps {
  rfq: EnhancedRFQRequest;
}

interface PromptPreviewResponse {
  rfq_id?: string;
  prompt: string;
  prompt_length: number;
  context_info: {
    rfq_title: string;
    rfq_description_length: number;
    product_category: string;
    target_segment: string;
    research_goal: string;
    enhanced_rfq_fields: number;
  };
  methodology_tags: string[];
  golden_examples_count: number;
  methodology_blocks_count: number;
  enhanced_rfq_used: boolean;
}

export const PromptPreview: React.FC<PromptPreviewProps> = ({ rfq }) => {
  const [promptData, setPromptData] = useState<PromptPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullPrompt, setShowFullPrompt] = useState(false);

  const fetchPromptPreview = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Convert Enhanced RFQ to the format expected by the API
      const requestData = {
        rfq_id: `preview-${Date.now()}`, // Generate a unique RFQ ID for preview
        title: rfq.title,
        description: rfq.description,
        product_category: rfq.advanced_classification?.industry_classification || 'General',
        target_segment: rfq.research_objectives?.research_audience || 'General',
        research_goal: rfq.research_objectives?.success_criteria || 'Market research',
        enhanced_rfq_data: rfq
      };

      console.log('🔍 [PromptPreview] Sending request:', requestData);

      const response = await fetch('/api/v1/rfq/preview-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PromptPreviewResponse = await response.json();
      setPromptData(data);
      console.log('✅ [PromptPreview] Received prompt data:', data);
    } catch (err) {
      console.error('❌ [PromptPreview] Error fetching prompt preview:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch prompt preview');
    } finally {
      setIsLoading(false);
    }
  }, [rfq]);

  useEffect(() => {
    fetchPromptPreview();
  }, [fetchPromptPreview]);

  if (isLoading) {
    return (
      <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Generating prompt preview...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-red-800 font-semibold">Error Loading Prompt Preview</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
              <button
                onClick={fetchPromptPreview}
                className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!promptData) {
    return null;
  }

  const promptPreview = showFullPrompt 
    ? promptData.prompt 
    : promptData.prompt.substring(0, 1000) + (promptData.prompt.length > 1000 ? '...' : '');

  return (
    <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">

      {/* RFQ ID */}
      {promptData.rfq_id && (
        <div className="mb-4 p-3 bg-gray-100 rounded-lg">
          <span className="text-sm font-medium text-gray-700">RFQ ID: </span>
          <span className="text-sm font-mono text-gray-900">{promptData.rfq_id}</span>
        </div>
      )}

      {/* Prompt Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-xl">
          <h4 className="font-semibold text-blue-800 mb-1">Prompt Length</h4>
          <p className="text-blue-700 text-lg font-bold">{promptData.prompt_length.toLocaleString()} chars</p>
        </div>
        <div className="p-4 bg-green-50 rounded-xl">
          <h4 className="font-semibold text-green-800 mb-1">Golden Examples</h4>
          <p className="text-green-700 text-lg font-bold">{promptData.golden_examples_count}</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-xl">
          <h4 className="font-semibold text-purple-800 mb-1">Methodology Blocks</h4>
          <p className="text-purple-700 text-lg font-bold">{promptData.methodology_blocks_count}</p>
        </div>
      </div>

      {/* Methodology Tags */}
      {promptData.methodology_tags.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-800 mb-3">Methodology Tags</h3>
          <div className="flex flex-wrap gap-2">
            {promptData.methodology_tags.map((tag, index) => (
              <span key={index} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Context Information */}
      <div className="mb-6 p-4 bg-gray-50 rounded-xl">
        <h3 className="font-semibold text-gray-800 mb-3">Context Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Title:</span>
            <span className="ml-2 font-medium">{promptData.context_info.rfq_title || 'Untitled'}</span>
          </div>
          <div>
            <span className="text-gray-600">Description Length:</span>
            <span className="ml-2 font-medium">{promptData.context_info.rfq_description_length} chars</span>
          </div>
          <div>
            <span className="text-gray-600">Product Category:</span>
            <span className="ml-2 font-medium">{promptData.context_info.product_category}</span>
          </div>
          <div>
            <span className="text-gray-600">Target Segment:</span>
            <span className="ml-2 font-medium">{promptData.context_info.target_segment}</span>
          </div>
          <div>
            <span className="text-gray-600">Research Goal:</span>
            <span className="ml-2 font-medium">{promptData.context_info.research_goal}</span>
          </div>
          <div>
            <span className="text-gray-600">Enhanced Fields:</span>
            <span className="ml-2 font-medium">{promptData.context_info.enhanced_rfq_fields}</span>
          </div>
        </div>
      </div>

      {/* Prompt Content */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">Generated Prompt</h3>
          <button
            onClick={() => setShowFullPrompt(!showFullPrompt)}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm"
          >
            {showFullPrompt ? 'Show Less' : 'Show Full Prompt'}
          </button>
        </div>
        
        <div className="bg-gray-900 text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto">
          <pre className="whitespace-pre-wrap">{promptPreview}</pre>
        </div>
        
        {!showFullPrompt && promptData.prompt.length > 1000 && (
          <p className="text-gray-500 text-sm mt-2 text-center">
            Showing first 1,000 characters of {promptData.prompt_length.toLocaleString()} total characters
          </p>
        )}
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchPromptPreview}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Refresh Preview
        </button>
      </div>
    </div>
  );
};
