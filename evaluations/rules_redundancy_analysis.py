#!/usr/bin/env python3
"""
Rules Redundancy Analysis
Compare existing rules with new pillar-based rules to identify overlaps and optimization opportunities
"""

# Existing rules from 003_add_survey_rules.sql
EXISTING_RULES = {
    "methodology": {
        "van_westendorp": {
            "validation_rules": [
                "Must have exactly 4 price questions",
                "Questions must follow the exact Van Westendorp format", 
                "Price ranges should be logical and sequential",
                "Include open-ended follow-up for reasoning",
                "Use currency-appropriate formatting"
            ],
            "best_practices": [
                "Present questions in random order to avoid bias",
                "Include product description before price questions",
                "Use realistic price ranges based on market research",
                "Add demographic questions for segmentation"
            ]
        },
        "conjoint": {
            "validation_rules": [
                "Must have balanced choice sets",
                "Attributes must be orthogonal (independent)",
                "Include appropriate sample size calculations", 
                "Use realistic attribute levels",
                "Include 'None of the above' option"
            ],
            "best_practices": [
                "Limit to 3-6 attributes to avoid cognitive overload",
                "Use 2-4 levels per attribute",
                "Include 8-12 choice tasks per respondent",
                "Randomize choice set presentation"
            ]
        },
        "nps": {
            "validation_rules": [
                "Must use 0-10 scale",
                "Include follow-up question for reasoning",
                "Properly categorize promoters (9-10), passives (7-8), detractors (0-6)",
                "Use consistent wording across surveys"
            ],
            "best_practices": [
                "Ask NPS question early in survey",
                "Include context about the product/service", 
                "Add behavioral questions for segmentation",
                "Use consistent timeframes (e.g., 'in the past 6 months')"
            ]
        }
    },
    "quality": {
        "question_quality": [
            "Questions must be clear, concise, and unambiguous",
            "Avoid leading, loaded, or double-barreled questions",
            "Use appropriate question types for the data needed",
            "Include proper validation and skip logic where needed",
            "Avoid jargon and technical terms unless necessary",
            "Use consistent terminology throughout the survey",
            "Ensure questions are culturally appropriate and inclusive"
        ],
        "survey_structure": [
            "Start with screening questions to qualify respondents",
            "Group related questions logically",
            "Place sensitive questions near the end",
            "Include demographic questions for segmentation",
            "Use progress indicators for long surveys",
            "Include clear instructions and context",
            "End with thank you message and next steps"
        ],
        "respondent_experience": [
            "Keep survey length appropriate (5-15 minutes)",
            "Use clear instructions and progress indicators",
            "Avoid repetitive or redundant questions",
            "Ensure mobile-friendly question formats",
            "Use engaging and conversational language",
            "Include appropriate incentives information",
            "Provide clear privacy and data usage information"
        ]
    },
    "industry": {
        "healthcare": [
            "Include HIPAA compliance considerations",
            "Use appropriate medical terminology",
            "Include consent and privacy statements",
            "Consider patient confidentiality",
            "Use validated health assessment tools",
            "Include appropriate demographic questions",
            "Ensure cultural sensitivity in health questions"
        ],
        "financial_services": [
            "Include appropriate disclaimers",
            "Use clear financial terminology", 
            "Include risk assessment questions",
            "Ensure regulatory compliance",
            "Include appropriate demographic questions",
            "Use validated financial scales",
            "Consider privacy and security requirements"
        ],
        "technology": [
            "Use current technology terminology",
            "Include appropriate technical questions",
            "Consider user experience factors",
            "Include adoption and usage questions",
            "Use appropriate demographic questions",
            "Consider privacy and security concerns",
            "Include innovation and future trends questions"
        ]
    }
}

# New pillar-based rules
PILLAR_RULES = {
    "content_validity": [
        "Survey questions must directly address all stated research objectives from the RFQ",
        "Each key research area mentioned in the RFQ should have corresponding questions",
        "Question coverage should be comprehensive without significant gaps in topic areas",
        "Survey scope should align with the research goals and target audience specified",
        "Questions should demonstrate clear mapping to business objectives or research hypotheses"
    ],
    "methodological_rigor": [
        "Questions must follow logical sequence from general to specific",
        "Avoid leading, loaded, or double-barreled questions that introduce bias",
        "Screening questions should appear early in the survey flow",
        "Sensitive or personal questions should be placed toward the end",
        "Question types must be appropriate for the methodology being implemented",
        "Sample size and targeting must align with statistical requirements",
        "Include proper randomization and bias mitigation techniques where applicable"
    ],
    "clarity_comprehensibility": [
        "Use clear, simple language appropriate for the target audience",
        "Avoid jargon, technical terms, and industry-specific language unless necessary",
        "Each question should focus on a single concept or idea",
        "Question wording should be neutral and unambiguous",
        "Instructions and context should be clear and easy to understand",
        "Reading level should be appropriate for the target demographic",
        "Use inclusive language that avoids cultural bias or assumptions"
    ],
    "structural_coherence": [
        "Survey sections should follow logical progression and organization",
        "Related questions should be grouped together appropriately",
        "Question types should be varied and engaging throughout the survey",
        "Response scales should be consistent within question groups",
        "Skip logic and branching should be clear and purposeful",
        "Question order should minimize response bias and priming effects",
        "Overall survey structure should support the research methodology"
    ],
    "deployment_readiness": [
        "Survey length should be appropriate for the target audience (typically 10-25 minutes)",
        "Question count should balance comprehensiveness with respondent fatigue",
        "Target sample size should be realistic and achievable for the audience",
        "Survey complexity should match the incentive and value proposition",
        "Technical requirements should be feasible for the deployment platform",
        "Compliance and privacy requirements should be addressed",
        "Survey should be optimized for the primary response channel (web, mobile, phone)"
    ]
}

def analyze_rule_overlap():
    """Analyze overlap between existing rules and new pillar rules"""
    print("🔍 RULES REDUNDANCY ANALYSIS")
    print("=" * 60)
    
    overlaps = []
    
    # Check Quality rules vs Pillar rules
    print("\n📊 QUALITY RULES vs PILLAR RULES")
    print("-" * 40)
    
    # Question Quality overlaps
    question_quality_rules = EXISTING_RULES["quality"]["question_quality"]
    
    for existing_rule in question_quality_rules:
        for pillar_name, pillar_rules in PILLAR_RULES.items():
            for pillar_rule in pillar_rules:
                if check_semantic_overlap(existing_rule, pillar_rule):
                    overlaps.append({
                        "existing_type": "quality/question_quality",
                        "existing_rule": existing_rule,
                        "pillar": pillar_name,
                        "pillar_rule": pillar_rule,
                        "overlap_level": "high"
                    })
                    print(f"🔄 OVERLAP FOUND:")
                    print(f"   Quality: {existing_rule}")
                    print(f"   {pillar_name}: {pillar_rule}")
                    print()
    
    # Survey Structure overlaps  
    structure_rules = EXISTING_RULES["quality"]["survey_structure"]
    
    for existing_rule in structure_rules:
        for pillar_name, pillar_rules in PILLAR_RULES.items():
            for pillar_rule in pillar_rules:
                if check_semantic_overlap(existing_rule, pillar_rule):
                    overlaps.append({
                        "existing_type": "quality/survey_structure", 
                        "existing_rule": existing_rule,
                        "pillar": pillar_name,
                        "pillar_rule": pillar_rule,
                        "overlap_level": "high"
                    })
                    print(f"🔄 OVERLAP FOUND:")
                    print(f"   Structure: {existing_rule}")
                    print(f"   {pillar_name}: {pillar_rule}")
                    print()
    
    # Respondent Experience overlaps
    experience_rules = EXISTING_RULES["quality"]["respondent_experience"]
    
    for existing_rule in experience_rules:
        for pillar_name, pillar_rules in PILLAR_RULES.items():
            for pillar_rule in pillar_rules:
                if check_semantic_overlap(existing_rule, pillar_rule):
                    overlaps.append({
                        "existing_type": "quality/respondent_experience",
                        "existing_rule": existing_rule, 
                        "pillar": pillar_name,
                        "pillar_rule": pillar_rule,
                        "overlap_level": "medium"
                    })
                    print(f"🔄 OVERLAP FOUND:")
                    print(f"   Experience: {existing_rule}")
                    print(f"   {pillar_name}: {pillar_rule}")
                    print()
    
    return overlaps

def check_semantic_overlap(rule1, rule2):
    """Check if two rules have semantic overlap"""
    # Convert to lowercase for comparison
    r1 = rule1.lower()
    r2 = rule2.lower()
    
    # Key phrase matching
    overlap_indicators = [
        # Question quality indicators
        ("clear", "clear"), ("concise", "simple"), ("unambiguous", "neutral"),
        ("avoid leading", "avoid leading"), ("double-barreled", "single concept"),
        ("jargon", "jargon"), ("technical terms", "technical"),
        
        # Structure indicators
        ("screening questions", "screening"), ("logical", "logical"),
        ("sensitive questions", "sensitive"), ("end", "end"),
        ("group", "group"), ("progress indicators", "progress"),
        
        # Experience indicators  
        ("survey length", "survey length"), ("appropriate", "appropriate"),
        ("instructions", "instructions"), ("mobile-friendly", "mobile"),
        
        # Bias indicators
        ("bias", "bias"), ("randomization", "randomization"),
        
        # Flow indicators
        ("sequence", "sequence"), ("flow", "flow"), ("order", "order")
    ]
    
    for indicator1, indicator2 in overlap_indicators:
        if indicator1 in r1 and indicator2 in r2:
            return True
        if indicator2 in r1 and indicator1 in r2:
            return True
    
    # Direct substring matching for high confidence
    if len(r1) > 20 and len(r2) > 20:
        words1 = set(r1.split())
        words2 = set(r2.split())
        common_words = words1 & words2
        if len(common_words) >= 3:
            return True
    
    return False

def generate_consolidation_recommendations(overlaps):
    """Generate recommendations for consolidating redundant rules"""
    print("\n💡 CONSOLIDATION RECOMMENDATIONS")
    print("=" * 50)
    
    # Group overlaps by pillar
    pillar_overlaps = {}
    for overlap in overlaps:
        pillar = overlap["pillar"]
        if pillar not in pillar_overlaps:
            pillar_overlaps[pillar] = []
        pillar_overlaps[pillar].append(overlap)
    
    recommendations = []
    
    for pillar, pillar_overlap_list in pillar_overlaps.items():
        print(f"\n🏛️  {pillar.upper().replace('_', ' ')} PILLAR")
        print("-" * 30)
        
        existing_types = set(o["existing_type"] for o in pillar_overlap_list)
        
        if len(pillar_overlap_list) >= 3:
            print(f"❌ HIGH REDUNDANCY: {len(pillar_overlap_list)} overlaps with existing rules")
            print("   RECOMMENDATION: Consolidate existing quality rules into this pillar")
            recommendations.append({
                "action": "consolidate",
                "pillar": pillar,
                "redundant_rules": len(pillar_overlap_list),
                "affected_types": list(existing_types)
            })
        elif len(pillar_overlap_list) >= 1:
            print(f"⚠️  MODERATE REDUNDANCY: {len(pillar_overlap_list)} overlaps")
            print("   RECOMMENDATION: Review and merge similar rules")
            recommendations.append({
                "action": "review_merge", 
                "pillar": pillar,
                "redundant_rules": len(pillar_overlap_list),
                "affected_types": list(existing_types)
            })
        else:
            print(f"✅ LOW REDUNDANCY: Pillar rules are mostly unique")
    
    return recommendations

def analyze_methodology_rules():
    """Analyze methodology rules for redundancy"""
    print(f"\n🔬 METHODOLOGY RULES ANALYSIS")
    print("-" * 40)
    
    methodology_rules = EXISTING_RULES["methodology"]
    
    print("📋 Current Methodology Rules:")
    for method_name, method_data in methodology_rules.items():
        val_rules = len(method_data.get("validation_rules", []))
        best_practices = len(method_data.get("best_practices", []))
        print(f"   • {method_name}: {val_rules} validation rules, {best_practices} best practices")
    
    print("\n💭 ASSESSMENT:")
    print("   ✅ Methodology rules are COMPLEMENTARY to pillar rules")
    print("   ✅ They provide specific implementation details")
    print("   ✅ Pillar rules provide high-level evaluation criteria")
    print("   ✅ NO REDUNDANCY - Keep both systems")
    
    return "keep_both"

def analyze_industry_rules():
    """Analyze industry rules for redundancy"""
    print(f"\n🏢 INDUSTRY RULES ANALYSIS") 
    print("-" * 40)
    
    industry_rules = EXISTING_RULES["industry"]
    
    print("📋 Current Industry Rules:")
    for industry, rules in industry_rules.items():
        print(f"   • {industry}: {len(rules)} specialized rules")
    
    print("\n💭 ASSESSMENT:")
    print("   ✅ Industry rules are DOMAIN-SPECIFIC")
    print("   ✅ They provide compliance and terminology guidance")
    print("   ✅ Pillar rules are domain-agnostic quality criteria")
    print("   ✅ NO REDUNDANCY - Keep both systems")
    
    return "keep_both"

def main():
    """Run complete redundancy analysis"""
    
    # Analyze overlaps
    overlaps = analyze_rule_overlap()
    
    # Analyze methodology rules
    methodology_assessment = analyze_methodology_rules()
    
    # Industry rules analysis  
    industry_assessment = analyze_industry_rules()
    
    # Generate recommendations
    recommendations = generate_consolidation_recommendations(overlaps)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"\n🔢 STATISTICS:")
    print(f"   Total overlaps found: {len(overlaps)}")
    print(f"   Pillars with redundancy: {len(set(o['pillar'] for o in overlaps))}")
    print(f"   Methodology rules status: {methodology_assessment}")
    print(f"   Industry rules status: {industry_assessment}")
    
    print(f"\n🎯 OVERALL RECOMMENDATION:")
    if len(overlaps) >= 10:
        print("   ⚠️  SIGNIFICANT REDUNDANCY DETECTED")
        print("   🔧 Action Required: Consolidate quality rules into pillar system")
        print("   📈 Benefit: Simplified rule management, clearer evaluation criteria")
        print("   🗂️  Keep: Methodology rules (complementary)")
        print("   🗂️  Keep: Industry rules (domain-specific)")
    elif len(overlaps) >= 5:
        print("   ⚠️  MODERATE REDUNDANCY DETECTED") 
        print("   🔧 Action Recommended: Review and merge overlapping rules")
        print("   📈 Benefit: Reduced complexity, better organization")
    else:
        print("   ✅ LOW REDUNDANCY - Current system is well-organized")
        print("   🔧 Action: Keep both systems, they serve different purposes")
    
    return {
        "overlaps": overlaps,
        "recommendations": recommendations,
        "methodology_status": methodology_assessment,
        "industry_status": industry_assessment
    }

if __name__ == "__main__":
    analysis_result = main()