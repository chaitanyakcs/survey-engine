import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon, 
  CheckIcon, 
  TagIcon,
  ChartBarIcon,
  UserGroupIcon,
  ClockIcon,
  DocumentTextIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { SurveyLevelAnnotation, LikertScale } from '../types';
import LabelsInput from './LabelsInput';

interface SurveyLevelAnnotationPanelProps {
  surveyId: string;
  annotation?: SurveyLevelAnnotation;
  onSave: (annotation: SurveyLevelAnnotation) => void;
  onCancel: () => void;
}

const LIKERT_OPTIONS: { value: LikertScale; label: string; color: string }[] = [
  { value: 1, label: 'Poor', color: 'text-red-600' },
  { value: 2, label: 'Fair', color: 'text-orange-600' },
  { value: 3, label: 'Good', color: 'text-yellow-600' },
  { value: 4, label: 'Very Good', color: 'text-blue-600' },
  { value: 5, label: 'Excellent', color: 'text-green-600' }
];

const SURVEY_TYPES = [
  'Customer Satisfaction',
  'Market Research',
  'Employee Engagement',
  'Product Feedback',
  'Brand Perception',
  'User Experience',
  'Compliance Survey',
  'Academic Research',
  'Other'
];

const INDUSTRY_CATEGORIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Retail',
  'Manufacturing',
  'Education',
  'Government',
  'Non-profit',
  'Other'
];

const RESEARCH_METHODOLOGIES = [
  'Quantitative',
  'Qualitative',
  'Mixed Methods',
  'Experimental',
  'Observational',
  'Survey Research',
  'Case Study',
  'Focus Groups',
  'Interviews'
];

const TARGET_AUDIENCES = [
  'General Public',
  'Customers',
  'Employees',
  'Students',
  'Patients',
  'Stakeholders',
  'Professionals',
  'Consumers',
  'Other'
];

export const SurveyLevelAnnotationPanel: React.FC<SurveyLevelAnnotationPanelProps> = ({
  surveyId,
  annotation,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<SurveyLevelAnnotation>({
    surveyId,
    overallComment: '',
    labels: [],
    annotatorId: 'current-user',
    timestamp: new Date().toISOString(),
    overallQuality: 3,
    surveyRelevance: 3,
    methodologyScore: 3,
    respondentExperienceScore: 3,
    businessValueScore: 3,
    surveyType: '',
    industryCategory: '',
    researchMethodology: [],
    targetAudience: '',
    surveyComplexity: 'moderate',
    estimatedDuration: 10,
    complianceStatus: 'needs-review',
    detectedLabels: {},
    complianceReport: {},
    advancedMetadata: {}
  });

  useEffect(() => {
    if (annotation) {
      setFormData(annotation);
    }
  }, [annotation]);

  const handleInputChange = (field: keyof SurveyLevelAnnotation, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayChange = (field: 'researchMethodology', value: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: checked 
        ? [...(prev[field] || []), value]
        : (prev[field] || []).filter(item => item !== value)
    }));
  };

  const handleSave = () => {
    onSave(formData);
  };

  const renderLikertScale = (
    label: string,
    value: LikertScale | undefined,
    onChange: (value: LikertScale) => void,
    icon?: React.ReactNode
  ) => (
    <div className="space-y-2">
      <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
        {icon}
        {label}
      </label>
      <div className="flex gap-2">
        {LIKERT_OPTIONS.map(option => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
              value === option.value
                ? `bg-${option.color.split('-')[1]}-100 border-${option.color.split('-')[1]}-300 ${option.color}`
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {option.value}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <TagIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Survey-Level Annotation</h2>
                <p className="text-sm text-gray-500">Add comprehensive annotations for the entire survey</p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          {/* Quality Ratings Section */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5" />
              Quality Ratings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {renderLikertScale(
                'Overall Quality',
                formData.overallQuality,
                (value) => handleInputChange('overallQuality', value),
                <ChartBarIcon className="w-4 h-4" />
              )}
              {renderLikertScale(
                'Survey Relevance',
                formData.surveyRelevance,
                (value) => handleInputChange('surveyRelevance', value),
                <DocumentTextIcon className="w-4 h-4" />
              )}
              {renderLikertScale(
                'Methodology Score',
                formData.methodologyScore,
                (value) => handleInputChange('methodologyScore', value),
                <ChartBarIcon className="w-4 h-4" />
              )}
              {renderLikertScale(
                'Respondent Experience',
                formData.respondentExperienceScore,
                (value) => handleInputChange('respondentExperienceScore', value),
                <UserGroupIcon className="w-4 h-4" />
              )}
              {renderLikertScale(
                'Business Value',
                formData.businessValueScore,
                (value) => handleInputChange('businessValueScore', value),
                <ChartBarIcon className="w-4 h-4" />
              )}
            </div>
          </div>

          {/* Labels Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TagIcon className="w-5 h-5" />
              Labels
            </h3>
            <LabelsInput
              labels={formData.labels || []}
              onLabelsChange={(labels) => handleInputChange('labels', labels)}
              placeholder="Add labels for this survey..."
              maxLabels={15}
            />
          </div>

          {/* Survey Classification Section */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TagIcon className="w-5 h-5" />
              Survey Classification
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Survey Type */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Survey Type</label>
                <select
                  value={formData.surveyType || ''}
                  onChange={(e) => handleInputChange('surveyType', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select survey type</option>
                  {SURVEY_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Industry Category */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Industry Category</label>
                <select
                  value={formData.industryCategory || ''}
                  onChange={(e) => handleInputChange('industryCategory', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select industry</option>
                  {INDUSTRY_CATEGORIES.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>

              {/* Target Audience */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Target Audience</label>
                <select
                  value={formData.targetAudience || ''}
                  onChange={(e) => handleInputChange('targetAudience', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select target audience</option>
                  {TARGET_AUDIENCES.map(audience => (
                    <option key={audience} value={audience}>{audience}</option>
                  ))}
                </select>
              </div>

              {/* Survey Complexity */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Survey Complexity</label>
                <select
                  value={formData.surveyComplexity || 'moderate'}
                  onChange={(e) => handleInputChange('surveyComplexity', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="simple">Simple</option>
                  <option value="moderate">Moderate</option>
                  <option value="complex">Complex</option>
                </select>
              </div>

              {/* Estimated Duration */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <ClockIcon className="w-4 h-4" />
                  Estimated Duration (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="120"
                  value={formData.estimatedDuration || 10}
                  onChange={(e) => handleInputChange('estimatedDuration', parseInt(e.target.value) || 10)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Compliance Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <ShieldCheckIcon className="w-4 h-4" />
                  Compliance Status
                </label>
                <select
                  value={formData.complianceStatus || 'needs-review'}
                  onChange={(e) => handleInputChange('complianceStatus', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="compliant">Compliant</option>
                  <option value="non-compliant">Non-compliant</option>
                  <option value="needs-review">Needs Review</option>
                </select>
              </div>
            </div>

            {/* Research Methodology */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700">Research Methodology</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {RESEARCH_METHODOLOGIES.map(methodology => (
                  <label key={methodology} className="flex items-center gap-2 p-2 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.researchMethodology?.includes(methodology) || false}
                      onChange={(e) => handleArrayChange('researchMethodology', methodology, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{methodology}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Overall Comment */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Overall Comment</label>
            <textarea
              value={formData.overallComment || ''}
              onChange={(e) => handleInputChange('overallComment', e.target.value)}
              placeholder="Add your overall assessment of the survey..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <CheckIcon className="w-4 h-4" />
              Override
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
