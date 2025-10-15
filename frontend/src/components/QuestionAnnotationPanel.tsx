import React, { useState, useEffect, useMemo } from 'react';
import {
  QuestionAnnotation,
  Question
} from '../types';
import LikertScale from './LikertScale';
import EnhancedLabelsInput from './EnhancedLabelsInput';
import TabGroup from './TabGroup';
import ProgressIndicator from './ProgressIndicator';
import PillarTooltip from './PillarTooltip';
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
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(annotation?.humanVerified || false);

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


  // Update form data when question or annotation changes (but not when we're in the middle of editing)
  useEffect(() => {
    // Only update if the annotation has actually changed and we're not currently editing
    if (annotation && annotation.timestamp !== formData.timestamp) {
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
      setIsVerified(annotation?.humanVerified || false);
    }
  }, [question.id, annotation, formData.timestamp]);

  const updateField = (field: keyof QuestionAnnotation, value: any) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    
    // Auto-save on ALL field changes in annotation mode
    console.log('🔄 [QuestionAnnotationPanel] Field changed, saving immediately...', { field, value });
    
    const annotationToSave: QuestionAnnotation = {
      ...newFormData,
      questionId: question.id,
      timestamp: new Date().toISOString()
    };
    
    console.log('🔄 [QuestionAnnotationPanel] Saving annotation:', annotationToSave);
    
    // Special logging for q1 changes
    if (question.id === 'q1') {
      console.log('🎯 [QuestionAnnotationPanel] Q1 CHANGES DETECTED:', {
        questionId: question.id,
        field,
        value,
        fullAnnotation: annotationToSave
      });
    }
    
    try {
      onSave(annotationToSave);
      console.log('✅ [QuestionAnnotationPanel] Annotation saved successfully');
    } catch (error) {
      console.error('❌ [QuestionAnnotationPanel] Failed to save annotation:', error);
    }
  };

  // Calculate completion progress
  const completionProgress = useMemo(() => {
    const essentialFields = [
      formData.required !== undefined,
      formData.quality !== undefined,
      formData.relevant !== undefined,
      (formData.comment || '').trim().length > 0,
      (formData.labels || []).length > 0
    ];
    
    const pillarFields = [
      formData.pillars.methodologicalRigor !== undefined,
      formData.pillars.contentValidity !== undefined,
      formData.pillars.respondentExperience !== undefined,
      formData.pillars.analyticalValue !== undefined,
      formData.pillars.businessImpact !== undefined
    ];
    
    const essentialCompleted = essentialFields.filter(Boolean).length;
    const pillarCompleted = pillarFields.filter(Boolean).length;
    
    return {
      essential: { completed: essentialCompleted, total: essentialFields.length },
      pillars: { completed: pillarCompleted, total: pillarFields.length },
      overall: { 
        completed: essentialCompleted + pillarCompleted,
        total: essentialFields.length + pillarFields.length
      }
    };
  }, [formData]);

  return (
    <div className="h-full flex flex-col">
      {/* Sticky Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
        <div className="flex justify-between items-start">
          {/* Left side - AI Status & Progress */}
          <div className="flex-1">
            <div className="flex items-center space-x-4">
              {/* AI Status Badge - Single consolidated version */}
              {annotation?.aiGenerated && (
                <div className="inline-flex items-center px-3 py-2 bg-blue-100 border border-blue-200 rounded-lg shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-blue-800">AI Generated</span>
                    {annotation.aiConfidence && (
                      <span className="text-xs text-blue-700 font-medium">
                        {(annotation.aiConfidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              {/* Progress Indicator */}
              <ProgressIndicator
                completed={completionProgress.overall.completed}
                total={completionProgress.overall.total}
                label="Annotation Progress"
              />
            </div>
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
                      console.log('🔍 [QuestionAnnotationPanel] Verifying annotation:', { surveyId: currentSurvey.survey_id, annotationId: annotation.id });
                      await verifyAIAnnotation(currentSurvey.survey_id, annotation.id, 'question');
                      setIsVerified(true);
                    } else {
                      console.error('🔍 [QuestionAnnotationPanel] Missing survey ID or annotation ID:', { surveyId: currentSurvey?.survey_id, annotationId: annotation?.id });
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


      {/* Tabbed Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <TabGroup
          tabs={[
            {
              id: 'essential',
              label: 'Essential',
              badge: `${completionProgress.essential.completed}/${completionProgress.essential.total}`,
              content: (
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

                  {/* Labels Section */}
                  <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Labels
                    </label>
                    <EnhancedLabelsInput
                      labels={formData.labels || []}
                      onLabelsChange={(labels) => updateField('labels', labels)}
                      placeholder="Add labels for this question..."
                      maxLabels={8}
                      showMasterList={true}
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
                      placeholder="Share your thoughts on this question's design, wording, placement, or any other observations that would help improve the survey..."
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
                      rows={4}
                    />
                  </div>
                </div>
              )
            },
            {
              id: 'pillars',
              label: 'Five Pillars',
              badge: `${completionProgress.pillars.completed}/${completionProgress.pillars.total}`,
              content: (
                <div className="space-y-6">
                  <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                    <h5 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                      Five Pillars Assessment
                    </h5>
                    <div className="space-y-6">
                      <div className="flex items-center space-x-2">
                        <LikertScale
                          label="Methodological Rigor"
                          value={formData.pillars.methodologicalRigor}
                          onChange={(value) => updateField('pillars', { ...formData.pillars, methodologicalRigor: value })}
                          lowLabel="Weak"
                          highLabel="Strong"
                        />
                        <PillarTooltip
                          pillarName="Methodological Rigor"
                          description="Measures the scientific rigor and methodological soundness of the question design."
                          examples={{
                            high: "Clear question wording, appropriate response options, follows survey best practices",
                            low: "Ambiguous wording, leading questions, inappropriate response scales"
                          }}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <LikertScale
                          label="Content Validity"
                          value={formData.pillars.contentValidity}
                          onChange={(value) => updateField('pillars', { ...formData.pillars, contentValidity: value })}
                          lowLabel="Weak"
                          highLabel="Strong"
                        />
                        <PillarTooltip
                          pillarName="Content Validity"
                          description="Assesses whether the question accurately measures what it intends to measure."
                          examples={{
                            high: "Question directly measures the intended construct without bias",
                            low: "Question measures something different than intended or has systematic bias"
                          }}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <LikertScale
                          label="Respondent Experience"
                          value={formData.pillars.respondentExperience}
                          onChange={(value) => updateField('pillars', { ...formData.pillars, respondentExperience: value })}
                          lowLabel="Poor"
                          highLabel="Excellent"
                        />
                        <PillarTooltip
                          pillarName="Respondent Experience"
                          description="Evaluates how easy and engaging the question is for survey respondents."
                          examples={{
                            high: "Clear, engaging, easy to understand and answer",
                            low: "Confusing, boring, difficult to understand or answer"
                          }}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <LikertScale
                          label="Analytical Value"
                          value={formData.pillars.analyticalValue}
                          onChange={(value) => updateField('pillars', { ...formData.pillars, analyticalValue: value })}
                          lowLabel="Low"
                          highLabel="High"
                        />
                        <PillarTooltip
                          pillarName="Analytical Value"
                          description="Measures the usefulness of responses for data analysis and insights."
                          examples={{
                            high: "Provides rich, actionable data for analysis and decision-making",
                            low: "Limited analytical value, difficult to interpret or act upon"
                          }}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <LikertScale
                          label="Business Impact"
                          value={formData.pillars.businessImpact}
                          onChange={(value) => updateField('pillars', { ...formData.pillars, businessImpact: value })}
                          lowLabel="Low"
                          highLabel="High"
                        />
                        <PillarTooltip
                          pillarName="Business Impact"
                          description="Evaluates the potential business value and strategic importance of this question."
                          examples={{
                            high: "Directly supports key business decisions and strategic objectives",
                            low: "Limited business relevance or unclear connection to objectives"
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )
            }
          ]}
        />
      </div>
    </div>
  );
};

export default QuestionAnnotationPanel;