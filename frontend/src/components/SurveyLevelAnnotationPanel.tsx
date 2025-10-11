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
  isModal?: boolean; // New prop to control rendering mode
}

const LIKERT_OPTIONS: { value: LikertScale; label: string; color: string }[] = [
  { value: 1, label: 'Poor', color: 'text-error-600' },
  { value: 2, label: 'Fair', color: 'text-primary-600' },
  { value: 3, label: 'Good', color: 'text-warning-600' },
  { value: 4, label: 'Very Good', color: 'text-secondary-600' },
  { value: 5, label: 'Excellent', color: 'text-success-600' }
];

const CATEGORY_OPTIONS = [
  'Demographics',
  'Behavior',
  'Preferences',
  'Attitudes',
  'Satisfaction',
  'Brand',
  'Product',
  'Service',
  'Experience',
  'Feedback',
  'Professionals',
  'Consumers',
  'Other'
];

const SurveyLevelAnnotationPanel: React.FC<SurveyLevelAnnotationPanelProps> = ({
  surveyId,
  annotation,
  onSave,
  onCancel,
  isModal = true // Default to modal for backward compatibility
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
    estimatedDuration: 0,
    complianceStatus: 'needs-review'
  });

  useEffect(() => {
    if (annotation) {
      setFormData({
        ...annotation,
        surveyId,
        timestamp: new Date().toISOString()
      });
    }
  }, [annotation, surveyId]);

  const handleInputChange = (field: keyof SurveyLevelAnnotation, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
      timestamp: new Date().toISOString()
    }));
  };

  const handleSave = () => {
    const annotationToSave: SurveyLevelAnnotation = {
      ...formData,
      surveyId,
      timestamp: new Date().toISOString()
    };
    onSave(annotationToSave);
  };

  const renderLikertScale = (
    label: string,
    value: LikertScale,
    onChange: (value: LikertScale) => void,
    icon: React.ReactNode
  ) => (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm font-medium text-gray-700">{label}</span>
      </div>
      <div className="flex gap-2">
        {LIKERT_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
              value === option.value
                ? `bg-${option.color.split('-')[1]}-100 ${option.color} border-2 border-${option.color.split('-')[1]}-300`
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {option.value}
          </button>
        ))}
      </div>
    </div>
  );

  const renderContent = () => {
    return (
    <div className={isModal ? "bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" : "h-full flex flex-col"}>
      {/* Header */}
      <div className={isModal ? "sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl" : "border-b border-gray-200 px-6 py-4"}>
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
          {isModal && (
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className={isModal ? "p-6 space-y-8" : "flex-1 overflow-y-auto p-6 space-y-8"}>
        {/* Quality Ratings Section */}
        <div className="space-y-6">
          <h3 className="heading-4 flex items-center gap-2">
            <ChartBarIcon className="w-5 h-5" />
            Quality Ratings
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {renderLikertScale(
              'Overall Quality',
              formData.overallQuality || 3,
              (value) => handleInputChange('overallQuality', value),
              <ChartBarIcon className="w-4 h-4" />
            )}
            {renderLikertScale(
              'Survey Relevance',
              formData.surveyRelevance || 3,
              (value) => handleInputChange('surveyRelevance', value),
              <DocumentTextIcon className="w-4 h-4" />
            )}
            {renderLikertScale(
              'Methodology Score',
              formData.methodologyScore || 3,
              (value) => handleInputChange('methodologyScore', value),
              <ShieldCheckIcon className="w-4 h-4" />
            )}
            {renderLikertScale(
              'Respondent Experience',
              formData.respondentExperienceScore || 3,
              (value) => handleInputChange('respondentExperienceScore', value),
              <UserGroupIcon className="w-4 h-4" />
            )}
            {renderLikertScale(
              'Business Value',
              formData.businessValueScore || 3,
              (value) => handleInputChange('businessValueScore', value),
              <ClockIcon className="w-4 h-4" />
            )}
          </div>
        </div>

        {/* Labels Section */}
        <div className="space-y-4">
          <h3 className="heading-4 flex items-center gap-2">
            <TagIcon className="w-5 h-5" />
            Labels
          </h3>
          <LabelsInput
            labels={formData.labels || []}
            onLabelsChange={(labels: string[]) => handleInputChange('labels', labels)}
            placeholder="Add labels for this survey..."
          />
        {/* Survey Classification Section */}
        <div className="space-y-6">
          <h3 className="heading-4 flex items-center gap-2">
            <DocumentTextIcon className="w-5 h-5" />
            Survey Classification
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Survey Type */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Survey Type
              </label>
              <select
                value={formData.surveyType || ''}
                onChange={(e) => handleInputChange('surveyType', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select survey type</option>
                <option value="market-research">Market Research</option>
                <option value="customer-satisfaction">Customer Satisfaction</option>
                <option value="employee-feedback">Employee Feedback</option>
                <option value="product-feedback">Product Feedback</option>
                <option value="brand-awareness">Brand Awareness</option>
                <option value="user-experience">User Experience</option>
                <option value="demographic">Demographic</option>
                <option value="behavioral">Behavioral</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Industry Category */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Industry Category
              </label>
              <select
                value={formData.industryCategory || ''}
                onChange={(e) => handleInputChange('industryCategory', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select industry</option>
                <option value="technology">Technology</option>
                <option value="healthcare">Healthcare</option>
                <option value="finance">Finance</option>
                <option value="retail">Retail</option>
                <option value="education">Education</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="consulting">Consulting</option>
                <option value="non-profit">Non-Profit</option>
                <option value="government">Government</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Target Audience */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Target Audience
              </label>
              <input
                type="text"
                value={formData.targetAudience || ''}
                onChange={(e) => handleInputChange('targetAudience', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., B2B customers, general consumers, employees"
              />
            </div>

            {/* Survey Complexity */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Survey Complexity
              </label>
              <select
                value={formData.surveyComplexity || 'moderate'}
                onChange={(e) => handleInputChange('surveyComplexity', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="simple">Simple</option>
                <option value="moderate">Moderate</option>
                <option value="complex">Complex</option>
              </select>
            </div>

            {/* Estimated Duration */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Estimated Duration (minutes)
              </label>
              <input
                type="number"
                min="0"
                max="120"
                value={formData.estimatedDuration || 0}
                onChange={(e) => handleInputChange('estimatedDuration', parseInt(e.target.value) || 0)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0"
              />
            </div>

            {/* Compliance Status */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Compliance Status
              </label>
              <select
                value={formData.complianceStatus || 'needs-review'}
                onChange={(e) => handleInputChange('complianceStatus', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="compliant">Compliant</option>
                <option value="non-compliant">Non-Compliant</option>
                <option value="needs-review">Needs Review</option>
              </select>
            </div>
          </div>
        </div>

        {/* Research Methodology Section */}
        <div className="space-y-4">
          <h3 className="heading-4 flex items-center gap-2">
            <ChartBarIcon className="w-5 h-5" />
            Research Methodology
          </h3>
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Select applicable methodologies
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                'Quantitative',
                'Qualitative',
                'Mixed Methods',
                'Cross-sectional',
                'Longitudinal',
                'Experimental',
                'Observational',
                'Survey Research',
                'Focus Groups',
                'Interviews',
                'Case Study',
                'Ethnography'
              ].map((method) => (
                <label key={method} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={(formData.researchMethodology || []).includes(method)}
                    onChange={(e) => {
                      const currentMethods = formData.researchMethodology || [];
                      const newMethods = e.target.checked
                        ? [...currentMethods, method]
                        : currentMethods.filter(m => m !== method);
                      handleInputChange('researchMethodology', newMethods);
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{method}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Overall Comment */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Overall Comment
          </label>
          <textarea
            value={formData.overallComment || ''}
            onChange={(e) => handleInputChange('overallComment', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={4}
            placeholder="Add any overall comments about this survey..."
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={onCancel}
            className="btn-secondary-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="btn-primary-sm"
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

  if (isModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        {renderContent()}
      </div>
    );
  }

  return renderContent();
};

export default SurveyLevelAnnotationPanel;