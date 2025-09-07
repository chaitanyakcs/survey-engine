#!/usr/bin/env python3
"""
Survey Engine Evaluation Test Cases
Store and run complex RFQ scenarios to validate system performance
"""

COMPLEX_RFQ_TEST_CASES = [
    {
        "id": "b2b_saas_evaluation",
        "category": "B2B Technology",
        "description": "Multi-stakeholder B2B SaaS platform evaluation with complex methodologies",
        "rfq_text": """
        We need comprehensive research for B2B SaaS platform evaluation targeting mid-market companies (500-2000 employees).
        Key research areas: decision-making process mapping, stakeholder influence analysis, feature importance across different user roles,
        implementation timeline expectations, budget approval workflows, competitive landscape analysis (Salesforce, HubSpot, Microsoft),
        TCO considerations, security compliance requirements, and integration complexity concerns.
        Use conjoint analysis for feature trade-offs, MaxDiff for priority ranking, Van Westendorp for pricing sensitivity across user tiers,
        and brand perception mapping. Need to segment by company size, industry vertical, and current tech stack maturity.
        Target: IT directors, business users, procurement teams, and C-level executives. Minimum 200 qualified responses.
        """,
        "expected_methodologies": ["conjoint_analysis", "maxdiff", "van_westendorp", "brand_perception"],
        "min_questions": 15,
        "target_time": "20-25 minutes"
    },
    {
        "id": "luxury_ev_journey",
        "category": "Automotive",
        "description": "Luxury electric vehicle consumer journey with advanced research methods",
        "rfq_text": """
        Luxury electric vehicle consumer journey study for $80k+ EV segment. Research focus: consideration set evolution,
        charging infrastructure concerns, brand prestige perception, range anxiety vs performance trade-offs,
        dealer experience expectations, financing vs leasing preferences, sustainability motivations vs luxury appeal,
        and competitive analysis against Tesla Model S, BMW iX, Mercedes EQS, Audi e-tron GT.
        Include ethnographic pre-study insights, choice-based conjoint with 8 attributes, Gabor-Granger pricing methodology,
        TURF analysis for feature combinations, implicit association testing for brand perceptions,
        and longitudinal tracking of consideration changes. Segment by income, lifestyle, and current vehicle ownership.
        Target: HHI $150k+, considering luxury EV purchase in next 18 months. 250 responses minimum.
        """,
        "expected_methodologies": ["choice_conjoint", "gabor_granger", "turf_analysis", "implicit_testing"],
        "min_questions": 20,
        "target_time": "25-30 minutes"
    },
    {
        "id": "healthcare_ai_adoption",
        "category": "Healthcare Technology",
        "description": "AI diagnostic tools adoption in mid-sized hospitals",
        "rfq_text": """
        We need comprehensive research on AI-powered diagnostic tools adoption in mid-sized hospitals (100-500 beds). 
        Key focus areas: decision-making hierarchy, budget approval processes, clinical staff acceptance, patient privacy concerns, 
        ROI expectations, integration challenges with existing HIS/EMR systems, regulatory compliance barriers, 
        and competitive landscape analysis for vendors like GE Healthcare, Philips, and Siemens Healthineers.
        Include KANO model analysis for feature prioritization and discrete choice modeling for pricing sensitivity.
        Target: C-suite executives, CIOs, Chief Medical Officers, and department heads. Need 150+ qualified responses.
        """,
        "expected_methodologies": ["kano_model", "discrete_choice", "stakeholder_mapping"],
        "min_questions": 12,
        "target_time": "15-20 minutes"
    },
    {
        "id": "fintech_digital_transformation",
        "category": "Financial Services",
        "description": "Digital banking transformation competitive study",
        "rfq_text": """
        Multi-phase study on digital banking transformation for regional banks competing with fintech disruptors. 
        Research objectives: customer journey mapping across digital touchpoints, security vs convenience trade-offs, 
        generational differences in banking preferences, willingness to switch banks for better digital experience,
        feature importance using MaxDiff methodology, price sensitivity for premium digital services using PSM,
        competitive benchmarking against Chase, Bank of America, and fintech players like Chime and SoFi.
        Include implicit testing for trust and security perceptions. Need segmentation analysis by age, income, and tech adoption.
        Target: 18-65 banking customers, mix of current digital users and traditional branch users. 400+ responses required.
        """,
        "expected_methodologies": ["maxdiff", "psm", "journey_mapping", "implicit_testing"],
        "min_questions": 18,
        "target_time": "22-28 minutes"
    },
    {
        "id": "sustainability_cpg_behavior",
        "category": "Sustainability/CPG",
        "description": "ESG consumer behavior for sustainable product lines",
        "rfq_text": """
        Comprehensive sustainability research for CPG brands exploring eco-friendly product lines. 
        Focus: purchase intent drivers for sustainable products, willingness to pay premium for eco-certifications,
        greenwashing sensitivity, brand authenticity perceptions, influence of sustainability on brand loyalty,
        environmental claim believability testing, packaging preferences (minimal vs informative),
        certification recognition (Fair Trade, Organic, Carbon Neutral, B-Corp), and behavioral economics
        nudging effectiveness for sustainable choices. Use choice-based conjoint with sustainability attributes,
        Van Westendorp for price premium tolerance, and social desirability bias correction techniques.
        Target: eco-conscious millennials and Gen Z, household decision makers, income $40k+. 300 responses needed.
        """,
        "expected_methodologies": ["choice_conjoint", "van_westendorp", "behavioral_economics"],
        "min_questions": 16,
        "target_time": "20-25 minutes"
    }
]