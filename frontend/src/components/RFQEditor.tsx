import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';

export const RFQEditor: React.FC = () => {
  const { rfqInput, setRFQInput, submitRFQ, workflow } = useAppStore();
  
  // Upload functionality state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [hasUploadedDocument, setHasUploadedDocument] = useState(false);

  // Set default values when component mounts
  React.useEffect(() => {
    if (!rfqInput.title && !rfqInput.description && !rfqInput.product_category && !rfqInput.target_segment && !rfqInput.research_goal) {
      setRFQInput({
        title: 'Market Research Study',
        description: 'We are conducting a comprehensive market research study to understand customer preferences, pricing sensitivity, and feature priorities for our new product. The research should include both quantitative and qualitative methodologies to provide actionable insights for our product development and go-to-market strategy.\n\nKey research objectives:\n- Understand customer willingness to pay and price sensitivity\n- Identify most important product features and their relative importance\n- Assess brand perception and competitive positioning\n- Evaluate market size and target segment characteristics\n\nPlease include methodologies such as Van Westendorp Price Sensitivity Meter, Conjoint Analysis, and MaxDiff for feature prioritization.',
        target_segment: 'General consumers',
        research_goal: 'pricing_research'
      });
    }
  }, [rfqInput, setRFQInput]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rfqInput.description.trim()) {
      await submitRFQ(rfqInput);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.docx')) {
      setUploadStatus('error');
      setUploadMessage('Please select a DOCX file');
      setTimeout(() => setUploadStatus('idle'), 3000);
      return;
    }

    setIsUploading(true);
    setUploadStatus('idle');
    setUploadMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/utils/extract-text', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to extract text from document');
      }

      const result = await response.json();
      
      // Update the RFQ input with the extracted text
      if (result.extracted_text) {
        const extractedText = result.extracted_text;
        
        // Use the extracted text as the description
        setRFQInput({
          ...rfqInput,
          description: extractedText
        });
        
        // Reset the file input
        event.target.value = '';
        
        // Show success message
        setUploadStatus('success');
        setUploadMessage('Text successfully extracted from document! Review and adjust the details below.');
        setHasUploadedDocument(true);
        
        // Clear success message after 5 seconds
        setTimeout(() => setUploadStatus('idle'), 5000);
      }

    } catch (error) {
      console.error('Text extraction failed:', error);
      setUploadStatus('error');
      setUploadMessage(`Text extraction failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Clear error message after 5 seconds
      setTimeout(() => setUploadStatus('idle'), 5000);
    } finally {
      setIsUploading(false);
    }
  };

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-yellow-50 to-amber-100 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-yellow-400/20 to-amber-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-amber-400/20 to-orange-600/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-yellow-400/10 to-amber-600/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      <div className="relative w-full p-4 lg:p-6">

        <div className="w-full">
          {/* Main Input Form */}
          <div className="w-full">
            <div className="bg-white/70 backdrop-blur-lg rounded-2xl shadow-xl border border-white/20 p-4">
              <form onSubmit={handleSubmit} className="space-y-2">

                {/* Title & Meta Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                      <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                      Survey Title
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={rfqInput.title || ''}
                        onChange={(e) => setRFQInput({ title: e.target.value })}
                        placeholder="Market Research Study"
                        className="w-full px-3 py-3 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl focus:ring-4 focus:ring-yellow-500/20 focus:border-yellow-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 placeholder-gray-400"
                      />
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-yellow-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                  
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                      <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                      Product Category
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.product_category || ''}
                        onChange={(e) => setRFQInput({ product_category: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-amber-500/20 focus:border-amber-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
                      >
                        <option value="">Select category...</option>
                        <option value="electronics">Electronics</option>
                        <option value="appliances">Appliances</option>
                        <option value="healthcare_technology">Healthcare Technology</option>
                        <option value="enterprise_software">Enterprise Software</option>
                        <option value="automotive">Automotive</option>
                        <option value="financial_services">Financial Services</option>
                        <option value="hospitality">Hospitality</option>
                      </select>
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-amber-500/10 to-yellow-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                      <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                      Target Segment
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.target_segment || ''}
                        onChange={(e) => setRFQInput({ target_segment: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
                      >
                        <option value="">Select segment...</option>
                        <option value="B2B decision makers">B2B Decision Makers</option>
                        <option value="General consumers">General Consumers</option>
                        <option value="Healthcare professionals">Healthcare Professionals</option>
                        <option value="IT professionals">IT Professionals</option>
                        <option value="C-suite executives">C-Suite Executives</option>
                      </select>
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-orange-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                  
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                      <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
                      Research Goal
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.research_goal || ''}
                        onChange={(e) => setRFQInput({ research_goal: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
                      >
                        <option value="">Select goal...</option>
                        <option value="pricing_research">Pricing Research</option>
                        <option value="feature_research">Feature Research</option>
                        <option value="satisfaction_research">Satisfaction Research</option>
                        <option value="brand_research">Brand Research</option>
                        <option value="market_sizing">Market Sizing</option>
                      </select>
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-yellow-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                </div>

                {/* Research Requirements Input */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-semibold text-gray-900 flex items-center">
                      <div className="w-5 h-5 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg mr-2 flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </div>
                      Research Requirements
                    </h4>
                    <div className="flex items-center text-xs text-gray-500">
                      <span className="w-2 h-2 bg-red-400 rounded-full mr-1"></span>
                      Required
                    </div>
                  </div>

                  {/* Document Upload Section - Always visible */}
                  <div className="space-y-2">
                    <div className="border-2 border-dashed border-gray-300 rounded-xl p-3 text-center hover:border-yellow-400 transition-colors duration-200">
                      <input
                        type="file"
                        accept=".docx"
                        onChange={handleFileUpload}
                        disabled={isUploading}
                        className="hidden"
                        id="rfq-file-upload"
                      />
                      <label
                        htmlFor="rfq-file-upload"
                        className={`cursor-pointer ${isUploading ? 'cursor-not-allowed opacity-50' : ''}`}
                      >
                        <div className="space-y-3">
                          <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                            {isUploading ? (
                              <svg className="animate-spin w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                              </svg>
                            )}
                          </div>
                          <div>
                            <p className="text-base font-medium text-gray-900">
                              {isUploading ? 'Processing document...' : hasUploadedDocument ? 'Upload another DOCX file' : 'Upload DOCX file to populate requirements'}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                              {isUploading ? 'Please wait while we parse your document' : 'Click to browse or drag and drop your DOCX file here'}
                            </p>
                          </div>
                        </div>
                      </label>
                    </div>

                    {/* Upload Status Messages */}
                    {uploadStatus !== 'idle' && (
                      <div className={`p-4 rounded-xl ${
                        uploadStatus === 'success' 
                          ? 'bg-amber-50 border border-amber-200' 
                          : 'bg-red-50 border border-red-200'
                      }`}>
                        <div className="flex items-center space-x-3">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                            uploadStatus === 'success' ? 'bg-amber-500' : 'bg-red-500'
                          }`}>
                            {uploadStatus === 'success' ? (
                              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            )}
                          </div>
                          <p className={`text-sm font-medium ${
                            uploadStatus === 'success' ? 'text-amber-800' : 'text-red-800'
                          }`}>
                            {uploadMessage}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Text Input Section - Always visible */}
                  <div className="group relative mb-2">
                    <textarea
                      value={rfqInput.description}
                      onChange={(e) => setRFQInput({ description: e.target.value })}
                      placeholder={hasUploadedDocument 
                        ? "Review and adjust the extracted text below, or type your research requirements directly..."
                        : "Upload a DOCX file above or describe your research requirements in detail. Include methodologies, target audience, key questions, and any specific analysis needed..."
                      }
                      rows={8}
                      required
                      className="w-full px-3 py-3 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 placeholder-gray-400 resize-none leading-relaxed"
                    />
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-orange-500/5 via-red-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    
                    {/* Character count indicator */}
                    <div className="absolute bottom-4 right-6 text-xs text-gray-400 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-lg">
                      {rfqInput.description.length} characters
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-3 border border-yellow-100">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-xs text-yellow-800">
                        <span className="font-medium">Pro Tip:</span> Be specific about methodologies (Van Westendorp, conjoint analysis, MaxDiff, etc.) and research objectives for better survey generation.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={!rfqInput.description.trim() || isLoading}
                    className={`
                      group relative w-full py-4 px-6 rounded-2xl font-bold text-base transition-all duration-300 transform
                      ${isLoading || !rfqInput.description.trim()
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-yellow-600 via-amber-600 to-yellow-600 text-white shadow-2xl hover:shadow-3xl hover:scale-105 active:scale-95'
                      }
                    `}
                  >
                    <div className="relative z-10 flex items-center justify-center space-x-3">
                      {isLoading ? (
                        <>
                          <svg className="animate-spin w-6 h-6 text-current" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Generating Survey...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-6 h-6 text-current group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span>Generate Professional Survey</span>
                          <svg className="w-5 h-5 text-current group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                          </svg>
                        </>
                      )}
                    </div>
                    
                    {/* Animated background gradient */}
                    {!isLoading && rfqInput.description.trim() && (
                      <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-amber-600 via-yellow-600 to-amber-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
