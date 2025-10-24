# AiRA V1 Evaluation Framework - Reference Documentation

## Overview

This document preserves the original AiRA V1 evaluation framework for historical reference. The 58 evaluation questions documented here have been converted to generation rules and are now implemented in the database-driven evaluation system.

**Status**: Deprecated - Use Multiple Calls evaluation mode instead, which provides the same functionality using customizable generation rules from the database.

## Framework Structure

The AiRA V1 framework consists of 58 structured evaluation questions organized into 5 pillars with specific weights:

- **Content Validity**: 20% weight (11 questions)
- **Methodological Rigor**: 25% weight (11 questions)  
- **Clarity & Comprehensibility**: 25% weight (11 questions)
- **Structural Coherence**: 20% weight (11 questions)
- **Deployment Readiness**: 10% weight (11 questions)
- **Summary Questions**: 3 questions

## Evaluation Questions

### Content Validity (20% weight)

#### Yes/No Questions (CV_YN_1 to CV_YN_6)
- **CV_YN_1**: Does the questionnaire cover all essential aspects of the research objectives stated in the requirement document? (true/false)
- **CV_YN_2**: Are demographic questions appropriate and sufficient for the target audience analysis? (true/false)
- **CV_YN_3**: Does the questionnaire include validation or consistency check questions to verify response reliability? (true/false)
- **CV_YN_4**: Are all key stakeholder information needs addressed within the questionnaire? (true/false)
- **CV_YN_5**: Does the questionnaire avoid including irrelevant or off-topic questions? (true/false)
- **CV_YN_6**: Are industry-specific considerations and terminology appropriately incorporated? (true/false)

#### Scaled Questions (CV_SC_1 to CV_SC_5)
- **CV_SC_1**: Rate the comprehensiveness of topic coverage relative to research objectives (1-5 scale)
- **CV_SC_2**: Evaluate the alignment between questionnaire content and stated research goals (1-5 scale)
- **CV_SC_3**: Assess the adequacy of demographic and classification questions for analysis needs (1-5 scale)
- **CV_SC_4**: Rate the inclusion of necessary validation questions to ensure data quality (1-5 scale)
- **CV_SC_5**: Evaluate how well the questionnaire addresses all stakeholder information requirements (1-5 scale)

### Methodological Rigor (25% weight)

#### Yes/No Questions (MR_YN_1 to MR_YN_6)
- **MR_YN_1**: Are questions sequenced logically from general to specific topics? (true/false)
- **MR_YN_2**: Does the questionnaire avoid leading or biased question formulations? (true/false)
- **MR_YN_3**: Are appropriate scale types (Likert, ranking, categorical) used consistently throughout? (true/false)
- **MR_YN_4**: Does the questionnaire include proper screening questions to ensure qualified respondents? (true/false)
- **MR_YN_5**: Are sensitive questions positioned appropriately (toward the end) to minimize dropout? (true/false)
- **MR_YN_6**: Does the questionnaire follow established market research best practices for question construction? (true/false)

#### Scaled Questions (MR_SC_1 to MR_SC_5)
- **MR_SC_1**: Rate the logical flow and sequence of questions throughout the questionnaire (1-5 scale)
- **MR_SC_2**: Evaluate the appropriateness of scale types and response formats used (1-5 scale)
- **MR_SC_3**: Assess the questionnaire's adherence to methodological standards for bias avoidance (1-5 scale)
- **MR_SC_4**: Rate the effectiveness of screening and qualification questions (1-5 scale)
- **MR_SC_5**: Evaluate the overall methodological soundness of the research design (1-5 scale)

### Clarity & Comprehensibility (25% weight)

#### Yes/No Questions (CC_YN_1 to CC_YN_6)
- **CC_YN_1**: Are all questions written in clear, simple language appropriate for the target audience? (true/false)
- **CC_YN_2**: Does the questionnaire avoid technical jargon or complex terminology without explanation? (true/false)
- **CC_YN_3**: Are question instructions clear and complete for each question type? (true/false)
- **CC_YN_4**: Does the questionnaire avoid double-barreled questions (asking multiple things at once)? (true/false)
- **CC_YN_5**: Are all response options mutually exclusive and collectively exhaustive where appropriate? (true/false)
- **CC_YN_6**: Is the estimated completion time reasonable for the questionnaire length? (true/false)

#### Scaled Questions (CC_SC_1 to CC_SC_5)
- **CC_SC_1**: Rate the clarity and understandability of question wording (1-5 scale)
- **CC_SC_2**: Evaluate the appropriateness of language level for the target audience (1-5 scale)
- **CC_SC_3**: Assess the completeness and clarity of instructions provided to respondents (1-5 scale)
- **CC_SC_4**: Rate the absence of ambiguous or confusing question formulations (1-5 scale)
- **CC_SC_5**: Evaluate the overall readability and user-friendliness of the questionnaire (1-5 scale)

### Structural Coherence (20% weight)

#### Yes/No Questions (SC_YN_1 to SC_YN_6)
- **SC_YN_1**: Does the questionnaire have a clear introduction explaining its purpose and importance? (true/false)
- **SC_YN_2**: Are question blocks or sections organized thematically and logically? (true/false)
- **SC_YN_3**: Does the questionnaire include appropriate transition statements between major sections? (true/false)
- **SC_YN_4**: Are skip patterns and routing logic implemented correctly and clearly? (true/false)
- **SC_YN_5**: Does the questionnaire conclude with appropriate closing statements or thank you messages? (true/false)
- **SC_YN_6**: Are open-ended and closed-ended questions balanced appropriately for the research objectives? (true/false)

#### Scaled Questions (SC_SC_1 to SC_SC_5)
- **SC_SC_1**: Rate the overall organization and structure of the questionnaire (1-5 scale)
- **SC_SC_2**: Evaluate the logical grouping of related questions into coherent sections (1-5 scale)
- **SC_SC_3**: Assess the effectiveness of transitions between different topic areas (1-5 scale)
- **SC_SC_4**: Rate the appropriateness of question type variety and distribution (1-5 scale)
- **SC_SC_5**: Evaluate the professional presentation and formatting of the questionnaire (1-5 scale)

### Deployment Readiness (10% weight)

#### Yes/No Questions (DR_YN_1 to DR_YN_6)
- **DR_YN_1**: Is the questionnaire length appropriate for the research objectives and target audience? (true/false)
- **DR_YN_2**: Does the questionnaire meet industry compliance and regulatory requirements? (true/false)
- **DR_YN_3**: Are data privacy and ethical considerations properly addressed in the questionnaire design? (true/false)
- **DR_YN_4**: Is the questionnaire technically compatible with intended distribution platforms? (true/false)
- **DR_YN_5**: Does the questionnaire include all necessary legal disclaimers and consent statements? (true/false)
- **DR_YN_6**: Are the resource requirements (time, cost, respondent burden) realistic for implementation? (true/false)

#### Scaled Questions (DR_SC_1 to DR_SC_5)
- **DR_SC_1**: Rate the overall feasibility of implementing this questionnaire in the field (1-5 scale)
- **DR_SC_2**: Evaluate the appropriateness of questionnaire length for target completion rates (1-5 scale)
- **DR_SC_3**: Assess compliance with relevant industry standards and regulations (1-5 scale)
- **DR_SC_4**: Rate the questionnaire's readiness for immediate deployment without modifications (1-5 scale)
- **DR_SC_5**: Evaluate the cost-effectiveness of the questionnaire design for achieving research objectives (1-5 scale)

### Summary Questions

#### Yes/No Questions (SUM_YN_1 to SUM_YN_3)
- **SUM_YN_1**: Would you recommend this questionnaire for deployment without major revisions? (true/false)
- **SUM_YN_2**: Does this questionnaire meet professional market research standards? (true/false)
- **SUM_YN_3**: Would this questionnaire likely achieve the stated research objectives? (true/false)

#### Scaled Questions (SUM_SC_1 to SUM_SC_3)
- **SUM_SC_1**: Overall questionnaire quality compared to industry benchmarks (1-5 scale)
- **SUM_SC_2**: Likelihood of achieving reliable and valid research results (1-5 scale)
- **SUM_SC_3**: Professional confidence in recommending this questionnaire to stakeholders (1-5 scale)

## Scoring Methodology

### Question Scoring
- **Yes/No Questions**: 1.0 for true, 0.0 for false
- **Scaled Questions**: Normalized from 1-5 scale to 0.0-1.0 range using formula: (score - 1) / 4

### Pillar Scoring
Each pillar score is calculated as the weighted average of all questions within that pillar.

### Overall Scoring
Overall score = Σ(pillar_score × pillar_weight)

Where pillar weights are:
- Content Validity: 0.20
- Methodological Rigor: 0.25
- Clarity & Comprehensibility: 0.25
- Structural Coherence: 0.20
- Deployment Readiness: 0.10

### Color Coding
- **Red**: < 60% (needs significant improvement)
- **Orange**: 60-80% (good with room for improvement)
- **Green**: > 80% (excellent quality)

## Migration to Generation Rules

The 58 questions in this framework have been converted to generation rules stored in the database (`survey_rules` table with `rule_type = 'generation'`). These rules are now used by:

1. **Survey Generation**: Rules guide the creation of surveys
2. **Multiple Calls Evaluation**: Rules are used to evaluate generated surveys

This provides the same evaluation capability with:
- Database-driven customization
- Better integration with the generation process
- More flexible rule management via API

## Current Evaluation Modes

- **Single Call**: Fast evaluation using generic independent criteria
- **Multiple Calls**: Detailed evaluation using customizable generation rules from database

Use Multiple Calls mode to get the same comprehensive evaluation that AiRA V1 provided, but with rules that can be customized via the API.
