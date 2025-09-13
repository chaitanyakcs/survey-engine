#!/usr/bin/env python3
"""
Pillar-Based Test Cases with Expected Scores
Enhanced test cases designed to validate 5-pillar evaluation framework
"""

PILLAR_BASED_TEST_CASES = [
    {
        "id": "high_quality_b2b_saas",
        "category": "B2B Technology",
        "description": "High-quality B2B SaaS evaluation with comprehensive methodologies",
        "rfq_text": """
        We need comprehensive research for enterprise B2B SaaS platform evaluation targeting Fortune 500 companies.
        
        Research Objectives:
        1. Map complete decision-making process across all stakeholder levels
        2. Quantify feature importance across different user roles (IT, Business Users, C-Suite)
        3. Analyze competitive positioning vs. Salesforce, HubSpot, Microsoft Dynamics
        4. Evaluate pricing sensitivity and budget approval workflows
        5. Assess integration complexity concerns and security compliance requirements
        
        Methodologies Required:
        - Choice-based conjoint analysis for feature trade-offs (8 attributes, 3-4 levels each)
        - MaxDiff for feature priority ranking across user segments  
        - Van Westendorp PSM for pricing sensitivity across enterprise tiers
        - Brand perception mapping with semantic differential scales
        - Journey mapping for implementation and adoption phases
        
        Target Audience:
        - IT Directors and CIOs (technology evaluation)
        - Business unit leaders (functional requirements)
        - Procurement teams (budget and contracting)
        - End users (usability and adoption)
        
        Sample Requirements:
        - Minimum 300 qualified responses
        - Company size: 1000+ employees
        - Industry spread across financial services, healthcare, manufacturing
        - Decision-making role verification required
        
        Timeline: 25-30 minute survey acceptable for this enterprise audience
        """,
        "expected_methodologies": ["choice_conjoint", "maxdiff", "van_westendorp", "brand_perception", "journey_mapping"],
        "min_questions": 20,
        "target_time": "25-30 minutes",
        "expected_pillar_scores": {
            "content_validity": 0.90,      # Excellent - comprehensive coverage of all stated objectives
            "methodological_rigor": 0.85,  # High - proper methodology implementation, good sequencing
            "clarity_comprehensibility": 0.80,  # Good - may have some B2B complexity but acceptable
            "structural_coherence": 0.88,  # High - well-structured with logical flow
            "deployment_readiness": 0.85   # High - appropriate length and targeting for audience
        },
        "expected_overall_score": 0.86,  # High quality survey
        "quality_tier": "excellent"
    },
    {
        "id": "medium_quality_consumer_cpg",
        "category": "Consumer Goods",
        "description": "Medium quality consumer product research with some gaps",
        "rfq_text": """
        Research needed for new sustainable laundry detergent launch.
        
        We want to understand consumer attitudes toward eco-friendly cleaning products.
        Looking at purchase intent, brand preferences, and price sensitivity.
        
        Target regular laundry detergent users, ages 25-55.
        Need about 200 responses. Survey should be quick, maybe 15 minutes.
        
        Would like some pricing research and competitive analysis.
        """,
        "expected_methodologies": ["pricing_research", "competitive_analysis"],
        "min_questions": 12,
        "target_time": "15 minutes",
        "expected_pillar_scores": {
            "content_validity": 0.65,      # Medium - covers basic objectives but lacks depth
            "methodological_rigor": 0.60,  # Medium - basic approach, limited methodology rigor
            "clarity_comprehensibility": 0.85,  # High - simple consumer language
            "structural_coherence": 0.70,  # Good - decent structure but could be better
            "deployment_readiness": 0.80   # High - appropriate length for consumer survey
        },
        "expected_overall_score": 0.70,  # Medium quality
        "quality_tier": "good"
    },
    {
        "id": "low_quality_vague_request",
        "category": "Healthcare",
        "description": "Poor quality RFQ with vague requirements and expectations",
        "rfq_text": """
        Need survey about healthcare technology. 
        
        Want to know what doctors think about new technology.
        
        Should be short survey.
        """,
        "expected_methodologies": [],
        "min_questions": 5,
        "target_time": "10 minutes",
        "expected_pillar_scores": {
            "content_validity": 0.40,      # Poor - very vague objectives, insufficient detail
            "methodological_rigor": 0.45,  # Poor - no clear methodology, likely basic questions
            "clarity_comprehensibility": 0.75,  # Good - simple language but may lack context
            "structural_coherence": 0.50,  # Poor - limited structure due to vague requirements
            "deployment_readiness": 0.70   # Good - short length is deployable
        },
        "expected_overall_score": 0.54,  # Low quality
        "quality_tier": "needs_improvement"
    },
    {
        "id": "excellent_luxury_automotive",
        "category": "Automotive",
        "description": "Excellent quality luxury vehicle research with sophisticated methods",
        "rfq_text": """
        Comprehensive luxury electric vehicle consumer journey study for premium EV segment ($80k+ vehicles).
        
        Detailed Research Objectives:
        1. Map complete customer journey from initial consideration to purchase decision
        2. Quantify the relative importance of performance vs. sustainability motivations
        3. Analyze charging infrastructure anxiety and mitigation strategies
        4. Evaluate brand prestige perception across Tesla, BMW, Mercedes, Audi luxury EVs
        5. Assess willingness to pay for premium features and services
        6. Understand financing vs. leasing preferences across different customer segments
        7. Identify key decision drivers and deal-breakers in the luxury EV space
        
        Advanced Methodology Requirements:
        - Choice-based conjoint with 8 attributes (range, charging speed, brand, price, etc.)
        - Gabor-Granger pricing methodology for feature-specific willingness to pay
        - TURF analysis for optimal feature combination identification
        - Implicit Association Testing for unconscious brand perceptions
        - MaxDiff for emotional vs. rational purchase driver prioritization
        - Longitudinal consideration set tracking (if feasible)
        
        Target Specifications:
        - Household income $150k+ verified
        - Currently considering luxury vehicle purchase within 18 months
        - Age 35-65, mix of current luxury ICE and EV owners
        - Geographic spread across major metropolitan areas
        - Minimum 250 qualified responses required
        
        Quality Requirements:
        - Professional survey design with branded presentation
        - Cognitive testing recommended for complex conjoint tasks
        - Mobile-optimized design essential
        - Survey length 25-30 minutes acceptable for this audience
        - Incentives aligned with target demographic (premium rewards)
        """,
        "expected_methodologies": ["choice_conjoint", "gabor_granger", "turf_analysis", "implicit_testing", "maxdiff"],
        "min_questions": 25,
        "target_time": "25-30 minutes",
        "expected_pillar_scores": {
            "content_validity": 0.95,      # Excellent - extremely comprehensive, all objectives covered
            "methodological_rigor": 0.90,  # Excellent - sophisticated methods, proper implementation
            "clarity_comprehensibility": 0.85,  # High - complex but appropriate for audience
            "structural_coherence": 0.92,  # Excellent - very well structured and logical
            "deployment_readiness": 0.88   # High - well-planned for target audience
        },
        "expected_overall_score": 0.90,  # Excellent quality
        "quality_tier": "excellent"
    },
    {
        "id": "biased_leading_questions",
        "category": "Political Research",
        "description": "Test case with methodological issues - biased and leading questions",
        "rfq_text": """
        We need research to prove that voters strongly support our candidate's policies.
        
        Want to show how much people agree with our environmental initiatives.
        Need data showing competitors' policies are unpopular.
        
        Survey should demonstrate clear voter preference for our candidate.
        Target 500 registered voters. Quick 10-minute survey.
        
        Focus on showing positive support for renewable energy policies and negative views of fossil fuel industry.
        """,
        "expected_methodologies": [],
        "min_questions": 10,
        "target_time": "10 minutes",
        "expected_pillar_scores": {
            "content_validity": 0.50,      # Poor - objectives are biased toward proving predetermined conclusions
            "methodological_rigor": 0.30,  # Very Poor - high bias risk, leading objectives
            "clarity_comprehensibility": 0.75,  # Good - likely simple language
            "structural_coherence": 0.45,  # Poor - structure compromised by bias
            "deployment_readiness": 0.65   # Medium - short survey is deployable but quality issues
        },
        "expected_overall_score": 0.52,  # Poor quality due to bias (calculated: 0.518)
        "quality_tier": "needs_improvement"
    }
]

# Mapping test cases to expected quality outcomes
QUALITY_EXPECTATIONS = {
    "excellent": {
        "min_overall_score": 0.80,
        "description": "Survey demonstrates excellent quality across all pillars",
        "deployment_recommendation": "Ready for immediate deployment"
    },
    "good": {
        "min_overall_score": 0.60,
        "max_overall_score": 0.79,
        "description": "Good quality survey with minor improvements needed",
        "deployment_recommendation": "Ready for deployment with minor revisions"
    },
    "needs_improvement": {
        "max_overall_score": 0.59,
        "description": "Significant improvements needed before deployment",
        "deployment_recommendation": "Requires substantial revision before deployment"
    }
}

# Framework validation criteria
PILLAR_WEIGHT_VALIDATION = {
    "content_validity": 0.20,
    "methodological_rigor": 0.25,
    "clarity_comprehensibility": 0.25,
    "structural_coherence": 0.20,
    "deployment_readiness": 0.10
}

def validate_test_case_scores(test_case):
    """
    Validate that test case expected scores align with framework weights
    """
    expected_scores = test_case["expected_pillar_scores"]
    calculated_score = (
        expected_scores["content_validity"] * PILLAR_WEIGHT_VALIDATION["content_validity"] +
        expected_scores["methodological_rigor"] * PILLAR_WEIGHT_VALIDATION["methodological_rigor"] +
        expected_scores["clarity_comprehensibility"] * PILLAR_WEIGHT_VALIDATION["clarity_comprehensibility"] +
        expected_scores["structural_coherence"] * PILLAR_WEIGHT_VALIDATION["structural_coherence"] +
        expected_scores["deployment_readiness"] * PILLAR_WEIGHT_VALIDATION["deployment_readiness"]
    )
    
    expected_overall = test_case["expected_overall_score"]
    tolerance = 0.02  # Allow 2% tolerance for rounding
    
    if abs(calculated_score - expected_overall) > tolerance:
        print(f"Warning: Test case {test_case['id']} score mismatch!")
        print(f"  Calculated: {calculated_score:.3f}")
        print(f"  Expected: {expected_overall:.3f}")
        print(f"  Difference: {abs(calculated_score - expected_overall):.3f}")
        return False
    
    return True

def validate_all_test_cases():
    """Validate all test cases for score consistency"""
    print("🔍 Validating pillar-based test cases...")
    
    all_valid = True
    for test_case in PILLAR_BASED_TEST_CASES:
        if not validate_test_case_scores(test_case):
            all_valid = False
    
    if all_valid:
        print("✅ All test cases validated successfully!")
    else:
        print("❌ Some test cases have scoring inconsistencies")
    
    return all_valid

if __name__ == "__main__":
    validate_all_test_cases()