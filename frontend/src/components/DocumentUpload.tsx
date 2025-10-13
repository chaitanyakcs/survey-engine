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

    try {
      // Set initial progress
      setUploadProgress({
        stage: 'uploading',
        progress: 10,
        message: 'Starting document upload...'
      });

      // Generate session ID for WebSocket tracking
      const sessionId = `rfq-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      // Connect to RFQ parsing WebSocket for real progress updates
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const backendHost = process.env.NODE_ENV === 'production' 
        ? window.location.host 
        : 'localhost:8000';
      const wsUrl = `${protocol}//${backendHost}/ws/rfq-parsing/${sessionId}`;
      console.log('🔌 [Document Upload] Connecting to WebSocket for real progress:', wsUrl);

      let websocket: WebSocket | null = null;

      try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
          console.log('🔌 [Document Upload] WebSocket connected successfully');
        };

        websocket.onmessage = (event) => {
          try {
            const progressData = JSON.parse(event.data);
            console.log('📥 [Document Upload] Received progress:', progressData);

            if (progressData.type === 'progress') {
              setUploadProgress({
                stage: progressData.stage,
                progress: progressData.progress,
                message: progressData.message,
                details: progressData.details,
                estimated_time: progressData.estimated_time,
                content_preview: progressData.content_preview
              });
            } else if (progressData.type === 'completed') {
              console.log('✅ [Document Upload] Received completion message from WebSocket');
              setUploadProgress({
                stage: 'completed',
                progress: 100,
                message: progressData.message || 'Document analysis completed!'
              });
            } else if (progressData.type === 'error') {
              console.log('❌ [Document Upload] Received error message from WebSocket');
              setUploadProgress({
                stage: 'error',
                progress: 0,
                message: progressData.message || 'Processing failed',
                error: progressData.error
              });
            }
          } catch (error) {
            console.warn('⚠️ [Document Upload] Failed to parse WebSocket message:', error);
          }
        };

        websocket.onerror = (error) => {
          console.error('❌ [Document Upload] WebSocket error:', error);
        };

        websocket.onclose = () => {
          console.log('🔌 [Document Upload] WebSocket disconnected');
        };

      } catch (error) {
        console.warn('⚠️ [Document Upload] WebSocket connection failed, using fallback progress');
      }

      // Start the actual upload with session ID for backend tracking
      const result: DocumentAnalysisResponse = await storeUploadDocument(file, sessionId);

      // Close WebSocket connection
      if (websocket) {
        websocket.close();
      }

      // Final completion
      setUploadProgress({
        stage: 'completed',
        progress: 100,
        message: 'Document analysis completed successfully!'
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
      }, 3000);

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
      }, 5000);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    uploadDocument(file);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // Enhanced progress indicator component
  const ProgressIndicator = () => {
    if (!uploadProgress) return null;

    const getProgressColor = () => {
      if (uploadProgress.stage === 'error') return 'from-red-500 to-red-600';
      if (uploadProgress.stage === 'completed') return 'from-green-500 to-emerald-500';
      return 'from-yellow-500 to-amber-500';
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

    const getStageDescription = () => {
      switch (uploadProgress.stage) {
        case 'uploading': return 'Uploading your document to our secure servers...';
        case 'parsing': return 'Extracting text and structure from your document...';
        case 'analyzing': return 'Using advanced AI to understand and analyze the content...';
        case 'mapping': return 'Mapping discovered fields to survey requirements...';
        case 'completed': return 'Document analysis completed successfully!';
        case 'error': return 'An error occurred during processing.';
        default: return 'Processing your document...';
      }
    };

    const getEstimatedTime = () => {
      switch (uploadProgress.stage) {
        case 'uploading': return '~5 seconds';
        case 'parsing': return '~10 seconds';
        case 'analyzing': return '~20-30 seconds';
        case 'mapping': return '~5 seconds';
        default: return '';
      }
    };

    return (
      <div className="mt-6 p-6 bg-gradient-to-br from-white to-gray-50 rounded-2xl border border-gray-200 shadow-lg">
        {/* Header with icon and title */}
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-amber-100 rounded-xl flex items-center justify-center">
              <span className="text-2xl">{getStageIcon()}</span>
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{uploadProgress.message}</h3>
            <p className="text-sm text-gray-600 mt-1">{getStageDescription()}</p>
            
            {/* Enhanced details display */}
            {uploadProgress.details && (
              <p className="text-xs text-blue-600 mt-1 font-medium">{uploadProgress.details}</p>
            )}
            
            {/* Content preview */}
            {uploadProgress.content_preview && (
              <div className="mt-2 p-2 bg-gray-50 rounded-lg border-l-4 border-blue-400">
                <p className="text-xs text-gray-500 mb-1">Content Preview:</p>
                <p className="text-xs text-gray-700 italic">{uploadProgress.content_preview}</p>
              </div>
            )}
            
            {/* Estimated time */}
            {(uploadProgress.estimated_time || getEstimatedTime()) && (
              <p className="text-xs text-gray-500 mt-1">
                Estimated time: {uploadProgress.estimated_time ? `${uploadProgress.estimated_time}s remaining` : getEstimatedTime()}
              </p>
            )}
          </div>
        </div>

        {/* Progress bar with animation */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm font-bold text-gray-900">{uploadProgress.progress}%</span>
          </div>
          
          <div className="relative w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`absolute top-0 left-0 h-3 bg-gradient-to-r ${getProgressColor()} rounded-full transition-all duration-500 ease-out`}
              style={{ width: `${uploadProgress.progress}%` }}
            />
            {/* Animated shimmer effect */}
            {uploadProgress.stage !== 'completed' && uploadProgress.stage !== 'error' && (
              <div className="absolute top-0 left-0 h-3 w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse" />
            )}
          </div>
        </div>

        {/* Stage indicators */}
        <div className="flex justify-between items-center text-xs text-gray-500">
          <div className={`flex items-center space-x-1 ${uploadProgress.stage === 'uploading' ? 'text-yellow-600 font-medium' : ''}`}>
            <span>📤</span>
            <span>Upload</span>
          </div>
          <div className={`flex items-center space-x-1 ${uploadProgress.stage === 'parsing' ? 'text-yellow-600 font-medium' : ''}`}>
            <span>📄</span>
            <span>Parse</span>
          </div>
          <div className={`flex items-center space-x-1 ${uploadProgress.stage === 'analyzing' ? 'text-yellow-600 font-medium' : ''}`}>
            <span>🤖</span>
            <span>Analyze</span>
          </div>
          <div className={`flex items-center space-x-1 ${uploadProgress.stage === 'mapping' ? 'text-yellow-600 font-medium' : ''}`}>
            <span>🔗</span>
            <span>Map</span>
          </div>
          <div className={`flex items-center space-x-1 ${uploadProgress.stage === 'completed' ? 'text-green-600 font-medium' : ''}`}>
            <span>✅</span>
            <span>Complete</span>
          </div>
        </div>

        {/* Error display */}
        {uploadProgress.error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">❌</span>
              <span className="text-sm text-red-700">{uploadProgress.error}</span>
            </div>
          </div>
        )}

        {/* Success message */}
        {uploadProgress.stage === 'completed' && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <span className="text-green-500">🎉</span>
              <span className="text-sm text-green-700">Document processed successfully! Your form has been auto-filled.</span>
            </div>
          </div>
        )}
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
          relative border-2 border-dashed rounded-2xl text-center transition-all duration-200
          ${isDragOver
            ? 'border-yellow-400 bg-yellow-50'
            : 'border-gray-300 bg-gray-50 hover:border-yellow-300 hover:bg-yellow-50'
          }
          ${(isUploading || isDocumentProcessing) ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
          ${(isUploading || isDocumentProcessing) ? 'p-4' : 'p-8'}
        `}
        onClick={!(isUploading || isDocumentProcessing) ? handleBrowseClick : undefined}
      >
        <div className={`flex flex-col items-center space-y-4 ${(isUploading || isDocumentProcessing) ? 'space-y-2' : ''}`}>
          <div className={`${(isUploading || isDocumentProcessing) ? 'text-3xl' : 'text-6xl'}`}>
            {isDragOver ? '📁' : '📄'}
          </div>

          <div className={`${(isUploading || isDocumentProcessing) ? 'text-center' : ''}`}>
            <h3 className={`font-semibold text-gray-700 mb-2 ${(isUploading || isDocumentProcessing) ? 'text-sm' : 'text-xl'}`}>
              {isUploading
                ? 'Processing Document...'
                : isDragOver
                ? 'Drop your document here'
                : 'Upload Research Brief'
              }
            </h3>

            {!isUploading && !isDocumentProcessing && (
              <p className="text-gray-500 text-sm">
                Drag and drop your DOCX file here, or{' '}
                <span className="text-yellow-600 font-medium">click to browse</span>
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
                <span className="text-yellow-600">🤖</span>
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