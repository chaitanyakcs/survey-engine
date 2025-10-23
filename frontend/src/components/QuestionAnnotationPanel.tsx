import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  QuestionAnnotation,
  Question
} from '../types';
import LikertScale from './LikertScale';
import EnhancedLabelsInput from './EnhancedLabelsInput';
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
  console.log('🚀 [QuestionAnnotationPanel] NEW VERSION LOADED - No more infinite loops!');
  
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(annotation?.humanVerified || false);

  // Single state object for all form data - no circular dependencies
  const [formData, setFormData] = useState<QuestionAnnotation>(() => {
    // Ensure labels are always arrays
    const questionLabels = Array.isArray(question.labels) ? question.labels : [];
    const annotationLabels = Array.isArray(annotation?.labels) ? annotation.labels : [];
    const removedLabels = new Set(Array.isArray(annotation?.removedLabels) ? annotation.removedLabels : []);
    
    // Merge labels: question labels + annotation labels - removed labels
    const mergedLabels = [...questionLabels, ...annotationLabels]
      .filter((label, index, arr) => arr.indexOf(label) === index) // Remove duplicates
      .filter(label => !removedLabels.has(label)); // Remove user-removed labels
    
    return {
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
      labels: mergedLabels,
      removedLabels: Array.from(removedLabels),
      timestamp: new Date().toISOString()
    };
  });

  // Track if we've initialized for this question
  const [initializedForQuestion, setInitializedForQuestion] = useState<string | null>(null);

  // Initialize form data when question changes - only once per question
  useEffect(() => {
    if (initializedForQuestion === question.id) {
      return; // Already initialized for this question
    }

    console.log('🔍 [QuestionAnnotationPanel] Initializing for question:', question.id);

    // Ensure labels are always arrays
    const questionLabels = Array.isArray(question.labels) ? question.labels : [];
    const annotationLabels = Array.isArray(annotation?.labels) ? annotation.labels : [];
    const removedLabels = new Set(Array.isArray(annotation?.removedLabels) ? annotation.removedLabels : []);
    
    // Merge labels: question labels + annotation labels - removed labels
    const mergedLabels = [...questionLabels, ...annotationLabels]
      .filter((label, index, arr) => arr.indexOf(label) === index) // Remove duplicates
      .filter(label => !removedLabels.has(label)); // Remove user-removed labels

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
      labels: mergedLabels,
      removedLabels: Array.from(removedLabels),
      timestamp: new Date().toISOString()
    });
    
    setIsVerified(annotation?.humanVerified || false);
    setInitializedForQuestion(question.id);
    
    console.log('✅ [QuestionAnnotationPanel] Initialized with labels:', mergedLabels);
  }, [question.id, annotation?.questionId, annotation?.removedLabels]);

  // Calculate current merged labels on-demand - no useMemo circular dependency
  const getCurrentMergedLabels = useCallback(() => {
    const questionLabels = Array.isArray(question.labels) ? question.labels : [];
    const currentLabels = Array.isArray(formData.labels) ? formData.labels : [];
    const removedLabels = new Set(Array.isArray(formData.removedLabels) ? formData.removedLabels : []);
    
    // Start with question labels (auto-generated)
    let merged = [...questionLabels];
    
        // Add any user-defined labels that aren't already in question labels
        currentLabels.forEach((label: string) => {
          if (!questionLabels.includes(label) && !merged.includes(label)) {
            merged.push(label);
          }
        });
        
        // Remove any labels that are in the removed set
        merged = merged.filter((label: string) => !removedLabels.has(label));
    
    return merged;
  }, [question.labels, formData.labels, formData.removedLabels]);

  // Use ref to track current form data for saving
  const formDataRef = useRef<QuestionAnnotation>(formData);
  
  // Update ref when form data changes
  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  // Save handler - uses ref to avoid circular dependencies
  const handleSave = useCallback(() => {
    const annotationToSave: QuestionAnnotation = {
      ...formDataRef.current,
      questionId: question.id,
      timestamp: new Date().toISOString()
    };
    
    console.log('🔄 [QuestionAnnotationPanel] Saving annotation:', annotationToSave);
    
    try {
      onSave(annotationToSave);
      console.log('✅ [QuestionAnnotationPanel] Annotation saved successfully');
    } catch (error) {
      console.error('❌ [QuestionAnnotationPanel] Failed to save annotation:', error);
    }
  }, [question.id, onSave]);

  // Update field handler - no circular dependencies
  const updateField = useCallback((field: keyof QuestionAnnotation, value: any) => {
    console.log('🔄 [QuestionAnnotationPanel] Field changed:', { field, value });
    
    setFormData(prev => {
      const newFormData = { ...prev, [field]: value };
      
      // If labels field is updated, recalculate merged labels
      if (field === 'labels') {
        const newLabels = Array.isArray(value) ? value : [];
        const removedLabels = new Set(Array.isArray(prev.removedLabels) ? prev.removedLabels : []);
        
        // Calculate what was removed and what was added back
        const previousLabels = Array.isArray(prev.labels) ? prev.labels : [];
        const removed = previousLabels.filter((label: string) => !newLabels.includes(label));
        const addedBack = newLabels.filter((label: string) => !previousLabels.includes(label));
        
        // Update removed labels
        const newRemovedLabels = new Set(removedLabels);
        removed.forEach((label: string) => newRemovedLabels.add(label));
        addedBack.forEach((label: string) => newRemovedLabels.delete(label));
        
        newFormData.removedLabels = Array.from(newRemovedLabels);
        
        console.log('🔍 [QuestionAnnotationPanel] Label change tracking:', {
          questionId: question.id,
          previousLabels,
          newLabels,
          removed,
          addedBack,
          removedLabels: Array.from(newRemovedLabels)
        });
      }
      
      return newFormData;
    });
    
    // Save after a short delay to debounce rapid changes
    setTimeout(() => {
      if (initializedForQuestion === question.id) {
        handleSave();
      }
    }, 100);
  }, [question.id, question.labels, handleSave, initializedForQuestion]);

  // Get current merged labels for display
  const currentMergedLabels = getCurrentMergedLabels();

  // Tab state
  const [activeTab, setActiveTab] = useState<'essential' | 'additional'>('essential');

  // Debug logging
  console.log('🔍 [QuestionAnnotationPanel] Render with:', {
    questionId: question.id,
    questionLabels: Array.isArray(question?.labels) ? question.labels : [],
    annotationLabels: Array.isArray(annotation?.labels) ? annotation.labels : [],
    currentMergedLabels,
    removedLabels: Array.isArray(formData.removedLabels) ? formData.removedLabels : [],
    annotationId: annotation?.id
  });

  const handleVerify = async () => {
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
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header - Simplified */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Question Annotation
            </h3>
            {/* Removed Question ID - keeping only the title */}
          </div>
          <div className="flex items-center space-x-2">
            {annotation?.id && (
              <button
                onClick={handleVerify}
                disabled={isVerifying || isVerified}
                className={`px-3 py-1 text-xs font-medium rounded-full ${
                  isVerified
                    ? 'bg-green-100 text-green-800'
                    : isVerifying
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {isVerified ? 'Verified' : isVerifying ? 'Verifying...' : 'Verify'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Question Text */}
        <div className="p-6 border-b border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Question Text
          </label>
          <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
            {question.text}
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('essential')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'essential'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Essential
            </button>
            <button
              onClick={() => setActiveTab('additional')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'additional'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Additional
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6 space-y-6">
          {activeTab === 'essential' && (
            <>
              {/* Labels */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Labels
                </label>
                <EnhancedLabelsInput
                  labels={currentMergedLabels}
                  onLabelsChange={(labels: string[]) => updateField('labels', labels)}
                  placeholder="Add labels..."
                />
                <div className="mt-2 text-xs text-gray-500">
                  Auto-generated labels: {Array.isArray(question.labels) ? question.labels.length : 0} | 
                  User-defined: {(currentMergedLabels.length - (Array.isArray(question.labels) ? question.labels.length : 0))} |
                  Removed: {Array.isArray(formData.removedLabels) ? formData.removedLabels.length : 0}
                </div>
              </div>

              {/* Quality and Relevance */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-sm text-gray-700 mr-2">Quality</span>
                    <PillarTooltip 
                      pillarName="Quality"
                      description="Assesses the overall quality and clarity of the question"
                    />
                  </div>
                  <LikertScale
                    value={formData.quality}
                    onChange={(value) => updateField('quality', value)}
                    lowLabel="Poor"
                    highLabel="Excellent"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-sm text-gray-700 mr-2">Relevance</span>
                    <PillarTooltip 
                      pillarName="Relevance"
                      description="Evaluates how relevant this question is to the research objectives"
                    />
                  </div>
                  <LikertScale
                    value={formData.relevant}
                    onChange={(value) => updateField('relevant', value)}
                    lowLabel="Not Relevant"
                    highLabel="Very Relevant"
                  />
                </div>
              </div>

              {/* Required Toggle */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-700 mr-2">Required</span>
                  <PillarTooltip 
                    pillarName="Required"
                    description="Indicates if this question is mandatory for the survey"
                  />
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.required}
                    onChange={(e) => updateField('required', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
            </>
          )}

          {activeTab === 'additional' && (
            <>
              {/* Pillars */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Evaluation Pillars
                </label>
                <div className="space-y-4">
                  {[
                    { key: 'methodologicalRigor', label: 'Methodological Rigor', tooltip: 'Assesses the scientific rigor and methodological soundness of the question' },
                    { key: 'contentValidity', label: 'Content Validity', tooltip: 'Evaluates how well the question measures what it intends to measure' },
                    { key: 'respondentExperience', label: 'Respondent Experience', tooltip: 'Considers the clarity and ease of understanding for survey respondents' },
                    { key: 'analyticalValue', label: 'Analytical Value', tooltip: 'Assesses the potential for meaningful data analysis and insights' },
                    { key: 'businessImpact', label: 'Business Impact', tooltip: 'Evaluates the strategic value and business relevance of the question' }
                  ].map(({ key, label, tooltip }) => (
                    <div key={key} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-700 mr-2">{label}</span>
                        <PillarTooltip 
                          pillarName={label}
                          description={tooltip}
                        />
                      </div>
                      <LikertScale
                        value={formData.pillars[key as keyof typeof formData.pillars]}
                        onChange={(value) => updateField('pillars', { ...formData.pillars, [key]: value })}
                        lowLabel="Low"
                        highLabel="High"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Comment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Comment
                </label>
                <textarea
                  value={formData.comment}
                  onChange={(e) => updateField('comment', e.target.value)}
                  placeholder="Add any additional comments..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200">
        <div className="flex justify-end">
          {/* Only show verify button if there's an AI-generated annotation */}
          {annotation?.aiGenerated && (
            <button
              onClick={handleVerify}
              disabled={isVerifying || isVerified}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isVerifying ? (
                <div className="flex items-center">
                  <div className="animate-spin -ml-1 mr-2 h-4 w-4 text-white">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  Verifying...
                </div>
              ) : isVerified ? (
                'Verified'
              ) : (
                'Verify AI Annotation'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionAnnotationPanel;