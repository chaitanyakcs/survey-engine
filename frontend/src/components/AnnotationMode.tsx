import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronRightIcon, TagIcon, CheckIcon } from '@heroicons/react/24/outline';
import LikertScale from './LikertScale';
import { QuestionAnnotation, SectionAnnotation } from '../types';
import { useAppStore } from '../store/useAppStore';

interface AnnotationModeProps {
  survey: any;
  currentAnnotations: any;
  onQuestionAnnotation: (annotation: QuestionAnnotation) => void;
  onSectionAnnotation: (annotation: SectionAnnotation) => void;
  onExitAnnotationMode: () => void;
}

const AnnotationMode: React.FC<AnnotationModeProps> = ({
  survey,
  currentAnnotations,
  onQuestionAnnotation,
  onSectionAnnotation,
  onExitAnnotationMode
}) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  
  // Debug: Log survey data structure
  console.log('🔍 [AnnotationMode] Survey data:', survey);
  console.log('🔍 [AnnotationMode] Survey sections:', survey?.sections);
  console.log('🔍 [AnnotationMode] Survey questions:', survey?.questions);
  console.log('🔍 [AnnotationMode] Survey final_output:', survey?.final_output);
  
  // Handle nested survey data structure
  const actualSurvey = survey?.final_output || survey;
  console.log('🔍 [AnnotationMode] Actual survey data:', actualSurvey);
  console.log('🔍 [AnnotationMode] Actual survey sections:', actualSurvey?.sections);
  console.log('🔍 [AnnotationMode] Actual survey questions:', actualSurvey?.questions);
  
  // Handle both sections format and legacy questions format
  const hasSections = actualSurvey?.sections && actualSurvey.sections.length > 0;
  const hasQuestions = actualSurvey?.questions && actualSurvey.questions.length > 0;
  
  console.log('🔍 [AnnotationMode] Has sections:', hasSections);
  console.log('🔍 [AnnotationMode] Has questions:', hasQuestions);
  
  // If no sections but has questions, create a default section
  const sectionsToUse = hasSections ? actualSurvey.sections : (hasQuestions ? [{
    id: 'default',
    title: 'Survey Questions',
    description: 'All survey questions',
    questions: actualSurvey.questions
  }] : []);
  
  console.log('🔍 [AnnotationMode] Sections to use:', sectionsToUse);
  
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(sectionsToUse.map((s: any) => String(s.id || s.section_id))));
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  
  // Use global state for selected question
  const selectedQuestion = selectedQuestionId;

  // When a question is selected, keep sections expanded
  const handleQuestionSelect = (questionId: string) => {
    console.log('🔍 [AnnotationMode] Question selected:', questionId);
    setSelectedQuestion(questionId);
    setSelectedSection(null);
    // Keep sections expanded since side panel shows entire question
  };

  // When a section is selected, minimize other sections
  const handleSectionSelect = (sectionId: string) => {
    console.log('🔍 [AnnotationMode] Section selected:', sectionId);
    setSelectedSection(sectionId);
    setSelectedQuestion(undefined);
    // Minimize all sections when a section is selected
    setExpandedSections(new Set());
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getQuestionAnnotation = (questionId: string) => {
    console.log('🔍 [AnnotationMode] Getting annotation for question:', questionId);
    console.log('🔍 [AnnotationMode] Current annotations:', currentAnnotations);
    console.log('🔍 [AnnotationMode] Question annotations:', currentAnnotations?.questionAnnotations);
    
    const annotation = currentAnnotations?.questionAnnotations?.find((qa: QuestionAnnotation) => qa.questionId === questionId);
    console.log('🔍 [AnnotationMode] Found annotation:', annotation);
    return annotation;
  };

  const getSectionAnnotation = (sectionId: string) => {
    return currentAnnotations?.sectionAnnotations?.find((sa: SectionAnnotation) => sa.sectionId === sectionId);
  };

  const handleQuestionAnnotation = (questionId: string, field: string, value: any) => {
    const existing = getQuestionAnnotation(questionId);
    const annotation: QuestionAnnotation = {
      questionId,
      required: field === 'required' ? value : existing?.required || false,
      quality: field === 'quality' ? value : existing?.quality || 3,
      relevant: field === 'relevant' ? value : existing?.relevant || 3,
      pillars: field === 'pillars' ? value : existing?.pillars || {},
      comment: field === 'comment' ? value : existing?.comment || '',
      annotatorId: 'current-user'
    };
    onQuestionAnnotation(annotation);
  };

  const handleSectionAnnotation = (sectionId: string, field: string, value: any) => {
    const existing = getSectionAnnotation(sectionId);
    const annotation: SectionAnnotation = {
      sectionId,
      quality: field === 'quality' ? value : existing?.quality || 3,
      relevant: field === 'relevant' ? value : existing?.relevant || 3,
      pillars: field === 'pillars' ? value : existing?.pillars || {},
      comment: field === 'comment' ? value : existing?.comment || '',
      annotatorId: 'current-user'
    };
    onSectionAnnotation(annotation);
  };

  const isAnnotated = (type: 'question' | 'section', id: string) => {
    if (type === 'question') {
      return getQuestionAnnotation(id) !== undefined;
    } else {
      return getSectionAnnotation(id) !== undefined;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
            <h2 className="text-lg font-semibold text-gray-900">Annotation Mode</h2>
            <div className="text-sm text-gray-500">
              {currentAnnotations?.questionAnnotations?.length || 0} questions • {currentAnnotations?.sectionAnnotations?.length || 0} sections
            </div>
          </div>
          <button
            onClick={onExitAnnotationMode}
            className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700"
          >
            Exit Annotation Mode
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Survey Structure */}
        <div className="w-1/2 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Survey Structure</h3>
            <div className="space-y-2">
              {sectionsToUse.map((section: any) => {
                const sectionId = String(section.id || section.section_id);
                return (
                <div key={sectionId} className={`border rounded-lg transition-all duration-200 ${
                  selectedSection === sectionId 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  {/* Section Header */}
                  <div className={`flex items-center justify-between p-3 transition-colors ${
                    selectedSection === sectionId 
                      ? 'bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}>
                    <div 
                      className="flex items-center space-x-2 cursor-pointer flex-1"
                      onClick={() => handleSectionSelect(sectionId)}
                    >
                      {selectedSection === sectionId && (
                        <div className="w-1 h-6 bg-blue-500 rounded-full"></div>
                      )}
                      <span className={`font-medium transition-colors ${
                        selectedSection === sectionId 
                          ? 'text-blue-900' 
                          : 'text-gray-900'
                      }`}>{section.title}</span>
                      {isAnnotated('section', sectionId) && (
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSection(sectionId);
                      }}
                      className={`p-1 rounded transition-colors ${
                        selectedSection === sectionId
                          ? 'text-blue-600 hover:text-blue-700 hover:bg-blue-100'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {expandedSections.has(sectionId) ? (
                        <ChevronDownIcon className="w-4 h-4" />
                      ) : (
                        <ChevronRightIcon className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Section Questions */}
                  {expandedSections.has(sectionId) && (
                    <div className="border-t border-gray-200 bg-gray-50">
                      {section.questions && section.questions.length > 0 ? (
                        section.questions.map((question: any) => {
                          const questionId = question.question_id || question.id;
                          return (
                            <div 
                              key={questionId}
                              className={`flex items-center justify-between p-3 cursor-pointer transition-all duration-200 ${
                                selectedQuestion === questionId
                                  ? 'bg-blue-100 border-l-4 border-blue-500 shadow-sm'
                                  : 'hover:bg-gray-100'
                              }`}
                              onClick={() => handleQuestionSelect(questionId)}
                            >
                              <div className="flex items-center space-x-2 flex-1 min-w-0">
                                {selectedQuestion === questionId && (
                                  <div className="w-1 h-4 bg-blue-500 rounded-full flex-shrink-0"></div>
                                )}
                                <span className={`text-sm transition-colors flex-1 min-w-0 ${
                                  selectedQuestion === questionId
                                    ? 'text-blue-900 font-medium'
                                    : 'text-gray-700'
                                }`}>
                                  {(() => {
                                    const fullText = question.question_text || question.text || 'No text';
                                    const words = fullText.split(' ');
                                    return words.length > 30 ? words.slice(0, 30).join(' ') + '...' : fullText;
                                  })()}
                                </span>
                                {isAnnotated('question', questionId) && (
                                  <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0 ml-2"></div>
                                )}
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-4 text-center text-gray-500">
                          <p className="text-sm">No questions in this section</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Panel - Annotation Form */}
        <div className="w-1/2 bg-gray-50 overflow-y-auto">
          <div className="p-4">
            {selectedQuestion ? (
              <QuestionAnnotationForm
                key={selectedQuestion}
                question={sectionsToUse.flatMap((s: any) => s.questions || []).find((q: any) => (q.question_id || q.id) === selectedQuestion)}
                annotation={getQuestionAnnotation(selectedQuestion)}
                onSave={(annotation) => {
                  onQuestionAnnotation(annotation);
                  setSelectedQuestion(undefined);
                }}
                onCancel={() => setSelectedQuestion(undefined)}
              />
            ) : selectedSection ? (
              <SectionAnnotationForm
                section={sectionsToUse.find((s: any) => String(s.id || s.section_id) === selectedSection)}
                annotation={getSectionAnnotation(selectedSection)}
                onSave={(annotation) => {
                  onSectionAnnotation(annotation);
                  setSelectedSection(null);
                }}
                onCancel={() => setSelectedSection(null)}
              />
            ) : (
              <div className="text-center py-12">
                <TagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select an Item to Annotate</h3>
                <p className="text-gray-500">Click on a question or section to start annotating</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Question Annotation Form with Pillars and Options
const QuestionAnnotationForm: React.FC<{
  question: any;
  annotation?: QuestionAnnotation;
  onSave: (annotation: QuestionAnnotation) => void;
  onCancel: () => void;
}> = ({ question, annotation, onSave, onCancel }) => {
  console.log('🔍 [QuestionAnnotationForm] Component rendered with:', {
    questionId: question?.id || question?.question_id,
    questionText: question?.text || question?.question_text,
    annotation,
    hasAnnotation: !!annotation
  });

  const [formData, setFormData] = useState({
    required: annotation?.required || false,
    quality: annotation?.quality || 3,
    relevant: annotation?.relevant || 3,
    pillars: annotation?.pillars || {
      methodologicalRigor: 3,
      contentValidity: 3,
      respondentExperience: 3,
      analyticalValue: 3,
      businessImpact: 3
    },
    comment: annotation?.comment || ''
  });

  // Update form data when annotation changes
  useEffect(() => {
    console.log('🔍 [QuestionAnnotationForm] useEffect triggered - annotation changed:', annotation);
    setFormData({
      required: annotation?.required || false,
      quality: annotation?.quality || 3,
      relevant: annotation?.relevant || 3,
      pillars: annotation?.pillars || {
        methodologicalRigor: 3,
        contentValidity: 3,
        respondentExperience: 3,
        analyticalValue: 3,
        businessImpact: 3
      },
      comment: annotation?.comment || ''
    });
  }, [annotation]);

  // Safety check for undefined question
  if (!question) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="text-center text-gray-500">
          <p>Question not found</p>
          <button
            onClick={onCancel}
            className="mt-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    const newAnnotation: QuestionAnnotation = {
      questionId: question.question_id || question.id,
      ...formData,
      annotatorId: 'current-user'
    };
    onSave(newAnnotation);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Question Annotation</h3>
        <p className="text-sm text-gray-600 mb-4">{question.question_text || question.text || 'No question text available'}</p>
        
        {/* Question Options */}
        {question.options && question.options.length > 0 && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Options:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              {question.options.map((option: any, index: number) => (
                <li key={index} className="flex items-center">
                  <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium mr-2">
                    {index + 1}
                  </span>
                  {option.text || option.label || option}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {/* Required Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">Required</label>
          <button
            onClick={() => setFormData({...formData, required: !formData.required})}
            className={`w-12 h-6 rounded-full transition-colors ${
              formData.required ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform ${
              formData.required ? 'translate-x-6' : 'translate-x-0.5'
            }`} />
          </button>
        </div>

        {/* Quality & Relevance Scales */}
        <div className="space-y-3">
          <LikertScale
            label="Quality"
            value={formData.quality}
            onChange={(value) => setFormData({...formData, quality: value})}
            lowLabel="Poor"
            highLabel="Excellent"
          />
          <LikertScale
            label="Relevance"
            value={formData.relevant}
            onChange={(value) => setFormData({...formData, relevant: value})}
            lowLabel="Low"
            highLabel="High"
          />
        </div>

        {/* Five Pillars */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Five Pillars Assessment</h4>
          <div className="grid grid-cols-1 gap-3">
            <LikertScale
              label="Methodological Rigor"
              value={formData.pillars.methodologicalRigor}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, methodologicalRigor: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Content Validity"
              value={formData.pillars.contentValidity}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, contentValidity: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Respondent Experience"
              value={formData.pillars.respondentExperience}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, respondentExperience: value }
              })}
              lowLabel="Poor"
              highLabel="Excellent"
            />
            <LikertScale
              label="Analytical Value"
              value={formData.pillars.analyticalValue}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, analyticalValue: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Business Impact"
              value={formData.pillars.businessImpact}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, businessImpact: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
          </div>
        </div>

        {/* Comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Comment</label>
          <textarea
            value={formData.comment}
            onChange={(e) => setFormData({...formData, comment: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
            rows={3}
            placeholder="Add your observations..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-2 pt-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Section Annotation Form with Pillars
const SectionAnnotationForm: React.FC<{
  section: any;
  annotation?: SectionAnnotation;
  onSave: (annotation: SectionAnnotation) => void;
  onCancel: () => void;
}> = ({ section, annotation, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    quality: annotation?.quality || 3,
    relevant: annotation?.relevant || 3,
    pillars: annotation?.pillars || {
      methodologicalRigor: 3,
      contentValidity: 3,
      respondentExperience: 3,
      analyticalValue: 3,
      businessImpact: 3
    },
    comment: annotation?.comment || ''
  });

  const handleSave = () => {
    const newAnnotation: SectionAnnotation = {
      sectionId: String(section.id || section.section_id),
      ...formData,
      annotatorId: 'current-user'
    };
    onSave(newAnnotation);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Section Annotation</h3>
        <p className="text-sm text-gray-600 mb-4">{section.title}</p>
      </div>

      <div className="space-y-4">
        {/* Quality & Relevance Scales */}
        <div className="space-y-3">
          <LikertScale
            label="Quality"
            value={formData.quality}
            onChange={(value) => setFormData({...formData, quality: value})}
            lowLabel="Poor"
            highLabel="Excellent"
          />
          <LikertScale
            label="Relevance"
            value={formData.relevant}
            onChange={(value) => setFormData({...formData, relevant: value})}
            lowLabel="Low"
            highLabel="High"
          />
        </div>

        {/* Five Pillars */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Five Pillars Assessment</h4>
          <div className="grid grid-cols-1 gap-3">
            <LikertScale
              label="Methodological Rigor"
              value={formData.pillars.methodologicalRigor}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, methodologicalRigor: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Content Validity"
              value={formData.pillars.contentValidity}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, contentValidity: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Respondent Experience"
              value={formData.pillars.respondentExperience}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, respondentExperience: value }
              })}
              lowLabel="Poor"
              highLabel="Excellent"
            />
            <LikertScale
              label="Analytical Value"
              value={formData.pillars.analyticalValue}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, analyticalValue: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Business Impact"
              value={formData.pillars.businessImpact}
              onChange={(value) => setFormData({
                ...formData,
                pillars: { ...formData.pillars, businessImpact: value }
              })}
              lowLabel="Low"
              highLabel="High"
            />
          </div>
        </div>

        {/* Comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Comment</label>
          <textarea
            value={formData.comment}
            onChange={(e) => setFormData({...formData, comment: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
            rows={3}
            placeholder="Add your observations..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-2 pt-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnnotationMode;
