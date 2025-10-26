import React from 'react';

interface PillarEvaluationProps {
  evaluation: {
    overall_grade: string;
    weighted_score: number;
    pillar_breakdown?: Array<{
      pillar_name: string;
      display_name: string;
      score: number;
      grade: string;
    }>;
    recommendations?: string[];
    summary?: string;
  };
}

const PillarEvaluation: React.FC<PillarEvaluationProps> = ({ evaluation }) => {
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-green-500';
      case 'B': return 'bg-blue-500';
      case 'C': return 'bg-yellow-500';
      case 'D': return 'bg-orange-500';
      case 'F': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const hasBreakdownData = evaluation.pillar_breakdown && evaluation.pillar_breakdown.length > 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">AI Pillar Evaluation</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Overall Grade:</span>
          <span className={`px-3 py-1 rounded-full text-lg font-bold text-white ${getGradeColor(evaluation.overall_grade)}`}>
            {evaluation.overall_grade}
          </span>
          <span className="text-sm font-semibold text-gray-700">
            {Math.round(evaluation.weighted_score * 100)}%
          </span>
        </div>
      </div>

      {evaluation.summary && (
        <p className="text-sm text-gray-600 mb-4 italic">{evaluation.summary}</p>
      )}

      {!hasBreakdownData && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-gray-600">
            Pillar breakdown data not available for this evaluation. 
            Overall score: <strong>{Math.round(evaluation.weighted_score * 100)}%</strong> (Grade {evaluation.overall_grade})
          </p>
        </div>
      )}

      {hasBreakdownData && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700">Pillar Breakdown</h4>
          {evaluation.pillar_breakdown?.map((pillar, index) => {
            const percent = Math.round(pillar.score * 100);
            
            return (
              <div key={index} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700">{pillar.display_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{percent}%</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${getGradeColor(pillar.grade)}`}>
                      {pillar.grade}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${getGradeColor(pillar.grade)}`}
                    style={{ width: `${percent}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {hasBreakdownData && evaluation.recommendations && evaluation.recommendations.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Recommendations</h4>
          <ul className="space-y-1">
            {evaluation.recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="mr-2">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!hasBreakdownData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Note:</strong> Detailed pillar breakdown is not available for this older survey.
          </p>
        </div>
      )}
    </div>
  );
};

export default PillarEvaluation;

