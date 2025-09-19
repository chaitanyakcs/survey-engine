import React, { useState } from 'react';
import { EnhancedRFQEditor } from './EnhancedRFQEditor';
import { PreGenerationPreview } from './PreGenerationPreview';
import { useAppStore } from '../store/useAppStore';

type ViewMode = 'editor' | 'preview';

export const EnhancedRFQApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('editor');
  const { enhancedRfq, submitEnhancedRFQ, workflow } = useAppStore();

  const handleShowPreview = () => {
    setCurrentView('preview');
  };

  const handleEditRequirements = () => {
    setCurrentView('editor');
  };

  const handleGenerate = async () => {
    try {
      await submitEnhancedRFQ(enhancedRfq);
    } catch (error) {
      console.error('Failed to generate survey:', error);
    }
  };

  // If workflow is active, don't show the enhanced RFQ interface
  if (workflow.status !== 'idle') {
    return null;
  }

  return (
    <div className="enhanced-rfq-app">
      {currentView === 'editor' && (
        <EnhancedRFQEditor onPreview={handleShowPreview} />
      )}

      {currentView === 'preview' && (
        <PreGenerationPreview
          rfq={enhancedRfq}
          onGenerate={handleGenerate}
          onEdit={handleEditRequirements}
        />
      )}
    </div>
  );
};

export default EnhancedRFQApp;