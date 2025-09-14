#!/usr/bin/env python3
"""
Seed State-of-the-Art Default Pillar Rules
Seeds comprehensive, research-backed evaluation criteria for all 5 pillars
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from database import get_db, engine
from database.models import SurveyRule
from sqlalchemy import func

def cleanup_existing_duplicates(db: Session):
    """Remove duplicate pillar rules based on rule_description and category"""
    
    try:
        # Find duplicates by rule_description and category
        duplicates_query = db.query(
            SurveyRule.rule_description,
            SurveyRule.category,
            func.count(SurveyRule.id).label('count'),
            func.array_agg(SurveyRule.id).label('rule_ids')
        ).filter(
            SurveyRule.rule_type == 'pillar',
            SurveyRule.is_active == True
        ).group_by(
            SurveyRule.rule_description,
            SurveyRule.category
        ).having(
            func.count(SurveyRule.id) > 1
        )
        
        duplicates = duplicates_query.all()
        
        if not duplicates:
            print("  ✅ No duplicate pillar rules found")
            return
        
        print(f"  🔍 Found {len(duplicates)} sets of duplicate rules")
        
        total_removed = 0
        
        for duplicate in duplicates:
            rule_description = duplicate.rule_description
            category = duplicate.category
            count = duplicate.count
            rule_ids = duplicate.rule_ids
            
            print(f"    📋 Processing duplicates for '{rule_description[:50]}...' in {category} ({count} copies)")
            
            # Keep the first rule (oldest by created_at) and remove the rest
            rules_to_check = db.query(SurveyRule).filter(
                SurveyRule.id.in_(rule_ids)
            ).order_by(SurveyRule.created_at.asc()).all()
            
            if len(rules_to_check) > 1:
                # Keep the first one, remove the rest
                rule_to_keep = rules_to_check[0]
                rules_to_remove = rules_to_check[1:]
                
                print(f"      ✅ Keeping rule ID {rule_to_keep.id} (created: {rule_to_keep.created_at})")
                
                for rule in rules_to_remove:
                    print(f"      🗑️  Removing duplicate rule ID {rule.id} (created: {rule.created_at})")
                    db.delete(rule)
                    total_removed += 1
        
        if total_removed > 0:
            db.commit()
            print(f"  🗑️  Removed {total_removed} duplicate rules")
        else:
            print("  ✅ No duplicates to remove")
            
    except Exception as e:
        print(f"  ❌ Error during cleanup: {e}")
        db.rollback()
        raise

def seed_pillar_rules():
    """Seed comprehensive pillar rules with state-of-the-art evaluation criteria"""
    
    # Create database session
    db: Session = next(get_db())
    
    try:
        # First, clean up any existing duplicates
        print("🧹 [Seed] Cleaning up existing duplicate pillar rules...")
        cleanup_existing_duplicates(db)
        
        # State-of-the-art pillar rules based on survey methodology research
        pillar_rules = [
            # ========== CONTENT VALIDITY (20%) ==========
            {
                'rule_type': 'pillar',
                'category': 'content_validity',
                'rule_name': 'Research Objective Alignment',
                'rule_description': 'Every survey question must directly address at least one stated research objective with clear traceability',
                'priority': 'critical',
                'rule_content': {
                    'evaluation_criteria': [
                        'Each question maps to specific research objectives',
                        'No research objective is left unaddressed',
                        'Question wording reflects the intended construct measurement',
                        'Question scope matches the depth required for each objective'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'construct_validity'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'content_validity',
                'rule_name': 'Comprehensive Coverage Assessment',
                'rule_description': 'Survey must comprehensively cover all key aspects of the research domain without significant gaps',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'All major topic areas within scope are addressed',
                        'Breadth of coverage matches research complexity',
                        'No critical knowledge gaps exist',
                        'Coverage depth is appropriate for research goals'
                    ],
                    'weight_factor': 0.30,
                    'pillar_focus': 'domain_coverage'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'content_validity',
                'rule_name': 'Business Objective Translation',
                'rule_description': 'Survey questions effectively translate business objectives into measurable research constructs',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Business goals are operationalized into measurable variables',
                        'Questions provide actionable insights for business decisions',
                        'Measurement approach matches business context',
                        'Results will directly inform business strategy'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'business_relevance'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'content_validity',
                'rule_name': 'Construct Measurement Validity',
                'rule_description': 'Questions accurately measure intended psychological, behavioral, or attitudinal constructs',
                'priority': 'critical',
                'rule_content': {
                    'evaluation_criteria': [
                        'Questions measure what they claim to measure',
                        'Construct definitions are operationally clear',
                        'Multiple indicators used for complex constructs',
                        'Face validity is evident to domain experts'
                    ],
                    'weight_factor': 0.20,
                    'pillar_focus': 'construct_measurement'
                }
            },

            # ========== METHODOLOGICAL RIGOR (25%) ==========
            {
                'rule_type': 'pillar',
                'category': 'methodological_rigor',
                'rule_name': 'Bias Prevention and Detection',
                'rule_description': 'Survey design systematically prevents and detects response bias, social desirability bias, and acquiescence bias',
                'priority': 'critical',
                'rule_content': {
                    'evaluation_criteria': [
                        'Questions avoid leading or loaded language',
                        'Response options are balanced and neutral',
                        'Social desirability bias is minimized through design',
                        'Acquiescence bias controls are implemented',
                        'Question order effects are mitigated'
                    ],
                    'weight_factor': 0.30,
                    'pillar_focus': 'bias_control'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'methodological_rigor',
                'rule_name': 'Optimal Question Sequencing',
                'rule_description': 'Questions follow psychologically optimal sequence from general to specific, with proper warm-up and sensitive question placement',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Funnel approach: general to specific questions',
                        'Screening questions placed early and efficiently',
                        'Sensitive questions positioned appropriately (typically later)',
                        'Question context effects are considered and controlled',
                        'Logical flow maintains respondent engagement'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'question_flow'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'methodological_rigor',
                'rule_name': 'Sampling Methodology Alignment',
                'rule_description': 'Survey design aligns with intended sampling strategy and supports statistical inference requirements',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Question design supports planned analysis methods',
                        'Sample size requirements are achievable',
                        'Stratification variables are captured if needed',
                        'Demographic questions support representativeness checks',
                        'Missing data patterns are anticipated and addressed'
                    ],
                    'weight_factor': 0.20,
                    'pillar_focus': 'sampling_support'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'methodological_rigor',
                'rule_name': 'Research Design Integration',
                'rule_description': 'Survey integrates seamlessly with overall research design (experimental, correlational, longitudinal, etc.)',
                'priority': 'medium',
                'rule_content': {
                    'evaluation_criteria': [
                        'Question types match research design requirements',
                        'Measurement scales support planned statistical analyses',
                        'Temporal considerations are properly addressed',
                        'Control variables are appropriately included',
                        'Design supports causal inference goals (if applicable)'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'design_integration'
                }
            },

            # ========== CLARITY & COMPREHENSIBILITY (25%) ==========
            {
                'rule_type': 'pillar',
                'category': 'clarity_comprehensibility',
                'rule_name': 'Audience-Appropriate Language',
                'rule_description': 'Language complexity, vocabulary, and reading level are optimized for the target audience demographic',
                'priority': 'critical',
                'rule_content': {
                    'evaluation_criteria': [
                        'Reading level matches target audience education',
                        'Technical jargon is avoided or clearly defined',
                        'Cultural and linguistic appropriateness is ensured',
                        'Sentence structure is clear and concise',
                        'Instructions are written in plain language'
                    ],
                    'weight_factor': 0.30,
                    'pillar_focus': 'language_accessibility'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'clarity_comprehensibility',
                'rule_name': 'Cognitive Load Optimization',
                'rule_description': 'Questions minimize cognitive burden and mental processing demands on respondents',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Each question addresses a single concept',
                        'Double-barreled questions are eliminated',
                        'Response tasks are intuitive and straightforward',
                        'Memory demands are minimized',
                        'Complex concepts are broken into digestible parts'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'cognitive_simplicity'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'clarity_comprehensibility',
                'rule_name': 'Unambiguous Question Construction',
                'rule_description': 'Question wording eliminates ambiguity and ensures consistent interpretation across respondents',
                'priority': 'critical',
                'rule_content': {
                    'evaluation_criteria': [
                        'Questions have single, clear meaning',
                        'Ambiguous terms are defined or avoided',
                        'Response options are mutually exclusive',
                        'Time frames and contexts are clearly specified',
                        'Hypothetical scenarios are realistic and concrete'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'semantic_clarity'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'clarity_comprehensibility',
                'rule_name': 'Response Interface Clarity',
                'rule_description': 'Response mechanisms (scales, options, input methods) are intuitive and error-resistant',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Response formats match question content naturally',
                        'Scale anchors are meaningful and well-defined',
                        'Instructions for complex responses are clear',
                        'Error prevention is built into response design',
                        'Visual hierarchy guides respondent attention'
                    ],
                    'weight_factor': 0.20,
                    'pillar_focus': 'interface_usability'
                }
            },

            # ========== STRUCTURAL COHERENCE (20%) ==========
            {
                'rule_type': 'pillar',
                'category': 'structural_coherence',
                'rule_name': 'Logical Section Architecture',
                'rule_description': 'Survey sections follow logical thematic progression with clear transitions and purposeful organization',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Sections represent coherent thematic blocks',
                        'Section transitions are smooth and logical',
                        'Related questions are grouped appropriately',
                        'Section order follows natural thought progression',
                        'Each section has clear purpose in overall design'
                    ],
                    'weight_factor': 0.30,
                    'pillar_focus': 'thematic_organization'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'structural_coherence',
                'rule_name': 'Response Scale Consistency',
                'rule_description': 'Response scales are consistent within question groups and optimize respondent cognitive processing',
                'priority': 'medium',
                'rule_content': {
                    'evaluation_criteria': [
                        'Similar constructs use consistent scaling',
                        'Scale direction is maintained within sections',
                        'Scale complexity progresses appropriately',
                        'Mixed scales are used strategically, not randomly',
                        'Scale anchors maintain semantic consistency'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'scale_harmony'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'structural_coherence',
                'rule_name': 'Strategic Question Type Variation',
                'rule_description': 'Question formats are varied strategically to maintain engagement while supporting measurement goals',
                'priority': 'medium',
                'rule_content': {
                    'evaluation_criteria': [
                        'Question types are varied to prevent monotony',
                        'Format changes serve measurement purposes',
                        'Cognitive demands are distributed across survey',
                        'Interactive elements enhance rather than complicate',
                        'Variety maintains rather than breaks survey flow'
                    ],
                    'weight_factor': 0.20,
                    'pillar_focus': 'format_diversity'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'structural_coherence',
                'rule_name': 'Intelligent Skip Logic Design',
                'rule_description': 'Skip logic is purposeful, efficient, and creates personalized survey paths without confusion',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Skip patterns are logically necessary, not arbitrary',
                        'Branching reduces irrelevant questions effectively',
                        'Logic paths are tested for all scenarios',
                        'Complex routing is invisible to respondents',
                        'Skip logic supports rather than complicates analysis'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'adaptive_routing'
                }
            },

            # ========== DEPLOYMENT READINESS (10%) ==========
            {
                'rule_type': 'pillar',
                'category': 'deployment_readiness',
                'rule_name': 'Optimized Survey Length',
                'rule_description': 'Survey length is optimized for target audience attention span and completion rates while maintaining research integrity',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Length matches audience tolerance and context',
                        'Question count balances comprehensiveness with completion',
                        'Time estimates are realistic and tested',
                        'Critical questions are prioritized early',
                        'Optional sections are used strategically'
                    ],
                    'weight_factor': 0.30,
                    'pillar_focus': 'length_optimization'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'deployment_readiness',
                'rule_name': 'Multi-Channel Compatibility',
                'rule_description': 'Survey is optimized for intended deployment channels (mobile, web, phone, in-person) with consistent experience',
                'priority': 'high',
                'rule_content': {
                    'evaluation_criteria': [
                        'Design works effectively on primary deployment channel',
                        'Mobile compatibility is ensured for mobile-first audiences',
                        'Visual elements scale appropriately across devices',
                        'Input methods are suitable for channel constraints',
                        'Accessibility standards are met for all channels'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'channel_optimization'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'deployment_readiness',
                'rule_name': 'Realistic Implementation Requirements',
                'rule_description': 'Technical and operational requirements are feasible within project constraints and organizational capabilities',
                'priority': 'medium',
                'rule_content': {
                    'evaluation_criteria': [
                        'Technical requirements match available resources',
                        'Data collection timeline is achievable',
                        'Sample size targets are realistic for population',
                        'Response rate expectations align with methodology',
                        'Analysis requirements are supported by data structure'
                    ],
                    'weight_factor': 0.25,
                    'pillar_focus': 'feasibility_assessment'
                }
            },
            {
                'rule_type': 'pillar',
                'category': 'deployment_readiness',
                'rule_name': 'Quality Assurance Framework',
                'rule_description': 'Survey includes built-in quality checks, validation mechanisms, and error prevention features',
                'priority': 'medium',
                'rule_content': {
                    'evaluation_criteria': [
                        'Data validation prevents obvious errors',
                        'Attention checks are strategically placed',
                        'Response pattern analysis is enabled',
                        'Open-ended responses have quality indicators',
                        'Real-time data monitoring is supported'
                    ],
                    'weight_factor': 0.20,
                    'pillar_focus': 'quality_control'
                }
            }
        ]
        
        # Check if ANY pillar rules already exist
        # Check for existing pillar rules and handle duplicates
        existing_pillar_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == 'pillar',
            SurveyRule.is_active == True
        ).all()
        
        # If rules already exist, perform deduplication first
        if existing_pillar_rules:
            print(f"⚠️  Found {len(existing_pillar_rules)} existing pillar rules")
            print("🔄 Performing deduplication of existing rules...")
            
            # Track unique rules by rule description
            seen_rules = {}
            duplicates_to_remove = []
            
            for rule in existing_pillar_rules:
                rule_key = (rule.category, rule.rule_description.strip())
                
                if rule_key in seen_rules:
                    # This is a duplicate - mark for removal
                    duplicates_to_remove.append(rule.id)
                    print(f"  📍 Found duplicate: {rule.category} - {rule.rule_description[:50]}...")
                else:
                    # Keep this rule (first occurrence)
                    seen_rules[rule_key] = rule.id
            
            # Remove duplicates
            if duplicates_to_remove:
                for rule_id in duplicates_to_remove:
                    db.query(SurveyRule).filter(
                        SurveyRule.id == rule_id
                    ).update({"is_active": False})
                    
                db.commit()
                print(f"✅ Removed {len(duplicates_to_remove)} duplicate rules")
            else:
                print("✅ No duplicates found")
            
            # Count remaining active rules
            remaining_count = db.query(SurveyRule).filter(
                SurveyRule.rule_type == 'pillar',
                SurveyRule.is_active == True
            ).count()
            
            # If we have a reasonable number of rules (15-25), skip seeding
            if remaining_count >= 15:
                print(f"✅ {remaining_count} unique pillar rules exist - skipping seeding")
                return
            else:
                print(f"ℹ️  Only {remaining_count} pillar rules found - proceeding with seeding missing rules")
        
        print(f"🌟 Seeding {len(pillar_rules)} state-of-the-art pillar rules...")
        if not existing_pillar_rules:
            print("ℹ️  No existing pillar rules found - proceeding with initial seeding")
        
        # Insert new pillar rules - only run if no pillar rules exist at all
        rules_created = 0
        
        for rule_data in pillar_rules:
            # Convert priority string to integer
            priority_map = {"critical": 10, "high": 8, "medium": 5, "low": 2}
            priority_value = priority_map.get(rule_data['priority'], 5)
            
            # Check if rule already exists (avoid creating duplicates during seeding)
            existing_rule = db.query(SurveyRule).filter(
                SurveyRule.rule_type == rule_data['rule_type'],
                SurveyRule.category == rule_data['category'],
                SurveyRule.rule_description == rule_data['rule_description'],
                SurveyRule.is_active == True
            ).first()
            
            if existing_rule:
                print(f"  ⚠️  Skipping duplicate: {rule_data['category']} - {rule_data['rule_name']}")
                continue
            
            rule = SurveyRule(
                rule_type=rule_data['rule_type'],
                category=rule_data['category'],
                rule_name=rule_data['rule_name'],
                rule_description=rule_data['rule_description'],
                rule_content=rule_data['rule_content'],
                priority=priority_value,
                is_active=True,
                created_by='system_seed'
            )
            
            db.add(rule)
            rules_created += 1
            
            pillar_name = rule_data['category'].replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility')
            print(f"  ✅ {pillar_name}: {rule_data['rule_name']} ({rule_data['priority']})")
        
        # Commit all changes
        db.commit()
        
        print(f"\n🎉 Successfully seeded {rules_created} pillar rules!")
        print("✅ Initial pillar rules setup complete")
        
        # Display summary by pillar
        pillar_summary = {}
        for rule_data in pillar_rules:
            pillar = rule_data['category']
            if pillar not in pillar_summary:
                pillar_summary[pillar] = {'count': 0, 'priorities': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}}
            pillar_summary[pillar]['count'] += 1
            pillar_summary[pillar]['priorities'][rule_data['priority']] += 1
        
        print(f"\n📊 PILLAR SUMMARY:")
        for pillar, data in pillar_summary.items():
            pillar_name = pillar.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility')
            priorities_str = f"🔴{data['priorities']['critical']} 🟡{data['priorities']['high']} 🔵{data['priorities']['medium']} ⚪{data['priorities']['low']}"
            print(f"   🏛️  {pillar_name}: {data['count']} rules ({priorities_str})")
        
        print(f"\n🔍 Next steps:")
        print(f"   1. Rules are now available in the pillar evaluation system")
        print(f"   2. Test with: python3 evaluations/consolidated_rules_integration.py")
        print(f"   3. View in UI: Navigate to Rules → 5-Pillar Evaluation Rules")
        print(f"   4. Run evaluations: python3 evaluations/evaluation_runner.py")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding pillar rules: {e}")
        raise
    finally:
        db.close()

def verify_pillar_rules():
    """Verify the seeded pillar rules"""
    db: Session = next(get_db())
    
    try:
        from sqlalchemy import text
        
        # Get pillar rule summary
        query = text("""
        SELECT 
            category,
            priority,
            COUNT(*) as count
        FROM survey_rules 
        WHERE rule_type = 'pillar' 
        AND is_active = true 
        AND created_by = 'system_seed'
        GROUP BY category, priority
        ORDER BY category, 
            CASE priority 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                WHEN 'low' THEN 4 
            END
        """)
        
        results = db.execute(query).fetchall()
        
        if not results:
            print("❌ No seeded pillar rules found")
            return
        
        print("🔍 PILLAR RULES VERIFICATION:")
        current_pillar = None
        for row in results:
            pillar_name = row.category.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility')
            if current_pillar != row.category:
                print(f"\n🏛️  {pillar_name}:")
                current_pillar = row.category
            
            priority_icon = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '⚪'}[row.priority]
            print(f"     {priority_icon} {row.priority.title()}: {row.count} rules")
        
        # Get total count
        total_query = text("""
        SELECT COUNT(*) as total 
        FROM survey_rules 
        WHERE rule_type = 'pillar' 
        AND is_active = true 
        AND created_by = 'system_seed'
        """)
        
        total_result = db.execute(total_query).fetchone()
        print(f"\n📊 Total seeded pillar rules: {total_result.total}")
        
    except Exception as e:
        print(f"❌ Error verifying pillar rules: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed state-of-the-art pillar rules')
    parser.add_argument('--verify', action='store_true', help='Verify existing pillar rules instead of seeding')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_pillar_rules()
    else:
        seed_pillar_rules()