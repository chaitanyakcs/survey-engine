import React, { useState, useRef, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { DocumentAnalysisResponse, DocumentUploadProgress } from '../types';

interface DocumentUploadProps {
  onDocumentAnalyzed?: (response: DocumentAnalysisResponse) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onDocumentAnalyzed,
  onError,
  className = ''
}) => {
  const { addToast, uploadDocument: storeUploadDocument, isDocumentProcessing } = useAppStore();
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<DocumentUploadProgress | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.docx')) {
      return 'Only DOCX files are supported. Please upload a Microsoft Word document.';
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return 'File too large. Maximum size is 10MB.';
    }

    // Check if file is empty
    if (file.size === 0) {
      return 'File appears to be empty. Please select a valid document.';
    }

    return null;
  };

  const uploadDocument = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      addToast({
        type: 'error',
        title: 'Invalid File',
        message: validationError
      });
      onError?.(validationError);
      return;
    }

    setIsUploading(true);
    setUploadProgress({
      stage: 'uploading',
      progress: 10,
      message: 'Uploading document...'
    });

    try {
      setUploadProgress({
        stage: 'parsing',
        progress: 30,
        message: 'Parsing document structure...'
      });

      // Use store method which also updates global state for UI population
      const result: DocumentAnalysisResponse = await storeUploadDocument(file);

      setUploadProgress({
        stage: 'analyzing',
        progress: 60,
        message: 'Analyzing content with AI...'
      });

      setUploadProgress({
        stage: 'mapping',
        progress: 80,
        message: 'Mapping fields to RFQ structure...'
      });

      setUploadProgress({
        stage: 'completed',
        progress: 100,
        message: 'Document analysis completed!'
      });

      // Show success notification
      addToast({
        type: 'success',
        title: 'Document Analyzed',
        message: `Found ${result.rfq_analysis.field_mappings?.length || 0} field mappings with ${Math.round((result.rfq_analysis.confidence || 0) * 100)}% confidence`,
        duration: 6000
      });

      // Call success callback
      onDocumentAnalyzed?.(result);

      // Clear progress after a short delay
      setTimeout(() => {
        setUploadProgress(null);
      }, 2000);

    } catch (error) {
      console.error('Document upload failed:', error);

      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

      setUploadProgress({
        stage: 'error',
        progress: 0,
        message: 'Upload failed',
        error: errorMessage
      });

      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: errorMessage,
        duration: 8000
      });

      onError?.(errorMessage);

      // Clear progress after delay
      setTimeout(() => {
        setUploadProgress(null);
      }, 3000);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    uploadDocument(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
  }, [handleFileSelect]);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  // Progress indicator component
  const ProgressIndicator = () => {
    if (!uploadProgress) return null;

    const getProgressColor = () => {
      if (uploadProgress.stage === 'error') return 'bg-red-500';
      if (uploadProgress.stage === 'completed') return 'bg-green-500';
      return 'bg-blue-500';
    };

    const getStageIcon = () => {
      switch (uploadProgress.stage) {
        case 'uploading': return '📤';
        case 'parsing': return '📄';
        case 'analyzing': return '🤖';
        case 'mapping': return '🔗';
        case 'completed': return '✅';
        case 'error': return '❌';
        default: return '⏳';
      }
    };

    return (
      <div className="mt-4 p-4 bg-white rounded-xl border border-gray-200">
        <div className="flex items-center space-x-3 mb-3">
          <span className="text-2xl">{getStageIcon()}</span>
          <div className="flex-1">
            <div className="text-sm font-medium text-gray-900">{uploadProgress.message}</div>
            {uploadProgress.error && (
              <div className="text-sm text-red-600 mt-1">{uploadProgress.error}</div>
            )}
          </div>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${uploadProgress.progress}%` }}
          />
        </div>

        <div className="text-xs text-gray-500 mt-1">
          {uploadProgress.progress}% complete
        </div>
      </div>
    );
  };

  return (
    <div className={`w-full ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept=".docx"
        onChange={handleFileInputChange}
        className="hidden"
      />

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200
          ${isDragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-300 hover:bg-blue-50'
          }
          ${(isUploading || isDocumentProcessing) ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
        `}
        onClick={!(isUploading || isDocumentProcessing) ? handleBrowseClick : undefined}
      >
        <div className="flex flex-col items-center space-y-4">
          <div className="text-6xl">
            {isUploading ? '⏳' : isDragOver ? '📁' : '📄'}
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              {isUploading
                ? 'Processing Document...'
                : isDragOver
                ? 'Drop your document here'
                : 'Upload Research Brief'
              }
            </h3>

            {!isUploading && (
              <p className="text-gray-500 text-sm">
                Drag and drop your DOCX file here, or{' '}
                <span className="text-blue-600 font-medium">click to browse</span>
              </p>
            )}
          </div>

          {!(isUploading || isDocumentProcessing) && (
            <div className="bg-white rounded-lg p-4 border border-gray-200 text-sm text-gray-600">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-green-600">✓</span>
                <span>Supports Microsoft Word (.docx) files</span>
              </div>
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-green-600">✓</span>
                <span>Maximum file size: 10MB</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">🤖</span>
                <span>AI-powered extraction of objectives, constraints, and requirements</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <ProgressIndicator />
    </div>
  );
};