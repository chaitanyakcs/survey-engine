import React from 'react';
import { 
  TrashIcon, 
  EyeIcon, 
  ClockIcon, 
  ChartBarIcon,
  TagIcon,
  StarIcon
} from '@heroicons/react/24/outline';

interface SurveyCardProps {
  survey: {
    id: string;
    title: string;
    description: string;
    status: string;
    created_at: string;
    methodology_tags: string[];
    quality_score?: number;
    estimated_time?: number;
    question_count: number;
  };
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onView: () => void;
}

export const SurveyCard: React.FC<SurveyCardProps> = ({
  survey,
  isSelected,
  onSelect,
  onDelete,
  onView
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getQualityColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div
      className={`
        relative group cursor-pointer transition-all duration-300 ease-out
        ${isSelected 
          ? 'transform scale-[1.02] shadow-2xl ring-2 ring-blue-500 ring-opacity-50' 
          : 'hover:transform hover:scale-[1.02] hover:shadow-xl'
        }
      `}
      onClick={onSelect}
    >
      <div className={`
        bg-gradient-to-br from-white to-gray-50/50 rounded-2xl border-2 transition-all duration-300 overflow-hidden backdrop-blur-sm
        ${isSelected 
          ? 'border-blue-500 shadow-2xl' 
          : 'border-gray-200/50 hover:border-blue-300 hover:shadow-xl'
        }
      `}>
        {/* Header */}
        <div className="p-6 pb-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start space-x-3 flex-1">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-gray-900 text-base leading-tight line-clamp-2 group-hover:text-blue-900 transition-colors">
                  {survey.title}
                </h3>
                <p className="text-sm text-gray-600 line-clamp-2 mt-1 leading-relaxed">
                  {survey.description}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1 ml-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onView();
                }}
                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200 group-hover:bg-blue-50"
                title="View Survey"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200 group-hover:bg-red-50"
                title="Delete Survey"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          {/* Status Badge and Quality Score */}
          <div className="flex items-center justify-between mb-4">
            <span className={`
              inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold border-2 shadow-sm
              ${getStatusColor(survey.status)}
            `}>
              <div className={`w-2 h-2 rounded-full mr-2 ${
                survey.status === 'completed' ? 'bg-green-400' :
                survey.status === 'failed' ? 'bg-red-400' :
                survey.status === 'in_progress' ? 'bg-blue-400' : 'bg-gray-400'
              }`}></div>
              {survey.status.charAt(0).toUpperCase() + survey.status.slice(1)}
            </span>
            
            {/* Quality Score */}
            {survey.quality_score && (
              <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-full">
                <StarIcon className={`h-4 w-4 ${getQualityColor(survey.quality_score)}`} />
                <span className={`text-sm font-semibold ${getQualityColor(survey.quality_score)}`}>
                  {(survey.quality_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 bg-gradient-to-r from-gray-50/50 to-white/50">
          {/* Stats */}
          <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-white/80 px-3 py-1.5 rounded-lg shadow-sm">
                <ChartBarIcon className="h-4 w-4 text-blue-500" />
                <span className="font-medium">{survey.question_count} questions</span>
              </div>
              {survey.estimated_time && (
                <div className="flex items-center space-x-2 bg-white/80 px-3 py-1.5 rounded-lg shadow-sm">
                  <ClockIcon className="h-4 w-4 text-green-500" />
                  <span className="font-medium">{survey.estimated_time}min</span>
                </div>
              )}
            </div>
            <span className="text-sm font-medium bg-white/80 px-3 py-1.5 rounded-lg shadow-sm">
              {formatDate(survey.created_at)}
            </span>
          </div>

          {/* Methodology Tags */}
          {survey.methodology_tags && survey.methodology_tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {survey.methodology_tags.slice(0, 3).map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 text-sm font-medium rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <TagIcon className="h-3 w-3 mr-1.5" />
                  {tag}
                </span>
              ))}
              {survey.methodology_tags.length > 3 && (
                <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 text-sm font-medium rounded-xl shadow-sm">
                  +{survey.methodology_tags.length - 3}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Selection Indicator */}
        {isSelected && (
          <div className="absolute -right-2 -top-2 w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full border-3 border-white shadow-xl flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};
