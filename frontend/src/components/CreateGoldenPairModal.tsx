import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { LLMAuditRecord } from '../types';

interface CreateGoldenPairModalProps {
  isOpen: boolean;
  onClose: () => void;
  auditRecord: LLMAuditRecord | null;
  onSuccess: () => void;
}

interface FormData {
  industryCategory: string;
  researchGoal: string;
  qualityScore: number | null;
  reviewNotes: string;
}

export const CreateGoldenPairModal: React.FC<CreateGoldenPairModalProps> = ({
  isOpen,
  onClose,
  auditRecord,
  onSuccess
}) => {
  const [formData, setFormData] = useState<FormData>({
    industryCategory: '',
    researchGoal: '',
    qualityScore: null,
    reviewNotes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Extract quality score from audit record
  useEffect(() => {
    if (auditRecord?.raw_response) {
      try {
        const response = typeof auditRecord.raw_response === 'string' 
          ? JSON.parse(auditRecord.raw_response) 
          : auditRecord.raw_response;
        
        const finalOutput = response.final_output || response;
        const metadata = finalOutput.metadata || {};
        const score = metadata.quality_score;
        
        if (score) {
          setFormData(prev => ({ ...prev, qualityScore: score }));
          
          // Add warning if score is low
          if (score < 0.7) {
            setWarnings(['Quality score is below 0.7 - review carefully before creating golden pair']);
          }
        }
      } catch (e) {
        console.error('Failed to extract quality score:', e);
      }
    }
  }, [auditRecord]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!auditRecord || !formData.industryCategory || !formData.researchGoal) {
      setError('Industry category and research goal are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/llm-audit/interactions/${auditRecord.interaction_id}/create-golden-pair`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            industry_category: formData.industryCategory,
            research_goal: formData.researchGoal,
            quality_score: formData.qualityScore,
            review_notes: formData.reviewNotes
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create golden pair');
      }

      const result = await response.json();
      console.log('Golden pair created:', result);
      
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error creating golden pair:', err);
      setError(err instanceof Error ? err.message : 'Failed to create golden pair');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !auditRecord) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Create Golden Pair from Audit Record
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Warnings</h3>
                  <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside">
                    {warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Form Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry Category <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.industryCategory}
              onChange={(e) => setFormData({ ...formData, industryCategory: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            >
              <option value="">Select Industry...</option>
              <option value="consumer_goods">Consumer Goods</option>
              <option value="technology">Technology</option>
              <option value="healthcare">Healthcare</option>
              <option value="financial_services">Financial Services</option>
              <option value="retail">Retail</option>
              <option value="automotive">Automotive</option>
              <option value="telecommunications">Telecommunications</option>
              <option value="media_entertainment">Media & Entertainment</option>
              <option value="travel_hospitality">Travel & Hospitality</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Research Goal <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.researchGoal}
              onChange={(e) => setFormData({ ...formData, researchGoal: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            >
              <option value="">Select Research Goal...</option>
              <option value="brand_tracking">Brand Tracking</option>
              <option value="concept_testing">Concept Testing</option>
              <option value="pricing_research">Pricing Research</option>
              <option value="customer_satisfaction">Customer Satisfaction</option>
              <option value="market_segmentation">Market Segmentation</option>
              <option value="product_development">Product Development</option>
              <option value="ad_testing">Ad Testing</option>
              <option value="usage_attitudes">Usage & Attitudes</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quality Score (0.0 - 1.0)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={formData.qualityScore || ''}
              onChange={(e) => setFormData({ ...formData, qualityScore: e.target.value ? parseFloat(e.target.value) : null })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Leave empty to use default (0.85)"
            />
            <p className="mt-1 text-sm text-gray-500">
              Extracted from audit record or defaults to 0.85
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Review Notes (Optional)
            </label>
            <textarea
              value={formData.reviewNotes}
              onChange={(e) => setFormData({ ...formData, reviewNotes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Any notes about this golden pair..."
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.industryCategory || !formData.researchGoal}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Golden Pair'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
