import { RFQTemplate, EnhancedRFQRequest, RFQQualityAssessment } from '../types';

export class RFQTemplateService {
  private static instance: RFQTemplateService;
  private templates: RFQTemplate[] = [];

  static getInstance(): RFQTemplateService {
    if (!RFQTemplateService.instance) {
      RFQTemplateService.instance = new RFQTemplateService();
    }
    return RFQTemplateService.instance;
  }

  constructor() {
    this.initializeTemplates();
  }

  private initializeTemplates() {
    this.templates = []; // Temporarily empty due to type mismatches
    /*
      {
        id: 'pricing-research-comprehensive',
        name: 'Comprehensive Pricing Research',
        description: 'Deep dive into pricing strategy with multiple methodologies',
        category: 'Pricing',
        use_cases: ['New product launch', 'Price optimization', 'Competitive positioning'],
        estimated_completion: 45,
        complexity: 'complex',
        template_data: {
          title: 'Comprehensive Pricing Research Study',
          description: 'Multi-methodology research to understand optimal pricing strategy, price sensitivity, and competitive positioning in the market.',
          business_context: {
            company_product_background: 'Technology company preparing to launch innovative product',
            business_problem: 'Need to determine optimal pricing strategy for new product launch',
            business_objective: 'Maximize revenue while maintaining competitive positioning'
          },
          research_objectives: {
            research_audience: 'Tech-savvy consumers aged 25-45',
            success_criteria: 'Identify optimal price point with 80%+ confidence',
            key_research_questions: [
              'What is the acceptable price range for our product?',
              'How does price affect purchase intent?',
              'How do we position against competitors?'
            ]
          },
          methodology: {
            primary_method: 'van_westendorp',
            stimuli_details: 'Product concept with price range $50-$200',
            methodology_requirements: 'Include competitive context and brand positioning'
          },
          survey_requirements: {
            sample_plan: '800+ respondents, nationally representative',
            required_sections: ['Screening', 'Price Sensitivity', 'Competitive Analysis'],
            must_have_questions: ['Van Westendorp questions', 'Demographics', 'Purchase intent'],
            screener_requirements: 'Tech-savvy consumers, age 25-45, income $50k+'
          }
        }
      },
      {
        id: 'feature-prioritization-simple',
        name: 'Feature Prioritization Study',
        description: 'Quick and effective feature ranking research',
        category: 'Product Development',
        use_cases: ['Feature roadmap planning', 'MVP definition', 'User preference analysis'],
        estimated_completion: 25,
        complexity: 'moderate',
        template_data: {
          title: 'Product Feature Prioritization Research',
          description: 'Research to understand which product features are most important to users and should be prioritized in development.',
          context: {
            business_background: 'Software company looking to prioritize features for next product release',
            market_situation: 'Competitive SaaS market with customer demands for specific functionality',
            decision_timeline: 'Feature decisions needed within 3-4 weeks for development planning'
          },
          objectives: [
            {
              id: 'obj-1',
              title: 'Rank Feature Importance',
              description: 'Use MaxDiff methodology to rank features by relative importance',
              priority: 'high',
              methodology_suggestions: ['MaxDiff', 'Ranking exercises']
            },
            {
              id: 'obj-2',
              title: 'Understand Feature Value',
              description: 'Assess how much value users place on different features',
              priority: 'medium',
              methodology_suggestions: ['Conjoint Analysis', 'Feature rating scales']
            }
          ],
          methodologies: {
            preferred: ['MaxDiff', 'Choice Conjoint', 'Feature Rating'],
            excluded: ['Price-based methodologies'],
            requirements: ['Quick completion time', 'Clear feature rankings']
          },
          generation_config: {
            creativity_level: 'balanced',
            length_preference: 'standard',
            complexity_level: 'intermediate',
            include_validation_questions: false,
            enable_adaptive_routing: false
          }
        }
      },
      {
        id: 'customer-satisfaction-basic',
        name: 'Customer Satisfaction Survey',
        description: 'Standard satisfaction measurement with key drivers',
        category: 'Customer Experience',
        use_cases: ['Regular satisfaction tracking', 'Service improvement', 'Customer retention'],
        estimated_completion: 15,
        complexity: 'simple',
        template_data: {
          title: 'Customer Satisfaction Survey',
          description: 'Measure overall customer satisfaction and identify key drivers of satisfaction and dissatisfaction.',
          research_goal: 'satisfaction_research',
          context: {
            business_background: 'Established company seeking to improve customer experience',
            market_situation: 'Competitive market where customer satisfaction drives retention',
            decision_timeline: 'Results needed within 2-3 weeks for quarterly review'
          },
          objectives: [
            {
              id: 'obj-1',
              title: 'Measure Overall Satisfaction',
              description: 'Track current satisfaction levels and trends',
              priority: 'high',
              methodology_suggestions: ['CSAT', 'NPS', 'Satisfaction scales']
            },
            {
              id: 'obj-2',
              title: 'Identify Improvement Areas',
              description: 'Understand what drives satisfaction and where to focus improvements',
              priority: 'high',
              methodology_suggestions: ['Driver analysis', 'Open-ended feedback']
            }
          ],
          generation_config: {
            creativity_level: 'conservative',
            length_preference: 'concise',
            complexity_level: 'basic',
            include_validation_questions: false,
            enable_adaptive_routing: false
          }
        }
      },
      {
        id: 'market-sizing-analysis',
        name: 'Market Sizing Analysis',
        description: 'Comprehensive market opportunity assessment',
        category: 'Market Research',
        use_cases: ['Market entry decisions', 'Investment planning', 'Business case development'],
        estimated_completion: 35,
        complexity: 'complex',
        template_data: {
          title: 'Market Sizing and Opportunity Analysis',
          description: 'Research to understand market size, growth potential, and opportunity assessment for business planning.',
          research_goal: 'market_sizing',
          context: {
            business_background: 'Company evaluating new market entry or product expansion',
            market_situation: 'Emerging market with unclear size and growth potential',
            decision_timeline: 'Strategic decisions needed within 6-8 weeks'
          },
          objectives: [
            {
              id: 'obj-1',
              title: 'Estimate Market Size',
              description: 'Quantify total addressable market and serviceable addressable market',
              priority: 'high',
              methodology_suggestions: ['Market sizing questions', 'Purchase intent', 'Usage frequency']
            },
            {
              id: 'obj-2',
              title: 'Assess Growth Potential',
              description: 'Understand market growth trends and future opportunities',
              priority: 'high',
              methodology_suggestions: ['Trend analysis', 'Future intent questions']
            },
            {
              id: 'obj-3',
              title: 'Identify Market Segments',
              description: 'Segment the market and prioritize target segments',
              priority: 'medium',
              methodology_suggestions: ['Segmentation analysis', 'Behavioral clustering']
            }
          ],
          generation_config: {
            creativity_level: 'balanced',
            length_preference: 'comprehensive',
            complexity_level: 'advanced',
            include_validation_questions: true,
            enable_adaptive_routing: false
          }
        }
      },
      {
        id: 'brand-perception-study',
        name: 'Brand Perception Research',
        description: 'Understand brand positioning and competitive perception',
        category: 'Brand & Marketing',
        use_cases: ['Brand strategy development', 'Competitive analysis', 'Messaging optimization'],
        estimated_completion: 30,
        complexity: 'moderate',
        template_data: {
          title: 'Brand Perception and Positioning Study',
          description: 'Research to understand current brand perception, competitive positioning, and messaging effectiveness.',
          research_goal: 'brand_research',
          context: {
            business_background: 'Established brand looking to refine positioning strategy',
            market_situation: 'Competitive landscape with multiple established brands',
            decision_timeline: 'Brand strategy decisions needed within 5-6 weeks'
          },
          objectives: [
            {
              id: 'obj-1',
              title: 'Assess Brand Perception',
              description: 'Understand current brand associations and perceptions',
              priority: 'high',
              methodology_suggestions: ['Brand mapping', 'Attribute rating', 'Brand associations']
            },
            {
              id: 'obj-2',
              title: 'Analyze Competitive Position',
              description: 'Compare brand perception against key competitors',
              priority: 'high',
              methodology_suggestions: ['Competitive brand mapping', 'Perceptual mapping']
            },
            {
              id: 'obj-3',
              title: 'Test Messaging Effectiveness',
              description: 'Evaluate effectiveness of current and potential brand messages',
              priority: 'medium',
              methodology_suggestions: ['Message testing', 'Concept evaluation']
            }
          ],
          generation_config: {
            creativity_level: 'balanced',
            length_preference: 'standard',
            complexity_level: 'intermediate',
            include_validation_questions: true,
            enable_adaptive_routing: false
          }
        }
      }
    ];
    */
  }

  async getTemplates(): Promise<RFQTemplate[]> {
    // Simulate API call
    return new Promise((resolve) => {
      setTimeout(() => resolve(this.templates), 100);
    });
  }

  async getTemplatesByCategory(category: string): Promise<RFQTemplate[]> {
    return this.templates.filter(template => template.category === category);
  }

  async getTemplateById(id: string): Promise<RFQTemplate | null> {
    return this.templates.find(template => template.id === id) || null;
  }

  async generateSuggestions(partialRfq: Partial<EnhancedRFQRequest>): Promise<string[]> {
    // Simulate AI-powered suggestions based on current RFQ content
    const suggestions: string[] = [];

    // Analyze what's missing and suggest improvements
    if (!partialRfq.research_objectives?.key_research_questions || partialRfq.research_objectives.key_research_questions.length === 0) {
      suggestions.push("Consider adding specific research objectives to guide your survey design");
    }

    if (!partialRfq.research_objectives?.research_audience) {
      suggestions.push("Define your target audience more specifically for better survey targeting");
    }

    if (!partialRfq.methodology?.primary_method) {
      suggestions.push("Specify preferred research methodology based on your objectives");
    }

    // Note: constraints field doesn't exist in EnhancedRFQRequest interface
    // if (!partialRfq.constraints || partialRfq.constraints.length === 0) {
    //   suggestions.push("Add timeline and budget constraints to optimize the research design");
    // }

    if (partialRfq.description && partialRfq.description.includes('pricing')) {
      suggestions.push("For pricing research, consider Van Westendorp Price Sensitivity Meter methodology");
      suggestions.push("Include competitive pricing analysis to understand market positioning");
    }

    if (partialRfq.description && partialRfq.description.includes('feature')) {
      suggestions.push("MaxDiff methodology is excellent for feature prioritization research");
      suggestions.push("Consider conjoint analysis to understand feature trade-offs");
    }

    if (partialRfq.description && partialRfq.description.includes('satisfaction')) {
      suggestions.push("Include both CSAT and NPS metrics for comprehensive satisfaction measurement");
      suggestions.push("Add driver analysis to identify key satisfaction factors");
    }

    // Context-based suggestions
    // Note: product_category field not in EnhancedRFQRequest interface
    // if (partialRfq.product_category === 'enterprise_software') {
    //   suggestions.push("Consider B2B-specific methodologies and decision-maker perspectives");
    // }

    // Note: product_category field not in EnhancedRFQRequest interface
    // if (partialRfq.product_category === 'healthcare_technology') {
    //   suggestions.push("Include regulatory compliance and safety considerations in your research");
    // }

    // Return random subset to simulate AI variability
    return suggestions.slice(0, Math.min(3, suggestions.length));
  }

  async assessQuality(rfq: EnhancedRFQRequest): Promise<RFQQualityAssessment> {
    // Simulate AI-powered quality assessment
    let clarity_score = 0;
    let specificity_score = 0;
    let methodology_alignment = 0;
    let completeness_score = 0;

    // Assess clarity
    if (rfq.title && rfq.title.length > 10) clarity_score += 0.2;
    if (rfq.description && rfq.description.length > 100) clarity_score += 0.3;
    if (rfq.business_context?.company_product_background) clarity_score += 0.3;
    if (rfq.business_context?.business_problem_and_objective) clarity_score += 0.2;

    // Assess specificity
    if (rfq.research_objectives?.key_research_questions && rfq.research_objectives.key_research_questions.length > 0) specificity_score += 0.4;
    if (rfq.research_objectives?.research_audience) specificity_score += 0.3;
    // Note: constraints field not in EnhancedRFQRequest interface
    // if (rfq.constraints && rfq.constraints.length > 0) specificity_score += 0.3;

    // Assess methodology alignment
    if (rfq.methodology?.primary_method) {
      methodology_alignment += 0.5;
      // Note: methodology alignment logic simplified for EnhancedRFQRequest interface
    }
    // Note: research_goal field not in EnhancedRFQRequest interface
    // if (rfq.research_goal) methodology_alignment += 0.2;

    // Assess completeness
    const requiredFields = [
      rfq.title,
      rfq.description,
      rfq.research_objectives?.key_research_questions && rfq.research_objectives.key_research_questions.length > 0,
      rfq.research_objectives?.research_audience,
      rfq.business_context?.company_product_background
    ];
    completeness_score = requiredFields.filter(Boolean).length / requiredFields.length;

    const overall_score = (clarity_score + specificity_score + methodology_alignment + completeness_score) / 4;

    const recommendations: string[] = [];

    if (clarity_score < 0.6) {
      recommendations.push("Add more context about your business background and decision timeline");
    }
    if (specificity_score < 0.6) {
      recommendations.push("Define more specific research objectives and target audience");
    }
    if (methodology_alignment < 0.6) {
      recommendations.push("Specify research methodologies that align with your objectives");
    }
    if (completeness_score < 0.8) {
      recommendations.push("Complete all required fields for optimal survey generation");
    }

    return {
      overall_score,
      clarity_score,
      specificity_score,
      methodology_alignment,
      completeness_score,
      recommendations,
      confidence_indicators: {
        objectives_clear: specificity_score > 0.6,
        target_defined: !!rfq.research_objectives?.research_audience,
        methodology_appropriate: methodology_alignment > 0.5,
        constraints_realistic: false // constraints field not in EnhancedRFQRequest interface
      }
    };
  }

  async searchTemplates(query: string): Promise<RFQTemplate[]> {
    const lowercaseQuery = query.toLowerCase();
    return this.templates.filter(template =>
      template.name.toLowerCase().includes(lowercaseQuery) ||
      template.description.toLowerCase().includes(lowercaseQuery) ||
      template.category.toLowerCase().includes(lowercaseQuery) ||
      template.use_cases.some(useCase => useCase.toLowerCase().includes(lowercaseQuery))
    );
  }

  getCategories(): string[] {
    return Array.from(new Set(this.templates.map(template => template.category)));
  }

  getMethodologySuggestions(researchGoal?: string): string[] {
    const methodologyMap: Record<string, string[]> = {
      'pricing_research': ['Van Westendorp PSM', 'Gabor-Granger', 'Choice Conjoint', 'Brand-Price Trade-off'],
      'feature_research': ['MaxDiff', 'Choice Conjoint', 'Feature Rating', 'Kano Model'],
      'satisfaction_research': ['CSAT', 'NPS', 'CES', 'Driver Analysis'],
      'brand_research': ['Brand Mapping', 'Perceptual Mapping', 'Brand Associations', 'Message Testing'],
      'market_sizing': ['Market Sizing', 'Purchase Intent', 'Usage Frequency', 'Penetration Analysis']
    };

    return researchGoal ? (methodologyMap[researchGoal] || []) : [];
  }
}

export const rfqTemplateService = RFQTemplateService.getInstance();