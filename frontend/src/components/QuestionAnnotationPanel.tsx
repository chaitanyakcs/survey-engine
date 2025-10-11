import React, { useState, useEffect } from 'react';
import {
  QuestionAnnotation,
  Question
} from '../types';
import LikertScale from './LikertScale';
import LabelsInput from './LabelsInput';
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
    labels: annotation?.labels ?? [],
    timestamp: new Date().toISOString()
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
      labels: annotation?.labels ?? [],
      timestamp: new Date().toISOString()
    });
  }, [question.id, annotation]);

  const handleSave = () => {
    onSave(formData);
  };

  const updateField = (field: keyof QuestionAnnotation, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };



  return (
    <div className="card-highlighted mt-4">
      {/* Header */}
      <div className="card-default-sm mb-6">
        <div className="flex justify-between items-start">
          {/* Left side - Title and AI Status */}
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-3 h-3 bg-primary-500 rounded-full"></div>
              <h4 className="heading-4">
                Question Annotation
              </h4>
            </div>
            
            {/* AI Status Card */}
            {annotation?.aiGenerated && (
              <div className="badge-secondary">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-secondary-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-secondary-800">AI Generated</span>
                  {annotation.aiConfidence && (
                    <div className="flex items-center space-x-1 ml-2">
                      <div className="w-1 h-1 bg-secondary-400 rounded-full"></div>
                      <span className="text-xs text-secondary-600 font-medium">
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
              Override
            </button>
            {annotation?.aiGenerated && !annotation.humanVerified && (
              <button
                onClick={async () => {
                  try {
                    const { verifyAIAnnotation, currentSurvey } = useAppStore.getState();
                    if (currentSurvey?.survey_id) {
                      await verifyAIAnnotation(currentSurvey.survey_id, parseInt(question.id), 'question');
                    }
                  } catch (error) {
                    console.error('Failed to verify annotation:', error);
                  }
                }}
                className="btn-success-sm"
              >
                Mark as Verified
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="space-y-8">
        {/* Basic Ratings - Each in its own row */}
        <div className="space-y-6">
          {/* Required Toggle */}
          <div className="card-default-sm">
            <label className="label-default mb-3">
              Required Question
            </label>
            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.required}
                  onChange={(e) => updateField('required', e.target.checked)}
                  className="w-5 h-5 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 focus:ring-2"
                />
                <span className="ml-3 text-sm font-medium text-gray-700">
                  {formData.required ? 'Yes, this question is required' : 'No, this question is optional'}
                </span>
              </label>
            </div>
          </div>

          {/* Quality Rating */}
          <div className="card-default-sm">
            <LikertScale
              label="Overall Quality"
              value={formData.quality}
              onChange={(value) => updateField('quality', value)}
              lowLabel="Poor"
              highLabel="Excellent"
            />
          </div>

          {/* Relevance Rating */}
          <div className="card-default-sm">
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
        <div className="card-default">
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

        {/* Labels Section */}
        <div className="card-default">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Labels
          </label>
          <LabelsInput
            labels={formData.labels || []}
            onLabelsChange={(labels) => updateField('labels', labels)}
            placeholder="Add labels for this question..."
            maxLabels={8}
          />
        </div>

        {/* AI Annotation Summary */}
        {annotation?.aiGenerated && (
          <div className="bg-blue-50 rounded-lg p-6 shadow-sm border border-blue-200">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <h5 className="text-lg font-semibold text-blue-800">AI Analysis Summary</h5>
            </div>
            <div className="space-y-3">
              <div className="bg-white rounded-lg p-4 border border-blue-100">
                <div className="text-sm font-medium text-blue-700 mb-2">AI Comment:</div>
                <div className="text-sm text-gray-700 leading-relaxed">{annotation.comment}</div>
              </div>
              <div className="flex items-center justify-between text-sm text-blue-600">
                <span>Generated: {annotation.generationTimestamp ? new Date(annotation.generationTimestamp).toLocaleString() : 'Unknown'}</span>
                <span>Confidence: {annotation.aiConfidence ? (annotation.aiConfidence * 100).toFixed(0) : 'N/A'}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Comment Section */}
        <div className="card-default">
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