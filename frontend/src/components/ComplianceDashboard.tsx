import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useAppStore } from '../store/useAppStore';
import { TextComplianceReport, Survey } from '../types';

interface ComplianceReport {
  overall_score: number;
  mandatory_elements_found: string[];
  missing_elements: string[];
  compliance_level: string;
  recommendations: string[];
  analysis_timestamp: string;
}

interface DetectedLabels {
  industry_analysis: {
    primary_industry: string;
    confidence: number;
    analysis_timestamp: string;
  };
  respondent_analysis: {
    primary_type: string;
    confidence: number;
    analysis_timestamp: string;
  };
  methodology_analysis: {
    tags: string[];
    primary_approach: string;
    analysis_timestamp: string;
  };
}

interface AdvancedMetadata {
  total_questions: number;
  total_sections: number;
  estimated_completion_time: number;
  complexity_score: number;
  analysis_timestamp: string;
}

interface ComplianceDashboardProps {
  surveyId: string;
  className?: string;
}

const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({ surveyId, className = '' }) => {
  const [complianceReport, setComplianceReport] = useState<ComplianceReport | null>(null);
  const [detectedLabels, setDetectedLabels] = useState<DetectedLabels | null>(null);
  const [advancedMetadata, setAdvancedMetadata] = useState<AdvancedMetadata | null>(null);
  const [textCompliance, setTextCompliance] = useState<TextComplianceReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'compliance' | 'labels' | 'metadata' | 'text'>('compliance');

  // Get survey data and validation functions from store
  const currentSurvey = useAppStore(state => state.currentSurvey);
  const validateSurveyTextCompliance = useAppStore(state => state.validateSurveyTextCompliance);

  useEffect(() => {
    if (surveyId) {
      fetchComplianceData();
    }
  }, [surveyId]);

  const fetchComplianceData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch compliance report
      const complianceResponse = await fetch(`/api/annotations/survey/${surveyId}/compliance-report`);
      if (complianceResponse.ok) {
        const complianceData = await complianceResponse.json();
        setComplianceReport(complianceData.compliance_report);
        setAdvancedMetadata(complianceData.advanced_metadata);
      }

      // Fetch detected labels
      const labelsResponse = await fetch(`/api/annotations/survey/${surveyId}/detected-labels`);
      if (labelsResponse.ok) {
        const labelsData = await labelsResponse.json();
        setDetectedLabels(labelsData.detected_labels);
      }

      // Generate text compliance report if we have survey data
      if (currentSurvey && currentSurvey.survey_id === surveyId) {
        const textComplianceReport = validateSurveyTextCompliance(currentSurvey);
        setTextCompliance(textComplianceReport);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load compliance data');
    } finally {
      setIsLoading(false);
    }
  };

  const getComplianceColor = (level: string) => {
    switch (level) {
      case 'full': return 'text-green-600 bg-green-100 border-green-200';
      case 'high': return 'text-green-600 bg-green-100 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-orange-600 bg-orange-100 border-orange-200';
      default: return 'text-red-600 bg-red-100 border-red-200';
    }
  };

  const getComplianceIcon = (level: string) => {
    switch (level) {
      case 'full':
      case 'high':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'medium':
      case 'low':
        return <ExclamationTriangleIcon className="w-5 h-5" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5" />;
    }
  };

  const exportReport = () => {
    const reportData = {
      survey_id: surveyId,
      compliance_report: complianceReport,
      detected_labels: detectedLabels,
      advanced_metadata: advancedMetadata,
      text_compliance: textCompliance,
      export_timestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `survey-${surveyId}-compliance-report.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="text-center py-8">
          <ExclamationTriangleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Compliance Data Available</h3>
          <p className="text-gray-500 mb-4">
            Run advanced labeling to generate compliance insights for this survey.
          </p>
          <button
            onClick={fetchComplianceData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <ChartBarIcon className="w-6 h-6 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Compliance Dashboard</h2>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={exportReport}
              className="inline-flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              <DocumentArrowDownIcon className="w-4 h-4 mr-1" />
              Export
            </button>
            <button
              onClick={fetchComplianceData}
              className="inline-flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <EyeIcon className="w-4 h-4 mr-1" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { id: 'compliance', label: 'Compliance', available: !!complianceReport },
            { id: 'text', label: 'Text Requirements', available: !!textCompliance },
            { id: 'labels', label: 'Classifications', available: !!detectedLabels },
            { id: 'metadata', label: 'Survey Metrics', available: !!advancedMetadata }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              disabled={!tab.available}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : tab.available
                  ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  : 'border-transparent text-gray-300 cursor-not-allowed'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'compliance' && complianceReport && (
          <div className="space-y-6">
            {/* Overall Score */}
            <div className="text-center">
              <div className="inline-flex items-center space-x-2 mb-2">
                {getComplianceIcon(complianceReport.compliance_level)}
                <span className="text-2xl font-bold text-gray-900">
                  {complianceReport.overall_score}%
                </span>
              </div>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getComplianceColor(complianceReport.compliance_level)}`}>
                {complianceReport.compliance_level.replace('_', ' ').toUpperCase()} COMPLIANCE
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  complianceReport.overall_score >= 80 ? 'bg-green-500' :
                  complianceReport.overall_score >= 60 ? 'bg-yellow-500' :
                  complianceReport.overall_score >= 40 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${complianceReport.overall_score}%` }}
              ></div>
            </div>

            {/* Elements Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Found Elements */}
              <div>
                <h4 className="text-sm font-medium text-green-700 mb-3">
                  ✓ Found Elements ({complianceReport.mandatory_elements_found.length})
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {complianceReport.mandatory_elements_found.map((element, index) => (
                    <div key={index} className="bg-green-50 text-green-800 px-3 py-1 rounded-full text-sm">
                      {element.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                  ))}
                </div>
              </div>

              {/* Missing Elements */}
              <div>
                <h4 className="text-sm font-medium text-red-700 mb-3">
                  ✗ Missing Elements ({complianceReport.missing_elements.length})
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {complianceReport.missing_elements.map((element, index) => (
                    <div key={index} className="bg-red-50 text-red-800 px-3 py-1 rounded-full text-sm">
                      {element.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {complianceReport.recommendations.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                  <InformationCircleIcon className="w-4 h-4 mr-1" />
                  Recommendations
                </h4>
                <ul className="space-y-2">
                  {complianceReport.recommendations.map((recommendation, index) => (
                    <li key={index} className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'text' && textCompliance && (
          <div className="space-y-6">
            {/* Text Compliance Overview */}
            <div className="text-center">
              <div className="inline-flex items-center space-x-2 mb-2">
                <DocumentTextIcon className="w-6 h-6 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {textCompliance.compliance_score}%
                </span>
              </div>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getComplianceColor(textCompliance.compliance_level)}`}>
                {textCompliance.compliance_level.toUpperCase()} TEXT COMPLIANCE
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  textCompliance.compliance_score >= 80 ? 'bg-green-500' :
                  textCompliance.compliance_score >= 60 ? 'bg-yellow-500' :
                  textCompliance.compliance_score >= 40 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${textCompliance.compliance_score}%` }}
              ></div>
            </div>

            {/* Methodology Info */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2">
                Required for Methodologies: {textCompliance.methodology.join(', ')}
              </h4>
            </div>

            {/* Text Requirements Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Found Text Elements */}
              <div>
                <h4 className="text-sm font-medium text-green-700 mb-3">
                  ✓ Required Text Found ({textCompliance.required_text_elements.filter(e => e.found).length})
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {textCompliance.required_text_elements
                    .filter(element => element.found)
                    .map((element, index) => (
                      <div key={index} className="bg-green-50 text-green-800 px-3 py-1 rounded-full text-sm flex justify-between items-center">
                        <span>{element.label.replace('_', ' ')}</span>
                        {element.section && (
                          <span className="text-xs text-green-600">in {element.section}</span>
                        )}
                      </div>
                    ))}
                </div>
              </div>

              {/* Missing Text Elements */}
              <div>
                <h4 className="text-sm font-medium text-red-700 mb-3">
                  ✗ Missing Text Elements ({textCompliance.missing_elements.length})
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {textCompliance.missing_elements.map((element, index) => (
                    <div key={index} className="bg-red-50 text-red-800 px-3 py-1 rounded-full text-sm">
                      {element.replace('_', ' ')}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Detailed Text Requirements */}
            {textCompliance.required_text_elements.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Detailed Text Requirements Analysis
                </h4>
                <div className="space-y-3">
                  {textCompliance.required_text_elements.map((element, index) => (
                    <div key={index} className={`p-3 rounded-lg border ${element.found ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-medium">{element.label.replace('_', ' ')}</span>
                          <span className={`ml-2 text-xs px-2 py-1 rounded ${element.found ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {element.found ? 'Found' : 'Missing'}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">{element.type.replace('_', ' ')}</span>
                      </div>
                      {element.content && (
                        <div className="text-sm text-gray-600 bg-white bg-opacity-50 p-2 rounded">
                          {element.content.content.substring(0, 150)}
                          {element.content.content.length > 150 && '...'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {textCompliance.recommendations.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                  <InformationCircleIcon className="w-4 h-4 mr-1" />
                  Text Compliance Recommendations
                </h4>
                <ul className="space-y-2">
                  {textCompliance.recommendations.map((recommendation, index) => (
                    <li key={index} className="text-sm text-gray-600 bg-amber-50 p-3 rounded-lg border border-amber-200">
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'labels' && detectedLabels && (
          <div className="space-y-6">
            {/* Industry Analysis */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Industry Classification</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium">
                    {detectedLabels.industry_analysis.primary_industry?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Not detected'}
                  </span>
                  <span className="text-sm text-gray-500">
                    {Math.round((detectedLabels.industry_analysis.confidence || 0) * 100)}% confidence
                  </span>
                </div>
              </div>
            </div>

            {/* Respondent Analysis */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Respondent Type</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium">
                    {detectedLabels.respondent_analysis.primary_type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Not detected'}
                  </span>
                  <span className="text-sm text-gray-500">
                    {Math.round((detectedLabels.respondent_analysis.confidence || 0) * 100)}% confidence
                  </span>
                </div>
              </div>
            </div>

            {/* Methodology Analysis */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Methodology Tags</h4>
              <div className="flex flex-wrap gap-2">
                {detectedLabels.methodology_analysis.tags.map((tag, index) => (
                  <span key={index} className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                    {tag.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Primary approach: {detectedLabels.methodology_analysis.primary_approach.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'metadata' && advancedMetadata && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{advancedMetadata.total_questions}</div>
              <div className="text-sm text-gray-500">Total Questions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{advancedMetadata.total_sections}</div>
              <div className="text-sm text-gray-500">Total Sections</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{advancedMetadata.estimated_completion_time}m</div>
              <div className="text-sm text-gray-500">Est. Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{advancedMetadata.complexity_score}/10</div>
              <div className="text-sm text-gray-500">Complexity</div>
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500 text-center">
          {activeTab === 'compliance' && complianceReport?.analysis_timestamp && (
            <>Last analyzed: {new Date(complianceReport.analysis_timestamp).toLocaleString()}</>
          )}
          {activeTab === 'text' && textCompliance?.analysis_timestamp && (
            <>Text compliance analyzed: {new Date(textCompliance.analysis_timestamp).toLocaleString()}</>
          )}
          {activeTab === 'labels' && detectedLabels?.industry_analysis?.analysis_timestamp && (
            <>Last analyzed: {new Date(detectedLabels.industry_analysis.analysis_timestamp).toLocaleString()}</>
          )}
          {activeTab === 'metadata' && advancedMetadata?.analysis_timestamp && (
            <>Last analyzed: {new Date(advancedMetadata.analysis_timestamp).toLocaleString()}</>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComplianceDashboard;