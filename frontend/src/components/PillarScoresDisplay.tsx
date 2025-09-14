import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  AcademicCapIcon,
  ChartBarIcon,
  EyeIcon,
  CogIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';

interface PillarScore {
  pillar_name: string;
  display_name: string;
  score: number;
  weighted_score: number;
  weight: number;
  criteria_met: number;
  total_criteria: number;
  grade: string;
}

interface PillarScores {
  overall_grade: string;
  weighted_score: number;
  total_score: number;
  summary: string;
  pillar_breakdown: PillarScore[];
  recommendations: string[];
}

interface PillarScoresDisplayProps {
  pillarScores: PillarScores;
  className?: string;
  compact?: boolean;
}

const PillarScoresDisplay: React.FC<PillarScoresDisplayProps> = ({ 
  pillarScores, 
  className = "",
  compact = false
}) => {
  if (!pillarScores) {
    return null;
  }

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'text-green-600 bg-green-100';
      case 'B': return 'text-blue-600 bg-blue-100';
      case 'C': return 'text-yellow-600 bg-yellow-100';
      case 'D': return 'text-orange-600 bg-orange-100';
      case 'F': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-blue-600';
    if (score >= 0.7) return 'text-yellow-600';
    if (score >= 0.6) return 'text-orange-600';
    return 'text-red-600';
  };

  const getPillarIcon = (pillarName: string) => {
    switch (pillarName) {
      case 'content_validity':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'methodological_rigor':
        return <AcademicCapIcon className="w-5 h-5" />;
      case 'clarity_comprehensibility':
        return <EyeIcon className="w-5 h-5" />;
      case 'structural_coherence':
        return <ChartBarIcon className="w-5 h-5" />;
      case 'deployment_readiness':
        return <RocketLaunchIcon className="w-5 h-5" />;
      default:
        return <CogIcon className="w-5 h-5" />;
    }
  };

  if (compact) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ChartBarIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">5-Pillar Evaluation</h3>
              <p className="text-sm text-gray-500">Survey quality assessment</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${getScoreColor(pillarScores.weighted_score)}`}>
              {Math.round(pillarScores.weighted_score * 100)}%
            </div>
            <div className={`text-sm font-semibold px-2 py-1 rounded-full ${getGradeColor(pillarScores.overall_grade)}`}>
              Grade {pillarScores.overall_grade}
            </div>
          </div>
        </div>

        {/* Compact Pillar Grid */}
        <div className="grid grid-cols-2 gap-3">
          {pillarScores.pillar_breakdown.map((pillar, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-1 bg-white rounded">
                    {getPillarIcon(pillar.pillar_name)}
                  </div>
                  <div>
                    <h5 className="text-sm font-medium text-gray-900">{pillar.display_name}</h5>
                    <p className="text-xs text-gray-500">{pillar.criteria_met}/{pillar.total_criteria}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-semibold ${getScoreColor(pillar.score)}`}>
                    {Math.round(pillar.score * 100)}%
                  </div>
                  <div className={`text-xs px-1.5 py-0.5 rounded-full ${getGradeColor(pillar.grade)}`}>
                    {pillar.grade}
                  </div>
                </div>
              </div>
              
              {/* Compact Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    pillar.score >= 0.9 ? 'bg-green-500' :
                    pillar.score >= 0.8 ? 'bg-blue-500' :
                    pillar.score >= 0.7 ? 'bg-yellow-500' :
                    pillar.score >= 0.6 ? 'bg-orange-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${pillar.score * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Compact Summary */}
        {pillarScores.summary && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">{pillarScores.summary}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <ChartBarIcon className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">5-Pillar Evaluation</h3>
            <p className="text-sm text-gray-600">Survey quality assessment</p>
          </div>
        </div>
        
        {/* Overall Grade */}
        <div className="text-right">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(pillarScores.overall_grade)}`}>
            Grade {pillarScores.overall_grade}
          </div>
          <div className={`text-2xl font-bold mt-1 ${getScoreColor(pillarScores.weighted_score)}`}>
            {Math.round(pillarScores.weighted_score * 100)}%
          </div>
        </div>
      </div>

      {/* Summary */}
      {pillarScores.summary && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">{pillarScores.summary}</p>
        </div>
      )}

      {/* Pillar Breakdown */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Pillar Breakdown</h4>
        {pillarScores.pillar_breakdown.map((pillar, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 bg-gray-100 rounded-md">
                  {getPillarIcon(pillar.pillar_name)}
                </div>
                <div>
                  <h5 className="font-medium text-gray-900">{pillar.display_name}</h5>
                  <p className="text-xs text-gray-500">
                    {pillar.criteria_met}/{pillar.total_criteria} criteria met
                  </p>
                </div>
              </div>
              
              <div className="text-right">
                <div className={`text-lg font-semibold ${getScoreColor(pillar.score)}`}>
                  {Math.round(pillar.score * 100)}%
                </div>
                <div className={`text-xs px-2 py-1 rounded-full ${getGradeColor(pillar.grade)}`}>
                  {pillar.grade}
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  pillar.score >= 0.9 ? 'bg-green-500' :
                  pillar.score >= 0.8 ? 'bg-blue-500' :
                  pillar.score >= 0.7 ? 'bg-yellow-500' :
                  pillar.score >= 0.6 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${pillar.score * 100}%` }}
              />
            </div>
            
            {/* Weight */}
            <div className="mt-2 text-xs text-gray-500">
              Weight: {Math.round(pillar.weight * 100)}% • 
              Weighted Score: {Math.round(pillar.weighted_score * 100)}%
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {pillarScores.recommendations && pillarScores.recommendations.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
            <ExclamationTriangleIcon className="w-4 h-4 mr-2 text-amber-500" />
            Recommendations
          </h4>
          <div className="space-y-2">
            {pillarScores.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                <div className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-2 flex-shrink-0" />
                <span>{recommendation}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PillarScoresDisplay;
