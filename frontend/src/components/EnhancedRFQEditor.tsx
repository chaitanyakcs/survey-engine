import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import {
  EnhancedRFQRequest,
  RFQObjective,
  RFQConstraint,
  RFQStakeholder,
  RFQSuccess,
  RFQTemplate,
  RFQQualityAssessment
} from '../types';
import { v4 as uuidv4 } from 'uuid';

interface EnhancedRFQEditorProps {
  onPreview?: () => void;
  mode?: 'create' | 'edit';
}

export const EnhancedRFQEditor: React.FC<EnhancedRFQEditorProps> = ({
  onPreview,
  mode = 'create'
}) => {
  const {
    enhancedRfq,
    setEnhancedRfq,
    rfqTemplates,
    selectedTemplate,
    setSelectedTemplate,
    rfqAssessment,
    fetchRfqTemplates,
    assessRfqQuality,
    generateRfqSuggestions,
    workflow
  } = useAppStore();

  const [currentSection, setCurrentSection] = useState<string>('basics');
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Initialize enhanced RFQ with defaults - using ref to prevent infinite loops
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (!hasInitialized.current && !enhancedRfq.title && !enhancedRfq.description) {
      hasInitialized.current = true;
      setEnhancedRfq({
        title: '',
        description: '',
        objectives: [],
        constraints: [],
        stakeholders: [],
        success_metrics: [],
        generation_config: {
          creativity_level: 'balanced',
          length_preference: 'standard',
          complexity_level: 'intermediate',
          include_validation_questions: true,
          enable_adaptive_routing: false
        }
      });
    }
  }, [enhancedRfq.title, enhancedRfq.description, setEnhancedRfq]);

  // Load templates on mount
  useEffect(() => {
    fetchRfqTemplates();
  }, [fetchRfqTemplates]);

  // Auto-assess quality when RFQ changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (enhancedRfq.description && enhancedRfq.description.length > 50) {
        assessRfqQuality(enhancedRfq);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [enhancedRfq, assessRfqQuality]);

  const handleTemplateSelect = (template: RFQTemplate) => {
    setSelectedTemplate(template);
    setEnhancedRfq({
      ...enhancedRfq,
      ...template.template_data,
      template_used: template.id
    });
  };

  const addObjective = () => {
    const newObjective: RFQObjective = {
      id: uuidv4(),
      title: '',
      description: '',
      priority: 'medium'
    };
    setEnhancedRfq({
      ...enhancedRfq,
      objectives: [...(enhancedRfq.objectives || []), newObjective]
    });
  };

  const updateObjective = (id: string, updates: Partial<RFQObjective>) => {
    setEnhancedRfq({
      ...enhancedRfq,
      objectives: enhancedRfq.objectives?.map(obj =>
        obj.id === id ? { ...obj, ...updates } : obj
      )
    });
  };

  const removeObjective = (id: string) => {
    setEnhancedRfq({
      ...enhancedRfq,
      objectives: enhancedRfq.objectives?.filter(obj => obj.id !== id)
    });
  };

  const addConstraint = () => {
    const newConstraint: RFQConstraint = {
      id: uuidv4(),
      type: 'custom',
      description: ''
    };
    setEnhancedRfq({
      ...enhancedRfq,
      constraints: [...(enhancedRfq.constraints || []), newConstraint]
    });
  };

  const updateConstraint = (id: string, updates: Partial<RFQConstraint>) => {
    setEnhancedRfq({
      ...enhancedRfq,
      constraints: enhancedRfq.constraints?.map(constraint =>
        constraint.id === id ? { ...constraint, ...updates } : constraint
      )
    });
  };

  const removeConstraint = (id: string) => {
    setEnhancedRfq({
      ...enhancedRfq,
      constraints: enhancedRfq.constraints?.filter(constraint => constraint.id !== id)
    });
  };

  const getSuggestions = async () => {
    setIsLoadingSuggestions(true);
    try {
      const suggestions = await generateRfqSuggestions(enhancedRfq);
      setSuggestions(suggestions);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  // Helper function to update generation config without mutations
  const updateGenerationConfig = (updates: any) => {
    const newConfig = {
      creativity_level: enhancedRfq.generation_config?.creativity_level || 'balanced',
      length_preference: enhancedRfq.generation_config?.length_preference || 'standard',
      complexity_level: enhancedRfq.generation_config?.complexity_level || 'intermediate',
      include_validation_questions: enhancedRfq.generation_config?.include_validation_questions || true,
      enable_adaptive_routing: enhancedRfq.generation_config?.enable_adaptive_routing || false,
      ...updates
    };
    setEnhancedRfq({ generation_config: newConfig });
  };

  // Helper functions to prevent target_audience mutations
  const updateTargetAudience = (updates: any) => {
    const newTargetAudience = {
      primary_segment: enhancedRfq.target_audience?.primary_segment || '',
      secondary_segments: enhancedRfq.target_audience?.secondary_segments || [],
      demographics: enhancedRfq.target_audience?.demographics || {},
      size_estimate: enhancedRfq.target_audience?.size_estimate || 0,
      accessibility_notes: enhancedRfq.target_audience?.accessibility_notes || '',
      ...updates
    };
    setEnhancedRfq({ target_audience: newTargetAudience });
  };

  // Helper function to prevent methodologies mutations
  const updateMethodologies = (updates: any) => {
    const newMethodologies = {
      preferred: enhancedRfq.methodologies?.preferred || [],
      excluded: enhancedRfq.methodologies?.excluded || [],
      requirements: enhancedRfq.methodologies?.requirements || [],
      ...updates
    };
    setEnhancedRfq({ methodologies: newMethodologies });
  };

  // Helper function to prevent context mutations
  const updateContext = (updates: any) => {
    const newContext = {
      business_background: enhancedRfq.context?.business_background || '',
      market_situation: enhancedRfq.context?.market_situation || '',
      decision_timeline: enhancedRfq.context?.decision_timeline || '',
      ...updates
    };
    setEnhancedRfq({ context: newContext });
  };

  const getQualityIndicator = (score: number) => {
    if (score >= 0.8) return { color: 'green', label: 'Excellent' };
    if (score >= 0.6) return { color: 'yellow', label: 'Good' };
    if (score >= 0.4) return { color: 'orange', label: 'Fair' };
    return { color: 'red', label: 'Needs Improvement' };
  };

  const sections = [
    { id: 'basics', title: 'Basics', icon: '📋', description: 'Core information' },
    { id: 'context', title: 'Context', icon: '🏢', description: 'Business background' },
    { id: 'objectives', title: 'Objectives', icon: '🎯', description: 'Research goals' },
    { id: 'audience', title: 'Audience', icon: '👥', description: 'Target participants' },
    { id: 'methodology', title: 'Methodology', icon: '🔬', description: 'Research approach' },
    { id: 'constraints', title: 'Constraints', icon: '⚖️', description: 'Limitations & requirements' },
    { id: 'config', title: 'AI Config', icon: '🤖', description: 'Generation settings' },
    { id: 'review', title: 'Review', icon: '✅', description: 'Final check' }
  ];

  const isLoading = workflow.status === 'started' || workflow.status === 'in_progress';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto p-6">

        {/* Header with Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced RFQ Builder</h1>
              <p className="text-gray-600">Create comprehensive research requirements with AI assistance</p>
            </div>
            {rfqAssessment && (
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm text-gray-500">Quality Score</p>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full bg-${getQualityIndicator(rfqAssessment.overall_score).color}-400`}></div>
                    <span className="font-semibold">{Math.round(rfqAssessment.overall_score * 100)}%</span>
                    <span className="text-sm text-gray-500">{getQualityIndicator(rfqAssessment.overall_score).label}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Section Navigation */}
          <div className="flex space-x-1 bg-white/70 backdrop-blur-sm rounded-2xl p-2 shadow-lg">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setCurrentSection(section.id)}
                className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  currentSection === section.id
                    ? 'bg-blue-500 text-white shadow-lg'
                    : 'text-gray-600 hover:bg-blue-50 hover:text-blue-700'
                }`}
              >
                <span className="text-lg">{section.icon}</span>
                <div className="text-left">
                  <div className="font-medium">{section.title}</div>
                  <div className="text-xs opacity-75">{section.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="xl:col-span-3">
            <div className="bg-white/70 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8">

              {/* Template Selection */}
              {currentSection === 'basics' && !selectedTemplate && (
                <div className="mb-8">
                  <h3 className="text-xl font-semibold mb-4">Choose a Template</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {rfqTemplates.map((template) => (
                      <div
                        key={template.id}
                        onClick={() => handleTemplateSelect(template)}
                        className="group cursor-pointer p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition-all duration-200"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-semibold text-gray-900 group-hover:text-blue-700">{template.name}</h4>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            template.complexity === 'simple' ? 'bg-green-100 text-green-700' :
                            template.complexity === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {template.complexity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">{template.category}</span>
                          <span className="text-xs text-gray-500">~{template.estimated_completion}min</span>
                        </div>
                      </div>
                    ))}
                    <div
                      onClick={() => setCurrentSection('basics')}
                      className="group cursor-pointer p-4 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-300 transition-all duration-200 flex items-center justify-center"
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">✨</div>
                        <p className="font-medium text-gray-700">Start from Scratch</p>
                        <p className="text-xs text-gray-500">Custom RFQ</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Section Content */}
              {currentSection === 'basics' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">📋</span>
                    Basic Information
                  </h2>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Project Title
                      </label>
                      <input
                        type="text"
                        value={enhancedRfq.title || ''}
                        onChange={(e) => setEnhancedRfq({ ...enhancedRfq, title: e.target.value })}
                        placeholder="Enter your research project title"
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Expected Timeline
                      </label>
                      <input
                        type="text"
                        value={enhancedRfq.expected_timeline || ''}
                        onChange={(e) => setEnhancedRfq({ ...enhancedRfq, expected_timeline: e.target.value })}
                        placeholder="e.g., 4-6 weeks"
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Research Description
                    </label>
                    <textarea
                      value={enhancedRfq.description}
                      onChange={(e) => setEnhancedRfq({ ...enhancedRfq, description: e.target.value })}
                      placeholder="Describe your research needs, goals, and any specific requirements..."
                      rows={8}
                      className="w-full px-6 py-6 bg-white/80 border border-gray-200 rounded-3xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 resize-none"
                    />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Estimated Budget
                      </label>
                      <select
                        value={enhancedRfq.estimated_budget || ''}
                        onChange={(e) => setEnhancedRfq({ ...enhancedRfq, estimated_budget: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      >
                        <option value="">Select budget range</option>
                        <option value="under-10k">Under $10,000</option>
                        <option value="10k-25k">$10,000 - $25,000</option>
                        <option value="25k-50k">$25,000 - $50,000</option>
                        <option value="50k-100k">$50,000 - $100,000</option>
                        <option value="over-100k">Over $100,000</option>
                      </select>
                    </div>

                    {/* Legacy compatibility fields */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Product Category
                      </label>
                      <select
                        value={enhancedRfq.product_category || ''}
                        onChange={(e) => setEnhancedRfq({ ...enhancedRfq, product_category: e.target.value })}
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      >
                        <option value="">Select category</option>
                        <option value="electronics">Electronics</option>
                        <option value="healthcare_technology">Healthcare Technology</option>
                        <option value="enterprise_software">Enterprise Software</option>
                        <option value="financial_services">Financial Services</option>
                        <option value="automotive">Automotive</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Context Section */}
              {currentSection === 'context' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">🏢</span>
                    Business Context
                  </h2>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Business Background
                    </label>
                    <textarea
                      value={enhancedRfq.context?.business_background || ''}
                      onChange={(e) => updateContext({ business_background: e.target.value })}
                      placeholder="Describe your company, industry, and current business situation..."
                      rows={4}
                      className="w-full px-6 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Market Situation
                    </label>
                    <textarea
                      value={enhancedRfq.context?.market_situation || ''}
                      onChange={(e) => updateContext({ market_situation: e.target.value })}
                      placeholder="Describe the current market conditions, competitive landscape, and relevant trends..."
                      rows={4}
                      className="w-full px-6 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Decision Timeline
                    </label>
                    <textarea
                      value={enhancedRfq.context?.decision_timeline || ''}
                      onChange={(e) => updateContext({ decision_timeline: e.target.value })}
                      placeholder="When do you need to make decisions based on this research? What are the key milestones?"
                      rows={3}
                      className="w-full px-6 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 resize-none"
                    />
                  </div>
                </div>
              )}

              {/* Objectives Section */}
              {currentSection === 'objectives' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">🎯</span>
                      Research Objectives
                    </h2>
                    <button
                      onClick={addObjective}
                      className="px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors flex items-center space-x-2"
                    >
                      <span>+</span>
                      <span>Add Objective</span>
                    </button>
                  </div>

                  {enhancedRfq.objectives?.map((objective, index) => (
                    <div key={objective.id} className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-100">
                      <div className="flex items-start justify-between mb-4">
                        <h3 className="font-semibold text-gray-900">Objective #{index + 1}</h3>
                        <button
                          onClick={() => removeObjective(objective.id)}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                          <input
                            type="text"
                            value={objective.title}
                            onChange={(e) => updateObjective(objective.id, { title: e.target.value })}
                            placeholder="Brief objective title"
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                          <select
                            value={objective.priority}
                            onChange={(e) => updateObjective(objective.id, { priority: e.target.value as 'high' | 'medium' | 'low' })}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                          >
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea
                          value={objective.description}
                          onChange={(e) => updateObjective(objective.id, { description: e.target.value })}
                          placeholder="Detailed description of what you want to learn or achieve"
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none"
                        />
                      </div>
                    </div>
                  ))}

                  {(!enhancedRfq.objectives || enhancedRfq.objectives.length === 0) && (
                    <div className="text-center py-12 bg-gray-50 rounded-2xl">
                      <div className="text-4xl mb-4">🎯</div>
                      <p className="text-gray-600 mb-4">No objectives defined yet</p>
                      <button
                        onClick={addObjective}
                        className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
                      >
                        Add Your First Objective
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Audience Section */}
              {currentSection === 'audience' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">👥</span>
                    Target Audience
                  </h2>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Primary Target Segment
                    </label>
                    <select
                      value={enhancedRfq.target_audience?.primary_segment || enhancedRfq.target_segment || ''}
                      onChange={(e) => {
                        updateTargetAudience({ primary_segment: e.target.value });
                        setEnhancedRfq({ target_segment: e.target.value }); // Legacy compatibility
                      }}
                      className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                    >
                      <option value="">Select primary segment</option>
                      <option value="B2B decision makers">B2B Decision Makers</option>
                      <option value="General consumers">General Consumers</option>
                      <option value="Healthcare professionals">Healthcare Professionals</option>
                      <option value="IT professionals">IT Professionals</option>
                      <option value="C-suite executives">C-Suite Executives</option>
                      <option value="Small business owners">Small Business Owners</option>
                      <option value="Students">Students</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Estimated Sample Size
                      </label>
                      <input
                        type="number"
                        value={enhancedRfq.target_audience?.size_estimate || ''}
                        onChange={(e) => updateTargetAudience({ size_estimate: parseInt(e.target.value) || undefined })}
                        placeholder="1000"
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Secondary Segments
                      </label>
                      <input
                        type="text"
                        value={enhancedRfq.target_audience?.secondary_segments?.join(', ') || ''}
                        onChange={(e) => updateTargetAudience({ secondary_segments: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                        placeholder="Tech enthusiasts, Early adopters"
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Accessibility Notes
                    </label>
                    <textarea
                      value={enhancedRfq.target_audience?.accessibility_notes || ''}
                      onChange={(e) => updateTargetAudience({ accessibility_notes: e.target.value })}
                      placeholder="How to reach this audience, recruitment channels, any accessibility considerations..."
                      rows={3}
                      className="w-full px-6 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 resize-none"
                    />
                  </div>
                </div>
              )}

              {/* Methodology Section */}
              {currentSection === 'methodology' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">🔬</span>
                    Research Methodology
                  </h2>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Preferred Methodologies
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {[
                        'Van Westendorp PSM', 'Gabor-Granger', 'Choice Conjoint', 'MaxDiff',
                        'Brand Mapping', 'CSAT', 'NPS', 'CES', 'Driver Analysis',
                        'Market Sizing', 'Kano Model', 'Purchase Intent'
                      ].map((method) => (
                        <label key={method} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-xl hover:bg-blue-50 transition-colors cursor-pointer">
                          <input
                            type="checkbox"
                            checked={enhancedRfq.methodologies?.preferred?.includes(method) || false}
                            onChange={(e) => {
                              const current = enhancedRfq.methodologies?.preferred || [];
                              const updated = e.target.checked
                                ? [...current, method]
                                : current.filter(m => m !== method);
                              updateMethodologies({ preferred: updated });
                            }}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm font-medium text-gray-700">{method}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Excluded Methodologies
                    </label>
                    <input
                      type="text"
                      value={enhancedRfq.methodologies?.excluded?.join(', ') || ''}
                      onChange={(e) => updateMethodologies({ excluded: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="Focus Groups, Open-ended questions"
                      className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">
                      Research Goal (Legacy Compatibility)
                    </label>
                    <select
                      value={enhancedRfq.research_goal || ''}
                      onChange={(e) => setEnhancedRfq({ ...enhancedRfq, research_goal: e.target.value })}
                      className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                    >
                      <option value="">Select research goal</option>
                      <option value="pricing_research">Pricing Research</option>
                      <option value="feature_research">Feature Research</option>
                      <option value="satisfaction_research">Satisfaction Research</option>
                      <option value="brand_research">Brand Research</option>
                      <option value="market_sizing">Market Sizing</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Constraints Section */}
              {currentSection === 'constraints' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="text-3xl mr-3">⚖️</span>
                      Constraints & Requirements
                    </h2>
                    <button
                      onClick={addConstraint}
                      className="px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors flex items-center space-x-2"
                    >
                      <span>+</span>
                      <span>Add Constraint</span>
                    </button>
                  </div>

                  {enhancedRfq.constraints?.map((constraint, index) => (
                    <div key={constraint.id} className="p-6 bg-gradient-to-r from-orange-50 to-red-50 rounded-2xl border border-orange-100">
                      <div className="flex items-start justify-between mb-4">
                        <h3 className="font-semibold text-gray-900">Constraint #{index + 1}</h3>
                        <button
                          onClick={() => removeConstraint(constraint.id)}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                          <select
                            value={constraint.type}
                            onChange={(e) => updateConstraint(constraint.id, { type: e.target.value as any })}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                          >
                            <option value="budget">Budget</option>
                            <option value="timeline">Timeline</option>
                            <option value="sample_size">Sample Size</option>
                            <option value="methodology">Methodology</option>
                            <option value="custom">Custom</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Value</label>
                          <input
                            type="text"
                            value={constraint.value || ''}
                            onChange={(e) => updateConstraint(constraint.id, { value: e.target.value })}
                            placeholder="e.g., $50,000 or 4 weeks"
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea
                          value={constraint.description}
                          onChange={(e) => updateConstraint(constraint.id, { description: e.target.value })}
                          placeholder="Detailed description of the constraint"
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none"
                        />
                      </div>
                    </div>
                  ))}

                  {(!enhancedRfq.constraints || enhancedRfq.constraints.length === 0) && (
                    <div className="text-center py-12 bg-gray-50 rounded-2xl">
                      <div className="text-4xl mb-4">⚖️</div>
                      <p className="text-gray-600 mb-4">No constraints defined yet</p>
                      <button
                        onClick={addConstraint}
                        className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
                      >
                        Add Your First Constraint
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* AI Configuration Section */}
              {currentSection === 'config' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">🤖</span>
                    AI Generation Configuration
                  </h2>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Creativity Level
                      </label>
                      <select
                        value={enhancedRfq.generation_config?.creativity_level || 'balanced'}
                        onChange={(e) => updateGenerationConfig({
                          creativity_level: e.target.value as any
                        })}
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      >
                        <option value="conservative">Conservative - Proven methodologies</option>
                        <option value="balanced">Balanced - Mix of proven and innovative</option>
                        <option value="innovative">Innovative - Creative approaches</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Survey Length
                      </label>
                      <select
                        value={enhancedRfq.generation_config?.length_preference || 'standard'}
                        onChange={(e) => updateGenerationConfig({
                          length_preference: e.target.value as any
                        })}
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      >
                        <option value="concise">Concise - 10-15 minutes</option>
                        <option value="standard">Standard - 15-25 minutes</option>
                        <option value="comprehensive">Comprehensive - 25+ minutes</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-800 mb-3">
                        Complexity Level
                      </label>
                      <select
                        value={enhancedRfq.generation_config?.complexity_level || 'intermediate'}
                        onChange={(e) => updateGenerationConfig({
                          complexity_level: e.target.value as any
                        })}
                        className="w-full px-4 py-4 bg-white/80 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300"
                      >
                        <option value="basic">Basic - Simple questions</option>
                        <option value="intermediate">Intermediate - Mixed complexity</option>
                        <option value="advanced">Advanced - Complex methodologies</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <label className="flex items-center space-x-3 p-4 bg-blue-50 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enhancedRfq.generation_config?.include_validation_questions || false}
                        onChange={(e) => updateGenerationConfig({
                          include_validation_questions: e.target.checked
                        })}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <span className="font-medium text-gray-900">Include Validation Questions</span>
                        <p className="text-sm text-gray-600">Add questions to check response consistency and quality</p>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3 p-4 bg-purple-50 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enhancedRfq.generation_config?.enable_adaptive_routing || false}
                        onChange={(e) => updateGenerationConfig({
                          enable_adaptive_routing: e.target.checked
                        })}
                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                      <div>
                        <span className="font-medium text-gray-900">Enable Adaptive Routing</span>
                        <p className="text-sm text-gray-600">Customize question flow based on previous responses</p>
                      </div>
                    </label>
                  </div>
                </div>
              )}

              {/* Review Section */}
              {currentSection === 'review' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <span className="text-3xl mr-3">✅</span>
                    Final Review
                  </h2>

                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-100">
                    <h3 className="font-semibold text-green-900 mb-3">Requirements Summary</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-green-700">Objectives:</span>
                        <p className="text-green-800">{enhancedRfq.objectives?.length || 0}</p>
                      </div>
                      <div>
                        <span className="font-medium text-green-700">Methodologies:</span>
                        <p className="text-green-800">{enhancedRfq.methodologies?.preferred?.length || 0}</p>
                      </div>
                      <div>
                        <span className="font-medium text-green-700">Constraints:</span>
                        <p className="text-green-800">{enhancedRfq.constraints?.length || 0}</p>
                      </div>
                      <div>
                        <span className="font-medium text-green-700">Target:</span>
                        <p className="text-green-800">{enhancedRfq.target_audience?.primary_segment ? 'Defined' : 'Not set'}</p>
                      </div>
                    </div>
                  </div>

                  {rfqAssessment && (
                    <div className="bg-white p-6 rounded-2xl border border-gray-200">
                      <h3 className="font-semibold text-gray-900 mb-4">Quality Assessment</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl bg-${rfqAssessment.overall_score > 0.7 ? 'green' : rfqAssessment.overall_score > 0.5 ? 'yellow' : 'red'}-500`}>
                            {Math.round(rfqAssessment.overall_score * 100)}%
                          </div>
                          <p className="text-sm font-medium">Overall</p>
                        </div>
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl bg-${rfqAssessment.clarity_score > 0.7 ? 'green' : rfqAssessment.clarity_score > 0.5 ? 'yellow' : 'red'}-500`}>
                            {Math.round(rfqAssessment.clarity_score * 100)}%
                          </div>
                          <p className="text-sm font-medium">Clarity</p>
                        </div>
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl bg-${rfqAssessment.specificity_score > 0.7 ? 'green' : rfqAssessment.specificity_score > 0.5 ? 'yellow' : 'red'}-500`}>
                            {Math.round(rfqAssessment.specificity_score * 100)}%
                          </div>
                          <p className="text-sm font-medium">Specificity</p>
                        </div>
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl bg-${rfqAssessment.completeness_score > 0.7 ? 'green' : rfqAssessment.completeness_score > 0.5 ? 'yellow' : 'red'}-500`}>
                            {Math.round(rfqAssessment.completeness_score * 100)}%
                          </div>
                          <p className="text-sm font-medium">Completeness</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-center">
                    <button
                      onClick={() => onPreview && onPreview()}
                      className="px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-2xl font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all duration-300"
                    >
                      Generate Preview & Submit
                    </button>
                  </div>
                </div>
              )}

              {/* Navigation */}
              <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={() => {
                    const currentIndex = sections.findIndex(s => s.id === currentSection);
                    if (currentIndex > 0) {
                      setCurrentSection(sections[currentIndex - 1].id);
                    }
                  }}
                  disabled={currentSection === sections[0].id}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>

                <button
                  onClick={() => {
                    const currentIndex = sections.findIndex(s => s.id === currentSection);
                    if (currentIndex < sections.length - 1) {
                      setCurrentSection(sections[currentIndex + 1].id);
                    } else if (onPreview) {
                      onPreview();
                    }
                  }}
                  className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
                >
                  {currentSection === sections[sections.length - 1].id ? 'Generate Preview' : 'Next'}
                </button>
              </div>
            </div>
          </div>

          {/* AI Assistant Panel */}
          <div className="xl:col-span-1">
            <div className="bg-white/60 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 p-6 sticky top-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 flex items-center">
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl mr-3 flex items-center justify-center">
                    <span className="text-white">🤖</span>
                  </div>
                  AI Assistant
                </h3>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>

              {/* Quality Assessment */}
              {rfqAssessment && (
                <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl">
                  <h4 className="font-semibold text-green-900 mb-3">Quality Assessment</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-700">Clarity</span>
                      <span className="text-sm font-medium">{Math.round(rfqAssessment.clarity_score * 100)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-700">Specificity</span>
                      <span className="text-sm font-medium">{Math.round(rfqAssessment.specificity_score * 100)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-700">Completeness</span>
                      <span className="text-sm font-medium">{Math.round(rfqAssessment.completeness_score * 100)}%</span>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Suggestions */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-800">Smart Suggestions</h4>
                  <button
                    onClick={getSuggestions}
                    disabled={isLoadingSuggestions}
                    className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
                  >
                    {isLoadingSuggestions ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
                <div className="space-y-2">
                  {suggestions.map((suggestion, index) => (
                    <div key={index} className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                      <p className="text-sm text-blue-800">{suggestion}</p>
                    </div>
                  ))}
                  {suggestions.length === 0 && (
                    <p className="text-sm text-gray-500 italic">Add more details to get AI suggestions</p>
                  )}
                </div>
              </div>

              {/* Progress Indicator */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-800 mb-3">Completion Progress</h4>
                <div className="space-y-2">
                  {sections.map((section) => {
                    const isComplete = section.id === 'basics' ?
                      enhancedRfq.title && enhancedRfq.description :
                      section.id === 'objectives' ?
                      enhancedRfq.objectives && enhancedRfq.objectives.length > 0 :
                      false;

                    return (
                      <div key={section.id} className="flex items-center space-x-3">
                        <div className={`w-4 h-4 rounded-full ${
                          isComplete ? 'bg-green-400' : 'bg-gray-200'
                        }`}></div>
                        <span className={`text-sm ${
                          currentSection === section.id ? 'font-medium text-blue-600' : 'text-gray-600'
                        }`}>
                          {section.title}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};