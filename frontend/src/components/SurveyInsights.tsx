import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAppStore } from '../store/useAppStore';
import BestMatchCard from './insights/BestMatchCard';
import SimilarityBreakdown from './insights/SimilarityBreakdown';
import AlignmentScores from './insights/AlignmentScores';
import PillarEvaluation from './insights/PillarEvaluation';

interface SurveyInsightsProps {
  surveyId: string;
}

const SurveyInsights: React.FC<SurveyInsightsProps> = ({ surveyId }) => {
  const { triggerEvaluationAsync, evaluationInProgress } = useAppStore();
  const [qualityAnalysis, setQualityAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isEvaluating = evaluationInProgress[surveyId];

  useEffect(() => {
    const loadQualityAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        // First try cached analysis
        let analysis = await apiService.fetchQualityAnalysis(surveyId);
        // If no detailed breakdown present, force a refresh to recompute on backend
        const hasBreakdown = !!analysis?.golden_similarity_analysis?.similarity_breakdown;
        if (!hasBreakdown) {
          analysis = await apiService.fetchQualityAnalysis(surveyId, true);
        }
        setQualityAnalysis(analysis);
      } catch (err: any) {
        console.error('Failed to load quality analysis:', err);
        setError(err.message || 'Failed to load quality analysis');
      } finally {
        setLoading(false);
      }
    };

    loadQualityAnalysis();
  }, [surveyId, isEvaluating]); // Reload when evaluation status changes

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <h3 className="text-red-800 font-medium">Error Loading Quality Analysis</h3>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!qualityAnalysis) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-yellow-800 font-medium">Analysis Not Available</h3>
          <p className="text-yellow-700 text-sm mt-1">
            No quality analysis data found for this survey.
          </p>
        </div>
      </div>
    );
  }

  const { golden_similarity_analysis, pillar_evaluation, evaluation_mode } = qualityAnalysis;
  const breakdown = golden_similarity_analysis?.similarity_breakdown;

  // Check if this is legacy data
  const isLegacyAnalysis = golden_similarity_analysis?.note?.includes("Legacy analysis");

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Quality Analysis</h2>
        <div className="flex items-center gap-2 mt-1">
          <p className="text-sm text-gray-500">
            Evaluation Mode: <span className="font-medium">{evaluation_mode.toUpperCase()}</span>
          </p>
          {isLegacyAnalysis && (
            <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
              Legacy Data
            </span>
          )}
        </div>
      </div>

      {/* Legacy notice */}
      {isLegacyAnalysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Note:</strong> This survey was generated before detailed similarity analysis was available. 
            Showing available legacy similarity data.
          </p>
        </div>
      )}

      {/* Best Match Card - only if we have meaningful data */}
      {golden_similarity_analysis?.best_match && 
       golden_similarity_analysis.best_match.similarity > 0 && (
        <BestMatchCard match={golden_similarity_analysis.best_match} />
      )}

      {/* Industry & Methodology Alignment - only if we have matching data */}
      {(golden_similarity_analysis?.best_industry_match || golden_similarity_analysis?.best_methodology_match) && 
       (golden_similarity_analysis?.best_industry_match?.similarity > 0 || golden_similarity_analysis?.best_methodology_match?.similarity > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {golden_similarity_analysis?.best_industry_match && golden_similarity_analysis.best_industry_match.similarity > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">🏭 Best Industry Match</h3>
              <p className="text-sm text-blue-700">
                <strong>{Math.round(golden_similarity_analysis.best_industry_match.similarity * 100)}%</strong> similar
              </p>
              <p className="text-xs text-blue-600 mt-1">
                {golden_similarity_analysis.best_industry_match.title}
              </p>
            </div>
          )}

          {golden_similarity_analysis?.best_methodology_match && golden_similarity_analysis.best_methodology_match.similarity > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-900 mb-2">📊 Best Methodology Match</h3>
              <p className="text-sm text-purple-700">
                <strong>{Math.round(golden_similarity_analysis.best_methodology_match.similarity * 100)}%</strong> similar
              </p>
              <p className="text-xs text-purple-600 mt-1">
                {golden_similarity_analysis.best_methodology_match.title}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Detailed Similarity Breakdown (new) */}
      {breakdown && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">Methodology Similarity</h3>
            <p className="text-2xl font-bold text-gray-800">{Math.round((breakdown.methodology_similarity || 0) * 100)}%</p>
            <p className="text-xs text-gray-500 mt-1">Jaccard overlap of methodology tags</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">Question Match Rate</h3>
            <p className="text-2xl font-bold text-gray-800">{Math.round((breakdown.question_match?.match_rate || 0) * 100)}%</p>
            <p className="text-xs text-gray-500 mt-1">
              {breakdown.question_match?.matched_pairs?.length || 0} matched · {breakdown.question_match?.total_a || 0} vs {breakdown.question_match?.total_b || 0}
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">Semantic Similarity</h3>
            <p className="text-2xl font-bold text-gray-800">{Math.round((breakdown.semantic_similarity || 0) * 100)}%</p>
            <p className="text-xs text-gray-500 mt-1">TF-IDF cosine on survey text</p>
          </div>
        </div>
      )}

      {/* Alignment Scores - only if we have meaningful scores */}
      {golden_similarity_analysis && 
       ((golden_similarity_analysis.methodology_alignment?.score > 0) || 
        (golden_similarity_analysis.industry_alignment?.score > 0)) && (
        <AlignmentScores
          methodologyAlignment={golden_similarity_analysis.methodology_alignment}
          industryAlignment={golden_similarity_analysis.industry_alignment}
        />
      )}

      {/* Similarity Breakdown - only if we have similarities */}
      {golden_similarity_analysis?.individual_similarities && 
       golden_similarity_analysis.individual_similarities.length > 0 &&
       golden_similarity_analysis.individual_similarities.some((s: any) => s.similarity > 0) && (
        <SimilarityBreakdown similarities={golden_similarity_analysis.individual_similarities} />
      )}

      {/* AI Pillar Evaluation */}
      {pillar_evaluation ? (
        <PillarEvaluation evaluation={pillar_evaluation} />
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">AI Pillar Evaluation</h3>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            {isEvaluating ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <p className="text-sm text-gray-600">Evaluation in progress...</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <p className="text-sm text-gray-600">
                  No pillar evaluation data available for this survey. Run an evaluation to get AI-powered quality assessment.
                </p>
                <button
                  onClick={() => triggerEvaluationAsync(surveyId)}
                  disabled={isEvaluating}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed w-fit"
                >
                  <span>Run Evaluation</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fallback for older surveys with limited data */}
      {isLegacyAnalysis && golden_similarity_analysis?.overall_average > 0 && 
       !golden_similarity_analysis?.best_match && 
       !pillar_evaluation && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <div className="max-w-md mx-auto">
            <div className="text-4xl mb-2">📊</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Similarity Score</h3>
            <div className="text-3xl font-bold text-blue-600 mb-4">
              {Math.round(golden_similarity_analysis.overall_average * 100)}%
            </div>
            <p className="text-sm text-gray-600">
              Overall similarity to golden examples
            </p>
            {golden_similarity_analysis.total_golden_examples_analyzed > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                Based on {golden_similarity_analysis.total_golden_examples_analyzed} golden example{golden_similarity_analysis.total_golden_examples_analyzed !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Show message when there's no similarity data at all */}
      {golden_similarity_analysis && 
       !golden_similarity_analysis?.best_match && 
       (!golden_similarity_analysis?.individual_similarities || golden_similarity_analysis.individual_similarities.length === 0) &&
       golden_similarity_analysis?.overall_average === 0 &&
       !pillar_evaluation && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="max-w-md mx-auto">
            <div className="text-4xl mb-2">🔍</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Similarity Analysis Available</h3>
            <p className="text-sm text-gray-600 mb-2">
              This survey doesn't have similarity data against golden examples yet.
            </p>
            {golden_similarity_analysis.total_golden_examples_analyzed === 0 && (
              <p className="text-xs text-gray-500 mt-2">
                No golden examples were used during generation or none are available for comparison.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveyInsights;

