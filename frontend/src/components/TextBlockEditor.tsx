import React, { useState, useEffect } from 'react';
import { EditableTextBlock } from '../types';
import { PencilIcon, CheckIcon } from '@heroicons/react/24/outline';

interface TextBlockEditorProps {
  textBlocks: EditableTextBlock[];
  onTextBlocksChange: (blocks: EditableTextBlock[]) => void;
}

// Default text blocks with prefilled content
const DEFAULT_TEXT_BLOCKS: EditableTextBlock[] = [
  {
    id: 'study_intro',
    name: 'Study Introduction',
    type: 'study_intro',
    content: 'Thank you for agreeing to participate in this research study. We are conducting a survey about [TOPIC]. The survey will take approximately [X] minutes. Your participation is voluntary, and you may stop at any time. Your responses will be kept confidential and used for research purposes only.',
    label: 'Study_Intro',
    mandatory: true,
    description: 'Participant welcome and study overview',
    section_mapping: 1
  },
  {
    id: 'concept_intro',
    name: 'Concept Introduction',
    type: 'concept_intro',
    content: 'We will now show you some concepts to evaluate. Please review each concept carefully and provide your honest feedback.',
    label: 'Concept_Intro',
    mandatory: false,
    description: 'Before concept evaluation sections',
    section_mapping: 4
  },
  {
    id: 'product_usage',
    name: 'Product Usage Introduction',
    type: 'product_usage',
    content: 'We would like to understand your experience with products in this category. Please answer the following questions about your usage and familiarity.',
    label: 'Product_Usage',
    mandatory: false,
    description: 'Before brand/usage awareness questions',
    section_mapping: 3
  },
  {
    id: 'confidentiality_agreement',
    name: 'Confidentiality Agreement',
    type: 'confidentiality_agreement',
    content: 'Confidentiality Agreement: Your identity will not be linked to your answers. Results will be used for research purposes only and shared in aggregate. Do not attempt to identify any product or brand during the study.',
    label: 'Confidentiality_Agreement',
    mandatory: false,
    description: 'For sensitive research topics',
    section_mapping: 1
  },
  {
    id: 'methodology_instructions',
    name: 'Methodology Instructions',
    type: 'methodology_instructions',
    content: 'Please follow the instructions carefully. Read each question thoroughly before responding.',
    label: 'Methodology_Instructions',
    mandatory: false,
    description: 'Method-specific instructions',
    section_mapping: 5
  },
  {
    id: 'closing_thank_you',
    name: 'Closing Thank You',
    type: 'closing_thank_you',
    content: 'Thank you for completing this survey. Your responses are valuable and will help inform important decisions. If you have any questions or concerns, please contact us.',
    label: 'Survey_Closing',
    mandatory: false,
    description: 'Final section thank you and next steps',
    section_mapping: 7
  }
];

const SECTION_NAMES: Record<number, string> = {
  1: 'Sample Plan (Section 1)',
  2: 'Screener (Section 2)',
  3: 'Brand/Product Awareness (Section 3)',
  4: 'Concept Exposure (Section 4)',
  5: 'Methodology (Section 5)',
  6: 'Additional Questions (Section 6)',
  7: 'Programmer Instructions (Section 7)'
};


export const TextBlockEditor: React.FC<TextBlockEditorProps> = ({
  textBlocks,
  onTextBlocksChange
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingBlock, setEditingBlock] = useState<EditableTextBlock | null>(null);

  // Initialize with defaults if empty
  const blocks = textBlocks.length > 0 ? textBlocks : DEFAULT_TEXT_BLOCKS;

  // Initialize defaults on mount if empty
  useEffect(() => {
    if (!textBlocks || textBlocks.length === 0) {
      onTextBlocksChange(DEFAULT_TEXT_BLOCKS);
    }
  }, [textBlocks, onTextBlocksChange]);

  const handleEdit = (block: EditableTextBlock) => {
    setEditingId(block.id);
    setEditingBlock({ ...block });
  };

  const handleSave = () => {
    if (!editingBlock) return;
    
    const updated = blocks.map(b => 
      b.id === editingBlock.id ? editingBlock : b
    );
    onTextBlocksChange(updated);
    setEditingId(null);
    setEditingBlock(null);
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditingBlock(null);
  };

  const renderBlockCard = (block: EditableTextBlock) => {
    const isEditing = editingId === block.id;

    if (isEditing && editingBlock) {
      return (
        <div key={block.id} className="border-2 border-blue-300 rounded-lg p-4 bg-blue-50">
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-gray-900">{editingBlock.name}</h4>
              <div className="flex items-center space-x-2">
                {editingBlock.mandatory && (
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                    Required
                  </span>
                )}
                <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                  {editingBlock.label}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <textarea
                value={editingBlock.content}
                onChange={(e) => setEditingBlock({ ...editingBlock, content: e.target.value })}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter the text content..."
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center space-x-1"
              >
                <CheckIcon className="w-4 h-4" />
                <span>Save</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div key={block.id} className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <h4 className="font-semibold text-gray-900">{block.name}</h4>
              {block.mandatory && (
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                  Required
                </span>
              )}
              <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                {block.label}
              </span>
              <span className="text-xs text-gray-500">
                {SECTION_NAMES[block.section_mapping || 1]}
              </span>
            </div>
            {block.description && (
              <p className="text-sm text-gray-600 mb-3">{block.description}</p>
            )}
            <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{block.content}</p>
            </div>
          </div>
          <div className="ml-4">
            <button
              onClick={() => handleEdit(block)}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              title="Edit content"
            >
              <PencilIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-800">Text Blocks</h3>
        <p className="text-sm text-gray-600 mt-1">
          Edit the content of text blocks that will appear in your survey. All standard text blocks are included by default with prefilled content.
        </p>
      </div>

      <div className="space-y-3">
        {blocks.map(renderBlockCard)}
      </div>
    </div>
  );
};

