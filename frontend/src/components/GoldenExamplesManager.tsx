import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenExample, GoldenExampleRequest } from '../types';

export const GoldenExamplesManager: React.FC = () => {
  const { goldenExamples, fetchGoldenExamples, createGoldenExample, updateGoldenExample, deleteGoldenExample } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedExample, setSelectedExample] = useState<GoldenExample | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
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

  const loadGoldenExamples = useCallback(async () => {
    setIsLoading(true);
    try {
      await fetchGoldenExamples();
    } catch (error) {
      console.error('Failed to load golden examples:', error);
    } finally {
      setIsLoading(false);
    }
  }, [fetchGoldenExamples]);

  useEffect(() => {
    loadGoldenExamples();
  }, [loadGoldenExamples]);

  const handleCreateExample = async () => {
    setIsLoading(true);
    try {
      await createGoldenExample(formData);
      resetForm();
      await loadGoldenExamples();
    } catch (error) {
      console.error('Failed to create golden example:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateExample = async () => {
    if (!selectedExample) return;
    
    setIsLoading(true);
    try {
      await updateGoldenExample(selectedExample.id, formData);
      setSelectedExample(null);
      setIsEditMode(false);
      resetForm();
      await loadGoldenExamples();
    } catch (error) {
      console.error('Failed to update golden example:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteExample = async (id: string) => {
    setIsLoading(true);
    try {
      await deleteGoldenExample(id);
      await loadGoldenExamples();
    } catch (error) {
      console.error('Failed to delete golden example:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      rfq_text: '',
      survey_json: { survey_id: '', title: '', description: '', estimated_time: 10, confidence_score: 0.8, methodologies: [], golden_examples: [], questions: [], metadata: { target_responses: 0, methodology: [] } },
      methodology_tags: [],
      industry_category: '',
      research_goal: '',
      quality_score: 0.8
    });
    setParseError('');
    setShowJsonPreview(false);
    setExtractedText('');
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.docx')) {
      setParseError('Please select a DOCX file');
      return;
    }

    setIsParsingDocument(true);
    setParseError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/golden-pairs/parse-document', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to parse document');
      }

      const result = await response.json();
      
      setExtractedText(result.extracted_text);
      setFormData(prev => ({
        ...prev,
        survey_json: result.survey_json,
        quality_score: result.confidence_score || 0.8
      }));
      setShowJsonPreview(true);

    } catch (error) {
      setParseError(error instanceof Error ? error.message : 'Failed to parse document');
    } finally {
      setIsParsingDocument(false);
    }
  };

  const editExample = (example: GoldenExample) => {
    setSelectedExample(example);
    setFormData({
      rfq_text: example.rfq_text,
      survey_json: example.survey_json,
      methodology_tags: example.methodology_tags,
      industry_category: example.industry_category,
      research_goal: example.research_goal,
      quality_score: example.quality_score
    });
    setIsEditMode(true);
  };

  const formatQualityScore = (score: number) => {
    return `${(score * 100).toFixed(0)}%`;
  };

  const getIndustryColor = (industry: string) => {
    const colors = {
      'Consumer Electronics': 'bg-gray-100 text-gray-800',
      'B2B Technology': 'bg-gray-200 text-gray-900', 
      'Automotive': 'bg-gray-300 text-black',
      'Healthcare': 'bg-gray-150 text-gray-800',
      'Financial Services': 'bg-gray-200 text-gray-900',
      'Retail': 'bg-gray-100 text-gray-700',
      default: 'bg-gray-100 text-gray-700'
    };
    return colors[industry as keyof typeof colors] || colors.default;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Golden Examples</h1>
              </div>
            </div>
            
            <button
              onClick={() => setIsEditMode(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 text-white hover:from-yellow-700 hover:to-orange-700 rounded-xl transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>Add New Example</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-200 border-t-yellow-600"></div>
              <p className="text-gray-600 text-lg">Loading golden examples...</p>
            </div>
          </div>
        ) : goldenExamples.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                <svg className="w-12 h-12 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3">No golden examples yet</h3>
              <p className="text-gray-600 mb-8 text-lg">Get started by creating your first golden example</p>
              <button
                onClick={() => setIsEditMode(true)}
                className="px-8 py-4 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Golden Example
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {goldenExamples.map((example) => (
              <div 
                key={example.id} 
                onClick={() => window.location.href = `/golden-examples/${example.id}/edit`}
                className="group bg-white rounded-xl border-2 border-gray-200 hover:border-yellow-300 hover:shadow-lg transition-all duration-200 bg-gradient-to-br from-white to-yellow-50/20 cursor-pointer"
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${getIndustryColor(example.industry_category)}`}>
                      {example.industry_category}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteExample(example.id);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Example"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-yellow-900 transition-colors">{example.survey_json.title}</h3>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3">{example.rfq_text}</p>
                  
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-2">
                      {example.methodology_tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                          {tag}
                        </span>
                      ))}
                      {example.methodology_tags.length > 3 && (
                        <span className="text-xs text-gray-500 italic">+{example.methodology_tags.length - 3} more</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                        {formatQualityScore(example.quality_score)}
                      </span>
                    </div>
                    <span className="text-gray-500">Used {example.usage_count} times</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create/Edit Modal */}
      {isEditMode && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl p-8 w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-gray-200 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedExample ? 'Edit Golden Example' : 'Create Golden Example'}
                  </h2>
                  <p className="text-gray-600">Add a reference example for survey generation</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setIsEditMode(false);
                  setSelectedExample(null);
                  resetForm();
                }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">RFQ Text</label>
                <textarea
                  value={formData.rfq_text}
                  onChange={(e) => setFormData({ ...formData, rfq_text: e.target.value })}
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                  rows={3}
                  placeholder="Enter the RFQ description..."
                />
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
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mb-2"></div>
                            <p className="text-sm text-gray-600">Parsing document...</p>
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
                      <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">{parseError}</p>
                      </div>
                    )}
                    
                    {extractedText && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-gray-700">Document Preview:</p>
                        <div className="p-3 bg-gray-50 border border-gray-200 rounded-md max-h-32 overflow-y-auto">
                          <p className="text-xs text-gray-600 whitespace-pre-wrap">{extractedText}</p>
                        </div>
                      </div>
                    )}
                    
                    {showJsonPreview && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-gray-700">Generated JSON Preview:</p>
                        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                            {JSON.stringify(formData.survey_json, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <textarea
                      value={JSON.stringify(formData.survey_json, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          setFormData({ ...formData, survey_json: parsed });
                        } catch (error) {
                          // Invalid JSON, keep the text but don't update the object
                        }
                      }}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
                      rows={12}
                      placeholder="Enter the survey JSON structure..."
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      This should be a valid JSON object representing the survey structure that will be used as a template.
                    </p>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-6">
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
                    <option value="pricing">Pricing Research</option>
                    <option value="feature_prioritization">Feature Prioritization</option>
                    <option value="brand_perception">Brand Perception</option>
                    <option value="purchase_journey">Purchase Journey</option>
                    <option value="market_segmentation">Market Segmentation</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Methodology Tags</label>
                <input
                  type="text"
                  value={formData.methodology_tags.join(', ')}
                  onChange={(e) => setFormData({ ...formData, methodology_tags: e.target.value.split(', ').filter(Boolean) })}
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                  placeholder="van_westendorp, conjoint, maxdiff, etc."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quality Score</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={formData.quality_score}
                  onChange={(e) => setFormData({ ...formData, quality_score: parseFloat(e.target.value) || 0.8 })}
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={() => {
                  setIsEditMode(false);
                  setSelectedExample(null);
                  resetForm();
                }}
                className="px-6 py-3 border border-gray-300 rounded-xl text-sm hover:bg-gray-50 text-gray-700 transition-all duration-200 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={selectedExample ? handleUpdateExample : handleCreateExample}
                disabled={isLoading}
                className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {isLoading ? 'Saving...' : selectedExample ? 'Update Example' : 'Create Example'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};