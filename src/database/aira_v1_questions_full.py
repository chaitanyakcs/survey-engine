"""
Complete AiRA v1 Evaluation Questions Dataset
All 58 evaluation questions from the AiRA_Evaluation_Framework_v1 specification
"""

# Complete AiRA v1 Questions Dataset (58 questions total)
AIRA_V1_COMPLETE_QUESTIONS = [

    # ============================================================================
    # CONTENT VALIDITY (20% weight) - 11 questions total
    # ============================================================================

    # Content Validity Yes/No Questions (6)
    {
        "question_id": "cv_yn_1",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire cover all essential aspects of the research objectives stated in the requirement document?",
        "evaluation_criteria": "Check if all research objectives from RFQ are addressed by survey questions",
        "scoring_weight": 0.091,  # 1/11 of pillar
        "response_format": "boolean",
        "llm_evaluation_prompt": "Analyze if the survey questions comprehensively address ALL research objectives mentioned in the RFQ. Return true only if all objectives are covered."
    },
    {
        "question_id": "cv_yn_2",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are demographic questions appropriate and sufficient for the target audience analysis?",
        "evaluation_criteria": "Evaluate demographic question coverage for target audience analysis needs",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if demographic questions are appropriate for the target audience and research objectives. Consider age, gender, income, geography, etc. as relevant."
    },
    {
        "question_id": "cv_yn_3",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire include validation or consistency check questions to verify response reliability?",
        "evaluation_criteria": "Check for validation questions, attention checks, or consistency verification",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Look for validation questions, attention checks, or questions that verify response consistency and reliability."
    },
    {
        "question_id": "cv_yn_4",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are all key stakeholder information needs addressed within the questionnaire?",
        "evaluation_criteria": "Verify that questionnaire addresses information needs of all key stakeholders",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the survey addresses information needs that would be important to key stakeholders mentioned in the RFQ."
    },
    {
        "question_id": "cv_yn_5",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire avoid including irrelevant or off-topic questions?",
        "evaluation_criteria": "Check for questions that don't align with research objectives",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Identify any questions that seem irrelevant or off-topic relative to the stated research objectives in the RFQ."
    },
    {
        "question_id": "cv_yn_6",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are industry-specific considerations and terminology appropriately incorporated?",
        "evaluation_criteria": "Evaluate use of appropriate industry terminology and considerations",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if the survey appropriately uses industry-specific terminology and addresses industry-specific considerations relevant to the research context."
    },

    # Content Validity Scaled Questions (5)
    {
        "question_id": "cv_sc_1",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Rate the comprehensiveness of topic coverage relative to research objectives",
        "evaluation_criteria": "Assess how comprehensively the survey covers the research topics",
        "scoring_weight": 0.109,  # 1/5 of remaining weight (0.545/5)
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how comprehensively the survey covers all aspects of the research objectives. 1=very poor coverage, 5=excellent comprehensive coverage."
    },
    {
        "question_id": "cv_sc_2",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Evaluate the alignment between questionnaire content and stated research goals",
        "evaluation_criteria": "Assess alignment between survey content and research goals",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well the questionnaire content aligns with the stated research goals. 1=very poor alignment, 5=excellent alignment."
    },
    {
        "question_id": "cv_sc_3",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Assess the adequacy of demographic and classification questions for analysis needs",
        "evaluation_criteria": "Evaluate if demographic questions support required analysis",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the adequacy of demographic and classification questions for supporting the analysis needs. 1=inadequate, 5=excellent coverage."
    },
    {
        "question_id": "cv_sc_4",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Rate the inclusion of necessary validation questions to ensure data quality",
        "evaluation_criteria": "Assess presence and quality of validation questions",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the inclusion of validation questions and data quality checks. 1=no validation, 5=excellent validation measures."
    },
    {
        "question_id": "cv_sc_5",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Evaluate how well the questionnaire addresses all stakeholder information requirements",
        "evaluation_criteria": "Assess coverage of all stakeholder information needs",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well the questionnaire addresses information requirements of all stakeholders. 1=poor coverage, 5=excellent coverage."
    },

    # ============================================================================
    # METHODOLOGICAL RIGOR (25% weight) - 11 questions total
    # ============================================================================

    # Methodological Rigor Yes/No Questions (6)
    {
        "question_id": "mr_yn_1",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Are questions sequenced logically from general to specific topics?",
        "evaluation_criteria": "Check for logical progression in question ordering",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if questions follow a logical sequence from general to specific topics. Check for proper warm-up and progression."
    },
    {
        "question_id": "mr_yn_2",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Does the questionnaire avoid leading or biased question formulations?",
        "evaluation_criteria": "Check for leading questions, loaded language, or bias",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Identify any leading questions, loaded language, or biased formulations that could influence responses."
    },
    {
        "question_id": "mr_yn_3",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Are appropriate scale types (Likert, ranking, categorical) used consistently throughout?",
        "evaluation_criteria": "Evaluate consistency and appropriateness of scale types",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if scale types are appropriate for the data being collected and used consistently throughout the survey."
    },
    {
        "question_id": "mr_yn_4",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Does the questionnaire include proper screening questions to ensure qualified respondents?",
        "evaluation_criteria": "Check for appropriate screening and qualification questions",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the survey includes proper screening questions to ensure respondents meet target criteria."
    },
    {
        "question_id": "mr_yn_5",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Are sensitive questions positioned appropriately (toward the end) to minimize dropout?",
        "evaluation_criteria": "Check positioning of sensitive or personal questions",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that sensitive or personal questions are positioned toward the end of the survey to minimize dropout."
    },
    {
        "question_id": "mr_yn_6",
        "question_type": "yes_no",
        "pillar": "methodological_rigor",
        "question_text": "Does the questionnaire follow established market research best practices for question construction?",
        "evaluation_criteria": "Evaluate adherence to market research best practices",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the questionnaire follows established market research best practices for question construction and survey design."
    },

    # Methodological Rigor Scaled Questions (5)
    {
        "question_id": "mr_sc_1",
        "question_type": "scaled",
        "pillar": "methodological_rigor",
        "question_text": "Rate the logical flow and sequence of questions throughout the questionnaire",
        "evaluation_criteria": "Assess overall logical flow and question sequencing",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the logical flow and sequence of questions. 1=poor flow/confusing, 5=excellent logical progression."
    },
    {
        "question_id": "mr_sc_2",
        "question_type": "scaled",
        "pillar": "methodological_rigor",
        "question_text": "Evaluate the appropriateness of scale types and response formats used",
        "evaluation_criteria": "Assess appropriateness of scales and response formats",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the appropriateness of scale types and response formats for the data being collected. 1=inappropriate, 5=perfectly appropriate."
    },
    {
        "question_id": "mr_sc_3",
        "question_type": "scaled",
        "pillar": "methodological_rigor",
        "question_text": "Assess the questionnaire's adherence to methodological standards for bias avoidance",
        "evaluation_criteria": "Evaluate bias avoidance and methodological soundness",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well the questionnaire avoids bias and follows methodological standards. 1=high bias risk, 5=excellent bias avoidance."
    },
    {
        "question_id": "mr_sc_4",
        "question_type": "scaled",
        "pillar": "methodological_rigor",
        "question_text": "Rate the effectiveness of screening and qualification questions",
        "evaluation_criteria": "Assess quality and effectiveness of screening questions",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the effectiveness of screening and qualification questions. 1=poor screening, 5=excellent qualification process."
    },
    {
        "question_id": "mr_sc_5",
        "question_type": "scaled",
        "pillar": "methodological_rigor",
        "question_text": "Evaluate the overall methodological soundness of the research design",
        "evaluation_criteria": "Assess overall methodological quality of the design",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the overall methodological soundness of the research design. 1=methodologically poor, 5=methodologically excellent."
    },

    # ============================================================================
    # CLARITY & COMPREHENSIBILITY (25% weight) - 11 questions total
    # ============================================================================

    # Clarity & Comprehensibility Yes/No Questions (6)
    {
        "question_id": "cc_yn_1",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Are all questions written in clear, simple language appropriate for the target audience?",
        "evaluation_criteria": "Check language clarity and appropriateness for audience",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if all questions use clear, simple language appropriate for the target audience demographic."
    },
    {
        "question_id": "cc_yn_2",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Does the questionnaire avoid technical jargon or complex terminology without explanation?",
        "evaluation_criteria": "Check for unexplained jargon or complex terms",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Identify any technical jargon or complex terminology that isn't explained or may confuse respondents."
    },
    {
        "question_id": "cc_yn_3",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Are question instructions clear and complete for each question type?",
        "evaluation_criteria": "Evaluate clarity and completeness of instructions",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if instructions for each question type are clear, complete, and help respondents understand how to answer."
    },
    {
        "question_id": "cc_yn_4",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Does the questionnaire avoid double-barreled questions (asking multiple things at once)?",
        "evaluation_criteria": "Check for double-barreled or compound questions",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Identify any double-barreled questions that ask about multiple concepts or issues simultaneously."
    },
    {
        "question_id": "cc_yn_5",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Are all response options mutually exclusive and collectively exhaustive where appropriate?",
        "evaluation_criteria": "Check response option quality and completeness",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that response options are mutually exclusive (don't overlap) and collectively exhaustive (cover all possibilities) where appropriate."
    },
    {
        "question_id": "cc_yn_6",
        "question_type": "yes_no",
        "pillar": "clarity_comprehensibility",
        "question_text": "Is the estimated completion time reasonable for the questionnaire length?",
        "evaluation_criteria": "Assess reasonableness of completion time vs length",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Evaluate if the estimated completion time is reasonable given the questionnaire length and complexity."
    },

    # Clarity & Comprehensibility Scaled Questions (5)
    {
        "question_id": "cc_sc_1",
        "question_type": "scaled",
        "pillar": "clarity_comprehensibility",
        "question_text": "Rate the clarity and understandability of question wording",
        "evaluation_criteria": "Assess overall clarity of question wording",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the clarity and understandability of question wording throughout the survey. 1=very unclear, 5=very clear."
    },
    {
        "question_id": "cc_sc_2",
        "question_type": "scaled",
        "pillar": "clarity_comprehensibility",
        "question_text": "Evaluate the appropriateness of language level for the target audience",
        "evaluation_criteria": "Assess language appropriateness for target demographic",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how appropriate the language level is for the target audience. 1=too complex/simple, 5=perfectly appropriate."
    },
    {
        "question_id": "cc_sc_3",
        "question_type": "scaled",
        "pillar": "clarity_comprehensibility",
        "question_text": "Assess the completeness and clarity of instructions provided to respondents",
        "evaluation_criteria": "Evaluate instruction quality and completeness",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the completeness and clarity of instructions provided to respondents. 1=poor instructions, 5=excellent guidance."
    },
    {
        "question_id": "cc_sc_4",
        "question_type": "scaled",
        "pillar": "clarity_comprehensibility",
        "question_text": "Rate the absence of ambiguous or confusing question formulations",
        "evaluation_criteria": "Assess presence of ambiguous or confusing questions",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the absence of ambiguous or confusing questions. 1=many ambiguous questions, 5=no ambiguous questions."
    },
    {
        "question_id": "cc_sc_5",
        "question_type": "scaled",
        "pillar": "clarity_comprehensibility",
        "question_text": "Evaluate the overall readability and user-friendliness of the questionnaire",
        "evaluation_criteria": "Assess overall readability and user experience",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the overall readability and user-friendliness of the questionnaire. 1=poor readability, 5=excellent user experience."
    },

    # ============================================================================
    # STRUCTURAL COHERENCE (20% weight) - 11 questions total
    # ============================================================================

    # Structural Coherence Yes/No Questions (6)
    {
        "question_id": "sc_yn_1",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Does the questionnaire have a clear introduction explaining its purpose and importance?",
        "evaluation_criteria": "Check for clear introduction and purpose statement",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that the questionnaire has a clear introduction that explains its purpose and importance to respondents."
    },
    {
        "question_id": "sc_yn_2",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Are question blocks or sections organized thematically and logically?",
        "evaluation_criteria": "Evaluate thematic organization of question blocks",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if question blocks or sections are organized thematically and follow a logical structure."
    },
    {
        "question_id": "sc_yn_3",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Does the questionnaire include appropriate transition statements between major sections?",
        "evaluation_criteria": "Check for transition statements between sections",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Look for appropriate transition statements that guide respondents between major sections of the questionnaire."
    },
    {
        "question_id": "sc_yn_4",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Are skip patterns and routing logic implemented correctly and clearly?",
        "evaluation_criteria": "Evaluate skip patterns and routing logic clarity",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if skip patterns and routing logic are implemented correctly and clearly communicated to respondents."
    },
    {
        "question_id": "sc_yn_5",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Does the questionnaire conclude with appropriate closing statements or thank you messages?",
        "evaluation_criteria": "Check for appropriate closing and thank you statements",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that the questionnaire concludes with appropriate closing statements or thank you messages."
    },
    {
        "question_id": "sc_yn_6",
        "question_type": "yes_no",
        "pillar": "structural_coherence",
        "question_text": "Are open-ended and closed-ended questions balanced appropriately for the research objectives?",
        "evaluation_criteria": "Evaluate balance of open-ended vs closed-ended questions",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the balance of open-ended and closed-ended questions is appropriate for the research objectives."
    },

    # Structural Coherence Scaled Questions (5)
    {
        "question_id": "sc_sc_1",
        "question_type": "scaled",
        "pillar": "structural_coherence",
        "question_text": "Rate the overall organization and structure of the questionnaire",
        "evaluation_criteria": "Assess overall structural organization quality",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the overall organization and structure of the questionnaire. 1=poorly organized, 5=excellently structured."
    },
    {
        "question_id": "sc_sc_2",
        "question_type": "scaled",
        "pillar": "structural_coherence",
        "question_text": "Evaluate the logical grouping of related questions into coherent sections",
        "evaluation_criteria": "Assess logical grouping and section coherence",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well related questions are logically grouped into coherent sections. 1=poor grouping, 5=excellent logical sections."
    },
    {
        "question_id": "sc_sc_3",
        "question_type": "scaled",
        "pillar": "structural_coherence",
        "question_text": "Assess the effectiveness of transitions between different topic areas",
        "evaluation_criteria": "Evaluate transition quality between topic areas",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the effectiveness of transitions between different topic areas. 1=abrupt/confusing transitions, 5=smooth effective transitions."
    },
    {
        "question_id": "sc_sc_4",
        "question_type": "scaled",
        "pillar": "structural_coherence",
        "question_text": "Rate the appropriateness of question type variety and distribution",
        "evaluation_criteria": "Assess question type variety and distribution",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the appropriateness of question type variety and distribution throughout the survey. 1=poor variety, 5=excellent mix."
    },
    {
        "question_id": "sc_sc_5",
        "question_type": "scaled",
        "pillar": "structural_coherence",
        "question_text": "Evaluate the professional presentation and formatting of the questionnaire",
        "evaluation_criteria": "Assess professional presentation and formatting quality",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the professional presentation and formatting of the questionnaire. 1=poor presentation, 5=highly professional."
    },

    # ============================================================================
    # DEPLOYMENT READINESS (10% weight) - 11 questions total
    # ============================================================================

    # Deployment Readiness Yes/No Questions (6)
    {
        "question_id": "dr_yn_1",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Is the questionnaire length appropriate for the research objectives and target audience?",
        "evaluation_criteria": "Check appropriateness of questionnaire length",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the questionnaire length is appropriate for achieving the research objectives and suitable for the target audience."
    },
    {
        "question_id": "dr_yn_2",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Does the questionnaire meet industry compliance and regulatory requirements?",
        "evaluation_criteria": "Check compliance with industry regulations",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that the questionnaire meets relevant industry compliance and regulatory requirements."
    },
    {
        "question_id": "dr_yn_3",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Are data privacy and ethical considerations properly addressed in the questionnaire design?",
        "evaluation_criteria": "Evaluate data privacy and ethical considerations",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if data privacy and ethical considerations are properly addressed in the questionnaire design."
    },
    {
        "question_id": "dr_yn_4",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Is the questionnaire technically compatible with intended distribution platforms?",
        "evaluation_criteria": "Check technical compatibility with distribution platforms",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the questionnaire is technically compatible with intended distribution platforms and methods."
    },
    {
        "question_id": "dr_yn_5",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Does the questionnaire include all necessary legal disclaimers and consent statements?",
        "evaluation_criteria": "Check for necessary legal disclaimers and consent",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Verify that all necessary legal disclaimers and consent statements are included in the questionnaire."
    },
    {
        "question_id": "dr_yn_6",
        "question_type": "yes_no",
        "pillar": "deployment_readiness",
        "question_text": "Are the resource requirements (time, cost, respondent burden) realistic for implementation?",
        "evaluation_criteria": "Evaluate realistic resource requirements",
        "scoring_weight": 0.091,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the resource requirements (time, cost, respondent burden) are realistic for successful implementation."
    },

    # Deployment Readiness Scaled Questions (5)
    {
        "question_id": "dr_sc_1",
        "question_type": "scaled",
        "pillar": "deployment_readiness",
        "question_text": "Rate the overall feasibility of implementing this questionnaire in the field",
        "evaluation_criteria": "Assess overall implementation feasibility",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the overall feasibility of implementing this questionnaire in the field. 1=very difficult to implement, 5=very easy to implement."
    },
    {
        "question_id": "dr_sc_2",
        "question_type": "scaled",
        "pillar": "deployment_readiness",
        "question_text": "Evaluate the appropriateness of questionnaire length for target completion rates",
        "evaluation_criteria": "Assess length appropriateness for completion rates",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how appropriate the questionnaire length is for achieving target completion rates. 1=too long/short, 5=perfect length."
    },
    {
        "question_id": "dr_sc_3",
        "question_type": "scaled",
        "pillar": "deployment_readiness",
        "question_text": "Assess compliance with relevant industry standards and regulations",
        "evaluation_criteria": "Evaluate compliance with industry standards",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 compliance with relevant industry standards and regulations. 1=poor compliance, 5=excellent compliance."
    },
    {
        "question_id": "dr_sc_4",
        "question_type": "scaled",
        "pillar": "deployment_readiness",
        "question_text": "Rate the questionnaire's readiness for immediate deployment without modifications",
        "evaluation_criteria": "Assess immediate deployment readiness",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the questionnaire's readiness for immediate deployment without modifications. 1=needs major changes, 5=ready to deploy."
    },
    {
        "question_id": "dr_sc_5",
        "question_type": "scaled",
        "pillar": "deployment_readiness",
        "question_text": "Evaluate the cost-effectiveness of the questionnaire design for achieving research objectives",
        "evaluation_criteria": "Assess cost-effectiveness for objectives",
        "scoring_weight": 0.109,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the cost-effectiveness of the questionnaire design for achieving research objectives. 1=poor value, 5=excellent value."
    },

    # ============================================================================
    # SUMMARY QUESTIONS (Overall Assessment) - 6 questions total
    # ============================================================================

    # Summary Yes/No Questions (3)
    {
        "question_id": "sum_yn_1",
        "question_type": "summary_yes_no",
        "pillar": "overall",
        "question_text": "Would you recommend this questionnaire for deployment without major revisions?",
        "evaluation_criteria": "Overall recommendation for deployment readiness",
        "scoring_weight": 0.333,  # 1/3 of summary questions
        "response_format": "boolean",
        "llm_evaluation_prompt": "Based on your comprehensive evaluation, would you recommend this questionnaire for deployment without major revisions?"
    },
    {
        "question_id": "sum_yn_2",
        "question_type": "summary_yes_no",
        "pillar": "overall",
        "question_text": "Does this questionnaire meet professional market research standards?",
        "evaluation_criteria": "Assessment of professional market research standards",
        "scoring_weight": 0.333,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Evaluate if this questionnaire meets professional market research standards and industry best practices."
    },
    {
        "question_id": "sum_yn_3",
        "question_type": "summary_yes_no",
        "pillar": "overall",
        "question_text": "Would this questionnaire likely achieve the stated research objectives?",
        "evaluation_criteria": "Assessment of objective achievement likelihood",
        "scoring_weight": 0.333,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess the likelihood that this questionnaire would achieve the stated research objectives effectively."
    },

    # Summary Scaled Questions (3)
    {
        "question_id": "sum_sc_1",
        "question_type": "summary_scaled",
        "pillar": "overall",
        "question_text": "Overall questionnaire quality compared to industry benchmarks",
        "evaluation_criteria": "Overall quality assessment vs industry benchmarks",
        "scoring_weight": 0.333,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the overall questionnaire quality compared to industry benchmarks. 1=well below standards, 5=exceeds industry standards."
    },
    {
        "question_id": "sum_sc_2",
        "question_type": "summary_scaled",
        "pillar": "overall",
        "question_text": "Likelihood of achieving reliable and valid research results",
        "evaluation_criteria": "Assessment of result reliability and validity likelihood",
        "scoring_weight": 0.333,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the likelihood of achieving reliable and valid research results with this questionnaire. 1=very unlikely, 5=very likely."
    },
    {
        "question_id": "sum_sc_3",
        "question_type": "summary_scaled",
        "pillar": "overall",
        "question_text": "Professional confidence in recommending this questionnaire to stakeholders",
        "evaluation_criteria": "Professional confidence in recommendation",
        "scoring_weight": 0.333,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 your professional confidence in recommending this questionnaire to stakeholders. 1=not confident, 5=very confident."
    }
]

# Validation: Ensure we have exactly 58 questions
def validate_question_count():
    """Validate that we have exactly 58 questions as per AiRA v1 spec"""
    total_questions = len(AIRA_V1_COMPLETE_QUESTIONS)

    # Count by pillar
    pillar_counts = {}
    for q in AIRA_V1_COMPLETE_QUESTIONS:
        pillar = q['pillar']
        if pillar not in pillar_counts:
            pillar_counts[pillar] = 0
        pillar_counts[pillar] += 1

    print(f"Total questions: {total_questions}")
    print("Questions per pillar:")
    for pillar, count in pillar_counts.items():
        print(f"  {pillar}: {count}")

    # Validate we have exactly 58 questions
    assert total_questions == 58, f"Expected 58 questions, got {total_questions}"

    # Validate each main pillar has 11 questions (6 yes/no + 5 scaled)
    main_pillars = ['content_validity', 'methodological_rigor', 'clarity_comprehensibility',
                   'structural_coherence', 'deployment_readiness']
    for pillar in main_pillars:
        assert pillar_counts[pillar] == 11, f"Expected 11 questions for {pillar}, got {pillar_counts[pillar]}"

    # Validate overall has 6 questions (3 yes/no + 3 scaled)
    assert pillar_counts['overall'] == 6, f"Expected 6 overall questions, got {pillar_counts['overall']}"

    print("✅ Question count validation passed!")

if __name__ == "__main__":
    validate_question_count()