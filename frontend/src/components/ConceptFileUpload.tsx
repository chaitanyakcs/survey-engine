import React, { useState, useRef, useCallback } from 'react';
import { ConceptFile } from '../types';
import { TrashIcon, PhotoIcon, DocumentIcon } from '@heroicons/react/24/outline';

interface ConceptFileUploadProps {
  rfqId: string;
  conceptStimulusId?: string;
  onFileUploaded: (file: ConceptFile) => void;
  onFileDeleted: (fileId: string) => void;
  existingFiles?: ConceptFile[];
  maxFiles?: number;
  className?: string;
}

const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
const ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const ALLOWED_TYPES = [...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOCUMENT_TYPES];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const ConceptFileUpload: React.FC<ConceptFileUploadProps> = ({
  rfqId,
  conceptStimulusId,
  onFileUploaded,
  onFileDeleted,
  existingFiles = [],
  maxFiles = 10,
  className = ''
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (!file.type || !ALLOWED_TYPES.includes(file.type)) {
      return 'File type not allowed. Allowed types: Images (PNG, JPG, GIF, WebP) and Documents (PDF, DOCX)';
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB`;
    }

    // Check if file is empty
    if (file.size === 0) {
      return 'File appears to be empty';
    }

    // Check max files limit
    if (existingFiles.length >= maxFiles) {
      return `Maximum ${maxFiles} files allowed`;
    }

    return null;
  }, [existingFiles.length, maxFiles]);

  const uploadFile = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadError(validationError);
      setTimeout(() => setUploadError(null), 5000);
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('rfq_id', rfqId);
      if (conceptStimulusId) {
        formData.append('concept_stimulus_id', conceptStimulusId);
      }
      formData.append('display_order', existingFiles.length.toString());

      const response = await fetch('/api/v1/rfq/concept/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const result: ConceptFile = await response.json();
      
      // Construct file URL for display
      result.file_url = `/api/v1/rfq/concept/${result.id}`;
      
      // Show success feedback
      setUploadError(null);
      setUploadSuccess(`File "${result.original_filename || result.filename}" uploaded successfully!`);
      setTimeout(() => setUploadSuccess(null), 3000);
      
      onFileUploaded(result);
    } catch (error: any) {
      setUploadError(error.message || 'Failed to upload file');
      setTimeout(() => setUploadError(null), 5000);
    } finally {
      setIsUploading(false);
    }
  }, [rfqId, conceptStimulusId, existingFiles.length, onFileUploaded, validateFile]);

  const deleteFile = async (fileId: string) => {
    try {
      const response = await fetch(`/api/v1/rfq/concept/${fileId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete file');
      }

      onFileDeleted(fileId);
    } catch (error: any) {
      setUploadError(error.message || 'Failed to delete file');
      setTimeout(() => setUploadError(null), 5000);
    }
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    Array.from(files).forEach(file => {
      uploadFile(file);
    });
  }, [uploadFile]);

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

  const isImage = (contentType: string) => ALLOWED_IMAGE_TYPES.includes(contentType);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className={className}>
      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-6 text-center transition-colors
          ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400 hover:bg-blue-50/50'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={!isUploading ? handleBrowseClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={ALLOWED_TYPES.join(',')}
          onChange={handleFileInputChange}
          multiple
          disabled={isUploading || existingFiles.length >= maxFiles}
        />

        {isUploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <p className="text-sm text-gray-600">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <PhotoIcon className="w-10 h-10 text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-700 mb-1">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-gray-500">
              Images (PNG, JPG, GIF, WebP) or Documents (PDF, DOCX) • Max 10MB
            </p>
            {existingFiles.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {existingFiles.length} / {maxFiles} files uploaded
              </p>
            )}
          </div>
        )}
      </div>

      {/* Success Message */}
      {uploadSuccess && (
        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700 flex items-center">
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          {uploadSuccess}
        </div>
      )}

      {/* Error Message */}
      {uploadError && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {uploadError}
        </div>
      )}

      {/* File List */}
      {existingFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Uploaded Files:</h4>
          {existingFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {isImage(file.content_type) ? (
                  <PhotoIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                ) : (
                  <DocumentIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.original_filename || file.filename}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.file_size)} • {file.content_type.split('/')[1].toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => deleteFile(file.id)}
                className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Delete file"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

