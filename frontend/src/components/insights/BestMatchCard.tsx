import React from 'react';

interface BestMatchCardProps {
  match: {
    golden_id: string;
    title: string;
    similarity: number;
    match_type?: string;
    match_reason?: string;
    methodology_tags?: string[];
    industry_category?: string;
  };
}

const BestMatchCard: React.FC<BestMatchCardProps> = ({ match }) => {
  const similarityPercent = Math.round(match.similarity * 100);

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 rounded-lg p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🎯</span>
            <h3 className="text-lg font-bold text-gray-900">Best Match</h3>
          </div>
          
          <div className="mb-3">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-blue-600">{similarityPercent}%</span>
              <span className="text-sm text-gray-600">similar to golden example</span>
            </div>
            
            {/* Similarity bar */}
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${similarityPercent}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-2">
            <p className="font-semibold text-gray-800">{match.title}</p>
            
            {match.match_reason && (
              <p className="text-sm text-gray-600 italic">{match.match_reason}</p>
            )}
          </div>

          {/* Metadata */}
          <div className="mt-4 flex flex-wrap gap-2">
            {match.methodology_tags && match.methodology_tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {match.methodology_tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {match.industry_category && (
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                {match.industry_category}
              </span>
            )}
          </div>
        </div>

        {/* Match type indicator */}
        {match.match_type && (
          <div className="ml-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✓ {match.match_type}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default BestMatchCard;

