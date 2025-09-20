import React from 'react';
import { Survey, getQuestionCount } from '../types';
import { 
  EyeIcon, 
  PencilIcon, 
  PlusIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface SurveyGenerationSummaryProps {
  survey: Survey;
  pillarScores: any;
  onViewSurvey: () => void;
  onEditSurvey: () => void;
  onStartNew: () => void;
}

export const SurveyGenerationSummary: React.FC<SurveyGenerationSummaryProps> = ({
  survey,
  pillarScores,
  onViewSurvey,
  onEditSurvey,
  onStartNew
}) => {
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-green-100 text-green-800';
      case 'B': return 'bg-yellow-100 text-yellow-800';
      case 'C': return 'bg-amber-100 text-amber-800';
      case 'D': return 'bg-orange-100 text-orange-800';
      case 'F': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-yellow-600';
    if (score >= 0.7) return 'text-amber-600';
    if (score >= 0.6) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-yellow-500 to-amber-500 rounded-full mb-6">
            <ChartBarIcon className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Analysis Complete
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Your survey has been generated and evaluated
          </p>
          <p className="text-lg text-gray-500 mb-8">
            {survey.title || 'Untitled Survey'}
          </p>
          
          {/* Action Buttons - Moved to top */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <button
              onClick={onViewSurvey}
              className="flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
            >
              <EyeIcon className="w-5 h-5 mr-2" />
              View Survey
            </button>
            <button
              onClick={onEditSurvey}
              className="flex items-center px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
            >
              <PencilIcon className="w-5 h-5 mr-2" />
              Edit Survey
            </button>
            <button
              onClick={onStartNew}
              className="flex items-center px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
            >
              <PlusIcon className="w-5 h-5 mr-2" />
              Create New Survey
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Survey Overview */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <CheckCircleIcon className="w-6 h-6 text-green-500 mr-3" />
                Survey Overview
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-xl">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {getQuestionCount(survey)}
                  </div>
                  <div className="text-sm font-medium text-blue-800">Questions</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-xl">
                  <div className="text-3xl font-bold text-purple-600 mb-2">
                    {survey.metadata?.estimated_time || 'N/A'}
                  </div>
                  <div className="text-sm font-medium text-purple-800">Minutes</div>
                </div>
                <div className="text-center p-4 bg-emerald-50 rounded-xl">
                  <div className="text-3xl font-bold text-emerald-600 mb-2">
                    {survey.metadata?.target_responses || 'N/A'}
                  </div>
                  <div className="text-sm font-medium text-emerald-800">Target Responses</div>
                </div>
              </div>

              {survey.description && (
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Description</h3>
                  <p className="text-gray-700 leading-relaxed">{survey.description}</p>
                </div>
              )}
            </div>

            {/* Pillar Scores */}
            {pillarScores && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <ChartBarIcon className="w-6 h-6 text-blue-500 mr-3" />
                  5-Pillar Quality Assessment
                </h2>
                
                {/* Overall Score */}
                <div className="text-center mb-8 p-6 bg-gradient-to-r from-blue-50 to-emerald-50 rounded-xl">
                  <div className="text-5xl font-bold text-gray-900 mb-2">
                    {Math.round(pillarScores.weighted_score * 100)}%
                  </div>
                  <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-semibold ${getGradeColor(pillarScores.overall_grade)}`}>
                    Grade {pillarScores.overall_grade}
                  </div>
                  {pillarScores.summary && (
                    <p className="text-gray-600 mt-4 text-lg">{pillarScores.summary}</p>
                  )}
                </div>

                {/* Pillar Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pillarScores.pillar_breakdown?.map((pillar: any, index: number) => (
                    <div key={index} className="bg-gray-50 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-gray-900">{pillar.display_name}</h3>
                        <div className="text-right">
                          <div className={`text-xl font-bold ${getScoreColor(pillar.score)}`}>
                            {Math.round(pillar.score * 100)}%
                          </div>
                          <div className={`text-sm px-2 py-1 rounded-full ${getGradeColor(pillar.grade)}`}>
                            {pillar.grade}
                          </div>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            pillar.score >= 0.9 ? 'bg-green-500' :
                            pillar.score >= 0.8 ? 'bg-yellow-500' :
                            pillar.score >= 0.7 ? 'bg-amber-500' :
                            pillar.score >= 0.6 ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${pillar.score * 100}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {pillar.criteria_met}/{pillar.total_criteria} criteria met
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recommendations */}
                {pillarScores.recommendations && pillarScores.recommendations.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <LightBulbIcon className="w-5 h-5 text-amber-500 mr-2" />
                      Recommendations
                    </h3>
                    <div className="space-y-2">
                      {pillarScores.recommendations.map((recommendation: string, index: number) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-amber-50 rounded-lg">
                          <ExclamationTriangleIcon className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{recommendation}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quality Score - Advanced Chain-of-Thought Evaluation */}
            {survey.pillar_scores?.weighted_score && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Score</h3>
                <div className="text-center">
                  <div className="text-4xl font-bold text-emerald-600 mb-2">
                    {Math.round(survey.pillar_scores.weighted_score * 100)}%
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-emerald-500 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${survey.pillar_scores.weighted_score * 100}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Grade {survey.pillar_scores.overall_grade} - Chain-of-Thought Evaluation
                  </p>
                </div>
              </div>
            )}

            {/* Methodologies */}
            {survey.methodologies && survey.methodologies.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Methodologies</h3>
                <div className="flex flex-wrap gap-2">
                  {survey.methodologies.map((method, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                    >
                      {method.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};