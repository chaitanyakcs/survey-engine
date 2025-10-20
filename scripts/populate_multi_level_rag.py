#!/usr/bin/env python3
"""
Populate Multi-Level RAG Tables

This script extracts sections and questions from existing golden pairs
and populates the golden_sections and golden_questions tables for
multi-level retrieval.
"""

import asyncio
import logging
from typing import Dict, Any
from src.database.connection import SessionLocal
from src.database.models import GoldenRFQSurveyPair
from src.services.multi_level_rag_service import MultiLevelRAGService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def populate_multi_level_rag(dry_run: bool = False) -> Dict[str, Any]:
    """
    Populate golden sections and questions from existing golden pairs
    
    Args:
        dry_run: If True, only report what would be created without creating
    
    Returns:
        Dict with statistics about the population operation
    """
    logger.info("🚀 [MultiLevelRAG] Starting multi-level RAG population")
    logger.info(f"🔍 [MultiLevelRAG] Dry run mode: {dry_run}")
    
    db = SessionLocal()
    stats = {
        'golden_pairs_processed': 0,
        'sections_created': 0,
        'questions_created': 0,
        'errors': [],
        'processed_pairs': []
    }
    
    try:
        # Get all golden pairs
        golden_pairs = db.query(GoldenRFQSurveyPair).all()
        logger.info(f"📊 [MultiLevelRAG] Found {len(golden_pairs)} golden pairs to process")
        
        if dry_run:
            logger.info("🔍 [MultiLevelRAG] DRY RUN - Analyzing golden pairs...")
            for pair in golden_pairs:
                survey_json = pair.survey_json
                if survey_json and 'sections' in survey_json:
                    sections_count = len(survey_json['sections'])
                    questions_count = sum(len(section.get('questions', [])) for section in survey_json['sections'])
                    logger.info(f"  - {pair.title}: {sections_count} sections, {questions_count} questions")
                    stats['sections_created'] += sections_count
                    stats['questions_created'] += questions_count
                    stats['golden_pairs_processed'] += 1
        else:
            # Process each golden pair
            rag_service = MultiLevelRAGService(db)
            
            for i, pair in enumerate(golden_pairs, 1):
                try:
                    logger.info(f"📝 [MultiLevelRAG] Processing golden pair {i}/{len(golden_pairs)}: {pair.title}")
                    
                    result = await rag_service.extract_and_index_sections_questions(str(pair.id))
                    
                    stats['golden_pairs_processed'] += 1
                    stats['sections_created'] += result['sections_created']
                    stats['questions_created'] += result['questions_created']
                    
                    stats['processed_pairs'].append({
                        'golden_pair_id': str(pair.id),
                        'title': pair.title,
                        'sections_created': result['sections_created'],
                        'questions_created': result['questions_created']
                    })
                    
                    logger.info(f"✅ [MultiLevelRAG] Created {result['sections_created']} sections and {result['questions_created']} questions")
                    
                except Exception as e:
                    logger.error(f"❌ [MultiLevelRAG] Error processing golden pair {pair.id}: {str(e)}")
                    stats['errors'].append({
                        'golden_pair_id': str(pair.id),
                        'title': pair.title,
                        'error': str(e)
                    })
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 [MultiLevelRAG] Final Summary:")
        logger.info(f"{'='*60}")
        logger.info(f"Golden pairs processed: {stats['golden_pairs_processed']}")
        logger.info(f"Sections created: {stats['sections_created']}")
        logger.info(f"Questions created: {stats['questions_created']}")
        logger.info(f"Errors encountered: {len(stats['errors'])}")
        
        if stats['processed_pairs']:
            logger.info(f"\n📋 [MultiLevelRAG] Processed Golden Pairs:")
            for pair in stats['processed_pairs']:
                logger.info(f"  - {pair['title']}: {pair['sections_created']} sections, {pair['questions_created']} questions")
        
        if stats['errors']:
            logger.info(f"\n❌ [MultiLevelRAG] Errors:")
            for error in stats['errors']:
                logger.info(f"  - {error['title']}: {error['error']}")
        
        logger.info(f"{'='*60}\n")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ [MultiLevelRAG] Fatal error: {str(e)}", exc_info=True)
        stats['errors'].append({
            'golden_pair_id': 'GLOBAL',
            'title': 'GLOBAL',
            'error': f"Fatal error: {str(e)}"
        })
        raise
    finally:
        db.close()


async def main():
    """Main entry point for multi-level RAG population script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate multi-level RAG tables')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes made)'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Multi-Level RAG Population")
    logger.info(f"Configuration:")
    logger.info(f"  - Dry run: {args.dry_run}")
    
    stats = await populate_multi_level_rag(dry_run=args.dry_run)
    
    # Write stats to file
    import json
    output_file = 'multi_level_rag_stats.json'
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    logger.info(f"📄 Stats written to {output_file}")
    
    if stats['sections_created'] > 0 or stats['questions_created'] > 0:
        logger.info(f"\n✅ Multi-level RAG population completed successfully!")
        logger.info(f"   {stats['sections_created']} sections created")
        logger.info(f"   {stats['questions_created']} questions created")
        logger.info(f"   Multi-level retrieval is now available!")
    else:
        logger.warning(f"\n⚠️  No sections or questions created")
        if args.dry_run:
            logger.info(f"   This was a dry run - no changes were made")
        else:
            logger.info(f"   Check logs for errors")


if __name__ == "__main__":
    asyncio.run(main())
