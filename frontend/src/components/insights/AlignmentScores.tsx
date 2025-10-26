import React from 'react';

interface AlignmentScoresProps {
  methodologyAlignment?: {
    score: number;
    methodology_details?: Array<{
      methodology: string;
      score: number;
      golden_examples_count: number;
    }>;
  };
  industryAlignment?: {
    score: number;
    industry: string;
    golden_examples_count?: number;
  };
}

const AlignmentScores: React.FC<AlignmentScoresProps> = ({
  methodologyAlignment,
  industryAlignment,
}) => {
  const ScoreBar = ({ label, score }: { label: string; score: number }) => {
    const percent = Math.round(score * 100);
    
    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700">{label}</span>
          <span className="font-semibold text-gray-900">{percent}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              percent >= 80 ? 'bg-green-500' : 
              percent >= 60 ? 'bg-yellow-500' : 
              'bg-red-500'
            }`}
            style={{ width: `${percent}%` }}
          ></div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Alignment Scores</h3>
      
      <div className="space-y-4">
        {methodologyAlignment && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Methodology Alignment</h4>
            <ScoreBar label="Overall" score={methodologyAlignment.score} />
            
            {methodologyAlignment.methodology_details && methodologyAlignment.methodology_details.length > 0 && (
              <div className="mt-3 space-y-2 pl-2 border-l-2 border-purple-200">
                {methodologyAlignment.methodology_details.map((detail, index) => (
                  <div key={index} className="text-xs">
                    <span className="font-medium text-purple-700">{detail.methodology}:</span>
                    <span className="text-gray-600 ml-1">{Math.round(detail.score * 100)}%</span>
                    {detail.golden_examples_count > 0 && (
                      <span className="text-gray-400 ml-2">
                        ({detail.golden_examples_count} examples)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {industryAlignment && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Industry Alignment</h4>
            <div className="flex items-center justify-between">
              <ScoreBar label={industryAlignment.industry || 'Unknown'} score={industryAlignment.score} />
            </div>
            {industryAlignment.golden_examples_count && industryAlignment.golden_examples_count > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Based on {industryAlignment.golden_examples_count} industry examples
              </p>
            )}
          </div>
        )}

        {!methodologyAlignment && !industryAlignment && (
          <p className="text-sm text-gray-500 text-center py-4">No alignment data available</p>
        )}
      </div>
    </div>
  );
};

export default AlignmentScores;

