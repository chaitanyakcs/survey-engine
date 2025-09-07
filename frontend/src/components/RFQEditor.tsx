import React from 'react';
import { useAppStore } from '../store/useAppStore';

export const RFQEditor: React.FC = () => {
  const { rfqInput, setRFQInput, submitRFQ, workflow } = useAppStore();

  // Set default values when component mounts
  React.useEffect(() => {
    if (!rfqInput.title && !rfqInput.description && !rfqInput.product_category && !rfqInput.target_segment && !rfqInput.research_goal) {
      setRFQInput({
        title: 'Market Research Study',
        description: 'We are conducting a comprehensive market research study to understand customer preferences, pricing sensitivity, and feature priorities for our new product. The research should include both quantitative and qualitative methodologies to provide actionable insights for our product development and go-to-market strategy.\n\nKey research objectives:\n- Understand customer willingness to pay and price sensitivity\n- Identify most important product features and their relative importance\n- Assess brand perception and competitive positioning\n- Evaluate market size and target segment characteristics\n\nPlease include methodologies such as Van Westendorp Price Sensitivity Meter, Conjoint Analysis, and MaxDiff for feature prioritization.',
        product_category: 'electronics',
        target_segment: 'General consumers',
        research_goal: 'pricing_research'
      });
    }
  }, [rfqInput, setRFQInput]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rfqInput.description.trim()) {
      await submitRFQ(rfqInput);
    }
  };

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Input Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title & Meta Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Survey Title
                </label>
                <input
                  type="text"
                  value={rfqInput.title || ''}
                  onChange={(e) => setRFQInput({ title: e.target.value })}
                  placeholder="Market Research Study"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Product Category
                </label>
                <select
                  value={rfqInput.product_category || ''}
                  onChange={(e) => setRFQInput({ product_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select category...</option>
                  <option value="electronics">Electronics</option>
                  <option value="appliances">Appliances</option>
                  <option value="healthcare_technology">Healthcare Technology</option>
                  <option value="enterprise_software">Enterprise Software</option>
                  <option value="automotive">Automotive</option>
                  <option value="financial_services">Financial Services</option>
                  <option value="hospitality">Hospitality</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Segment
                </label>
                <select
                  value={rfqInput.target_segment || ''}
                  onChange={(e) => setRFQInput({ target_segment: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select segment...</option>
                  <option value="B2B decision makers">B2B Decision Makers</option>
                  <option value="General consumers">General Consumers</option>
                  <option value="Healthcare professionals">Healthcare Professionals</option>
                  <option value="IT professionals">IT Professionals</option>
                  <option value="C-suite executives">C-Suite Executives</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Research Goal
                </label>
                <select
                  value={rfqInput.research_goal || ''}
                  onChange={(e) => setRFQInput({ research_goal: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select goal...</option>
                  <option value="pricing_research">Pricing Research</option>
                  <option value="feature_research">Feature Research</option>
                  <option value="satisfaction_research">Satisfaction Research</option>
                  <option value="brand_research">Brand Research</option>
                  <option value="market_sizing">Market Sizing</option>
                </select>
              </div>
            </div>

            {/* RFQ Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                RFQ Description *
              </label>
              <textarea
                value={rfqInput.description}
                onChange={(e) => setRFQInput({ description: e.target.value })}
                placeholder="Describe your research requirements in detail. Include methodologies, target audience, key questions, and any specific analysis needed..."
                rows={8}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
              />
              <p className="mt-1 text-sm text-gray-500">
                Be specific about methodologies (Van Westendorp, conjoint analysis, MaxDiff, etc.) and research objectives.
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!rfqInput.description.trim() || isLoading}
              className={`
                w-full py-3 px-4 rounded-md font-medium transition-all duration-200
                ${isLoading || !rfqInput.description.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                }
              `}
            >
              {isLoading ? 'Generating Survey...' : 'Generate Survey'}
            </button>
          </form>
        </div>

        {/* AI Hints Panel */}
        <div className="space-y-6">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">AI Suggestions</h3>
            
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Pricing Methodologies</h4>
                <div className="space-y-1">
                  <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">Van Westendorp PSM</span>
                  <span className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded text-xs ml-1">Gabor-Granger</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Feature Analysis</h4>
                <div className="space-y-1">
                  <span className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">Choice Conjoint</span>
                  <span className="inline-block bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs ml-1">MaxDiff</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Golden Examples</h4>
                <div className="space-y-2">
                  <div className="p-2 bg-white rounded border border-gray-200">
                    <p className="font-medium text-xs text-gray-700">Healthcare Technology Pricing</p>
                    <p className="text-xs text-gray-500">Van Westendorp + Gabor-Granger</p>
                  </div>
                  <div className="p-2 bg-white rounded border border-gray-200">
                    <p className="font-medium text-xs text-gray-700">B2B SaaS Feature Analysis</p>
                    <p className="text-xs text-gray-500">Choice Conjoint + Competitive</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};