import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, Survey } from '../types';

const QuestionCard: React.FC<{ 
  question: Question; 
  index: number; 
  onUpdate: (updatedQuestion: Question) => void; 
  onDelete: () => void;
  onRegenerate: (questionId: string) => void;
  onMove: (questionId: string, direction: 'up' | 'down') => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isEditingSurvey: boolean;
}> = ({ question, index, onUpdate, onDelete, onRegenerate, onMove, canMoveUp, canMoveDown, isEditingSurvey }) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  const isSelected = selectedQuestionId === question.id;
  const [isEditing, setIsEditing] = useState(false);
  const [editedQuestion, setEditedQuestion] = useState<Question>(question);

  const handleSaveEdit = () => {
    onUpdate(editedQuestion);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedQuestion(question);
    setIsEditing(false);
  };

  const updateQuestionField = (field: keyof Question, value: any) => {
    setEditedQuestion(prev => ({ ...prev, [field]: value }));
  };

  const addOption = () => {
    const newOptions = [...(editedQuestion.options || []), ''];
    updateQuestionField('options', newOptions);
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...(editedQuestion.options || [])];
    newOptions[index] = value;
    updateQuestionField('options', newOptions);
  };

  const removeOption = (index: number) => {
    const newOptions = editedQuestion.options?.filter((_, i) => i !== index) || [];
    updateQuestionField('options', newOptions);
  };

  return (
    <div 
      className={`
        border rounded-lg p-4 cursor-pointer transition-all duration-200
        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
      `}
      onClick={() => setSelectedQuestion(isSelected ? undefined : question.id)}
    >
      {/* Question Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-500">Q{index + 1}</span>
          {question.methodology && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {question.methodology}
            </span>
          )}
          <span className={`
            inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
            ${question.category === 'screening' ? 'bg-yellow-100 text-yellow-800' :
              question.category === 'pricing' ? 'bg-green-100 text-green-800' :
              question.category === 'features' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'}
          `}>
            {question.category}
          </span>
        </div>
        
        {question.required && (
          <span className="text-red-500 text-sm">*</span>
        )}
      </div>

      {/* Question Text */}
      {isEditing ? (
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">Question Text</label>
          <textarea
            value={editedQuestion.text}
            onChange={(e) => updateQuestionField('text', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            rows={2}
          />
        </div>
      ) : (
        <h3 className="font-medium text-gray-900 mb-3">
          {question.text}
        </h3>
      )}

      {/* Question Options/Input */}
      <div className="mb-3">
        {question.type === 'multiple_choice' && (
          <div className="space-y-2">
            {isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Options</label>
                <div className="space-y-2">
                  {editedQuestion.options?.map((option, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={option}
                        onChange={(e) => updateOption(idx, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        placeholder={`Option ${idx + 1}`}
                      />
                      <button
                        onClick={() => removeOption(idx)}
                        className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addOption}
                    className="px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
                  >
                    Add Option
                  </button>
                </div>
              </div>
            ) : (
              question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center">
                  <input
                    type="radio"
                    disabled
                    className="h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {option}
                  </label>
                </div>
              ))
            )}
          </div>
        )}
        
        {question.type === 'scale' && (
          <div className="space-y-3">
            {/* Scale options as radio buttons */}
            <div className="space-y-2">
              {question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center">
                  <input
                    type="radio"
                    disabled
                    className="h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    {option}
                  </label>
                </div>
              ))}
            </div>
            
            {/* Scale labels if available */}
            {question.scale_labels && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md">
                <div className="text-xs font-medium text-gray-600 mb-2">Scale Labels:</div>
                <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                  {Object.entries(question.scale_labels).map(([key, value]) => (
                    <span key={key} className="flex items-center">
                      <span className="font-medium">{key}:</span>
                      <span className="ml-1">{value}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {question.type === 'ranking' && (
          <div className="space-y-3">
            <div className="text-sm text-gray-600 mb-3">
              Please rank the following options in order of importance (drag to reorder):
            </div>
            <div className="space-y-2">
              {question.options?.map((option, idx) => (
                <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 rounded-full text-sm font-medium mr-3">
                    {idx + 1}
                  </div>
                  <span className="text-sm text-gray-700 flex-1">{option}</span>
                  <div className="flex space-x-1">
                    <button
                      disabled
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      disabled
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Move down"
                    >
                      ↓
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {question.type === 'text' && (
          <input
            type="text"
            disabled
            placeholder="Respondent will enter text here..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
          />
        )}
      </div>

      {/* AI Rationale (when expanded) */}
      {isSelected && question.ai_rationale && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <h4 className="text-sm font-medium text-blue-900 mb-1">AI Rationale</h4>
          <p className="text-sm text-blue-800">{question.ai_rationale}</p>
        </div>
      )}
      
      {/* Question Controls (when expanded and in edit mode) */}
      {isSelected && isEditingSurvey && (
        <div className="mt-4 flex space-x-2">
          {isEditing ? (
            <>
              <button 
                onClick={handleSaveEdit}
                className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              >
                Save
              </button>
              <button 
                onClick={handleCancelEdit}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button 
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Edit
              </button>
              <button 
                onClick={() => onRegenerate(question.id)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Regenerate
              </button>
              <button 
                onClick={() => onMove(question.id, 'up')}
                disabled={!canMoveUp}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
              >
                Move Up
              </button>
              <button 
                onClick={() => onMove(question.id, 'down')}
                disabled={!canMoveDown}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
              >
                Move Down
              </button>
              <button 
                onClick={onDelete}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                Delete
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

interface SurveyPreviewProps {
  survey?: Survey;
  isEditable?: boolean;
  onSurveyChange?: (survey: Survey) => void;
}

export const SurveyPreview: React.FC<SurveyPreviewProps> = ({ 
  survey: propSurvey, 
  isEditable = false, 
  onSurveyChange 
}) => {
  const { currentSurvey, setSurvey, rfqInput, createGoldenExample } = useAppStore();
  const survey = propSurvey || currentSurvey;
  const [editedSurvey, setEditedSurvey] = useState<Survey | null>(null);
  const [isEditingSurvey, setIsEditingSurvey] = useState(isEditable);
  const [showGoldenModal, setShowGoldenModal] = useState(false);
  const [goldenFormData, setGoldenFormData] = useState({
    title: '',
    industry_category: '',
    research_goal: '',
    methodology_tags: [] as string[],
    quality_score: 0.9
  });

  // Comprehensive debug logging
  React.useEffect(() => {
    console.log('🔍 [SurveyPreview] ===== COMPONENT STATE UPDATE =====');
    console.log('🔍 [SurveyPreview] currentSurvey from store:', currentSurvey);
    console.log('🔍 [SurveyPreview] propSurvey from props:', propSurvey);
    console.log('🔍 [SurveyPreview] survey (propSurvey || currentSurvey):', survey);
    console.log('🔍 [SurveyPreview] isEditingSurvey:', isEditingSurvey);
    console.log('🔍 [SurveyPreview] editedSurvey:', editedSurvey);
    
    if (survey) {
      console.log('📊 [SurveyPreview] Survey structure analysis:');
      console.log('  - survey_id:', survey.survey_id);
      console.log('  - title:', survey.title);
      console.log('  - questions type:', typeof survey.questions);
      console.log('  - questions length:', survey.questions?.length);
      console.log('  - methodologies:', survey.methodologies);
      console.log('  - confidence_score:', survey.confidence_score);
      console.log('  - Has final_output:', !!survey.final_output);
      console.log('  - Has raw_output:', !!survey.raw_output);
      
      // Check if this looks like a valid survey
      const isValidSurvey = survey.title && survey.questions && Array.isArray(survey.questions);
      console.log('✅ [SurveyPreview] Is valid survey structure:', isValidSurvey);
    } else {
      console.log('❌ [SurveyPreview] No survey data available');
    }
    console.log('🔍 [SurveyPreview] ===== END STATE UPDATE =====');
  }, [currentSurvey, propSurvey, survey, isEditingSurvey, editedSurvey]);

  // Initialize edited survey when survey changes
  React.useEffect(() => {
    if (survey && !isEditingSurvey) {
      setEditedSurvey({ ...survey });
    }
  }, [survey, isEditingSurvey]);

  // Prepopulate golden form data when modal opens
  React.useEffect(() => {
    if (showGoldenModal && survey && rfqInput) {
      setGoldenFormData({
        title: survey.title || rfqInput.title || '',
        industry_category: rfqInput.product_category || '',
        research_goal: rfqInput.research_goal || '',
        methodology_tags: survey.methodologies || [],
        quality_score: survey.confidence_score || 0.9
      });
    }
  }, [showGoldenModal, survey, rfqInput]);

  const surveyToDisplay = isEditingSurvey ? editedSurvey : survey;

  const handleStartEditing = () => {
    setEditedSurvey({ ...survey! });
    setIsEditingSurvey(true);
  };

  const handleSaveEdits = () => {
    if (editedSurvey) {
      if (onSurveyChange) {
        onSurveyChange(editedSurvey);
      } else {
        setSurvey(editedSurvey);
      }
      setIsEditingSurvey(false);
    }
  };

  const handleCancelEdits = () => {
    setEditedSurvey({ ...survey! });
    setIsEditingSurvey(false);
  };

  const handleQuestionUpdate = (updatedQuestion: Question) => {
    if (!editedSurvey || !editedSurvey.questions) return;
    const updatedQuestions = editedSurvey.questions.map(q =>
      q.id === updatedQuestion.id ? updatedQuestion : q
    );
    setEditedSurvey({ ...editedSurvey, questions: updatedQuestions });
  };

  const handleQuestionDelete = (questionId: string) => {
    if (!editedSurvey || !editedSurvey.questions) return;
    const updatedQuestions = editedSurvey.questions.filter(q => q.id !== questionId);
    setEditedSurvey({ ...editedSurvey, questions: updatedQuestions });
  };

  const handleQuestionRegenerate = async (questionId: string) => {
    // TODO: Implement question regeneration using AI
    console.log('Regenerating question:', questionId);
    alert('Question regeneration coming soon!');
  };

  const handleMoveQuestion = (questionId: string, direction: 'up' | 'down') => {
    if (!editedSurvey || !editedSurvey.questions) return;
    const questions = [...editedSurvey.questions];
    const currentIndex = questions.findIndex(q => q.id === questionId);
    
    if (currentIndex === -1) return;
    
    let newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= questions.length) return;
    
    // Swap questions
    [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
    setEditedSurvey({ ...editedSurvey, questions });
  };

  const handleExportSurvey = (format: 'json' | 'clipboard' | 'qualtrics') => {
    if (!surveyToDisplay) return;
    
    const surveyData = JSON.stringify(surveyToDisplay, null, 2);
    
    switch (format) {
      case 'json':
        // Download as JSON file
        const blob = new Blob([surveyData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${surveyToDisplay.title || 'survey'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        break;
        
      case 'clipboard':
        // Copy to clipboard
        navigator.clipboard.writeText(surveyData).then(() => {
          alert('Survey data copied to clipboard!');
        }).catch(() => {
          alert('Failed to copy to clipboard');
        });
        break;
        
      case 'qualtrics':
        // TODO: Implement Qualtrics integration
        alert('Qualtrics integration coming soon!');
        break;
    }
  };

  const handleSaveAsGoldenExample = async () => {
    if (!surveyToDisplay || !rfqInput.description) return;

    try {
      await createGoldenExample({
        title: goldenFormData.title,
        rfq_text: rfqInput.description,
        survey_json: surveyToDisplay,
        methodology_tags: goldenFormData.methodology_tags,
        industry_category: goldenFormData.industry_category,
        research_goal: goldenFormData.research_goal,
        quality_score: goldenFormData.quality_score
      });
      setShowGoldenModal(false);
      alert('Successfully saved as golden example!');
    } catch (error) {
      alert('Failed to save as golden example. Please try again.');
    }
  };

  // Validate survey data before rendering
  const isValidSurvey = survey && 
                       typeof survey === 'object' && 
                       survey.title && 
                       survey.questions && 
                       Array.isArray(survey.questions);

  if (!survey) {
    console.log('❌ [SurveyPreview] No survey available');
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <p className="text-gray-500">No survey to preview yet.</p>
        <p className="text-sm text-gray-400 mt-2">Debug: survey is {typeof survey}</p>
      </div>
    );
  }

  if (!isValidSurvey) {
    console.log('❌ [SurveyPreview] Survey data is invalid or malformed');
    console.log('❌ [SurveyPreview] Survey structure:', {
      hasTitle: !!survey.title,
      hasQuestions: !!survey.questions,
      questionsIsArray: Array.isArray(survey.questions),
      questionsLength: survey.questions?.length,
      surveyKeys: Object.keys(survey || {})
    });
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <p className="text-gray-500">Survey data is invalid or malformed.</p>
        <p className="text-sm text-gray-400 mt-2">Debug: survey structure is invalid</p>
        <div className="mt-4 p-4 bg-gray-100 rounded text-left text-xs">
          <pre>{JSON.stringify(survey, null, 2)}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Survey Preview */}
        <div className="lg:col-span-3">
          {/* Survey Header */}
          <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg">
            {isEditingSurvey ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Survey Title</label>
                  <input
                    type="text"
                    value={editedSurvey?.title || ''}
                    onChange={(e) => setEditedSurvey(prev => prev ? { ...prev, title: e.target.value } : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Survey Description</label>
                  <textarea
                    value={editedSurvey?.description || ''}
                    onChange={(e) => setEditedSurvey(prev => prev ? { ...prev, description: e.target.value } : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    rows={3}
                  />
                </div>
              </div>
            ) : (
              <>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  {surveyToDisplay?.title}
                </h1>
                <p className="text-gray-600 mb-4">
                  {surveyToDisplay?.description}
                </p>
              </>
            )}
            <div className="flex items-center space-x-4 text-sm text-gray-500 mt-4">
              <span>⏱️ ~{surveyToDisplay?.estimated_time} minutes</span>
              <span>📊 {surveyToDisplay?.questions?.length || 0} questions</span>
            </div>
          </div>

          {/* Questions */}
          <div className="space-y-4">
            {surveyToDisplay?.questions && surveyToDisplay.questions.length > 0 ? (
              surveyToDisplay.questions?.map((question, index) => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  index={index}
                  onUpdate={handleQuestionUpdate}
                  onDelete={() => handleQuestionDelete(question.id)}
                  onRegenerate={handleQuestionRegenerate}
                  onMove={handleMoveQuestion}
                  canMoveUp={index > 0}
                  canMoveDown={index < (surveyToDisplay?.questions?.length || 0) - 1}
                  isEditingSurvey={isEditingSurvey}
                />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No questions available for this survey.</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-8 flex space-x-4">
            {isEditingSurvey ? (
              <>
                <button 
                  onClick={handleSaveEdits}
                  className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Save Changes
                </button>
                <button 
                  onClick={handleCancelEdits}
                  className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Cancel Editing
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={handleStartEditing}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Edit Survey
                </button>
                <button 
                  onClick={() => {
                    // Pre-populate form with survey methodologies
                    setGoldenFormData(prev => ({
                      ...prev,
                      methodology_tags: surveyToDisplay?.methodologies || [],
                      industry_category: rfqInput.product_category || '',
                      research_goal: rfqInput.research_goal || ''
                    }));
                    setShowGoldenModal(true);
                  }}
                  className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                >
                  Save as Golden Example
                </button>
                <button 
                  onClick={() => handleExportSurvey('json')}
                  className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Export
                </button>
              </>
            )}
          </div>
        </div>

        {/* Meta Panel */}
        <div className="space-y-6">
          {/* Confidence Score */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Quality Score</h3>
            <div className="flex items-center">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${surveyToDisplay?.confidence_score ? surveyToDisplay.confidence_score * 100 : 0}%` }}
                />
              </div>
              <span className="ml-3 text-sm font-medium text-gray-700">
                {Math.round((surveyToDisplay?.confidence_score || 0) * 100)}%
              </span>
            </div>
          </div>

          {/* Methodologies */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Methodologies</h3>
            <div className="flex flex-wrap gap-2">
              {surveyToDisplay?.methodologies?.map((method) => (
                <span 
                  key={method}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                >
                  {method.replace('_', ' ')}
                </span>
              )) || []}
            </div>
          </div>

          {/* Golden Examples */}
          {surveyToDisplay?.golden_examples && surveyToDisplay.golden_examples.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">Reference Examples</h3>
              <div className="space-y-2">
                {surveyToDisplay.golden_examples?.map((example) => (
                  <div key={example.id} className="p-2 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-700">{example.industry_category}</p>
                    <p className="text-xs text-gray-500">{example.research_goal}</p>
                  </div>
                )) || []}
              </div>
            </div>
          )}

          {/* Export Options */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Export Options</h3>
            <div className="space-y-2">
              <button 
                onClick={() => handleExportSurvey('json')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                📄 Download JSON
              </button>
              <button 
                onClick={() => handleExportSurvey('clipboard')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                📋 Copy to Clipboard
              </button>
              <button 
                onClick={() => handleExportSurvey('qualtrics')}
                className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                🔗 Send to Qualtrics
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Save as Golden Example Modal */}
      {showGoldenModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">Save Survey as Golden Example</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={goldenFormData.title}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="Enter a title for this golden example"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry Category</label>
                <select
                  value={goldenFormData.industry_category}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, industry_category: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select Industry</option>
                  <option value="Consumer Electronics">Consumer Electronics</option>
                  <option value="B2B Technology">B2B Technology</option>
                  <option value="Automotive">Automotive</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Financial Services">Financial Services</option>
                  <option value="Retail">Retail</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Research Goal</label>
                <select
                  value={goldenFormData.research_goal}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, research_goal: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select Research Goal</option>
                  <option value="pricing">Pricing Research</option>
                  <option value="feature_prioritization">Feature Prioritization</option>
                  <option value="brand_perception">Brand Perception</option>
                  <option value="purchase_journey">Purchase Journey</option>
                  <option value="market_segmentation">Market Segmentation</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Methodology Tags</label>
                <input
                  type="text"
                  value={goldenFormData.methodology_tags.join(', ')}
                  onChange={(e) => setGoldenFormData(prev => ({ 
                    ...prev, 
                    methodology_tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) 
                  }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="van_westendorp, conjoint, maxdiff, etc."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quality Score</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={goldenFormData.quality_score}
                  onChange={(e) => setGoldenFormData(prev => ({ ...prev, quality_score: parseFloat(e.target.value) || 0.9 }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div className="bg-gray-50 p-3 rounded-md">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Preview</h4>
                
                {/* RFQ Preview - First 5 lines */}
                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">RFQ (first 5 lines):</p>
                  <div className="text-xs text-gray-600 mt-1">
                    {rfqInput.description.split('\n').slice(0, 5).map((line, idx) => (
                      <p key={idx} className="truncate">{line}</p>
                    ))}
                    {rfqInput.description.split('\n').length > 5 && (
                      <p className="text-gray-500">... ({rfqInput.description.split('\n').length - 5} more lines)</p>
                    )}
                  </div>
                </div>

                <p className="text-sm text-gray-600 mt-1"><strong>Survey Title:</strong> {surveyToDisplay?.title}</p>
                <p className="text-sm text-gray-600 mt-1"><strong>Total Questions:</strong> {surveyToDisplay?.questions?.length || 0}</p>
                
                {/* Sample Questions - First 5 questions */}
                {surveyToDisplay?.questions && surveyToDisplay.questions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-gray-700">Sample Questions:</p>
                    <ul className="text-xs text-gray-600 mt-1 space-y-1">
                      {surveyToDisplay.questions?.slice(0, 5).map((q, idx) => (
                        <li key={idx} className="truncate">• {q.text}</li>
                      )) || []}
                      {surveyToDisplay.questions && surveyToDisplay.questions.length > 5 && (
                        <li className="text-gray-500">... and {surveyToDisplay.questions.length - 5} more questions</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowGoldenModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAsGoldenExample}
                disabled={!goldenFormData.industry_category || !goldenFormData.research_goal}
                className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                Save as Golden Example
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};