import React, { useState } from 'react';
import { SurveySection } from '../../types';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { 
  PencilIcon, 
  TrashIcon, 
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

interface SectionControlsProps {
  section: SurveySection;
  isEditingSurvey: boolean;
  onEdit: (section: SurveySection) => void;
  onDelete: (sectionId: number) => void;
  onMoveUp: (sectionId: number) => void;
  onMoveDown: (sectionId: number) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isLoading?: boolean;
}

export const SectionControls: React.FC<SectionControlsProps> = ({
  section,
  isEditingSurvey,
  onEdit,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  isLoading = false
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(section.id);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Failed to delete section:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isEditingSurvey) {
    return null;
  }

  return (
    <>
      <div className="flex items-center space-x-2">
        {/* Edit Section */}
        <button
          onClick={() => onEdit(section)}
          disabled={isLoading}
          className="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-50"
          title="Edit section"
        >
          <PencilIcon className="h-4 w-4" />
        </button>

        {/* Delete Section */}
        <button
          onClick={() => setShowDeleteConfirm(true)}
          disabled={isLoading}
          className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-50"
          title="Delete section"
        >
          <TrashIcon className="h-4 w-4" />
        </button>

        {/* Move Section Up */}
        <button
          onClick={() => onMoveUp(section.id)}
          disabled={!canMoveUp || isLoading}
          className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          title="Move section up"
        >
          <ArrowUpIcon className="h-4 w-4" />
        </button>

        {/* Move Section Down */}
        <button
          onClick={() => onMoveDown(section.id)}
          disabled={!canMoveDown || isLoading}
          className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          title="Move section down"
        >
          <ArrowDownIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Section"
        message={`Are you sure you want to delete the section "${section.title}"? This will also delete all questions in this section. This action cannot be undone.`}
        confirmText="Delete Section"
        cancelText="Cancel"
        type="danger"
        isLoading={isDeleting}
      />
    </>
  );
};

export default SectionControls;
