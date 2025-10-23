import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenExampleRequest, DocumentParseResponse } from '../types';
import { Sidebar } from '../components/Sidebar';
import { IntelligentFieldExtractor } from '../components/IntelligentFieldExtractor';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import MethodologyTagsInput from '../components/MethodologyTagsInput';

export const GoldenExampleCreatePage: React.FC = () => {
  const { 
    createGoldenExample, 
    toasts, 
    removeToast,
    persistGoldenExampleState,
    restoreGoldenExampleState,
    clearGoldenExampleState,
    addToast
  } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const { mainContentClasses } = useSidebarLayout();
  
  // Add session ID state
  const [sessionId] = useState(() => {
    return localStorage.getItem('golden_example_session_id') || 
           `golden-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  });
  
  const [formData, setFormData] = useState<GoldenExampleRequest>({
    rfq_text: '',
    survey_json: { survey_id: '', title: '', description: '', estimated_time: 10, confidence_score: 0.8, methodologies: [], golden_examples: [], questions: [], metadata: { target_responses: 0, methodology: [] } },
    methodology_tags: [],
    industry_category: '',
    research_goal: '',
    quality_score: undefined
  });
  
  // Document parsing states
  const [isParsingDocument, setIsParsingDocument] = useState(false);
  const [parseError, setParseError] = useState<string>('');
  const [showJsonPreview, setShowJsonPreview] = useState(false);
  const [extractedText, setExtractedText] = useState<string>('');
  const [rfqInputMode, setRfqInputMode] = useState<'text' | 'upload'>('text');
  const [isUploadingRfq, setIsUploadingRfq] = useState(false);
  const [extractedMethodologyTags, setExtractedMethodologyTags] = useState<string[]>([]);
  const [rfqUploadStatus, setRfqUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [rfqUploadMessage, setRfqUploadMessage] = useState('');
  const [autoGenerateRfq, setAutoGenerateRfq] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastUploadedFile, setLastUploadedFile] = useState<File | null>(null);
  
  // Intelligent field extraction states
  const [showFieldExtractor, setShowFieldExtractor] = useState(false);

  // Restore state on mount
  useEffect(() => {
    const restoreState = async () => {
      console.log('🔄 [GoldenExampleCreatePage] Attempting to restore state...');
      console.log('🔄 [GoldenExampleCreatePage] Session ID:', sessionId);
      
      const restored = await restoreGoldenExampleState();
      console.log('🔄 [GoldenExampleCreatePage] Restore result:', restored);
      
      // Get the current state after restoration
      const currentState = useAppStore.getState().goldenExampleState;
      console.log('🔄 [GoldenExampleCreatePage] Golden example state:', currentState);
      
      if (restored && currentState) {
        console.log('✅ [GoldenExampleCreatePage] Restoring form data:', currentState.formData);
        setFormData(currentState.formData);
        setAutoGenerateRfq(currentState.autoGenerateRfq);
        setRfqInputMode(currentState.rfqInputMode);
        // Show toast notification with specific details about what was restored
        const hasRfq = currentState.formData?.rfq_text && currentState.formData.rfq_text.trim().length > 0;
        const hasSurvey = currentState.formData?.survey_json?.questions && currentState.formData.survey_json.questions.length > 0;
        const hasMetadata = currentState.formData?.industry_category || currentState.formData?.research_goal || (currentState.formData?.methodology_tags && currentState.formData.methodology_tags.length > 0);
        
        let restoredItems = [];
        if (hasRfq) restoredItems.push('RFQ text');
        if (hasSurvey) restoredItems.push('survey template');
        if (hasMetadata) restoredItems.push('metadata fields');
        
        const restoredText = restoredItems.length > 0 
          ? `Restored: ${restoredItems.join(', ')}`
          : 'Previous form data restored';
        
        addToast({
          type: 'info',
          title: 'Form Restored',
          message: restoredText,
          duration: 4000
        });
      } else {
        console.log('⚠️ [GoldenExampleCreatePage] No state to restore');
      }
    };
    restoreState();
  }, [addToast, restoreGoldenExampleState, sessionId]);

  // Auto-save state on changes (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      const hasContent = (formData.survey_json.questions?.length ?? 0) > 0 || formData.rfq_text;
      console.log('💾 [GoldenExampleCreatePage] Auto-save check:', {
        hasContent,
        questionsLength: formData.survey_json.questions?.length ?? 0,
        rfqTextLength: formData.rfq_text.length,
        sessionId
      });
      
      if (hasContent) {
        console.log('💾 [GoldenExampleCreatePage] Auto-saving state...');
        persistGoldenExampleState(sessionId, {
          formData,
          autoGenerateRfq,
          rfqInputMode,
          timestamp: Date.now()
        });
      }
    }, 1000); // Debounce 1 second
    
    return () => clearTimeout(timeoutId);
  }, [formData, autoGenerateRfq, rfqInputMode, sessionId, persistGoldenExampleState]);

  // Handle field extraction results
  const handleFieldsExtracted = (fields: any) => {
    console.log('🎯 [Golden Create] Fields extracted:', fields);
    setFormData(prev => ({
      ...prev,
      methodology_tags: fields.methodology_tags || [],
      industry_category: fields.industry_category || '',
      research_goal: fields.research_goal || '',
      quality_score: fields.quality_score || undefined
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
  };

  // Show field extractor when Survey is available and either RFQ is provided or auto-generate is enabled
  useEffect(() => {
    const hasRfq = Boolean(formData.rfq_text && formData.rfq_text.trim().length > 0);
    const hasSurvey = Boolean(formData.survey_json &&
                     formData.survey_json.questions &&
                     formData.survey_json.questions.length > 0);

    setShowFieldExtractor(hasSurvey && (hasRfq || autoGenerateRfq));
  }, [formData.rfq_text, formData.survey_json, autoGenerateRfq]);

  // Auto-enable RFQ generation when survey is uploaded and no RFQ text is provided
  useEffect(() => {
    const hasSurvey = Boolean(formData.survey_json &&
                     formData.survey_json.questions &&
                     formData.survey_json.questions.length > 0);
    const hasRfq = Boolean(formData.rfq_text && formData.rfq_text.trim().length > 0);
    
    // If we have a survey but no RFQ text, auto-enable RFQ generation
    if (hasSurvey && !hasRfq && !autoGenerateRfq) {
      console.log('🤖 [Golden Create] Auto-enabling RFQ generation since survey is available but no RFQ text provided');
      setAutoGenerateRfq(true);
    }
  }, [formData.survey_json, formData.rfq_text, autoGenerateRfq]);

  // Auto-enable RFQ generation when survey is uploaded (even if user unchecks it)
  useEffect(() => {
    const hasSurvey = Boolean(formData.survey_json &&
                     formData.survey_json.questions &&
                     formData.survey_json.questions.length > 0);
    
    // Always enable auto-generation when a survey is uploaded
    if (hasSurvey && !autoGenerateRfq) {
      console.log('🤖 [Golden Create] Auto-enabling RFQ generation for uploaded survey');
      setAutoGenerateRfq(true);
    }
  }, [formData.survey_json, autoGenerateRfq]);

  // Auto-trigger field extraction when survey is uploaded and no fields are populated
  useEffect(() => {
    const hasSurvey = Boolean(formData.survey_json &&
                     formData.survey_json.questions &&
                     formData.survey_json.questions.length > 0);
    const hasFields = formData.methodology_tags.length > 0 || 
                     formData.industry_category || 
                     formData.research_goal;
    
    // If we have a survey but no extracted fields, trigger field extraction
    if (hasSurvey && !hasFields) {
      console.log('🎯 [Golden Create] Survey uploaded but no fields extracted - triggering field extraction');
      // The IntelligentFieldExtractor will handle this automatically when it becomes visible
    }
  }, [formData.survey_json, formData.methodology_tags, formData.industry_category, formData.research_goal]);

  const handleCreateExample = async () => {
    console.log('🏆 [Golden Create] Starting golden example creation');

    // Prepare the submission data
    const submissionData = {
      ...formData,
      // If auto-generate is enabled, send empty string to trigger generation
      rfq_text: autoGenerateRfq ? '' : formData.rfq_text,
      // Include the auto-generate flag
      auto_generate_rfq: autoGenerateRfq
    };

    // Remove quality_score if it's null/undefined to avoid validation errors
    if (submissionData.quality_score === null || submissionData.quality_score === undefined) {
      delete submissionData.quality_score;
    }

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
      
      // Clear saved state after successful creation
      await clearGoldenExampleState(sessionId);
      
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
      
      const result: DocumentParseResponse = await response.json();
      console.log('✅ [Document Parse] API response received:', {
        has_survey_json: !!result.survey_json,
        survey_json_type: typeof result.survey_json,
        survey_json_keys: result.survey_json ? Object.keys(result.survey_json) : 'No survey_json',
        has_extracted_text: !!result.extracted_text,
        extracted_text_length: result.extracted_text?.length || 0,
        confidence_score: result.confidence_score,
        product_category: result.product_category,
        research_goal: result.research_goal,
        methodologies: result.methodologies
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

        // Mapping functions for metadata fields
        const mapProductCategoryToIndustry = (productCategory: string): string => {
          const mapping: Record<string, string> = {
            'electronics': 'technology',
            'appliances': 'technology',
            'healthcare_technology': 'healthcare',
            'enterprise_software': 'technology',
            'automotive': 'automotive',
            'financial_services': 'finance',
            'hospitality': 'hospitality',
            'retail': 'retail',
            'education': 'education',
            'manufacturing': 'manufacturing',
            'other': 'other'
          };
          return mapping[productCategory?.toLowerCase()] || '';
        };

        const mapMethodologiesToTags = (methodologies: string[]): string[] => {
          if (!Array.isArray(methodologies)) return [];
          return methodologies.map(m => m.toLowerCase().replace(/_/g, ' '));
        };

        // Extract and map metadata fields
        const industryCategory = mapProductCategoryToIndustry(result.product_category || '');
        const researchGoal = result.research_goal || '';
        const methodologyTags = mapMethodologiesToTags(result.methodologies || []);

        console.log('🔧 [Document Parse] Metadata mapping:', {
          product_category: result.product_category,
          mapped_industry_category: industryCategory,
          research_goal: researchGoal,
          methodologies: result.methodologies,
          mapped_methodology_tags: methodologyTags
        });

        // Store extracted methodology tags for display
        setExtractedMethodologyTags(methodologyTags);

        setFormData(prev => ({
          ...prev,
          survey_json: surveyJson,
          industry_category: industryCategory,
          research_goal: researchGoal,
          methodology_tags: methodologyTags
        }));
        console.log('💾 [Document Parse] Survey JSON and metadata saved to form data');

        // Show success toast if metadata was auto-populated
        if (industryCategory || researchGoal || methodologyTags.length > 0) {
          addToast({
            type: 'success',
            title: 'Document Parsed Successfully',
            message: 'Metadata fields auto-populated!'
          });
        }
        
        // Trigger automatic field extraction after document parsing
        console.log('🤖 [Document Parse] Triggering automatic field extraction...');
        // The field extraction will be triggered by the useEffect that watches formData.survey_json
        
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

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
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
            <div className="bg-white rounded-2xl p-8 w-full border border-gray-200 shadow-lg relative">
              {isLoading && (
                <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-2xl flex items-center justify-center z-10">
                  <div className="text-center">
                    <div className="w-16 h-16 border-4 border-yellow-200 rounded-full mb-4 mx-auto">
                      <div className="w-16 h-16 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Creating Golden Example</h3>
                    <p className="text-sm text-gray-600">Please wait while we process your request...</p>
                  </div>
                </div>
              )}
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <label className="text-lg font-semibold text-gray-900">RFQ Text</label>
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
                          disabled={isLoading}
                          className="h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <label htmlFor="auto-generate-rfq" className="text-xs text-gray-600">
                          Auto-generate from survey
                        </label>
                        {formData.survey_json?.questions && formData.survey_json.questions.length > 0 && !formData.rfq_text && (
                          <span className="text-xs text-blue-600 ml-2">
                            (Recommended when survey is uploaded)
                          </span>
                        )}
                        {!autoGenerateRfq && !formData.rfq_text && (
                          <span className="text-xs text-gray-500 ml-2">
                            (Can create without RFQ)
                          </span>
                        )}
                      </div>
                      {!autoGenerateRfq && (
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={() => setRfqInputMode('upload')}
                            disabled={isLoading}
                            className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 ${
                              rfqInputMode === 'upload'
                                ? 'bg-yellow-600 text-white shadow-lg'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
                            }`}
                          >
                            Upload DOCX
                          </button>
                          <button
                            type="button"
                            onClick={() => setRfqInputMode('text')}
                            disabled={isLoading}
                            className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 ${
                              rfqInputMode === 'text'
                                ? 'bg-yellow-600 text-white shadow-lg'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
                            }`}
                          >
                            Manual Entry
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
                        disabled={isLoading}
                        className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50 placeholder-gray-400"
                        rows={4}
                        placeholder="Enter the RFQ description..."
                      />
                    ) : (
                      <div className="space-y-3">
                        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-yellow-400 hover:bg-yellow-50/30 transition-all duration-300 group">
                          <input
                            type="file"
                            accept=".docx"
                            onChange={handleRfqFileUpload}
                            className="hidden"
                            id="rfq-docx-upload"
                            disabled={isUploadingRfq || isLoading}
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
                                  <p className="text-xs text-gray-500">Processing your RFQ document...</p>
                                </div>
                              </div>
                            ) : (
                              <div className="flex flex-col items-center group-hover:scale-105 transition-transform duration-200">
                                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mb-3 group-hover:bg-yellow-200 transition-colors duration-200">
                                  <svg className="w-6 h-6 text-yellow-600 group-hover:text-yellow-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                  </svg>
                                </div>
                                <div className="text-center">
                                  <p className="text-sm font-medium text-gray-900 group-hover:text-gray-800">Drop a DOCX file here or click to browse</p>
                                  <p className="text-xs text-gray-500 group-hover:text-gray-600">RFQ documents will be processed automatically</p>
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
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <label className="text-lg font-semibold text-gray-900">Survey Document</label>
                  </div>

                  <div className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-yellow-400 hover:bg-yellow-50/30 transition-all duration-300 group">
                      <input
                        type="file"
                        accept=".docx"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="docx-upload"
                        disabled={isParsingDocument || isLoading}
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
                              <p className="text-xs text-gray-500">Processing your survey document...</p>
                              <p className="text-xs text-yellow-600 mt-2 bg-yellow-50 px-2 py-1 rounded">
                                ⏱️ This process typically takes 5-15 minutes
                              </p>
                              <p className="text-xs text-red-600 mt-1 bg-red-50 px-2 py-1 rounded">
                                ⚠️ Please do not navigate away from this page during processing
                              </p>
                              {retryCount > 0 && (
                                <p className="text-xs text-yellow-600 mt-1">Retry attempt {retryCount + 1}</p>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center group-hover:scale-105 transition-transform duration-200">
                            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-3 group-hover:bg-yellow-200 transition-colors duration-200">
                              <svg className="w-8 h-8 text-yellow-600 group-hover:text-yellow-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                              </svg>
                            </div>
                            <p className="text-sm font-medium text-gray-900 group-hover:text-gray-800 mb-1">Drop a DOCX file here or click to browse</p>
                            <p className="text-xs text-gray-500 group-hover:text-gray-600">Survey documents will be processed automatically</p>
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
                      <div className="space-y-4">
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

                        {/* Comment Metadata Display */}
                        {formData.survey_json?.comment_metadata && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <label className="text-sm font-medium text-gray-700">Comment Metadata</label>
                              <span className="text-xs text-gray-500">
                                {formData.survey_json.comment_metadata.total_comments} comments found
                              </span>
                            </div>
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                              <div className="space-y-2">
                                <div className="text-xs text-blue-800">
                                  <strong>Categories:</strong> {formData.survey_json.comment_metadata.comment_categories?.join(', ')}
                                </div>
                                <div className="text-xs text-blue-800">
                                  <strong>Extracted:</strong> {new Date(formData.survey_json.comment_metadata.extraction_timestamp).toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
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
                    <input
                      type="text"
                      value={formData.industry_category}
                      onChange={(e) => setFormData({ ...formData, industry_category: e.target.value })}
                      disabled={isLoading}
                      className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50 placeholder-gray-400"
                      placeholder="Enter industry category (e.g., Consumer Electronics, Healthcare, Finance)"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Research Goal</label>
                    <input
                      type="text"
                      value={formData.research_goal}
                      onChange={(e) => setFormData({ ...formData, research_goal: e.target.value })}
                      disabled={isLoading}
                      className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50 placeholder-gray-400"
                      placeholder="Enter research goal (e.g., Pricing Research, Product Development, Market Segmentation)"
                    />
                  </div>
                </div>

                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Methodology Tags
                    {extractedMethodologyTags.length > 0 && (
                      <span className="text-xs text-green-600 ml-2">
                        (Extracted from document)
                      </span>
                    )}
                  </label>
                  <MethodologyTagsInput
                    tags={formData.methodology_tags}
                    onTagsChange={(tags) => setFormData({ ...formData, methodology_tags: tags })}
                    placeholder="Add methodology tags..."
                    maxTags={20}
                    showDropdownMenu={true}
                    extractedTags={extractedMethodologyTags}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => window.location.href = '/golden-examples'}
                    disabled={isLoading}
                    className="px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateExample}
                    disabled={isLoading}
                    className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 hover:scale-105 active:scale-95 flex items-center space-x-2"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating Golden Example...</span>
                      </>
                    ) : (
                      'Create Example'
                    )}
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
