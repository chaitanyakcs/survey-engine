import React, { useState, useEffect, useRef } from 'react';
import { 
  XMarkIcon, 
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

  // Initialize from annotation prop only on mount or when surveyId changes
  useEffect(() => {
    // Only update from annotation prop if:
    // 1. Annotation exists
    // 2. We're not currently editing (user isn't typing)
    // 3. We haven't initialized from this survey yet (lastAnnotationIdRef is undefined or different surveyId)
    // This prevents the form from resetting after we save (which updates the annotation prop)
    const currentSurveyId = surveyId;
    const lastSurveyId = lastAnnotationIdRef.current?.split('|')[0]; // Store as "surveyId|timestamp"
    
    const isNewSurvey = lastSurveyId !== currentSurveyId;
    const shouldUpdate = annotation && 
                         !isEditingRef.current && 
                         (lastAnnotationIdRef.current === undefined || isNewSurvey);
    
    if (shouldUpdate) {
      console.log('🔄 [SurveyLevelAnnotationPanel] Initializing formData from annotation prop', {
        isNewSurvey,
        isEditing: isEditingRef.current,
        currentSurveyId,
        lastSurveyId,
        annotationTimestamp: annotation.timestamp,
        annotationFields: {
          overallComment: annotation.overallComment,
          overallQuality: annotation.overallQuality,
          surveyRelevance: annotation.surveyRelevance,
          methodologyScore: annotation.methodologyScore,
          surveyType: annotation.surveyType,
          researchMethodology: annotation.researchMethodology,
          labels: annotation.labels
        }
      });
      // Initialize with all fields from annotation, using defaults for missing fields
      const initializedFormData: SurveyLevelAnnotation = {
        surveyId,
        overallComment: annotation.overallComment || '',
        labels: annotation.labels || [],
        annotatorId: annotation.annotatorId || 'current-user',
        timestamp: annotation.timestamp || new Date().toISOString(),
        overallQuality: annotation.overallQuality ?? 3,
        surveyRelevance: annotation.surveyRelevance ?? 3,
        methodologyScore: annotation.methodologyScore ?? 3,
        respondentExperienceScore: annotation.respondentExperienceScore ?? 3,
        businessValueScore: annotation.businessValueScore ?? 3,
        surveyType: annotation.surveyType || '',
        industryCategory: annotation.industryCategory || '',
        researchMethodology: annotation.researchMethodology || [],
        targetAudience: annotation.targetAudience || '',
        surveyComplexity: annotation.surveyComplexity || 'moderate',
        estimatedDuration: annotation.estimatedDuration ?? 0,
        complianceStatus: annotation.complianceStatus || 'needs-review',
        detectedLabels: annotation.detectedLabels,
        complianceReport: annotation.complianceReport,
        advancedMetadata: annotation.advancedMetadata
      };
      setFormData(initializedFormData);
      // Store surveyId|timestamp to track both
      lastAnnotationIdRef.current = `${currentSurveyId}|${annotation.timestamp || 'new'}`;
      // Also update the ref
      formDataRef.current = initializedFormData;
    }
  }, [annotation, surveyId]);

  // Use ref to track debounce timeout
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const formDataRef = useRef<SurveyLevelAnnotation>(formData);
  const isEditingRef = useRef<boolean>(false); // Track if user is actively editing
  const lastAnnotationIdRef = useRef<string | undefined>(undefined); // Track last annotation ID we initialized from
  
  // Update ref when form data changes
  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  const handleInputChange = (field: keyof SurveyLevelAnnotation, value: any) => {
    const newFormData = {
      ...formData,
      [field]: value,
      timestamp: new Date().toISOString()
    };
    setFormData(newFormData);
    
    // Mark that user is actively editing
    isEditingRef.current = true;
    
    // Update ref immediately so debounced save uses latest data
    formDataRef.current = { ...newFormData, surveyId };
    
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Auto-save with debouncing to avoid too many API calls
    // Use longer delay for comments to ensure user finishes typing
    const debounceDelay = field === 'overallComment' ? 500 : 200;
    
    console.log('🔄 [SurveyLevelAnnotationPanel] Field changed, scheduling save...', { field, value, debounceDelay });
    
    saveTimeoutRef.current = setTimeout(() => {
      const annotationToSave: SurveyLevelAnnotation = {
        ...formDataRef.current,
        surveyId,
        timestamp: new Date().toISOString()
      };
      
      console.log('🔄 [SurveyLevelAnnotationPanel] Saving annotation:', annotationToSave);
      console.log('💬 [SurveyLevelAnnotationPanel] Overall comment being saved:', annotationToSave.overallComment);
      
      try {
        onSave(annotationToSave);
        console.log('✅ [SurveyLevelAnnotationPanel] Annotation saved successfully');
        // Mark editing as complete after save
        isEditingRef.current = false;
      } catch (error) {
        console.error('❌ [SurveyLevelAnnotationPanel] Failed to save annotation:', error);
        isEditingRef.current = false;
      }
    }, debounceDelay);
  };

  // Note: Manual save is no longer needed - auto-save handles all changes via handleInputChange

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
              <h2 className="text-xl font-semibold text-gray-900">Survey Annotation</h2>
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
                max="45"
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
            placeholder="Provide comprehensive survey-level analysis. Explain WHY the overall survey design works or doesn't work, and HOW to improve strategic alignment, methodology compliance, and respondent experience."
          />
          <div className="mt-2 text-xs text-gray-500 space-y-2">
            <div className="font-semibold text-gray-700 mb-1">Write actionable survey comments that:</div>
            <div className="space-y-1">
              <div className="flex items-start gap-1">
                <span className="text-green-600 font-medium">✓</span>
                <span><strong>Analyze strategic alignment:</strong> "Survey successfully balances quantitative metrics with qualitative insights, directly addressing all three research objectives"</span>
              </div>
              <div className="flex items-start gap-1">
                <span className="text-green-600 font-medium">✓</span>
                <span><strong>Identify methodology strengths:</strong> "Van Westendorp implementation follows best practices with proper price point sequencing and clear respondent instructions"</span>
              </div>
              <div className="flex items-start gap-1">
                <span className="text-green-600 font-medium">✓</span>
                <span><strong>Suggest structural improvements:</strong> "Add demographic questions at the end to avoid priming effects, and include progress indicators to improve completion rates"</span>
              </div>
              <div className="flex items-start gap-1">
                <span className="text-red-600 font-medium">✗</span>
                <span><strong>Avoid generic assessments:</strong> "Nice survey" or "Looks good" (provides no strategic guidance)</span>
              </div>
              <div className="flex items-start gap-1">
                <span className="text-red-600 font-medium">✗</span>
                <span><strong>Avoid vague criticism:</strong> "This survey is bad" or "Poor design" (doesn't explain what's wrong or how to fix it)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons - Only show Cancel in modal mode (to close modal) */}
        {isModal && (
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onCancel}
              className="btn-secondary-sm"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
    </div>
  );
};

  if (isModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-4">
        {renderContent()}
      </div>
    );
  }

  return renderContent();
};

export default SurveyLevelAnnotationPanel;