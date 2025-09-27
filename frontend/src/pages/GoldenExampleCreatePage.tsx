import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenExampleRequest } from '../types';
import { Sidebar } from '../components/Sidebar';
import { IntelligentFieldExtractor } from '../components/IntelligentFieldExtractor';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export const GoldenExampleCreatePage: React.FC = () => {
  const { createGoldenExample, toasts, removeToast } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const { mainContentClasses } = useSidebarLayout();
  const [formData, setFormData] = useState<GoldenExampleRequest>({
    rfq_text: '',
    survey_json: { survey_id: '', title: '', description: '', estimated_time: 10, confidence_score: 0.8, methodologies: [], golden_examples: [], questions: [], metadata: { target_responses: 0, methodology: [] } },
    methodology_tags: [],
    industry_category: '',
    research_goal: '',
    quality_score: 0.8
  });
  
  // Document parsing states
  const [isParsingDocument, setIsParsingDocument] = useState(false);
  const [parseError, setParseError] = useState<string>('');
  const [showJsonPreview, setShowJsonPreview] = useState(false);
  const [extractedText, setExtractedText] = useState<string>('');
  const [inputMode, setInputMode] = useState<'upload' | 'manual'>('upload');
  const [rfqInputMode, setRfqInputMode] = useState<'text' | 'upload'>('text');
  const [isUploadingRfq, setIsUploadingRfq] = useState(false);
  const [rfqUploadStatus, setRfqUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [rfqUploadMessage, setRfqUploadMessage] = useState('');
  const [autoGenerateRfq, setAutoGenerateRfq] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastUploadedFile, setLastUploadedFile] = useState<File | null>(null);
  
  // Intelligent field extraction states
  const [showFieldExtractor, setShowFieldExtractor] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState<any>(null);

  // Handle field extraction results
  const handleFieldsExtracted = (fields: any) => {
    console.log('🎯 [Golden Create] Fields extracted:', fields);
    setFormData(prev => ({
      ...prev,
      methodology_tags: fields.methodology_tags || [],
      industry_category: fields.industry_category || '',
      research_goal: fields.research_goal || '',
      quality_score: fields.quality_score || 0.8
    }));
    
    // Update title if suggested
    if (fields.suggested_title) {
      setFormData(prev => ({
        ...prev,
        survey_json: {
          ...prev.survey_json,
          title: fields.suggested_title
        }
      }));
    }
  };

  // Handle extraction progress updates
  const handleProgressUpdate = (progress: any) => {
    console.log('📊 [Golden Create] Progress update:', progress);
    setExtractionProgress(progress);
  };

  // Show field extractor when Survey is available and either RFQ is provided or auto-generate is enabled
  useEffect(() => {
    const hasRfq = Boolean(formData.rfq_text && formData.rfq_text.trim().length > 0);
    const hasSurvey = Boolean(formData.survey_json &&
                     formData.survey_json.questions &&
                     formData.survey_json.questions.length > 0);

    setShowFieldExtractor(hasSurvey && (hasRfq || autoGenerateRfq));
  }, [formData.rfq_text, formData.survey_json, autoGenerateRfq]);

  const handleCreateExample = async () => {
    console.log('🏆 [Golden Create] Starting golden example creation');

    // Prepare the submission data
    const submissionData = {
      ...formData,
      // If auto-generate is enabled, send empty string to trigger generation
      rfq_text: autoGenerateRfq ? '' : formData.rfq_text
    };

    console.log('📝 [Golden Create] Form data:', {
      auto_generate_rfq: autoGenerateRfq,
      rfq_text_length: submissionData.rfq_text.length,
      survey_json_keys: Object.keys(formData.survey_json || {}),
      methodology_tags: formData.methodology_tags,
      industry_category: formData.industry_category,
      research_goal: formData.research_goal,
      quality_score: formData.quality_score
    });
    console.log('📊 [Golden Create] Survey JSON:', formData.survey_json);

    setIsLoading(true);
    try {
      console.log('🚀 [Golden Create] Calling createGoldenExample API');
      await createGoldenExample(submissionData);
      console.log('✅ [Golden Create] Golden example created successfully');
      // Navigate back to golden examples list
      window.location.href = '/golden-examples';
    } catch (error) {
      console.error('❌ [Golden Create] Failed to create golden example:', error);
      console.error('❌ [Golden Create] Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
    } finally {
      setIsLoading(false);
    }
  };


  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.docx')) {
      setParseError('Please select a DOCX file');
      return;
    }

    setLastUploadedFile(file);
    setRetryCount(0);
    await parseDocument(file);
  };

  const handleRfqFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    console.log('📄 [RFQ Upload] Starting RFQ text extraction');
    console.log('📁 [RFQ Upload] File details:', {
      name: file.name,
      size: file.size,
      type: file.type
    });

    if (!file.name.toLowerCase().endsWith('.docx')) {
      console.error('❌ [RFQ Upload] Invalid file type:', file.name);
      setRfqUploadStatus('error');
      setRfqUploadMessage('Please select a DOCX file');
      setTimeout(() => setRfqUploadStatus('idle'), 3000);
      return;
    }

    setIsUploadingRfq(true);
    setRfqUploadStatus('idle');
    setRfqUploadMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('🚀 [RFQ Upload] Sending request to /api/v1/utils/extract-text');
      const response = await fetch('/api/v1/utils/extract-text', {
        method: 'POST',
        body: formData
      });

      console.log('📡 [RFQ Upload] Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ [RFQ Upload] API error:', errorData);
        throw new Error(errorData.detail || 'Failed to extract text from document');
      }

      const result = await response.json();
      console.log('✅ [RFQ Upload] API response received:', {
        has_extracted_text: !!result.extracted_text,
        extracted_text_length: result.extracted_text?.length || 0,
        text_preview: result.extracted_text?.substring(0, 100) + '...'
      });
      
      // Update the RFQ text with the extracted text
      if (result.extracted_text) {
        console.log('💾 [RFQ Upload] Updating form data with extracted text');
        setFormData(prev => ({
          ...prev,
          rfq_text: result.extracted_text
        }));
        
        // Reset the file input
        event.target.value = '';
        
        // Show success message
        setRfqUploadStatus('success');
        setRfqUploadMessage('RFQ text successfully extracted from document!');
        console.log('✅ [RFQ Upload] RFQ text extraction completed successfully');
        
        // Clear success message after 5 seconds
        setTimeout(() => setRfqUploadStatus('idle'), 5000);
      } else {
        console.error('❌ [RFQ Upload] No text extracted from document');
        throw new Error('No text extracted from document');
      }

    } catch (error) {
      console.error('❌ [RFQ Upload] RFQ document upload failed:', error);
      console.error('❌ [RFQ Upload] Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      setRfqUploadStatus('error');
      setRfqUploadMessage(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Clear error message after 5 seconds
      setTimeout(() => setRfqUploadStatus('idle'), 5000);
    } finally {
      setIsUploadingRfq(false);
    }
  };

  const parseDocument = async (file: File) => {
    console.log('📄 [Document Parse] Starting document parsing for survey JSON');
    console.log('📁 [Document Parse] File details:', {
      name: file.name,
      size: file.size,
      type: file.type
    });
    
    setIsParsingDocument(true);
    setParseError('');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('🚀 [Document Parse] Sending request to /api/v1/golden-pairs/parse-document');
      const response = await fetch('/api/v1/golden-pairs/parse-document', {
        method: 'POST',
        body: formData,
      });
      
      console.log('📡 [Document Parse] Response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ [Document Parse] API error:', errorData);
        throw new Error(errorData.detail || 'Failed to parse document');
      }
      
      const result = await response.json();
      console.log('✅ [Document Parse] API response received:', {
        has_survey_json: !!result.survey_json,
        survey_json_type: typeof result.survey_json,
        survey_json_keys: result.survey_json ? Object.keys(result.survey_json) : 'No survey_json',
        has_extracted_text: !!result.extracted_text,
        extracted_text_length: result.extracted_text?.length || 0,
        confidence_score: result.confidence_score
      });
      
      setExtractedText(result.extracted_text);
      setShowJsonPreview(true);
      
      // Try to parse the survey JSON
      try {
        console.log('🔍 [Document Parse] Attempting to parse survey JSON');
        console.log('📊 [Document Parse] Raw survey_json:', result.survey_json);
        
        let surveyJson: any;
        if (typeof result.survey_json === 'string') {
          console.log('📝 [Document Parse] Survey JSON is a string, parsing...');
          surveyJson = JSON.parse(result.survey_json);
        } else if (typeof result.survey_json === 'object') {
          console.log('📦 [Document Parse] Survey JSON is already an object');
          surveyJson = result.survey_json;
        } else {
          console.error('❌ [Document Parse] Survey JSON is neither string nor object:', typeof result.survey_json);
          throw new Error('Invalid survey JSON format');
        }
        
        console.log('✅ [Document Parse] Survey JSON parsed successfully:', {
          keys: Object.keys(surveyJson),
          title: surveyJson.title,
          questions_count: surveyJson.questions?.length || 0,
          methodologies: surveyJson.methodologies
        });
        
        setFormData(prev => ({ ...prev, survey_json: surveyJson }));
        console.log('💾 [Document Parse] Survey JSON saved to form data');
        
      } catch (jsonError) {
        console.error('❌ [Document Parse] Failed to parse survey JSON:', jsonError);
        console.error('❌ [Document Parse] JSON error details:', {
          message: jsonError instanceof Error ? jsonError.message : 'Unknown error',
          survey_json: result.survey_json
        });
        setParseError('Failed to parse survey JSON from document');
      }
      
    } catch (error) {
      console.error('❌ [Document Parse] Document parsing failed:', error);
      console.error('❌ [Document Parse] Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      setParseError(error instanceof Error ? error.message : 'Failed to parse document');
      
      if (retryCount < 3) {
        console.log(`🔄 [Document Parse] Retrying in 2 seconds (attempt ${retryCount + 1}/3)`);
        setRetryCount(prev => prev + 1);
        setTimeout(() => {
          if (lastUploadedFile) {
            parseDocument(lastUploadedFile);
          }
        }, 2000);
      } else {
        console.error('❌ [Document Parse] Max retries reached, giving up');
      }
    } finally {
      setIsParsingDocument(false);
    }
  };

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => {
    if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'survey') {
      window.location.href = '/';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      <div className="flex">
        {/* Sidebar */}
        <Sidebar currentView="golden-examples" onViewChange={handleViewChange} />
        
        {/* Main Content */}
        <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>
          <main className="py-8 px-6">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => window.location.href = '/golden-examples'}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <ArrowLeftIcon className="h-6 w-6" />
                  </button>
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                        Create Reference Example
                      </h1>
                      <p className="text-gray-600">Add a reference example for survey generation</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Create Form */}
            <div className="bg-white rounded-2xl p-8 w-full border border-gray-200 shadow-lg">
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-medium text-gray-700">RFQ Text</label>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="auto-generate-rfq"
                          checked={autoGenerateRfq}
                          onChange={(e) => {
                            setAutoGenerateRfq(e.target.checked);
                            if (e.target.checked) {
                              setFormData({ ...formData, rfq_text: '' });
                            }
                          }}
                          className="h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded"
                        />
                        <label htmlFor="auto-generate-rfq" className="text-xs text-gray-600">
                          Auto-generate from survey
                        </label>
                      </div>
                      {!autoGenerateRfq && (
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={() => setRfqInputMode('text')}
                            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all duration-200 ${
                              rfqInputMode === 'text'
                                ? 'bg-yellow-600 text-white shadow-sm'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            Text Input
                          </button>
                          <button
                            type="button"
                            onClick={() => setRfqInputMode('upload')}
                            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all duration-200 ${
                              rfqInputMode === 'upload'
                                ? 'bg-yellow-600 text-white shadow-sm'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            Upload DOCX
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

{!autoGenerateRfq ? (
                    rfqInputMode === 'text' ? (
                      <textarea
                        value={formData.rfq_text}
                        onChange={(e) => setFormData({ ...formData, rfq_text: e.target.value })}
                        className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                        rows={3}
                        placeholder="Enter the RFQ description..."
                      />
                    ) : (
                      <div className="space-y-3">
                        <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-yellow-400 hover:bg-yellow-50/30 transition-all duration-200">
                          <input
                            type="file"
                            accept=".docx"
                            onChange={handleRfqFileUpload}
                            className="hidden"
                            id="rfq-docx-upload"
                            disabled={isUploadingRfq}
                          />
                          <label htmlFor="rfq-docx-upload" className="cursor-pointer">
                            {isUploadingRfq ? (
                              <div className="flex flex-col items-center">
                                <div className="relative mb-3">
                                  <div className="w-12 h-12 border-4 border-yellow-200 rounded-full"></div>
                                  <div className="absolute top-0 left-0 w-12 h-12 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
                                </div>
                                <div className="text-center">
                                  <p className="text-sm font-medium text-gray-900">Processing document...</p>
                                  <p className="text-xs text-gray-500">Please wait while we extract the RFQ text</p>
                                </div>
                              </div>
                            ) : (
                              <div className="flex flex-col items-center">
                                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mb-3">
                                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                  </svg>
                                </div>
                                <div className="text-center">
                                  <p className="text-sm font-medium text-gray-900">Upload DOCX file</p>
                                  <p className="text-xs text-gray-500">Click to browse or drag and drop your DOCX file here</p>
                                </div>
                              </div>
                            )}
                          </label>
                        </div>

                        {/* RFQ Upload Status Messages */}
                        {rfqUploadStatus !== 'idle' && (
                          <div className={`p-3 rounded-lg ${
                            rfqUploadStatus === 'success'
                              ? 'bg-green-50 border border-green-200'
                              : 'bg-red-50 border border-red-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                                rfqUploadStatus === 'success' ? 'bg-green-500' : 'bg-red-500'
                              }`}>
                                {rfqUploadStatus === 'success' ? (
                                  <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                ) : (
                                  <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                )}
                              </div>
                              <p className={`text-xs font-medium ${
                                rfqUploadStatus === 'success' ? 'text-green-800' : 'text-red-800'
                              }`}>
                                {rfqUploadMessage}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  ) : (
                    <div className="p-6 bg-blue-50 border border-blue-200 rounded-xl">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-blue-900">RFQ will be auto-generated</p>
                          <p className="text-xs text-blue-700">An RFQ will be automatically created from your survey content and metadata</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Survey JSON Template</label>
                  
                  <div className="mb-4">
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={() => setInputMode('upload')}
                        className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 ${
                          inputMode === 'upload' 
                            ? 'bg-yellow-600 text-white shadow-lg' 
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Upload DOCX
                      </button>
                      <button
                        type="button"
                        onClick={() => setInputMode('manual')}
                        className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 ${
                          inputMode === 'manual' 
                            ? 'bg-yellow-600 text-white shadow-lg' 
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Manual Entry
                      </button>
                    </div>
                  </div>

                  {inputMode === 'upload' ? (
                    <div className="space-y-4">
                      <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-yellow-400 hover:bg-yellow-50/30 transition-all duration-200">
                        <input
                          type="file"
                          accept=".docx"
                          onChange={handleFileUpload}
                          className="hidden"
                          id="docx-upload"
                          disabled={isParsingDocument}
                        />
                        <label htmlFor="docx-upload" className="cursor-pointer">
                          {isParsingDocument ? (
                            <div className="flex flex-col items-center">
                              <div className="relative mb-4">
                                <div className="w-16 h-16 border-4 border-yellow-200 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-16 h-16 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
                              </div>
                              <div className="text-center">
                                <p className="text-sm font-medium text-gray-700 mb-1">Processing Document</p>
                                <p className="text-xs text-gray-500">Converting your DOCX to survey JSON...</p>
                                {retryCount > 0 && (
                                  <p className="text-xs text-yellow-600 mt-1">Retry attempt {retryCount + 1}</p>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-col items-center">
                              <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                              </svg>
                              <p className="text-sm text-gray-600 mb-1">Drop a DOCX file here or click to browse</p>
                              <p className="text-xs text-gray-500">Survey documents will be converted to JSON automatically</p>
                            </div>
                          )}
                        </label>
                      </div>

                      {parseError && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                          <div className="flex">
                            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div className="ml-3">
                              <h3 className="text-sm font-medium text-red-800">Parse Error</h3>
                              <p className="text-sm text-red-700 mt-1">{parseError}</p>
                              {retryCount < 3 && (
                                <button
                                  onClick={() => lastUploadedFile && parseDocument(lastUploadedFile)}
                                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                                >
                                  Retry parsing
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {showJsonPreview && extractedText && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-medium text-gray-700">Extracted Text Preview</label>
                            <button
                              onClick={() => setShowJsonPreview(false)}
                              className="text-sm text-gray-500 hover:text-gray-700"
                            >
                              Hide
                            </button>
                          </div>
                          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-40 overflow-y-auto">
                            <pre className="text-xs text-gray-600 whitespace-pre-wrap">{extractedText}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <textarea
                        value={JSON.stringify(formData.survey_json, null, 2)}
                        onChange={(e) => {
                          try {
                            const parsed = JSON.parse(e.target.value);
                            setFormData({ ...formData, survey_json: parsed });
                          } catch (error) {
                            // Invalid JSON, but let user continue typing
                          }
                        }}
                        className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm font-mono focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                        rows={12}
                        placeholder="Enter survey JSON manually..."
                      />
                      <p className="text-xs text-gray-500">Enter valid JSON for the survey structure</p>
                    </div>
                  )}
                </div>

                {/* Intelligent Field Extraction */}
                {showFieldExtractor && (
                  <div className="mb-8">
                    <IntelligentFieldExtractor
                      rfqText={formData.rfq_text}
                      surveyJson={formData.survey_json}
                      onFieldsExtracted={handleFieldsExtracted}
                      onProgressUpdate={handleProgressUpdate}
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Industry Category</label>
                    <select
                      value={formData.industry_category}
                      onChange={(e) => setFormData({ ...formData, industry_category: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                    >
                      <option value="">Select Industry</option>
                      <option value="Consumer Electronics">Consumer Electronics</option>
                      <option value="B2B Technology">B2B Technology</option>
                      <option value="Automotive">Automotive</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Financial Services">Financial Services</option>
                      <option value="Retail">Retail</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Research Goal</label>
                    <select
                      value={formData.research_goal}
                      onChange={(e) => setFormData({ ...formData, research_goal: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                    >
                      <option value="">Select Research Goal</option>
                      <option value="pricing_research">Pricing Research</option>
                      <option value="product_development">Product Development</option>
                      <option value="market_segmentation">Market Segmentation</option>
                      <option value="brand_positioning">Brand Positioning</option>
                      <option value="customer_satisfaction">Customer Satisfaction</option>
                      <option value="competitive_analysis">Competitive Analysis</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Methodology Tags</label>
                  <div className="flex flex-wrap gap-2">
                    {['VW', 'GG', 'Conjoint', 'MaxDiff', 'Choice', 'TURF'].map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => {
                          const tags = formData.methodology_tags;
                          if (tags.includes(tag)) {
                            setFormData({ ...formData, methodology_tags: tags.filter(t => t !== tag) });
                          } else {
                            setFormData({ ...formData, methodology_tags: [...tags, tag] });
                          }
                        }}
                        className={`px-3 py-1 text-sm rounded-full transition-all duration-200 ${
                          formData.methodology_tags.includes(tag)
                            ? 'bg-yellow-600 text-white shadow-lg'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => window.location.href = '/golden-examples'}
                    className="px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200 font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateExample}
                    disabled={isLoading}
                    className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    {isLoading ? 'Saving...' : 'Create Example'}
                  </button>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
};
