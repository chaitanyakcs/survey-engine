import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, SparklesIcon } from '@heroicons/react/24/solid';

interface FieldExtractionData {
  methodology_tags: string[];
  industry_category: string;
  research_goal: string;
  quality_score: number;
  suggested_title: string;
  confidence_level: number;
  reasoning: Record<string, string>;
}

interface ProgressUpdate {
  step: string;
  percent: number;
  message: string;
  details?: {
    extracted_data?: FieldExtractionData;
    step_details?: string;
  };
}

interface IntelligentFieldExtractorProps {
  rfqText: string;
  surveyJson: Record<string, any>;
  onFieldsExtracted: (fields: FieldExtractionData) => void;
  onProgressUpdate?: (progress: ProgressUpdate) => void;
  disabled?: boolean;
}

export const IntelligentFieldExtractor: React.FC<IntelligentFieldExtractorProps> = ({
  rfqText,
  surveyJson,
  onFieldsExtracted,
  onProgressUpdate,
  disabled = false
}) => {
  const [isExtracting, setIsExtracting] = useState(false);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [extractedFields, setExtractedFields] = useState<FieldExtractionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));

  // WebSocket connection for real-time progress
  useEffect(() => {
    if (isExtracting) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const backendHost = process.env.NODE_ENV === 'production' 
        ? window.location.host 
        : 'localhost:8000';
      const wsUrl = `${protocol}//${backendHost}/api/v1/field-extraction/progress/${sessionId}`;
      
      console.log('🔌 [Field Extractor] Connecting to WebSocket:', wsUrl);
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('✅ [Field Extractor] WebSocket connected');
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 [Field Extractor] Progress update received:', data);
          
          if (data.type === 'golden_example_progress') {
            const progressUpdate: ProgressUpdate = {
              step: data.step,
              percent: data.percent,
              message: data.message,
              details: data.details
            };
            
            setProgress(progressUpdate);
            onProgressUpdate?.(progressUpdate);
            
            // If extraction is complete, update extracted fields
            if (data.details?.extracted_data) {
              setExtractedFields(data.details.extracted_data);
              onFieldsExtracted(data.details.extracted_data);
            }
          }
        } catch (err) {
          console.error('❌ [Field Extractor] Failed to parse WebSocket message:', err);
        }
      };
      
      websocket.onclose = () => {
        console.log('🔌 [Field Extractor] WebSocket disconnected');
        setWs(null);
      };
      
      websocket.onerror = (error) => {
        console.error('❌ [Field Extractor] WebSocket error:', error);
        setError('Connection error occurred during field extraction');
      };
      
      return () => {
        websocket.close();
      };
    }
  }, [isExtracting, sessionId, onProgressUpdate, onFieldsExtracted]);

  const extractFields = useCallback(async () => {
    if (!rfqText.trim() || !surveyJson || Object.keys(surveyJson).length === 0) {
      setError('Please provide both RFQ text and Survey JSON for field extraction');
      return;
    }

    console.log('🔍 [Field Extractor] Starting intelligent field extraction');
    console.log('📝 [Field Extractor] RFQ length:', rfqText.length);
    console.log('📊 [Field Extractor] Survey keys:', Object.keys(surveyJson));

    setIsExtracting(true);
    setError(null);
    setProgress(null);
    setExtractedFields(null);

    try {
      const response = await fetch('/api/v1/field-extraction/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rfq_text: rfqText,
          survey_json: surveyJson,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to extract fields');
      }

      const result = await response.json();
      console.log('✅ [Field Extractor] Field extraction completed:', result);
      
      setExtractedFields(result);
      onFieldsExtracted(result);
      
    } catch (err) {
      console.error('❌ [Field Extractor] Field extraction failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to extract fields');
    } finally {
      setIsExtracting(false);
    }
  }, [rfqText, surveyJson, sessionId, onFieldsExtracted]);

  const canExtract = rfqText.trim().length > 0 && 
                    surveyJson && 
                    Object.keys(surveyJson).length > 0 && 
                    !isExtracting && 
                    !disabled;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Intelligent Field Extraction</h3>
            <p className="text-sm text-gray-600">AI-powered auto-population of golden example fields</p>
          </div>
        </div>
        
        <button
          onClick={extractFields}
          disabled={!canExtract}
          className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
            canExtract
              ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white hover:from-blue-600 hover:to-indigo-600 shadow-lg hover:shadow-blue-200 transform hover:scale-105'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isExtracting ? 'Extracting...' : 'Extract Fields'}
        </button>
      </div>

      {/* Progress Bar */}
      {isExtracting && progress && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-700">{progress.message}</span>
            <span className="text-sm font-medium text-blue-600">{progress.percent}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          
          {/* Step Details */}
          {progress.details?.step_details && (
            <div className="mt-2 text-xs text-blue-600">
              Step: {progress.details.step_details}
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Extracted Fields Preview */}
      {extractedFields && (
        <div className="bg-white border border-green-200 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-3">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="font-medium text-green-700">Fields Extracted Successfully!</span>
            <span className="text-sm text-green-600">Fields extracted successfully</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Methodology Tags:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {extractedFields.methodology_tags.map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <span className="font-medium text-gray-700">Industry:</span>
              <span className="ml-2 text-gray-600 capitalize">{extractedFields.industry_category.replace('_', ' ')}</span>
            </div>
            
            <div>
              <span className="font-medium text-gray-700">Research Goal:</span>
              <span className="ml-2 text-gray-600 capitalize">{extractedFields.research_goal.replace('_', ' ')}</span>
            </div>
            
            <div>
              <span className="font-medium text-gray-700">Quality Score:</span>
              <span className="ml-2 text-gray-600">{Math.round(extractedFields.quality_score * 100)}%</span>
            </div>
            
            <div className="md:col-span-2">
              <span className="font-medium text-gray-700">Suggested Title:</span>
              <span className="ml-2 text-gray-600">{extractedFields.suggested_title}</span>
            </div>
          </div>
          
          {/* Reasoning */}
          {Object.keys(extractedFields.reasoning).length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="font-medium text-gray-700 mb-2">AI Reasoning:</h4>
              <div className="space-y-2 text-sm text-gray-600">
                {Object.entries(extractedFields.reasoning).map(([key, value]) => (
                  <div key={key}>
                    <span className="font-medium capitalize">{key.replace('_', ' ')}:</span> {value}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Requirements */}
      {!isExtracting && !extractedFields && (
        <div className="text-sm text-gray-600">
          <p className="mb-2">Requirements for field extraction:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>RFQ text must be provided</li>
            <li>Survey JSON must contain questions and structure</li>
            <li>AI will analyze both to suggest appropriate fields</li>
          </ul>
        </div>
      )}
    </div>
  );
};

