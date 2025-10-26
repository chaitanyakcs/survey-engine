import React from 'react';

interface SimilarityBreakdownProps {
  similarities: Array<{
    golden_id: string;
    title: string;
    similarity: number;
    methodology_tags?: string[];
    industry_category?: string;
  }>;
}

const SimilarityBreakdown: React.FC<SimilarityBreakdownProps> = ({ similarities }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Similarity Breakdown</h3>
      
      <div className="space-y-3">
        {similarities.map((similarity, index) => {
          const percent = Math.round(similarity.similarity * 100);
          
          return (
            <div key={similarity.golden_id || index} className="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-gray-800 truncate flex-1">
                  {similarity.title}
                </p>
                <span className="text-sm font-bold text-gray-700 ml-2">{percent}%</span>
              </div>
              
              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    percent >= 80 ? 'bg-green-500' : 
                    percent >= 60 ? 'bg-yellow-500' : 
                    'bg-red-500'
                  }`}
                  style={{ width: `${percent}%` }}
                ></div>
              </div>

              {/* Tags */}
              {(similarity.methodology_tags || similarity.industry_category) && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {similarity.methodology_tags?.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="px-1.5 py-0.5 text-xs bg-purple-50 text-purple-600 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                  {similarity.industry_category && (
                    <span className="px-1.5 py-0.5 text-xs bg-blue-50 text-blue-600 rounded">
                      {similarity.industry_category}
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {similarities.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">No similarity data available</p>
      )}
    </div>
  );
};

export default SimilarityBreakdown;

