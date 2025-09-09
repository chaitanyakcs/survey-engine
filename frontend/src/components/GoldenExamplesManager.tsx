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
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-black">Golden Examples Manager</h1>
          <p className="text-gray-600">Manage reference examples for survey generation</p>
        </div>
        <button
          onClick={() => setIsEditMode(true)}
          className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
        >
          Add New Example
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
        </div>
      )}

      {/* Examples Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
        {goldenExamples.map((example) => (
          <div key={example.id} className="bg-white rounded-lg border border-gray-300 p-6 hover:shadow-lg transition-all duration-200 hover:border-gray-400">
            <div className="flex justify-between items-start mb-4">
              <div className={`px-3 py-1 rounded-md text-xs font-medium ${getIndustryColor(example.industry_category)}`}>
                {example.industry_category}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => editExample(example)}
                  className="text-gray-700 hover:text-black text-sm font-medium transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteExample(example.id)}
                  className="text-gray-500 hover:text-red-600 text-sm font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
            
            <h3 className="font-semibold text-black mb-2">{example.survey_json.title}</h3>
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">{example.rfq_text}</p>
            
            <div className="mb-3">
              <div className="flex flex-wrap gap-1">
                {example.methodology_tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-xs font-medium">
                    {tag}
                  </span>
                ))}
                {example.methodology_tags.length > 3 && (
                  <span className="text-xs text-gray-500">+{example.methodology_tags.length - 3} more</span>
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center text-sm text-gray-500">
              <span>Quality: {formatQualityScore(example.quality_score)}</span>
              <span>Used {example.usage_count} times</span>
            </div>
          </div>
        ))}
      </div>

      {/* Create/Edit Modal */}
      {isEditMode && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-200 shadow-2xl">
            <h2 className="text-lg font-semibold mb-4 text-black">
              {selectedExample ? 'Edit Golden Example' : 'Create Golden Example'}
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-800 mb-1">RFQ Text</label>
                <textarea
                  value={formData.rfq_text}
                  onChange={(e) => setFormData({ ...formData, rfq_text: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
                  rows={3}
                  placeholder="Enter the RFQ description..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-800 mb-1">Survey JSON Template</label>
                
                <div className="mb-3">
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={() => setInputMode('upload')}
                      className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                        inputMode === 'upload' 
                          ? 'bg-black text-white' 
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      Upload DOCX
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputMode('manual')}
                      className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                        inputMode === 'manual' 
                          ? 'bg-black text-white' 
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      Manual Entry
                    </button>
                  </div>
                </div>

                {inputMode === 'upload' ? (
                  <div className="space-y-3">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
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
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-800 mb-1">Industry Category</label>
                  <select
                    value={formData.industry_category}
                    onChange={(e) => setFormData({ ...formData, industry_category: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
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
                  <label className="block text-sm font-medium text-gray-800 mb-1">Research Goal</label>
                  <select
                    value={formData.research_goal}
                    onChange={(e) => setFormData({ ...formData, research_goal: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
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
                <label className="block text-sm font-medium text-gray-800 mb-1">Methodology Tags</label>
                <input
                  type="text"
                  value={formData.methodology_tags.join(', ')}
                  onChange={(e) => setFormData({ ...formData, methodology_tags: e.target.value.split(', ').filter(Boolean) })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
                  placeholder="van_westendorp, conjoint, maxdiff, etc."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-800 mb-1">Quality Score</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={formData.quality_score}
                  onChange={(e) => setFormData({ ...formData, quality_score: parseFloat(e.target.value) || 0.8 })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setIsEditMode(false);
                  setSelectedExample(null);
                  resetForm();
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50 text-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={selectedExample ? handleUpdateExample : handleCreateExample}
                disabled={isLoading}
                className="px-4 py-2 bg-black text-white rounded-md text-sm hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Saving...' : selectedExample ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};