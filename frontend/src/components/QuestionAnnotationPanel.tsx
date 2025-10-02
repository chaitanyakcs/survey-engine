import React, { useState, useEffect } from 'react';
import {
  QuestionAnnotation,
  LikertScale as LikertScaleType,
  Question,
  INDUSTRY_CLASSIFICATIONS,
  RESPONDENT_TYPES,
  METHODOLOGY_TAGS,
  COMPLIANCE_STATUS_OPTIONS,
  IndustryClassification,
  RespondentType,
  MethodologyTag,
  ComplianceStatus
} from '../types';
import LikertScale from './LikertScale';
import { useAppStore } from '../store/useAppStore';

interface QuestionAnnotationPanelProps {
  question: Question;
  annotation?: QuestionAnnotation;
  onSave: (annotation: QuestionAnnotation) => void;
  onCancel: () => void;
}

const QuestionAnnotationPanel: React.FC<QuestionAnnotationPanelProps> = ({
  question,
  annotation,
  onSave,
  onCancel
}) => {
  console.log('🔍 [QuestionAnnotationPanel] Component rendered with:', {
    questionId: question?.id,
    questionText: question?.text,
    annotation,
    hasAnnotation: !!annotation
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [formData, setFormData] = useState<QuestionAnnotation>({
    questionId: question.id,
    required: annotation?.required ?? true,
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
    timestamp: new Date().toISOString(),
    // Advanced labeling fields
    advanced_labels: annotation?.advanced_labels ?? {},
    industry_classification: annotation?.industry_classification ?? '',
    respondent_type: annotation?.respondent_type ?? '',
    methodology_tags: annotation?.methodology_tags ?? [],
    is_mandatory: annotation?.is_mandatory ?? false,
    compliance_status: annotation?.compliance_status ?? 'not_checked'
  });

  // Update form data when question or annotation changes
  useEffect(() => {
    console.log('🔍 [QuestionAnnotationPanel] useEffect triggered - question or annotation changed:', {
      questionId: question.id,
      annotation,
      hasAnnotation: !!annotation
    });
    
    // Always reset form data when question changes
    setFormData({
      questionId: question.id,
      required: annotation?.required ?? true,
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
      timestamp: new Date().toISOString(),
      // Advanced labeling fields
      advanced_labels: annotation?.advanced_labels ?? {},
      industry_classification: annotation?.industry_classification ?? '',
      respondent_type: annotation?.respondent_type ?? '',
      methodology_tags: annotation?.methodology_tags ?? [],
      is_mandatory: annotation?.is_mandatory ?? false,
      compliance_status: annotation?.compliance_status ?? 'not_checked'
    });
  }, [question.id, annotation]);


  const handleSave = () => {
    onSave(formData);
  };

  const updateField = (field: keyof QuestionAnnotation, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleMethodologyTagChange = (tag: MethodologyTag, checked: boolean) => {
    const currentTags = formData.methodology_tags || [];
    if (checked) {
      updateField('methodology_tags', [...currentTags, tag]);
    } else {
      updateField('methodology_tags', currentTags.filter(t => t !== tag));
    }
  };

  const getComplianceStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'needs_review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'non_compliant':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getComplianceStatusLabel = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'Compliant';
      case 'needs_review':
        return 'Needs Review';
      case 'non_compliant':
        return 'Non-Compliant';
      default:
        return 'Not Checked';
    }
  };

  return (
    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-200 rounded-xl p-6 mt-4 shadow-lg">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
          <h4 className="text-lg font-semibold text-gray-800">
            Annotating Question: {question.id}
          </h4>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            Save Annotation
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-500 text-white text-sm font-medium rounded-lg hover:bg-gray-600 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="space-y-8">
        {/* Basic Ratings - Each in its own row */}
        <div className="space-y-6">
          {/* Required Toggle */}
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Required Question
            </label>
            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.required}
                  onChange={(e) => updateField('required', e.target.checked)}
                  className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                />
                <span className="ml-3 text-sm font-medium text-gray-700">
                  {formData.required ? 'Yes, this question is required' : 'No, this question is optional'}
                </span>
              </label>
            </div>
          </div>

          {/* Quality Rating */}
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
            <LikertScale
              label="Overall Quality"
              value={formData.quality}
              onChange={(value) => updateField('quality', value)}
              lowLabel="Poor"
              highLabel="Excellent"
            />
          </div>

          {/* Relevance Rating */}
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
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
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h5 className="text-lg font-semibold text-gray-800 mb-6 flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
            Five Pillars Assessment
          </h5>
          <div className="space-y-6">
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

        {/* Advanced Labeling Section */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h5 className="text-lg font-semibold text-gray-800 flex items-center">
              <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
              Advanced Classification
            </h5>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
            </button>
          </div>

          {showAdvanced && (
            <div className="space-y-6">
              {/* Industry Classification */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Industry Classification
                </label>
                <select
                  value={formData.industry_classification || ''}
                  onChange={(e) => updateField('industry_classification', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                >
                  <option value="">Select industry...</option>
                  {INDUSTRY_CLASSIFICATIONS.map(industry => (
                    <option key={industry} value={industry}>
                      {industry.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              {/* Respondent Type */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Respondent Type
                </label>
                <select
                  value={formData.respondent_type || ''}
                  onChange={(e) => updateField('respondent_type', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                >
                  <option value="">Select respondent type...</option>
                  {RESPONDENT_TYPES.map(type => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              {/* Methodology Tags */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Methodology Tags
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {METHODOLOGY_TAGS.map(tag => (
                    <label key={tag} className="flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.methodology_tags?.includes(tag) || false}
                        onChange={(e) => handleMethodologyTagChange(tag, e.target.checked)}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {tag.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Mandatory Question Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-semibold text-gray-700">
                    Mandatory Question
                  </label>
                  <p className="text-xs text-gray-500 mt-1">
                    Mark if this question is essential for survey validity
                  </p>
                </div>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_mandatory || false}
                    onChange={(e) => updateField('is_mandatory', e.target.checked)}
                    className="w-5 h-5 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700">
                    {formData.is_mandatory ? 'Yes, this is mandatory' : 'No, this is optional'}
                  </span>
                </label>
              </div>

              {/* Compliance Status */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Compliance Status
                </label>
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getComplianceStatusColor(formData.compliance_status || 'not_checked')}`}>
                  {getComplianceStatusLabel(formData.compliance_status || 'not_checked')}
                </div>
              </div>

              {/* Advanced Labels Display */}
              {formData.advanced_labels && Object.keys(formData.advanced_labels).length > 0 && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Auto-Generated Insights
                  </label>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                      {JSON.stringify(formData.advanced_labels, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Comment Section */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Additional Comments & Observations
          </label>
          <textarea
            value={formData.comment}
            onChange={(e) => updateField('comment', e.target.value)}
            placeholder="Share your thoughts on this question's design, wording, placement, or any other observations that would help improve the survey..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
            rows={4}
          />
        </div>

        {/* Question Preview */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm font-semibold text-gray-700 mb-2">Question Preview:</div>
          <div className="text-sm text-gray-600 leading-relaxed">{question.text}</div>
        </div>
      </div>
    </div>
  );
};

export default QuestionAnnotationPanel;