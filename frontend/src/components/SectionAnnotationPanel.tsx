import React, { useState, useEffect } from 'react';
import {
  SectionAnnotation,
  SurveySection,
  SECTION_CLASSIFICATIONS
} from '../types';
import LikertScale from './LikertScale';
import LabelsInput from './LabelsInput';
import { useAppStore } from '../store/useAppStore';

interface SectionAnnotationPanelProps {
  section: SurveySection;
  annotation?: SectionAnnotation;
  onSave: (annotation: SectionAnnotation) => void;
  onCancel: () => void;
}

const SectionAnnotationPanel: React.FC<SectionAnnotationPanelProps> = ({
  section,
  annotation,
  onSave,
  onCancel
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(annotation?.humanVerified || false);

  const [formData, setFormData] = useState<SectionAnnotation>({
    sectionId: String(section.id),
    quality: annotation?.quality ?? 3,
    relevant: annotation?.relevant ?? 3,
    pillars: {
      methodologicalRigor: annotation?.pillars?.methodologicalRigor ?? 3,
      contentValidity: annotation?.pillars?.contentValidity ?? 3,
      respondentExperience: annotation?.pillars?.respondentExperience ?? 3,
      analyticalValue: annotation?.pillars?.analyticalValue ?? 3,
      businessImpact: annotation?.pillars?.businessImpact ?? 3,
    },
    comment: annotation?.comment ?? '',
    labels: annotation?.labels ?? [],
    timestamp: new Date().toISOString(),
    // Advanced labeling fields
    section_classification: annotation?.section_classification ?? '',
    mandatory_elements: annotation?.mandatory_elements ?? {},
    compliance_score: annotation?.compliance_score ?? 0
  });

  // Update form data when section or annotation changes
  useEffect(() => {
    setFormData({
      sectionId: String(section.id),
      quality: annotation?.quality ?? 3,
      relevant: annotation?.relevant ?? 3,
      pillars: {
        methodologicalRigor: annotation?.pillars?.methodologicalRigor ?? 3,
        contentValidity: annotation?.pillars?.contentValidity ?? 3,
        respondentExperience: annotation?.pillars?.respondentExperience ?? 3,
        analyticalValue: annotation?.pillars?.analyticalValue ?? 3,
        businessImpact: annotation?.pillars?.businessImpact ?? 3,
      },
      comment: annotation?.comment ?? '',
      labels: annotation?.labels ?? [],
      timestamp: new Date().toISOString(),
      // Advanced labeling fields
      section_classification: annotation?.section_classification ?? '',
      mandatory_elements: annotation?.mandatory_elements ?? {},
      compliance_score: annotation?.compliance_score ?? 0
    });
    setIsVerified(annotation?.humanVerified || false);
  }, [section.id, annotation]);

  const updateField = (field: keyof SectionAnnotation, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 80) return 'bg-success-500';
    if (score >= 60) return 'bg-warning-500';
    if (score >= 40) return 'bg-primary-500';
    return 'bg-error-500';
  };

  const getComplianceScoreLabel = (score: number) => {
    if (score >= 80) return 'High Compliance';
    if (score >= 60) return 'Medium Compliance';
    if (score >= 40) return 'Low Compliance';
    return 'Poor Compliance';
  };

  const mandatoryElements = formData.mandatory_elements || {};
  const foundElements = mandatoryElements.found || [];
  const missingElements = mandatoryElements.missing || [];

  return (
    <div className="card-highlighted mt-4">
      {/* Header */}
      <div className="card-default-sm mb-6">
        <div className="flex justify-between items-start">
          {/* Left side - AI Status */}
          <div className="flex-1">
            {/* AI Status Card */}
            {annotation?.aiGenerated && (
              <div className="inline-flex items-center px-3 py-2 bg-blue-100 border border-blue-200 rounded-lg shadow-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-semibold text-blue-800">AI Generated</span>
                  {annotation.aiConfidence && (
                    <div className="flex items-center space-x-1 ml-2 px-2 py-1 bg-blue-50 rounded-full">
                      <div className="w-1 h-1 bg-blue-400 rounded-full"></div>
                      <span className="text-xs text-blue-700 font-medium">
                        {(annotation.aiConfidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right side - Action Buttons */}
          <div className="flex items-center gap-2 ml-4">
            {annotation?.aiGenerated && !isVerified && (
              <button
                onClick={async () => {
                  try {
                    setIsVerifying(true);
                    const { verifyAIAnnotation, currentSurvey } = useAppStore.getState();
                    if (currentSurvey?.survey_id && annotation?.id) {
                      console.log('🔍 [SectionAnnotationPanel] Verifying annotation:', { surveyId: currentSurvey.survey_id, annotationId: annotation.id });
                      await verifyAIAnnotation(currentSurvey.survey_id, annotation.id, 'section');
                      setIsVerified(true);
                    } else {
                      console.error('🔍 [SectionAnnotationPanel] Missing survey ID or annotation ID:', { surveyId: currentSurvey?.survey_id, annotationId: annotation?.id });
                    }
                  } catch (error) {
                    console.error('Failed to verify annotation:', error);
                  } finally {
                    setIsVerifying(false);
                  }
                }}
                disabled={isVerifying}
                className="px-4 py-2 bg-green-500 text-white text-sm font-medium rounded-lg hover:bg-green-600 transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isVerifying ? 'Verifying...' : 'Mark as Reviewed'}
              </button>
            )}
            {annotation?.aiGenerated && isVerified && (
              <div className="px-4 py-2 bg-green-100 text-green-800 text-sm font-medium rounded-lg border border-green-200">
                ✓ Human Verified
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="space-y-4">
        {/* Basic Ratings - Each in its own row */}
        <div className="space-y-3">
          {/* Quality Rating */}
          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
            <LikertScale
              label="Overall Quality"
              value={formData.quality}
              onChange={(value) => updateField('quality', value)}
              lowLabel="Poor"
              highLabel="Excellent"
            />
          </div>

          {/* Relevance Rating */}
          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
            <LikertScale
              label="Relevance"
              value={formData.relevant}
              onChange={(value) => updateField('relevant', value)}
              lowLabel="Not Relevant"
              highLabel="Very Relevant"
            />
          </div>
        </div>

        {/* Five Pillars Section - Each pillar in its own row */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <h5 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
            Five Pillars Assessment
          </h5>
          <div className="space-y-3">
            <LikertScale
              label="Methodological Rigor"
              value={formData.pillars.methodologicalRigor}
              onChange={(value) => updateField('pillars', { ...formData.pillars, methodologicalRigor: value })}
              lowLabel="Weak"
              highLabel="Strong"
            />
            <LikertScale
              label="Content Validity"
              value={formData.pillars.contentValidity}
              onChange={(value) => updateField('pillars', { ...formData.pillars, contentValidity: value })}
              lowLabel="Weak"
              highLabel="Strong"
            />
            <LikertScale
              label="Respondent Experience"
              value={formData.pillars.respondentExperience}
              onChange={(value) => updateField('pillars', { ...formData.pillars, respondentExperience: value })}
              lowLabel="Poor"
              highLabel="Excellent"
            />
            <LikertScale
              label="Analytical Value"
              value={formData.pillars.analyticalValue}
              onChange={(value) => updateField('pillars', { ...formData.pillars, analyticalValue: value })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Business Impact"
              value={formData.pillars.businessImpact}
              onChange={(value) => updateField('pillars', { ...formData.pillars, businessImpact: value })}
              lowLabel="Low"
              highLabel="High"
            />
          </div>
        </div>

        {/* Advanced Classification Section */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h5 className="text-lg font-semibold text-gray-800 flex items-center">
              <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
              Section Analysis
            </h5>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {showAdvanced ? 'Hide Analysis' : 'Show Analysis'}
            </button>
          </div>

          {showAdvanced && (
            <div className="space-y-6">
              {/* Section Classification */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Section Classification
                </label>
                <select
                  value={formData.section_classification || ''}
                  onChange={(e) => updateField('section_classification', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                >
                  <option value="">Select section type...</option>
                  {SECTION_CLASSIFICATIONS.map(type => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              {/* Compliance Score */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Compliance Score: {formData.compliance_score || 0}%
                </label>
                <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                  <div
                    className={`h-4 rounded-full transition-all duration-300 ${getComplianceScoreColor(formData.compliance_score || 0)}`}
                    style={{ width: `${formData.compliance_score || 0}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-600">
                  <span>0%</span>
                  <span className={`font-medium ${
                    (formData.compliance_score || 0) >= 80 ? 'text-green-600' :
                    (formData.compliance_score || 0) >= 60 ? 'text-yellow-600' :
                    (formData.compliance_score || 0) >= 40 ? 'text-orange-600' : 'text-red-600'
                  }`}>
                    {getComplianceScoreLabel(formData.compliance_score || 0)}
                  </span>
                  <span>100%</span>
                </div>
              </div>

              {/* Mandatory Elements */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Mandatory Elements Analysis
                </label>

                {foundElements.length > 0 && (
                  <div className="mb-4">
                    <div className="text-sm font-medium text-green-700 mb-2">✓ Found Elements:</div>
                    <div className="flex flex-wrap gap-2">
                      {foundElements.map((element: string, index: number) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                          {element.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {missingElements.length > 0 && (
                  <div className="mb-4">
                    <div className="text-sm font-medium text-red-700 mb-2">✗ Missing Elements:</div>
                    <div className="flex flex-wrap gap-2">
                      {missingElements.map((element: string, index: number) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                          {element.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {foundElements.length === 0 && missingElements.length === 0 && (
                  <div className="text-sm text-gray-500 italic">
                    No mandatory elements analysis available. Run advanced labeling to generate insights.
                  </div>
                )}
              </div>

              {/* Analysis Timestamp */}
              {mandatoryElements.analysis_timestamp && (
                <div className="text-xs text-gray-500">
                  Last analyzed: {new Date(mandatoryElements.analysis_timestamp).toLocaleString()}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Labels Section */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Labels
          </label>
          <LabelsInput
            labels={formData.labels || []}
            onLabelsChange={(labels) => setFormData({...formData, labels})}
            placeholder="Add labels for this section..."
            maxLabels={10}
          />
        </div>

        {/* Comment Section */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Additional Comments & Observations
          </label>
          <textarea
            value={formData.comment}
            onChange={(e) => updateField('comment', e.target.value)}
            placeholder="Share your thoughts on this section's structure, flow, question grouping, or any other observations that would help improve the survey..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
            rows={4}
          />
        </div>

        {/* Section Preview */}
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="text-sm font-semibold text-gray-700 mb-2">
            Section Preview: {section.title} ({section.questions.length} questions)
          </div>
          <div className="text-sm text-gray-600 leading-relaxed">{section.description}</div>
        </div>
      </div>
    </div>
  );
};

export default SectionAnnotationPanel;