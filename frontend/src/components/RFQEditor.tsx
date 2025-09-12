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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-indigo-400/20 to-pink-600/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-cyan-400/10 to-blue-600/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      <div className="relative max-w-7xl mx-auto p-4 lg:p-6">

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Input Form */}
          <div className="xl:col-span-3">
            <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-6 lg:p-8">
              <form onSubmit={handleSubmit} className="space-y-6">

                {/* Title & Meta Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                      Survey Title
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={rfqInput.title || ''}
                        onChange={(e) => setRFQInput({ title: e.target.value })}
                        placeholder="Market Research Study"
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 placeholder-gray-400"
                      />
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                  
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                      Product Category
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.product_category || ''}
                        onChange={(e) => setRFQInput({ product_category: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-green-500/20 focus:border-green-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
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
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-green-500/10 to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center">
                      <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                      Target Segment
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.target_segment || ''}
                        onChange={(e) => setRFQInput({ target_segment: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
                      >
                        <option value="">Select segment...</option>
                        <option value="B2B decision makers">B2B Decision Makers</option>
                        <option value="General consumers">General Consumers</option>
                        <option value="Healthcare professionals">Healthcare Professionals</option>
                        <option value="IT professionals">IT Professionals</option>
                        <option value="C-suite executives">C-Suite Executives</option>
                      </select>
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                  
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center">
                      <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
                      Research Goal
                    </label>
                    <div className="relative">
                      <select
                        value={rfqInput.research_goal || ''}
                        onChange={(e) => setRFQInput({ research_goal: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 appearance-none cursor-pointer"
                      >
                        <option value="">Select goal...</option>
                        <option value="pricing_research">Pricing Research</option>
                        <option value="feature_research">Feature Research</option>
                        <option value="satisfaction_research">Satisfaction Research</option>
                        <option value="brand_research">Brand Research</option>
                        <option value="market_sizing">Market Sizing</option>
                      </select>
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>
                  </div>
                </div>

                {/* RFQ Description */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-lg font-semibold text-gray-900 flex items-center">
                      <div className="w-6 h-6 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg mr-3 flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </div>
                      Research Requirements
                    </h4>
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                      Required
                    </div>
                  </div>
                  
                  <div className="group relative">
                    <textarea
                      value={rfqInput.description}
                      onChange={(e) => setRFQInput({ description: e.target.value })}
                      placeholder="Describe your research requirements in detail. Include methodologies, target audience, key questions, and any specific analysis needed..."
                      rows={10}
                      required
                      className="w-full px-6 py-6 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-3xl focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all duration-300 shadow-lg hover:shadow-xl group-hover:shadow-xl text-gray-900 placeholder-gray-400 resize-none leading-relaxed"
                    />
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-orange-500/5 via-red-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    
                    {/* Character count indicator */}
                    <div className="absolute bottom-4 right-6 text-xs text-gray-400 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-lg">
                      {rfqInput.description.length} characters
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-4 border border-blue-100">
                    <div className="flex items-start space-x-3">
                      <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-blue-900 mb-1">Pro Tip</p>
                        <p className="text-sm text-blue-800">
                          Be specific about methodologies (Van Westendorp, conjoint analysis, MaxDiff, etc.) and research objectives for better survey generation.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="pt-6">
                  <button
                    type="submit"
                    disabled={!rfqInput.description.trim() || isLoading}
                    className={`
                      group relative w-full py-6 px-8 rounded-3xl font-bold text-lg transition-all duration-300 transform
                      ${isLoading || !rfqInput.description.trim()
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 text-white shadow-2xl hover:shadow-3xl hover:scale-105 active:scale-95'
                      }
                    `}
                  >
                    <div className="relative z-10 flex items-center justify-center space-x-3">
                      {isLoading ? (
                        <>
                          <svg className="animate-spin w-6 h-6 text-current" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Generating Survey...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-6 h-6 text-current group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span>Generate Professional Survey</span>
                          <svg className="w-5 h-5 text-current group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                          </svg>
                        </>
                      )}
                    </div>
                    
                    {/* Animated background gradient */}
                    {!isLoading && rfqInput.description.trim() && (
                      <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* AI Intelligence Panel */}
          <div className="xl:col-span-1">
            <div className="relative">
              {/* Main AI Panel */}
              <div className="bg-white/60 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 p-4 lg:p-6 relative overflow-hidden">
                {/* Animated background pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full blur-2xl animate-pulse"></div>
                  <div className="absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full blur-2xl animate-pulse" style={{animationDelay: '1s'}}></div>
                </div>
                
                <div className="relative z-10">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900 flex items-center">
                      <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl mr-3 flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      AI Intelligence
                    </h3>
                    <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  </div>
                  
                  {/* Methodologies Section */}
                  <div className="space-y-4">
                    <div className="group">
                      <div className="flex items-center mb-3">
                        <div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg mr-3 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                        </div>
                        <h4 className="font-semibold text-gray-800">Pricing Methodologies</h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="inline-flex items-center px-3 py-2 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-200/50 text-blue-700 font-medium rounded-xl text-xs hover:shadow-lg transition-all duration-300 cursor-pointer group-hover:scale-105">
                          <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                          Van Westendorp PSM
                        </span>
                        <span className="inline-flex items-center px-3 py-2 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-200/50 text-green-700 font-medium rounded-xl text-xs hover:shadow-lg transition-all duration-300 cursor-pointer group-hover:scale-105">
                          <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                          Gabor-Granger
                        </span>
                      </div>
                    </div>
                    
                    <div className="group">
                      <div className="flex items-center mb-3">
                        <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg mr-3 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                          </svg>
                        </div>
                        <h4 className="font-semibold text-gray-800">Feature Analysis</h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="inline-flex items-center px-3 py-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-200/50 text-purple-700 font-medium rounded-xl text-xs hover:shadow-lg transition-all duration-300 cursor-pointer group-hover:scale-105">
                          <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                          Choice Conjoint
                        </span>
                        <span className="inline-flex items-center px-3 py-2 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-200/50 text-amber-700 font-medium rounded-xl text-xs hover:shadow-lg transition-all duration-300 cursor-pointer group-hover:scale-105">
                          <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                          MaxDiff
                        </span>
                      </div>
                    </div>
                    
                    {/* Reference Examples */}
                    <div className="space-y-3">
                      <div className="flex items-center">
                        <div className="w-6 h-6 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-lg mr-3 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                          </svg>
                        </div>
                        <h4 className="font-semibold text-gray-800">Reference Examples</h4>
                      </div>
                      
                      <div className="space-y-3">
                        <div className="group relative bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-4 hover:shadow-xl transition-all duration-300 cursor-pointer">
                          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative z-10">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-bold text-sm text-gray-800 group-hover:text-blue-900 transition-colors duration-300">Healthcare Technology Pricing</h5>
                              <div className="flex items-center space-x-1">
                                <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
                                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                              </div>
                            </div>
                            <p className="text-xs text-gray-600 flex items-center">
                              <svg className="w-3 h-3 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                              Van Westendorp + Gabor-Granger
                            </p>
                          </div>
                        </div>
                        
                        <div className="group relative bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-4 hover:shadow-xl transition-all duration-300 cursor-pointer">
                          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative z-10">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-bold text-sm text-gray-800 group-hover:text-purple-900 transition-colors duration-300">B2B SaaS Feature Analysis</h5>
                              <div className="flex items-center space-x-1">
                                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                                <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
                              </div>
                            </div>
                            <p className="text-xs text-gray-600 flex items-center">
                              <svg className="w-3 h-3 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                              Choice Conjoint + Competitive
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* AI Status Indicator */}
                    <div className="mt-6 p-3 bg-gradient-to-r from-emerald-50 to-cyan-50 rounded-2xl border border-emerald-100">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full flex items-center justify-center">
                          <svg className="w-4 h-4 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-emerald-900">AI Ready</p>
                          <p className="text-xs text-emerald-700">Advanced algorithms standing by</p>
                        </div>
                      </div>
                    </div>
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