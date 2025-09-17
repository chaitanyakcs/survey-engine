import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';

interface SystemPrompt {
  id: string;
  prompt_text: string;
  created_at?: string;
  updated_at?: string;
}

interface SystemPromptProps {
  systemPrompt: SystemPrompt;
  onUpdateSystemPrompt: (systemPrompt: SystemPrompt) => void;
  onShowDeleteConfirm: (config: {
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt';
    title: string;
    message: string;
    onConfirm: () => void;
  }) => void;
}

export const SystemPromptComponent: React.FC<SystemPromptProps> = ({
  systemPrompt,
  onUpdateSystemPrompt,
  onShowDeleteConfirm
}) => {
  const { addToast } = useAppStore();
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);
  const [tempPromptText, setTempPromptText] = useState(systemPrompt.prompt_text || '');

  const handleEditSystemPrompt = () => {
    setIsEditingPrompt(true);
  };

  const handleSaveSystemPrompt = async () => {
    try {
      const response = await fetch('/api/v1/rules/system-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_text: tempPromptText })
      });

      if (response.ok) {
        const result = await response.json();
        onUpdateSystemPrompt({
          id: result.id,
          prompt_text: result.prompt_text,
          created_at: result.created_at || '',
          updated_at: result.updated_at || ''
        });
        setIsEditingPrompt(false);
        addToast({
          type: 'success',
          title: 'System Prompt Saved',
          message: 'System prompt has been saved successfully',
          duration: 3000
        });
      } else {
        addToast({
          type: 'error',
          title: 'Save Failed',
          message: 'Failed to save system prompt',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to save system prompt:', error);
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: 'Failed to save system prompt',
        duration: 5000
      });
    }
  };

  const handleCancelEdit = () => {
    setTempPromptText(systemPrompt.prompt_text);
    setIsEditingPrompt(false);
  };

  const handleDeleteSystemPrompt = async () => {
    onShowDeleteConfirm({
      show: true,
      type: 'system-prompt',
      title: 'Delete System Prompt',
      message: 'Are you sure you want to delete the system prompt? This action cannot be undone.',
      onConfirm: async () => {
        await performSystemPromptDeletion();
      }
    });
  };

  const performSystemPromptDeletion = async () => {
    try {
      const response = await fetch('/api/v1/rules/system-prompt', { method: 'DELETE' });
      if (response.ok) {
        onUpdateSystemPrompt({ id: '', prompt_text: '', created_at: '', updated_at: '' });
        setTempPromptText('');
        addToast({
          type: 'success',
          title: 'System Prompt Deleted',
          message: 'System prompt has been deleted successfully',
          duration: 3000
        });
        // Close the delete confirmation popup
        onShowDeleteConfirm({
          show: false,
          type: 'system-prompt',
          title: '',
          message: '',
          onConfirm: () => {}
        });
      } else {
        addToast({
          type: 'error',
          title: 'Delete Failed',
          message: 'Failed to delete system prompt',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to delete system prompt:', error);
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: 'Network error occurred while deleting system prompt',
        duration: 5000
      });
    }
  };

  return (
    <div className="mb-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-start space-x-3">
          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">How System Prompt Works</h4>
            <p className="text-sm text-blue-800">
              Your custom system prompt will be added to every AI generation request, allowing you to provide
              specific instructions, context, or requirements that will be followed consistently across all survey generations.
            </p>
          </div>
        </div>
      </div>

      {!isEditingPrompt ? (
        <div className="space-y-4">
          {systemPrompt.prompt_text ? (
            <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">Current System Prompt</h4>
                <div className="flex space-x-2">
                  <button
                    onClick={handleEditSystemPrompt}
                    className="px-3 py-1 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDeleteSystemPrompt}
                    className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
              <div className="whitespace-pre-wrap text-sm text-gray-600 leading-relaxed">
                {systemPrompt.prompt_text}
              </div>
              {systemPrompt.updated_at && (
                <div className="text-xs text-gray-500 mt-2">
                  Last updated: {new Date(systemPrompt.updated_at).toLocaleString()}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <p className="text-lg font-medium">No system prompt yet</p>
              <p className="text-sm mb-4">Add custom instructions to guide the AI</p>
              <button
                onClick={handleEditSystemPrompt}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Add System Prompt
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              System Prompt Instructions
            </label>
            <textarea
              value={tempPromptText}
              onChange={(e) => setTempPromptText(e.target.value)}
              placeholder="Enter your custom system prompt instructions here. These will be added to every AI generation request..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent h-32 resize-y"
            />
            <p className="text-xs text-gray-500 mt-1">
              These instructions will be injected into every AI prompt to guide survey generation.
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleSaveSystemPrompt}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Save Prompt
            </button>
            <button
              onClick={handleCancelEdit}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
