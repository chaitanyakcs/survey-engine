import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { SurveyPreview } from '../components/SurveyPreview';
import { useAppStore } from '../store/useAppStore';
import { GoldenExample, GoldenExampleRequest } from '../types';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import MethodologyTagsInput from '../components/MethodologyTagsInput';
import { 
  ArrowLeftIcon, 
  DocumentTextIcon, 
  CodeBracketIcon, 
  EyeIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  DocumentIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';

export const GoldenExampleEditPage: React.FC = () => {
  // Extract ID from URL path
  const getGoldenExampleId = () => {
    const path = window.location.pathname;
    console.log('🔍 [GoldenExampleEdit] Current path:', path);
    // Try to match both /golden-examples/{id}/edit and /golden-examples/{id}
    const match = path.match(/\/golden-examples\/([^/]+)(?:\/edit)?$/);
    const extractedId = match ? match[1] : null;
    console.log('🔍 [GoldenExampleEdit] Extracted ID:', extractedId);
    return extractedId;
  };
  
  const [id] = useState<string | null>(getGoldenExampleId());
  const { fetchGoldenExamples, updateGoldenExample, loadAnnotations } = useAppStore();
  const { mainContentClasses } = useSidebarLayout();
  
  const [example, setExample] = useState<GoldenExample | null>(null);
  const [actualSurvey, setActualSurvey] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [activeMainTab, setActiveMainTab] = useState<'rfq' | 'survey'>('survey');
  const [activeSurveyTab, setActiveSurveyTab] = useState<'preview' | 'json' | 'docx'>('preview');
  const [formData, setFormData] = useState<GoldenExampleRequest>({
    rfq_text: '',
    survey_json: { survey_id: '', title: '', description: '', estimated_time: 10, confidence_score: 0.8, methodologies: [], golden_examples: [], questions: [], metadata: { target_responses: 0, methodology: [] } },
    methodology_tags: [],
    industry_category: '',
    research_goal: '',
    quality_score: undefined
  });

  const loadGoldenExample = useCallback(async () => {
    if (!id) {
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    try {
      // Fetch golden examples first
      await fetchGoldenExamples();
      
      // Get the updated golden examples from the store
      const currentGoldenExamples = useAppStore.getState().goldenExamples;
      console.log('🔍 [GoldenExampleEdit] Loading golden example with ID:', id);
      console.log('🔍 [GoldenExampleEdit] Available golden examples:', currentGoldenExamples.length);
      console.log('🔍 [GoldenExampleEdit] Golden example IDs:', currentGoldenExamples.map(ex => ex.id));
      
      const foundExample = currentGoldenExamples.find(ex => ex.id === id);
      if (foundExample) {
        console.log('✅ [GoldenExampleEdit] Found golden example:', foundExample);
        console.log('🔍 [GoldenExampleEdit] Survey JSON structure:', foundExample.survey_json);
        console.log('🔍 [GoldenExampleEdit] Survey JSON keys:', Object.keys(foundExample.survey_json || {}));
        console.log('🔍 [GoldenExampleEdit] Survey JSON title:', foundExample.survey_json?.title);
        console.log('🔍 [GoldenExampleEdit] Survey JSON final_output:', foundExample.survey_json?.final_output);
        console.log('🔍 [GoldenExampleEdit] Survey JSON raw_output:', foundExample.survey_json?.raw_output);
        
        // Check if we need to extract survey from final_output or raw_output
        let actualSurvey: any = foundExample.survey_json;
        
        // Helper function to validate if data looks like a survey
        const isValidSurvey = (data: any): boolean => {
          return data && 
                 typeof data === 'object' && 
                 data.title && 
                 ((data.questions && Array.isArray(data.questions) && data.questions.length > 0) ||
                  (data.sections && Array.isArray(data.sections) && data.sections.length > 0));
        };
        
        console.log('🔍 [GoldenExampleEdit] Original survey_json:', foundExample.survey_json);
        console.log('🔍 [GoldenExampleEdit] Is original valid survey:', isValidSurvey(foundExample.survey_json));
        
        if (foundExample.survey_json?.final_output) {
          console.log('🔍 [GoldenExampleEdit] Found final_output, checking validity...');
          console.log('🔍 [GoldenExampleEdit] final_output:', foundExample.survey_json.final_output);
          console.log('🔍 [GoldenExampleEdit] Is final_output valid survey:', isValidSurvey(foundExample.survey_json.final_output));
          
          if (isValidSurvey(foundExample.survey_json.final_output)) {
            console.log('🔍 [GoldenExampleEdit] Using final_output as survey data');
            actualSurvey = foundExample.survey_json.final_output;
          } else {
            console.log('🔍 [GoldenExampleEdit] final_output is not valid, keeping original');
          }
        } else if (foundExample.survey_json?.raw_output) {
          console.log('🔍 [GoldenExampleEdit] Found raw_output, but it\'s not a survey structure');
          console.log('🔍 [GoldenExampleEdit] raw_output:', foundExample.survey_json.raw_output);
          // raw_output is not a Survey type, so we keep the original
          console.log('🔍 [GoldenExampleEdit] Keeping original survey_json');
        }
        
        console.log('🔍 [GoldenExampleEdit] Final actualSurvey validation:', isValidSurvey(actualSurvey));
        
        console.log('🔍 [GoldenExampleEdit] ===== SURVEY EXTRACTION =====');
        console.log('🔍 [GoldenExampleEdit] Found example:', foundExample);
        console.log('🔍 [GoldenExampleEdit] Survey JSON structure:', foundExample.survey_json);
        console.log('🔍 [GoldenExampleEdit] Extracted actualSurvey:', actualSurvey);
        console.log('🔍 [GoldenExampleEdit] Actual survey title:', actualSurvey?.title);
        console.log('🔍 [GoldenExampleEdit] Actual survey questions:', actualSurvey?.questions?.length);
        console.log('🔍 [GoldenExampleEdit] Actual survey sections:', actualSurvey?.sections?.length);
        console.log('🔍 [GoldenExampleEdit] Actual survey type:', typeof actualSurvey);
        console.log('🔍 [GoldenExampleEdit] ===== END EXTRACTION =====');
        
        setExample(foundExample);
        setActualSurvey(actualSurvey);
        
        // Generate a survey_id for reference examples if they don't have one
        // This allows annotation functionality to work properly
        if (actualSurvey && !actualSurvey.survey_id) {
          actualSurvey.survey_id = foundExample.id;  // Use the golden example ID directly as UUID
          console.log('🔍 [GoldenExampleEdit] Using golden example ID as survey_id:', actualSurvey.survey_id);
        }
        
        setFormData({
          rfq_text: foundExample.rfq_text,
          survey_json: actualSurvey,
          methodology_tags: foundExample.methodology_tags,
          industry_category: foundExample.industry_category || '',
          research_goal: foundExample.research_goal || '',
          quality_score: foundExample.quality_score
        });

        // Load annotations for this survey if it has a survey_id
        if (actualSurvey?.survey_id) {
          try {
            console.log('🔍 [GoldenExampleEdit] Loading annotations for survey:', actualSurvey.survey_id);
            await loadAnnotations(actualSurvey.survey_id);
            console.log('✅ [GoldenExampleEdit] Annotations loaded successfully');
          } catch (error) {
            console.warn('⚠️ [GoldenExampleEdit] Failed to load annotations:', error);
            // Continue without annotations - they'll be created when needed
          }
        } else {
          console.log('⚠️ [GoldenExampleEdit] No survey_id found, skipping annotation loading');
        }
      } else {
        console.log('❌ [GoldenExampleEdit] Golden example not found with ID:', id);
      }
    } catch (error) {
      console.error('Failed to load golden example:', error);
    } finally {
      setIsLoading(false);
    }
  }, [id, fetchGoldenExamples, loadAnnotations]);

  useEffect(() => {
    loadGoldenExample();
  }, [loadGoldenExample]);

  const handleSave = async () => {
    if (!example) return;
    
    try {
      await updateGoldenExample(example.id, formData);
      setIsEditing(false);
      await loadGoldenExample(); // Refresh data
    } catch (error) {
      console.error('Failed to update golden example:', error);
    }
  };

  const handleCancel = () => {
    if (example && actualSurvey) {
      // Ensure the generated survey_id is preserved when canceling
      const surveyToUse = { ...actualSurvey };
      if (!surveyToUse.survey_id) {
        surveyToUse.survey_id = example.id;  // Use the golden example ID directly as UUID
      }
      
      setFormData({
        rfq_text: example.rfq_text,
        survey_json: surveyToUse,
        methodology_tags: example.methodology_tags,
        industry_category: example.industry_category || '',
        research_goal: example.research_goal || '',
        quality_score: example.quality_score
      });
    }
    setIsEditing(false);
  };

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/?view=golden-examples';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex">
        <Sidebar currentView="golden-examples" onViewChange={handleViewChange} />
        <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out flex items-center justify-center`}>
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-200 border-t-amber-600"></div>
            <p className="text-gray-600 text-lg">Loading golden example...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!example) {
    return (
      <div className="min-h-screen bg-white flex">
        <Sidebar currentView="golden-examples" onViewChange={handleViewChange} />
        <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out flex items-center justify-center`}>
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Reference Example Not Found</h2>
            <p className="text-gray-600 mb-4">The reference example you're looking for doesn't exist.</p>
            <button
              onClick={() => window.location.href = '/golden-examples'}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Back to Reference Examples
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 flex">
      {/* Sidebar */}
      <Sidebar currentView="golden-examples" onViewChange={handleViewChange} />

      {/* Main Content */}
      <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>
        {/* Top Bar */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
          <div className="px-6 py-6">
            <div className="flex flex-col space-y-6">
              {/* Header Section */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                <button
                  onClick={() => window.location.href = '/golden-examples'}
                  className="p-3 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200 group"
                >
                  <ArrowLeftIcon className="h-6 w-6 group-hover:-translate-x-1 transition-transform" />
                </button>
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                  <DocumentTextIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                    {isEditing ? 'Edit Reference Example' : 'Reference Example'}
                  </h1>
                  <p className="text-gray-600 mt-1">
                    {isEditing ? 'Modify the reference example details' : 'View and edit reference example'}
                  </p>
                </div>
              </div>
              </div>
              
              {/* Stats and Actions Section */}
              <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-8">
                {/* Stats Cards */}
                <div className="flex flex-wrap gap-4">
                  {/* Quality Score Card */}
                  <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-200 rounded-xl p-4 min-w-[120px]">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <span className="text-xs font-medium text-yellow-700 uppercase tracking-wide">Quality</span>
                    </div>
                    <div className="text-2xl font-bold text-yellow-800">
                      {example.quality_score ? example.quality_score.toFixed(2) : 'N/A'}
                    </div>
                  </div>

                  {/* Usage Count Card */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 min-w-[120px]">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-xs font-medium text-blue-700 uppercase tracking-wide">Usage</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-800">
                      {example.usage_count}
                    </div>
                  </div>

                  {/* Industry Card */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 min-w-[140px]">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-xs font-medium text-green-700 uppercase tracking-wide">Industry</span>
                    </div>
                    <div className="text-lg font-semibold text-green-800 truncate">
                      {example.industry_category || 'N/A'}
                    </div>
                  </div>

                  {/* Research Goal Card */}
                  <div className="bg-gradient-to-br from-purple-50 to-violet-50 border border-purple-200 rounded-xl p-4 min-w-[160px]">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span className="text-xs font-medium text-purple-700 uppercase tracking-wide">Research Goal</span>
                    </div>
                    <div className="text-lg font-semibold text-purple-800 truncate">
                      {example.research_goal || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Methodology Tags Section */}
                {example.methodology_tags.length > 0 && (
                  <div className="flex flex-col space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                      <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">Methodologies</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {example.methodology_tags.map((tag, index) => (
                        <span 
                          key={tag} 
                          className="px-3 py-1.5 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-lg text-sm font-medium border border-gray-300 hover:from-gray-200 hover:to-gray-300 transition-all duration-200"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center space-x-3 lg:ml-auto">
                  {isEditing ? (
                    <>
                      <button
                        onClick={handleCancel}
                        className="px-6 py-3 text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200 flex items-center space-x-2 font-medium"
                      >
                        <XMarkIcon className="h-4 w-4" />
                        <span>Cancel</span>
                      </button>
                      <button
                        onClick={handleSave}
                        className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-amber-600 text-white rounded-xl hover:from-yellow-700 hover:to-amber-700 transition-all duration-200 flex items-center space-x-2 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                      >
                        <CheckIcon className="h-4 w-4" />
                        <span>Save Changes</span>
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-amber-600 text-white rounded-xl hover:from-yellow-700 hover:to-amber-700 transition-all duration-200 flex items-center space-x-2 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      <PencilIcon className="h-4 w-4" />
                      <span>Edit</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Main Content Tabs */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
              {/* Main Tab Navigation */}
              <div className="border-b border-gray-200">
                <div className="flex space-x-1">
                  <button
                    onClick={() => setActiveMainTab('survey')}
                    className={`px-8 py-4 text-sm font-medium transition-all duration-200 flex items-center space-x-3 rounded-t-xl ${
                      activeMainTab === 'survey'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <ClipboardDocumentListIcon className="h-5 w-5" />
                    <span>Survey</span>
                  </button>
                  <button
                    onClick={() => setActiveMainTab('rfq')}
                    className={`px-8 py-4 text-sm font-medium transition-all duration-200 flex items-center space-x-3 rounded-t-xl ${
                      activeMainTab === 'rfq'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <DocumentIcon className="h-5 w-5" />
                    <span>RFQ Text</span>
                  </button>
                </div>
              </div>

              <div className="p-8">
                {/* Survey Tab Content */}
                {activeMainTab === 'survey' && (
                  <div className="space-y-6">
                    {/* Survey Sub-tabs */}
                    <div className="border-b border-gray-200">
                      <div className="flex space-x-1">
                        <button
                          onClick={() => setActiveSurveyTab('preview')}
                          className={`px-6 py-3 text-sm font-medium transition-all duration-200 flex items-center space-x-2 rounded-t-xl ${
                            activeSurveyTab === 'preview'
                              ? 'text-yellow-600 border-b-2 border-yellow-600 bg-yellow-50'
                              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <EyeIcon className="h-4 w-4" />
                          <span>Survey Preview</span>
                        </button>
                        <button
                          onClick={() => setActiveSurveyTab('json')}
                          className={`px-6 py-3 text-sm font-medium transition-all duration-200 flex items-center space-x-2 rounded-t-xl ${
                            activeSurveyTab === 'json'
                              ? 'text-yellow-600 border-b-2 border-yellow-600 bg-yellow-50'
                              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <CodeBracketIcon className="h-4 w-4" />
                          <span>JSON View</span>
                        </button>
                        <button
                          onClick={() => setActiveSurveyTab('docx')}
                          className={`px-6 py-3 text-sm font-medium transition-all duration-200 flex items-center space-x-2 rounded-t-xl ${
                            activeSurveyTab === 'docx'
                              ? 'text-yellow-600 border-b-2 border-yellow-600 bg-yellow-50'
                              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <DocumentTextIcon className="h-4 w-4" />
                          <span>Document Text</span>
                        </button>
                      </div>
                    </div>

                    {/* Survey Sub-tab Content */}
                    <div>
                      {activeSurveyTab === 'preview' && (
                        <div className="w-full border border-gray-200 rounded-xl overflow-hidden">
                          {(() => {
                            console.log('🔍 [GoldenExampleEdit] ===== RENDERING SURVEY PREVIEW =====');
                            console.log('🔍 [GoldenExampleEdit] activeSurveyTab:', activeSurveyTab);
                            console.log('🔍 [GoldenExampleEdit] actualSurvey exists:', !!actualSurvey);
                            console.log('🔍 [GoldenExampleEdit] actualSurvey:', actualSurvey);
                            console.log('🔍 [GoldenExampleEdit] isEditing:', isEditing);
                            console.log('🔍 [GoldenExampleEdit] formData.survey_json:', formData.survey_json);
                            console.log('🔍 [GoldenExampleEdit] Survey to pass to SurveyPreview:', isEditing ? formData.survey_json : actualSurvey);
                            console.log('🔍 [GoldenExampleEdit] ===== END RENDERING LOGIC =====');
                            
                            return actualSurvey ? (
                              <div>
                                <SurveyPreview 
                                  survey={isEditing ? formData.survey_json : actualSurvey}
                                  isEditable={isEditing}
                                  onSurveyChange={isEditing ? (survey) => setFormData({ ...formData, survey_json: survey }) : undefined}
                                  hideHeader={true}
                                />
                              </div>
                            ) : (
                              <div className="text-center py-12">
                                <div className="text-gray-500 text-lg mb-2">No survey data available</div>
                                <div className="text-gray-400 text-sm">The golden example doesn't contain valid survey data</div>
                                <div className="text-xs text-gray-400 mt-2">Debug: actualSurvey is {typeof actualSurvey}</div>
                                <div className="text-xs text-gray-400 mt-1">actualSurvey value: {JSON.stringify(actualSurvey)}</div>
                              </div>
                            );
                          })()}
                        </div>
                      )}
                      
                      {activeSurveyTab === 'json' && (
                        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 overflow-x-auto border border-gray-700">
                          {actualSurvey ? (
                            <pre className="text-green-400 text-sm leading-relaxed">
                              {JSON.stringify(isEditing ? formData.survey_json : actualSurvey, null, 2)}
                            </pre>
                          ) : (
                            <div className="text-center py-12">
                              <div className="text-gray-400 text-lg mb-2">No JSON data available</div>
                              <div className="text-gray-500 text-sm">The golden example doesn't contain valid survey JSON</div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      
                      {activeSurveyTab === 'docx' && (
                        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200">
                          {example?.survey_json?.raw_output?.document_text ? (
                            <div className="prose max-w-none">
                              <pre className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">
                                {example.survey_json.raw_output.document_text}
                              </pre>
                            </div>
                          ) : (
                            <div className="text-center py-12">
                              <div className="text-gray-500 text-lg mb-2">No document text available</div>
                              <div className="text-gray-400 text-sm">The golden example doesn't contain document text data</div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* RFQ Tab Content */}
                {activeMainTab === 'rfq' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900">Request for Quotation (RFQ)</h2>
                    
                    {/* RFQ Text Section */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-gray-800">RFQ Text</h3>
                      {isEditing ? (
                        <textarea
                          value={formData.rfq_text}
                          onChange={(e) => setFormData({ ...formData, rfq_text: e.target.value })}
                          className="w-full h-96 border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                          placeholder="Enter the RFQ description..."
                        />
                      ) : (
                        <div className="prose max-w-none">
                          <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                            <pre className="text-gray-700 whitespace-pre-wrap leading-relaxed text-sm font-mono">
                              {example.rfq_text}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Metadata Section - Only show when editing */}
                    {isEditing && (
                      <div className="space-y-6 pt-6 border-t border-gray-200">
                        <h3 className="text-lg font-medium text-gray-800">Metadata</h3>
                        
                        {/* Industry Category */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Industry Category
                          </label>
                          <input
                            type="text"
                            value={formData.industry_category}
                            onChange={(e) => setFormData({ ...formData, industry_category: e.target.value })}
                            className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                            placeholder="Enter industry category (e.g., Consumer Electronics, Healthcare, Finance)"
                          />
                        </div>

                        {/* Research Goal */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Research Goal
                          </label>
                          <input
                            type="text"
                            value={formData.research_goal}
                            onChange={(e) => setFormData({ ...formData, research_goal: e.target.value })}
                            className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                            placeholder="Enter research goal (e.g., Pricing Research, Product Development, Market Segmentation)"
                          />
                        </div>

                        {/* Methodology Tags */}
                        <div className="relative">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Methodology Tags
                          </label>
                          <MethodologyTagsInput
                            tags={formData.methodology_tags}
                            onTagsChange={(tags) => setFormData({ ...formData, methodology_tags: tags })}
                            placeholder="Add methodology tags..."
                            maxTags={20}
                            showDropdownMenu={true}
                            extractedTags={[]}
                          />
                        </div>
                      </div>
                    )}

                    {/* Display metadata when not editing */}
                    {!isEditing && (
                      <div className="space-y-4 pt-6 border-t border-gray-200">
                        <h3 className="text-lg font-medium text-gray-800">Metadata</h3>
                        
                        {/* Industry Category */}
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                          <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">Industry</span>
                          <div className="text-sm text-gray-600">
                            {example.industry_category || 'N/A'}
                          </div>
                        </div>

                        {/* Research Goal */}
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                          <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">Research Goal</span>
                          <div className="text-sm text-gray-600">
                            {example.research_goal || 'N/A'}
                          </div>
                        </div>

                        {/* Methodology Tags */}
                        {example.methodology_tags.length > 0 && (
                          <div className="flex flex-col space-y-2">
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                              <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">Methodologies</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {example.methodology_tags.map((tag, index) => (
                                <span 
                                  key={tag} 
                                  className="px-3 py-1.5 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-lg text-sm font-medium border border-gray-300 hover:from-gray-200 hover:to-gray-300 transition-all duration-200"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};


