#!/usr/bin/env python3
"""
Bootstrap Golden Pairs from Existing High-Quality Surveys

One-time migration script to convert existing surveys with pillar scores >= 0.5
into golden RFQ-survey pairs for retrieval.

Run once after deploying to production to give researchers immediate value.
"""

import asyncio
import logging
from typing import List, Set
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import Survey, RFQ, GoldenRFQSurveyPair
from src.services.golden_service import GoldenService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def extract_methodologies(survey_json: dict) -> List[str]:
    """Extract methodology tags from survey JSON"""
    methodologies = []
    
    # Check top-level methodology field
    if survey_json.get('methodology'):
        methodologies.append(survey_json['methodology'])
    
    # Extract from questions
    questions = survey_json.get('questions', [])
    for question in questions:
        if question.get('methodology'):
            method = question['methodology']
            if method not in methodologies:
                methodologies.append(method)
    
    # Normalize methodology names
    normalized = []
    for method in methodologies:
        method_lower = method.lower()
        if 'van westendorp' in method_lower or 'vw' == method_lower:
            normalized.append('van_westendorp')
        elif 'gabor' in method_lower or 'gg' in method_lower:
            normalized.append('gabor_granger')
        elif 'conjoint' in method_lower or 'cbc' in method_lower:
            normalized.append('conjoint')
        elif 'maxdiff' in method_lower:
            normalized.append('maxdiff')
        elif 'nps' in method_lower:
            normalized.append('nps')
        elif 'csat' in method_lower:
            normalized.append('csat')
        else:
            normalized.append(method_lower.replace(' ', '_'))
    
    return list(set(normalized))  # Remove duplicates


def get_existing_rfq_texts(db: Session) -> Set[str]:
    """Get set of existing RFQ texts to check for duplicates"""
    existing_pairs = db.query(GoldenRFQSurveyPair).all()
    return {pair.rfq_text.strip().lower() for pair in existing_pairs}


async def bootstrap_golden_pairs(
    min_quality_score: float = 0.5,
    dry_run: bool = False,
    production_mode: bool = False
) -> dict:
    """
    Bootstrap golden pairs from existing high-quality surveys
    
    Args:
        min_quality_score: Minimum pillar score threshold (default 0.5)
        dry_run: If True, only report what would be created without creating
    
    Returns:
        dict with statistics about the bootstrap operation
    """
    logger.info("🚀 [Bootstrap] Starting golden pairs bootstrap")
    logger.info(f"📊 [Bootstrap] Minimum quality score: {min_quality_score}")
    logger.info(f"🔍 [Bootstrap] Dry run mode: {dry_run}")
    logger.info(f"🏭 [Bootstrap] Production mode: {production_mode}")
    
    db = SessionLocal()
    stats = {
        'total_surveys_checked': 0,
        'surveys_above_threshold': 0,
        'surveys_with_rfq': 0,
        'duplicates_skipped': 0,
        'golden_pairs_created': 0,
        'errors': [],
        'created_pairs': [],
        'skipped': False,
        'existing_count': 0
    }
    
    try:
        # Get existing golden pairs for deduplication and production check
        existing_pairs = db.query(GoldenRFQSurveyPair).all()
        existing_count = len(existing_pairs)
        stats['existing_count'] = existing_count
        logger.info(f"📋 [Bootstrap] Found {existing_count} existing golden pairs")
        
        # Production mode: Skip if already has enough golden pairs
        if production_mode and existing_count >= 10:
            logger.info(f"✅ [Bootstrap] Production already has {existing_count} golden pairs (>= 10) - skipping bootstrap")
            stats['skipped'] = True
            return stats
        
        existing_rfq_texts = {pair.rfq_text.strip().lower() for pair in existing_pairs}
        
        # Get all surveys with pillar scores
        surveys = db.query(Survey).filter(
            Survey.pillar_scores.is_not(None)
        ).all()
        
        stats['total_surveys_checked'] = len(surveys)
        logger.info(f"📊 [Bootstrap] Checking {len(surveys)} surveys with pillar scores")
        
        # Process each survey
        for i, survey in enumerate(surveys, 1):
            try:
                # Extract weighted score
                pillar_scores = survey.pillar_scores
                if not isinstance(pillar_scores, dict):
                    logger.warning(f"⚠️ [Bootstrap] Survey {survey.id}: invalid pillar_scores format")
                    continue
                
                weighted_score = pillar_scores.get('weighted_score', 0)
                
                # Check quality threshold
                if weighted_score < min_quality_score:
                    continue
                
                stats['surveys_above_threshold'] += 1
                logger.info(f"✅ [Bootstrap] Survey {survey.id}: quality score {weighted_score:.2f}")
                
                # Get associated RFQ
                rfq = db.query(RFQ).filter(RFQ.id == survey.rfq_id).first()
                
                if not rfq:
                    logger.warning(f"⚠️ [Bootstrap] Survey {survey.id}: no associated RFQ found")
                    stats['errors'].append({
                        'survey_id': str(survey.id),
                        'error': 'No RFQ found'
                    })
                    continue
                
                if not survey.final_output:
                    logger.warning(f"⚠️ [Bootstrap] Survey {survey.id}: no final_output")
                    stats['errors'].append({
                        'survey_id': str(survey.id),
                        'error': 'No final_output'
                    })
                    continue
                
                stats['surveys_with_rfq'] += 1
                
                # Check for duplicates
                rfq_text_normalized = rfq.description.strip().lower()
                if rfq_text_normalized in existing_rfq_texts:
                    logger.info(f"⏭️  [Bootstrap] Survey {survey.id}: duplicate RFQ, skipping")
                    stats['duplicates_skipped'] += 1
                    continue
                
                # Extract metadata
                title = survey.final_output.get('title', f'Migrated Survey {i}')
                methodologies = extract_methodologies(survey.final_output)
                industry = rfq.product_category or 'general'
                research_goal = rfq.research_goal or 'market_research'
                
                logger.info(f"📝 [Bootstrap] Survey {survey.id}:")
                logger.info(f"   Title: {title}")
                logger.info(f"   Methodologies: {methodologies}")
                logger.info(f"   Industry: {industry}")
                logger.info(f"   Quality: {weighted_score:.2f}")
                
                if dry_run:
                    logger.info(f"🔍 [Bootstrap] DRY RUN: Would create golden pair")
                    stats['created_pairs'].append({
                        'survey_id': str(survey.id),
                        'title': title,
                        'quality_score': weighted_score,
                        'methodologies': methodologies
                    })
                    continue
                
                # Create golden pair
                logger.info(f"💾 [Bootstrap] Creating golden pair for survey {survey.id}")
                
                golden_service = GoldenService(db)
                golden_pair = await golden_service.create_golden_pair(
                    rfq_text=rfq.description,
                    survey_json=survey.final_output,
                    title=title,
                    methodology_tags=methodologies if methodologies else None,
                    industry_category=industry,
                    research_goal=research_goal,
                    quality_score=float(weighted_score)
                )
                
                # Mark as auto-migrated (not human-verified)
                golden_pair.human_verified = False
                db.add(golden_pair)
                
                stats['golden_pairs_created'] += 1
                stats['created_pairs'].append({
                    'golden_pair_id': str(golden_pair.id),
                    'survey_id': str(survey.id),
                    'title': title,
                    'quality_score': weighted_score,
                    'methodologies': methodologies
                })
                
                # Add to existing set for deduplication
                existing_rfq_texts.add(rfq_text_normalized)
                
                logger.info(f"✅ [Bootstrap] Created golden pair {golden_pair.id}")
                
                # Rate limiting to avoid overloading embedding service
                await asyncio.sleep(0.5)
                
                # Progress reporting
                if i % 5 == 0:
                    logger.info(f"📊 [Bootstrap] Progress: {i}/{len(surveys)} surveys processed, {stats['golden_pairs_created']} golden pairs created")
                
            except Exception as e:
                logger.error(f"❌ [Bootstrap] Error processing survey {survey.id}: {str(e)}", exc_info=True)
                stats['errors'].append({
                    'survey_id': str(survey.id),
                    'error': str(e)
                })
        
        # Commit transaction
        if not dry_run:
            db.commit()
            logger.info(f"✅ [Bootstrap] Transaction committed successfully")
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 [Bootstrap] Final Summary:")
        logger.info(f"{'='*60}")
        logger.info(f"Total surveys checked: {stats['total_surveys_checked']}")
        logger.info(f"Surveys above threshold (>= {min_quality_score}): {stats['surveys_above_threshold']}")
        logger.info(f"Surveys with valid RFQ: {stats['surveys_with_rfq']}")
        logger.info(f"Duplicates skipped: {stats['duplicates_skipped']}")
        logger.info(f"Golden pairs created: {stats['golden_pairs_created']}")
        logger.info(f"Errors encountered: {len(stats['errors'])}")
        
        if stats['created_pairs']:
            logger.info(f"\n📋 [Bootstrap] Created Golden Pairs:")
            for pair in stats['created_pairs']:
                logger.info(f"  - {pair['title']} (score: {pair['quality_score']:.2f})")
        
        if stats['errors']:
            logger.info(f"\n❌ [Bootstrap] Errors:")
            for error in stats['errors']:
                logger.info(f"  - Survey {error['survey_id']}: {error['error']}")
        
        logger.info(f"{'='*60}\n")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ [Bootstrap] Fatal error: {str(e)}", exc_info=True)
        db.rollback()
        stats['errors'].append({
            'survey_id': 'GLOBAL',
            'error': f"Fatal error: {str(e)}"
        })
        raise
    finally:
        db.close()


async def main():
    """Main entry point for bootstrap script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bootstrap golden pairs from existing surveys')
    parser.add_argument(
        '--min-quality',
        type=float,
        default=0.5,
        help='Minimum quality score threshold (default: 0.5)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes made)'
    )
    parser.add_argument(
        '--production',
        action='store_true',
        help='Run in production mode (skip if already has 10+ golden pairs)'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Golden Pairs Bootstrap")
    logger.info(f"Configuration:")
    logger.info(f"  - Minimum quality score: {args.min_quality}")
    logger.info(f"  - Dry run: {args.dry_run}")
    logger.info(f"  - Production mode: {args.production}")
    
    stats = await bootstrap_golden_pairs(
        min_quality_score=args.min_quality,
        dry_run=args.dry_run,
        production_mode=args.production
    )
    
    # Write stats to file
    import json
    output_file = 'bootstrap_golden_pairs_stats.json'
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    logger.info(f"📄 Stats written to {output_file}")
    
    if stats.get('skipped', False):
        logger.info(f"\n✅ Bootstrap skipped - production already has {stats['existing_count']} golden pairs")
        logger.info(f"   No additional golden pairs needed")
    elif stats['golden_pairs_created'] > 0:
        logger.info(f"\n✅ Bootstrap completed successfully!")
        logger.info(f"   {stats['golden_pairs_created']} golden pairs created")
        logger.info(f"   Total golden pairs: {stats['existing_count'] + stats['golden_pairs_created']}")
    else:
        logger.warning(f"\n⚠️  No golden pairs created")
        if args.dry_run:
            logger.info(f"   This was a dry run - no changes were made")
        else:
            logger.info(f"   Check logs for errors or lower the quality threshold")


if __name__ == "__main__":
    asyncio.run(main())

