"""
Core Generation Rules Dataset
Converted from AiRA v1 evaluation criteria to proactive generation guidelines
Organized by the 5 quality pillars for seamless integration
"""

# Core Generation Rules Dataset (58 rules total, converted from AiRA v1 evaluation criteria)
CORE_GENERATION_RULES = [

    # ============================================================================
    # CONTENT VALIDITY (20% weight) - 11 rules total
    # ============================================================================

    # Content Validity Core Rules (6)
    {
        "rule_id": "gen_cv_1",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "core",
        "weight": 0.018,  # (0.20/11) - Content Validity pillar weight divided by number of rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure the questionnaire comprehensively covers all essential research objectives stated in the RFQ document",
        "implementation_notes": [
            "Review all RFQ objectives carefully before question design",
            "Map each research objective to specific survey questions",
            "Verify no objectives are overlooked or inadequately addressed"
        ],
        "quality_indicators": [
            "All RFQ objectives have corresponding questions",
            "Clear alignment between objectives and question content"
        ]
    },
    {
        "rule_id": "gen_cv_2",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "core",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate and sufficient demographic questions for target audience analysis",
        "implementation_notes": [
            "Consider age, gender, income, geography as relevant to research goals",
            "Include occupation, education level when business-relevant",
            "Tailor demographic questions to specific target audience needs"
        ],
        "quality_indicators": [
            "Demographic questions align with target audience analysis needs",
            "Sufficient demographic coverage for segmentation requirements"
        ]
    },
    {
        "rule_id": "gen_cv_3",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "high",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include validation questions or consistency checks to verify response reliability",
        "implementation_notes": [
            "Add attention check questions in longer surveys",
            "Include consistency verification questions for critical data",
            "Design validation questions that don't frustrate respondents"
        ],
        "quality_indicators": [
            "Validation questions present for response quality assurance",
            "Consistency checks included for reliability verification"
        ]
    },
    {
        "rule_id": "gen_cv_4",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "core",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Address information needs of all key stakeholders identified in the research",
        "implementation_notes": [
            "Identify all stakeholders mentioned in RFQ",
            "Ensure questions address each stakeholder's information needs",
            "Balance stakeholder priorities based on research objectives"
        ],
        "quality_indicators": [
            "All stakeholder information needs are addressed",
            "Balanced coverage across different stakeholder requirements"
        ]
    },
    {
        "rule_id": "gen_cv_5",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "core",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include sufficient screening questions to identify and qualify the target respondent population",
        "implementation_notes": [
            "Design screening questions early in survey flow",
            "Ensure screening criteria match target population definition",
            "Include disqualification logic where appropriate"
        ],
        "quality_indicators": [
            "Screening questions properly identify target population",
            "Clear qualification criteria for respondent inclusion"
        ]
    },
    {
        "rule_id": "gen_cv_6",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "high",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure questions capture data at the appropriate level of detail for analysis requirements",
        "implementation_notes": [
            "Consider analysis granularity needs when designing questions",
            "Balance detail level with respondent burden",
            "Ensure data collected supports intended statistical analysis"
        ],
        "quality_indicators": [
            "Question detail level matches analysis requirements",
            "Data granularity supports planned research analysis"
        ]
    },

    # Content Validity Scaled Rules (5)
    {
        "rule_id": "gen_cv_7",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "medium",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to comprehensively cover the breadth and depth of the research domain",
        "implementation_notes": [
            "Map research domain comprehensively before question design",
            "Ensure adequate coverage of all domain aspects",
            "Balance breadth with survey length constraints"
        ],
        "quality_indicators": [
            "Comprehensive coverage of research domain",
            "Balanced breadth and depth in question coverage"
        ]
    },
    {
        "rule_id": "gen_cv_8",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "medium",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include questions that address both current state and future intentions or behaviors",
        "implementation_notes": [
            "Balance current behavior and future intention questions",
            "Include temporal aspects relevant to research objectives",
            "Consider predictive value of future-oriented questions"
        ],
        "quality_indicators": [
            "Both current and future aspects are covered",
            "Temporal balance appropriate for research goals"
        ]
    },
    {
        "rule_id": "gen_cv_9",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "medium",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to capture nuanced and context-specific information when required",
        "implementation_notes": [
            "Include context-specific questions where relevant",
            "Capture nuances important for research understanding",
            "Balance detail with survey completion feasibility"
        ],
        "quality_indicators": [
            "Context-specific information captured where needed",
            "Nuanced data collection supports research depth"
        ]
    },
    {
        "rule_id": "gen_cv_10",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "medium",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure cultural sensitivity and appropriateness for the target demographic",
        "implementation_notes": [
            "Consider cultural context of target demographic",
            "Ensure questions are culturally appropriate and sensitive",
            "Adapt language and concepts for cultural relevance"
        ],
        "quality_indicators": [
            "Questions are culturally sensitive and appropriate",
            "Language and concepts resonate with target demographic"
        ]
    },
    {
        "rule_id": "gen_cv_11",
        "rule_type": "generation",
        "category": "content_validity",
        "priority": "medium",
        "weight": 0.018,  # Content Validity: 0.20/11 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include questions that support triangulation and cross-validation of key findings",
        "implementation_notes": [
            "Design questions that can validate key findings from multiple angles",
            "Include cross-check questions for critical data points",
            "Enable triangulation through complementary question approaches"
        ],
        "quality_indicators": [
            "Multiple questions support key finding validation",
            "Cross-validation opportunities built into survey design"
        ]
    },

    # ============================================================================
    # METHODOLOGICAL RIGOR (25% weight) - 15 rules total
    # ============================================================================

    # Methodological Rigor Core Rules (8)
    {
        "rule_id": "gen_mr_1",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "core",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Use methodologically sound question types appropriate for the specific data collection needs",
        "implementation_notes": [
            "Match question types to data requirements (categorical, ordinal, interval)",
            "Use established question formats for validated constructs",
            "Ensure question types support intended statistical analysis"
        ],
        "quality_indicators": [
            "Question types match data collection requirements",
            "Methodologically appropriate question formats used"
        ]
    },
    {
        "rule_id": "gen_mr_2",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "core",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate sample size considerations and statistical power requirements",
        "implementation_notes": [
            "Consider minimum sample size for intended analysis",
            "Include sample size guidance in survey metadata",
            "Account for expected response rates in sample planning"
        ],
        "quality_indicators": [
            "Sample size considerations included in survey design",
            "Statistical power requirements addressed"
        ]
    },
    {
        "rule_id": "gen_mr_3",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "core",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to minimize measurement error and response bias",
        "implementation_notes": [
            "Use neutral, unbiased question wording",
            "Avoid leading or loaded questions",
            "Design balanced response scales and options"
        ],
        "quality_indicators": [
            "Questions minimize measurement error",
            "Response bias is minimized through design"
        ]
    },
    {
        "rule_id": "gen_mr_4",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "core",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate control questions and randomization where methodologically required",
        "implementation_notes": [
            "Add control questions for experimental designs",
            "Include randomization instructions where needed",
            "Implement appropriate experimental controls"
        ],
        "quality_indicators": [
            "Control questions included where methodologically required",
            "Appropriate randomization implemented"
        ]
    },
    {
        "rule_id": "gen_mr_5",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "core",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure response scales and formats are consistent with established research practices",
        "implementation_notes": [
            "Use standard Likert scales (5-point, 7-point) where appropriate",
            "Maintain consistent scale directions throughout survey",
            "Follow established practices for specific methodologies"
        ],
        "quality_indicators": [
            "Response scales follow established research practices",
            "Consistent scale usage throughout survey"
        ]
    },
    {
        "rule_id": "gen_mr_6",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "high",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include questions that enable reliability and validity testing of key constructs",
        "implementation_notes": [
            "Include multiple questions for key constructs when possible",
            "Design questions to enable internal consistency testing",
            "Support construct validity through question design"
        ],
        "quality_indicators": [
            "Key constructs can be tested for reliability",
            "Question design supports validity testing"
        ]
    },
    {
        "rule_id": "gen_mr_7",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "high",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design survey structure to minimize order effects and response patterns",
        "implementation_notes": [
            "Randomize question order where appropriate",
            "Vary response scale directions to avoid pattern responses",
            "Consider question sequence effects in design"
        ],
        "quality_indicators": [
            "Order effects are minimized through design",
            "Response pattern bias is addressed"
        ]
    },
    {
        "rule_id": "gen_mr_8",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "high",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate benchmarking questions for result contextualization",
        "implementation_notes": [
            "Include industry standard benchmark questions where relevant",
            "Add comparative questions for result interpretation",
            "Enable benchmarking against established norms"
        ],
        "quality_indicators": [
            "Benchmarking questions included where appropriate",
            "Results can be contextualized against standards"
        ]
    },

    # Methodological Rigor Scaled Rules (7)
    {
        "rule_id": "gen_mr_9",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to support rigorous statistical analysis and hypothesis testing",
        "implementation_notes": [
            "Ensure questions support planned statistical tests",
            "Design for appropriate levels of measurement",
            "Consider analysis requirements in question structure"
        ],
        "quality_indicators": [
            "Questions support planned statistical analysis",
            "Appropriate measurement levels for hypothesis testing"
        ]
    },
    {
        "rule_id": "gen_mr_10",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include questions that address potential confounding variables and alternative explanations",
        "implementation_notes": [
            "Identify and measure potential confounding variables",
            "Include questions that address alternative explanations",
            "Design for causal inference where appropriate"
        ],
        "quality_indicators": [
            "Confounding variables are addressed",
            "Alternative explanations can be tested"
        ]
    },
    {
        "rule_id": "gen_mr_11",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure survey design supports the intended generalizability of findings",
        "implementation_notes": [
            "Consider population representativeness in design",
            "Include questions that support generalization claims",
            "Address external validity through question design"
        ],
        "quality_indicators": [
            "Survey design supports intended generalizability",
            "External validity considerations addressed"
        ]
    },
    {
        "rule_id": "gen_mr_12",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include temporal considerations and time-sensitive questions where methodologically relevant",
        "implementation_notes": [
            "Consider timing effects in question design",
            "Include time-sensitive questions where relevant",
            "Address temporal validity in survey structure"
        ],
        "quality_indicators": [
            "Temporal considerations included where relevant",
            "Time-sensitive aspects properly addressed"
        ]
    },
    {
        "rule_id": "gen_mr_13",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to minimize social desirability bias and demand characteristics",
        "implementation_notes": [
            "Use indirect questioning techniques where appropriate",
            "Minimize social desirability pressure in question wording",
            "Address demand characteristics through design"
        ],
        "quality_indicators": [
            "Social desirability bias is minimized",
            "Demand characteristics are addressed"
        ]
    },
    {
        "rule_id": "gen_mr_14",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate pilot testing and validation recommendations in survey metadata",
        "implementation_notes": [
            "Recommend pilot testing procedures",
            "Include validation testing suggestions",
            "Provide guidance for survey refinement"
        ],
        "quality_indicators": [
            "Pilot testing recommendations included",
            "Validation procedures suggested"
        ]
    },
    {
        "rule_id": "gen_mr_15",
        "rule_type": "generation",
        "category": "methodological_rigor",
        "priority": "medium",
        "weight": 0.017,  # Methodological Rigor: 0.25/15 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure survey methodology aligns with industry standards and best practices",
        "implementation_notes": [
            "Follow established industry standards for survey methodology",
            "Align with professional research association guidelines",
            "Implement recognized best practices"
        ],
        "quality_indicators": [
            "Methodology aligns with industry standards",
            "Best practices are implemented"
        ]
    },

    # ============================================================================
    # CLARITY & COMPREHENSIBILITY (25% weight) - 13 rules total
    # ============================================================================

    # Clarity & Comprehensibility Core Rules (7)
    {
        "rule_id": "gen_cc_1",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Write all questions using clear, unambiguous language that is easily understood by the target audience",
        "implementation_notes": [
            "Use simple, direct language appropriate for target demographic",
            "Avoid ambiguous terms that could be interpreted multiple ways",
            "Test language clarity with target audience when possible"
        ],
        "quality_indicators": [
            "Questions use clear, unambiguous language",
            "Language appropriate for target audience education level"
        ]
    },
    {
        "rule_id": "gen_cc_2",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Avoid unnecessary technical jargon and define technical terms when they must be used",
        "implementation_notes": [
            "Use plain language instead of technical jargon where possible",
            "Provide clear definitions for necessary technical terms",
            "Consider target audience's technical knowledge level"
        ],
        "quality_indicators": [
            "Technical jargon is minimized or explained",
            "Terms are defined appropriately for audience"
        ]
    },
    {
        "rule_id": "gen_cc_3",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure response options are mutually exclusive and collectively exhaustive",
        "implementation_notes": [
            "Design response options that don't overlap",
            "Include all reasonable response possibilities",
            "Add 'Other' options where appropriate"
        ],
        "quality_indicators": [
            "Response options are mutually exclusive",
            "Options are collectively exhaustive"
        ]
    },
    {
        "rule_id": "gen_cc_4",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Provide clear, comprehensive instructions for completing each question type",
        "implementation_notes": [
            "Include specific instructions for complex question types",
            "Explain how to use scales, rankings, or special formats",
            "Provide examples where helpful"
        ],
        "quality_indicators": [
            "Clear instructions provided for each question type",
            "Complex formats are well-explained"
        ]
    },
    {
        "rule_id": "gen_cc_5",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Use consistent terminology and question formats throughout the survey",
        "implementation_notes": [
            "Maintain consistent terms for the same concepts",
            "Use consistent question format patterns",
            "Avoid confusing variation in terminology"
        ],
        "quality_indicators": [
            "Terminology is consistent throughout survey",
            "Question formats follow consistent patterns"
        ]
    },
    {
        "rule_id": "gen_cc_6",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "core",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to avoid double-barreled, leading, or loaded constructions",
        "implementation_notes": [
            "Ask about one concept per question",
            "Use neutral wording that doesn't suggest preferred answers",
            "Avoid emotionally charged or biased language"
        ],
        "quality_indicators": [
            "Questions address single concepts",
            "Neutral, unbiased wording used"
        ]
    },
    {
        "rule_id": "gen_cc_7",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "high",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Structure questions with appropriate cognitive load for target respondents",
        "implementation_notes": [
            "Consider respondent attention span and cognitive capacity",
            "Break complex concepts into simpler questions",
            "Manage overall survey cognitive burden"
        ],
        "quality_indicators": [
            "Cognitive load is appropriate for target audience",
            "Complex concepts are appropriately simplified"
        ]
    },

    # Clarity & Comprehensibility Scaled Rules (6)
    {
        "rule_id": "gen_cc_8",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design question wording to be culturally appropriate and accessible across diverse populations",
        "implementation_notes": [
            "Use inclusive language that works across cultural groups",
            "Avoid culturally specific references that may confuse",
            "Consider linguistic accessibility for diverse populations"
        ],
        "quality_indicators": [
            "Language is culturally inclusive and accessible",
            "Questions work across diverse populations"
        ]
    },
    {
        "rule_id": "gen_cc_9",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure readability level is appropriate for the target demographic",
        "implementation_notes": [
            "Match reading level to target audience education",
            "Use sentence structures appropriate for audience",
            "Test readability using standard metrics when possible"
        ],
        "quality_indicators": [
            "Readability level matches target demographic",
            "Sentence complexity is appropriate"
        ]
    },
    {
        "rule_id": "gen_cc_10",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Use examples and clarifications to enhance question understanding when needed",
        "implementation_notes": [
            "Provide examples for abstract or complex concepts",
            "Include clarifying information where helpful",
            "Balance clarity with survey length"
        ],
        "quality_indicators": [
            "Examples provided where needed for clarity",
            "Clarifications enhance understanding"
        ]
    },
    {
        "rule_id": "gen_cc_11",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design scales and response formats that are intuitive and easy to use",
        "implementation_notes": [
            "Use familiar scale formats (1-5, 1-10, etc.)",
            "Make scale directions clear and intuitive",
            "Provide scale labels that are meaningful"
        ],
        "quality_indicators": [
            "Scales are intuitive and easy to use",
            "Response formats are user-friendly"
        ]
    },
    {
        "rule_id": "gen_cc_12",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure questions can be understood without requiring extensive context from previous questions",
        "implementation_notes": [
            "Make each question self-contained when possible",
            "Provide necessary context within the question",
            "Minimize dependencies on previous question understanding"
        ],
        "quality_indicators": [
            "Questions are largely self-contained",
            "Necessary context is provided within questions"
        ]
    },
    {
        "rule_id": "gen_cc_13",
        "rule_type": "generation",
        "category": "clarity_comprehensibility",
        "priority": "medium",
        "weight": 0.019,  # Clarity & Comprehensibility: 0.25/13 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Use active voice and direct language to improve question clarity and engagement",
        "implementation_notes": [
            "Write questions in active voice where possible",
            "Use direct, engaging language",
            "Avoid passive constructions that may confuse"
        ],
        "quality_indicators": [
            "Active voice used where appropriate",
            "Language is direct and engaging"
        ]
    },

    # ============================================================================
    # STRUCTURAL COHERENCE (20% weight) - 12 rules total
    # ============================================================================

    # Structural Coherence Core Rules (6)
    {
        "rule_id": "gen_sc_1",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "core",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Organize questions in a logical, coherent flow that guides respondents naturally through the survey",
        "implementation_notes": [
            "Start with general questions and move to specific",
            "Group related questions together logically",
            "Ensure smooth transitions between question topics"
        ],
        "quality_indicators": [
            "Question flow is logical and natural",
            "Transitions between topics are smooth"
        ]
    },
    {
        "rule_id": "gen_sc_2",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "core",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Structure survey sections in a logical sequence that supports the research objectives",
        "implementation_notes": [
            "Organize sections to build understanding progressively",
            "Place screening questions early in survey",
            "Position sensitive questions appropriately"
        ],
        "quality_indicators": [
            "Section sequence supports research objectives",
            "Progressive structure builds understanding"
        ]
    },
    {
        "rule_id": "gen_sc_3",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "core",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Implement appropriate skip logic and branching to maintain survey relevance for all respondents",
        "implementation_notes": [
            "Design skip logic to avoid irrelevant questions",
            "Create clear branching paths for different respondent types",
            "Ensure all paths lead to appropriate survey completion"
        ],
        "quality_indicators": [
            "Skip logic maintains relevance for all respondents",
            "Branching paths are well-designed"
        ]
    },
    {
        "rule_id": "gen_sc_4",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "core",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Balance survey length appropriately for the target audience and research depth required",
        "implementation_notes": [
            "Consider target audience attention span",
            "Balance comprehensiveness with completion rates",
            "Provide time estimates for survey completion"
        ],
        "quality_indicators": [
            "Survey length is appropriate for audience and objectives",
            "Good balance between depth and completion feasibility"
        ]
    },
    {
        "rule_id": "gen_sc_5",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "high",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Create clear section breaks and transitions that help respondents understand survey structure",
        "implementation_notes": [
            "Provide clear section headings and descriptions",
            "Use transition text between major topic changes",
            "Help respondents understand survey progress"
        ],
        "quality_indicators": [
            "Clear section breaks and transitions provided",
            "Survey structure is transparent to respondents"
        ]
    },
    {
        "rule_id": "gen_sc_6",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "high",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure consistent question numbering and formatting throughout the survey",
        "implementation_notes": [
            "Use consistent numbering scheme",
            "Maintain consistent question format patterns",
            "Apply consistent styling and presentation"
        ],
        "quality_indicators": [
            "Question numbering is consistent",
            "Formatting follows consistent patterns"
        ]
    },

    # Structural Coherence Scaled Rules (6)
    {
        "rule_id": "gen_sc_7",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design survey structure to minimize respondent fatigue and maintain engagement",
        "implementation_notes": [
            "Vary question types to maintain interest",
            "Avoid long sequences of similar questions",
            "Include engaging elements where appropriate"
        ],
        "quality_indicators": [
            "Survey structure minimizes respondent fatigue",
            "Question variety maintains engagement"
        ]
    },
    {
        "rule_id": "gen_sc_8",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Implement appropriate question dependencies and relationships throughout the survey",
        "implementation_notes": [
            "Design clear relationships between related questions",
            "Implement logical dependencies",
            "Ensure question relationships support analysis"
        ],
        "quality_indicators": [
            "Question dependencies are well-implemented",
            "Relationships between questions are clear"
        ]
    },
    {
        "rule_id": "gen_sc_9",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Create a survey structure that facilitates efficient data analysis and interpretation",
        "implementation_notes": [
            "Group questions to support analysis workflows",
            "Structure data collection for efficient processing",
            "Consider analysis requirements in survey organization"
        ],
        "quality_indicators": [
            "Structure facilitates efficient data analysis",
            "Organization supports interpretation needs"
        ]
    },
    {
        "rule_id": "gen_sc_10",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Balance the distribution of different question types throughout the survey",
        "implementation_notes": [
            "Distribute different question types evenly",
            "Avoid clustering similar question types",
            "Create balanced cognitive load distribution"
        ],
        "quality_indicators": [
            "Question types are well-distributed",
            "Balanced cognitive load throughout survey"
        ]
    },
    {
        "rule_id": "gen_sc_11",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design survey structure to accommodate different completion scenarios and timeframes",
        "implementation_notes": [
            "Consider partial completion and resumption",
            "Design for different completion timeframes",
            "Accommodate various respondent schedules"
        ],
        "quality_indicators": [
            "Structure accommodates different completion scenarios",
            "Flexible for various respondent needs"
        ]
    },
    {
        "rule_id": "gen_sc_12",
        "rule_type": "generation",
        "category": "structural_coherence",
        "priority": "medium",
        "weight": 0.017,  # Structural Coherence: 0.20/12 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Ensure survey structure supports quality assurance and data validation processes",
        "implementation_notes": [
            "Design structure to support quality checks",
            "Enable validation at appropriate points",
            "Support data quality assurance workflows"
        ],
        "quality_indicators": [
            "Structure supports quality assurance",
            "Data validation processes are facilitated"
        ]
    },

    # ============================================================================
    # DEPLOYMENT READINESS (10% weight) - 7 rules total
    # ============================================================================

    # Deployment Readiness Core Rules (4)
    {
        "rule_id": "gen_dr_1",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "core",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Provide clear, comprehensive instructions for survey respondents and administrators",
        "implementation_notes": [
            "Include detailed respondent instructions",
            "Provide administrator guidance where needed",
            "Ensure instructions are complete and actionable"
        ],
        "quality_indicators": [
            "Clear instructions provided for all users",
            "Instructions are comprehensive and actionable"
        ]
    },
    {
        "rule_id": "gen_dr_2",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "core",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design questions to be mobile-friendly and accessible across different devices and platforms",
        "implementation_notes": [
            "Ensure questions work well on mobile devices",
            "Consider accessibility requirements",
            "Test across different platforms and browsers"
        ],
        "quality_indicators": [
            "Questions are mobile-friendly",
            "Survey is accessible across devices"
        ]
    },
    {
        "rule_id": "gen_dr_3",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "core",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate time estimates and progress indicators in survey design",
        "implementation_notes": [
            "Provide realistic completion time estimates",
            "Design for progress tracking",
            "Help respondents understand survey length"
        ],
        "quality_indicators": [
            "Accurate time estimates provided",
            "Progress indicators included in design"
        ]
    },
    {
        "rule_id": "gen_dr_4",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "high",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design survey with appropriate error handling and validation mechanisms",
        "implementation_notes": [
            "Include input validation for data quality",
            "Design error messages that help respondents",
            "Implement appropriate required field validation"
        ],
        "quality_indicators": [
            "Error handling is well-designed",
            "Validation mechanisms support data quality"
        ]
    },

    # Deployment Readiness Scaled Rules (3)
    {
        "rule_id": "gen_dr_5",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "medium",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include appropriate privacy and data handling information in survey design",
        "implementation_notes": [
            "Address privacy concerns in survey introduction",
            "Include data handling information where required",
            "Ensure compliance with relevant privacy regulations"
        ],
        "quality_indicators": [
            "Privacy information is appropriately included",
            "Data handling is transparently addressed"
        ]
    },
    {
        "rule_id": "gen_dr_6",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "medium",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Design survey to facilitate efficient data collection and management processes",
        "implementation_notes": [
            "Structure data collection for efficient processing",
            "Consider data management workflow requirements",
            "Design for smooth data collection operations"
        ],
        "quality_indicators": [
            "Survey facilitates efficient data collection",
            "Data management processes are well-supported"
        ]
    },
    {
        "rule_id": "gen_dr_7",
        "rule_type": "generation",
        "category": "deployment_readiness",
        "priority": "medium",
        "weight": 0.014,  # Deployment Readiness: 0.10/7 rules
        "source_framework": "aira_v1",
        "generation_guideline": "Include testing recommendations and quality assurance guidelines for survey deployment",
        "implementation_notes": [
            "Recommend pre-deployment testing procedures",
            "Include quality assurance checkpoints",
            "Provide deployment best practices"
        ],
        "quality_indicators": [
            "Testing recommendations are included",
            "Quality assurance guidelines provided"
        ]
    }
]

def validate_rules_structure():
    """Validate that the rules structure is correct"""
    total_rules = len(CORE_GENERATION_RULES)

    # Count by pillar
    pillar_counts = {}
    pillar_weights = {}

    for rule in CORE_GENERATION_RULES:
        pillar = rule['category']
        if pillar not in pillar_counts:
            pillar_counts[pillar] = 0
            pillar_weights[pillar] = 0
        pillar_counts[pillar] += 1
        pillar_weights[pillar] += rule['weight']

    # Expected counts
    expected_counts = {
        'content_validity': 11,
        'methodological_rigor': 15,
        'clarity_comprehensibility': 13,
        'structural_coherence': 12,
        'deployment_readiness': 7
    }

    # Expected weights (should sum to pillar weight)
    expected_weights = {
        'content_validity': 0.20,
        'methodological_rigor': 0.25,
        'clarity_comprehensibility': 0.25,
        'structural_coherence': 0.20,
        'deployment_readiness': 0.10
    }

    print(f"🔍 Total rules: {total_rules} (expected: 58)")
    print("\n📊 Rules by pillar:")

    for pillar, count in pillar_counts.items():
        expected = expected_counts.get(pillar, 0)
        weight = pillar_weights.get(pillar, 0)
        expected_weight = expected_weights.get(pillar, 0)
        status = "✅" if count == expected else "❌"
        weight_status = "✅" if abs(weight - expected_weight) < 0.01 else "❌"
        print(f"  {status} {pillar}: {count} rules (expected: {expected})")
        print(f"  {weight_status} Weight: {weight:.3f} (expected: {expected_weight:.3f})")

    # Check total weight
    total_weight = sum(pillar_weights.values())
    print(f"\n🎯 Total weight: {total_weight:.3f} (expected: 1.000)")

    # Validation summary
    is_valid = (
        total_rules == 58 and
        all(pillar_counts.get(p, 0) == expected_counts[p] for p in expected_counts) and
        abs(total_weight - 1.0) < 0.01
    )

    print(f"\n{'✅ Validation PASSED' if is_valid else '❌ Validation FAILED'}")
    return is_valid

if __name__ == "__main__":
    validate_rules_structure()