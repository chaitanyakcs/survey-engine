import React, { useState, useEffect, useCallback } from 'react';
import { EnhancedRFQRequest } from '../types';

interface PromptPreviewProps {
  rfq: EnhancedRFQRequest;
  onPromptEdited?: (editedPrompt: string) => void;
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

export const PromptPreview: React.FC<PromptPreviewProps> = ({ rfq, onPromptEdited }) => {
  const [promptData, setPromptData] = useState<PromptPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullPrompt, setShowFullPrompt] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState<string>('');
  const [activePrompt, setActivePrompt] = useState<string>(''); // Stores the current prompt being displayed

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
      setActivePrompt(data.prompt); // Initialize active prompt with original
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

  const handleStartEdit = () => {
    if (promptData) {
      setEditedPrompt(promptData.prompt);
      setIsEditing(true);
    }
  };

  const handleSaveEdit = () => {
    if (onPromptEdited) {
      onPromptEdited(editedPrompt);
    }
    // Update active prompt to show the edited version
    setActivePrompt(editedPrompt);
    setIsEditing(false);
    setError(null);
  };

  const handleCancelEdit = () => {
    setEditedPrompt('');
    setIsEditing(false);
    setError(null);
  };

  const handleRestoreOriginal = () => {
    if (promptData) {
      setEditedPrompt(promptData.prompt);
    }
  };

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

  // Use activePrompt (which may be edited) or original promptData.prompt
  const displayedPrompt = activePrompt || promptData.prompt;
  const promptPreview = showFullPrompt 
    ? displayedPrompt
    : displayedPrompt.substring(0, 5000) + (displayedPrompt.length > 5000 ? '...' : '');

  return (
    <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">
      
      {/* Warning Banner */}
      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start">
        <span className="text-yellow-600 text-lg mr-2">⚠️</span>
        <p className="text-yellow-800 text-sm">
          <strong>Note:</strong> Any custom edits to this prompt will be lost if you navigate away without generating the survey.
        </p>
      </div>

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
          <div className="flex items-center space-x-2">
            {!isEditing && (
              <>
                  <button
                  onClick={handleStartEdit}
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
                >
                  {activePrompt !== promptData.prompt ? '✏️ Re-edit Prompt' : '✏️ Edit Prompt'}
                </button>
                {activePrompt !== promptData.prompt && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium flex items-center">
                    <span className="mr-1">✏️</span>
                    Custom Prompt Active
                  </span>
                )}
                <button
                  onClick={() => setShowFullPrompt(!showFullPrompt)}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm"
                >
                  {showFullPrompt ? 'Show Less' : 'Show Full Prompt'}
                </button>
              </>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleRestoreOriginal}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                >
                  Restore Original
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  ✓ Save Changes
                </button>
              </>
            )}
          </div>
        </div>
        
        {isEditing ? (
          <>
            <textarea
              value={editedPrompt}
              onChange={(e) => setEditedPrompt(e.target.value)}
              className="w-full bg-gray-900 text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto"
              style={{
                minHeight: '400px',
                resize: 'vertical',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace'
              }}
            />
            <div className="mt-2 text-sm text-gray-600">
              Character count: {editedPrompt.length.toLocaleString()} chars
            </div>
          </>
        ) : (
          <>
            <div className="bg-gray-900 text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto">
              <pre className="whitespace-pre-wrap">{promptPreview}</pre>
            </div>
            
            {!showFullPrompt && displayedPrompt.length > 1000 && (
              <p className="text-gray-500 text-sm mt-2 text-center">
                Showing first 1,000 characters of {displayedPrompt.length.toLocaleString()} total characters
              </p>
            )}
          </>
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
