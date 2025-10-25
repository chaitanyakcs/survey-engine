#!/usr/bin/env python3
"""
Migration script to backfill annotations for all existing golden pairs.
Extracts embedded annotation fields from questions in survey_json and creates QuestionAnnotation records.
"""

import sys
import os
sys.path.append('src')

from database.connection import get_db
from database.models import GoldenRFQSurveyPair, QuestionAnnotation, Survey
from services.annotation_rag_sync_service import AnnotationRAGSyncService
import logging
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backfill_all_golden_pair_annotations():
    """Backfill annotations for all golden pairs that have embedded annotation data"""
    
    db = next(get_db())
    stats = {
        'total_golden_pairs': 0,
        'pairs_with_annotations': 0,
        'annotations_created': 0,
        'annotations_updated': 0,
        'annotations_synced': 0,
        'errors': [],
        'debug_info': []
    }
    
    try:
        # Get all golden pairs
        golden_pairs = db.query(GoldenRFQSurveyPair).all()
        stats['total_golden_pairs'] = len(golden_pairs)
        logger.info(f"📊 Found {len(golden_pairs)} golden pairs to process")
        
        for golden_pair in golden_pairs:
            try:
                pair_id = str(golden_pair.id)
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing golden pair: {pair_id}")
                logger.info(f"Title: {golden_pair.title}")
                
                # Check if survey_json exists
                if not golden_pair.survey_json:
                    logger.warning(f"⚠️ No survey_json found, skipping")
                    continue
                
                # Extract questions from survey_json
                questions = []
                survey_data = golden_pair.survey_json.get('final_output', golden_pair.survey_json)
                
                # Get survey_id - try multiple extraction methods
                survey_id = None
                survey_id_source = None
                
                if survey_data.get('survey_id'):
                    survey_id = survey_data.get('survey_id')
                    survey_id_source = 'final_output'
                elif golden_pair.survey_json.get('survey_id'):
                    survey_id = golden_pair.survey_json.get('survey_id')
                    survey_id_source = 'root'
                else:
                    survey_id = pair_id
                    survey_id_source = 'fallback_to_pair_id'
                
                logger.info(f"📋 Using survey_id: {survey_id} (source: {survey_id_source})")
                
                if 'questions' in survey_data:
                    questions = survey_data['questions']
                    logger.info(f"📝 Found {len(questions)} questions in flat structure")
                elif 'sections' in survey_data:
                    for section in survey_data['sections']:
                        if 'questions' in section:
                            questions.extend(section['questions'])
                    logger.info(f"📝 Found {len(questions)} questions in sections structure")
                
                if not questions:
                    logger.info(f"ℹ️ No questions found, skipping")
                    continue
                
                # Check if any questions have annotation fields
                questions_with_annotations = [q for q in questions if 'annotation' in q and isinstance(q['annotation'], dict)]
                logger.info(f"🔍 Found {len(questions_with_annotations)} questions with embedded annotations out of {len(questions)} total questions")
                
                if not questions_with_annotations:
                    logger.info(f"ℹ️ No embedded annotations found, skipping")
                    continue
                
                logger.info(f"✨ Found {len(questions_with_annotations)} questions with embedded annotations")
                stats['pairs_with_annotations'] += 1
                
                # DEBUG: Log all questions with embedded annotations
                logger.info(f"🔍 [DEBUG] Questions with embedded annotations:")
                debug_questions = []
                for i, q in enumerate(questions_with_annotations):
                    question_id = q.get("id", f"q_{i+1}")
                    comment = q.get("annotation", {}).get("comment", "")
                    logger.info(f"  - {question_id}: '{comment}'")
                    debug_questions.append(f"{question_id}: {comment}")
                
                stats['debug_info'].append(f"Golden pair {pair_id}: Found {len(questions_with_annotations)} questions with embedded annotations")
                stats['debug_info'].extend(debug_questions[:10])  # First 10 for brevity
                
                
                # Process annotations - create new or update existing
                annotations_created = 0
                annotations_updated = 0
                annotations_skipped = 0
                questions_with_errors = 0
                annotation_ids = []
                
                logger.info(f"🔍 [DEBUG] Processing {len(questions)} total questions")
                stats['debug_info'].append(f"Golden pair {pair_id}: Processing {len(questions)} total questions")
                
                processed_questions = []
                for i, question in enumerate(questions):
                    question_id = question.get("id", f"q_{i+1}")
                    
                    # Skip questions without annotations
                    if "annotation" not in question or not isinstance(question["annotation"], dict):
                        logger.info(f"🔍 [DEBUG] Skipping question {question_id} - no annotation field")
                        processed_questions.append(f"{question_id}: NO_ANNOTATION")
                        continue
                    
                    annotation_data = question["annotation"]
                    comment_text = annotation_data.get("comment", "")
                    
                    if not comment_text:
                        logger.info(f"🔍 [DEBUG] Skipping question {question_id} - no comment text")
                        processed_questions.append(f"{question_id}: NO_COMMENT")
                        continue
                    
                    logger.info(f"🔍 [DEBUG] Processing question {question_id} with comment: '{comment_text}'")
                    processed_questions.append(f"{question_id}: {comment_text}")
                    
                    # Wrap each question processing in try-except for individual error handling
                    try:
                        # Process the question with annotation
                        anchored_text = annotation_data.get("anchored_text", "")
                        author = annotation_data.get("author", "docx_parser")
                        date = annotation_data.get("date", "")
                        
                        # Normalize label
                        from src.services.label_normalizer import LabelNormalizer
                        label_normalizer = LabelNormalizer()
                        normalized_label = label_normalizer.normalize(comment_text)
                    
                        # Check if annotation already exists for this question BEFORE creating
                        # Look for any annotation with this question_id and survey_id, regardless of annotator_id
                        existing = db.query(QuestionAnnotation).filter(
                            QuestionAnnotation.question_id == question_id,
                            QuestionAnnotation.survey_id == survey_id
                        ).first()
                        
                        if existing:
                            logger.info(f"🔍 [DEBUG] Found existing annotation for question {question_id} with annotator_id '{existing.annotator_id}'")
                            # Check if comment is already in labels
                            existing_labels = existing.labels if existing.labels else []
                            
                            # Handle both list and dict formats for labels
                            if isinstance(existing_labels, dict):
                                existing_labels = []
                            elif not isinstance(existing_labels, list):
                                existing_labels = []
                            
                            if normalized_label not in existing_labels:
                                # Add the comment as a label to existing annotation
                                existing_labels.append(normalized_label)
                                existing.labels = existing_labels
                                
                                # Also update advanced_labels to include the embedded comment info
                                if not existing.advanced_labels:
                                    existing.advanced_labels = {}
                                
                                if not isinstance(existing.advanced_labels, dict):
                                    existing.advanced_labels = {}
                                
                                existing.advanced_labels["embedded_comment"] = {
                                    "comment_text": comment_text,
                                    "anchored_text": anchored_text,
                                    "comment_author": author,
                                    "comment_date": date,
                                    "normalized_label": normalized_label,
                                    "backfilled": True,
                                    "backfill_date": datetime.now().isoformat()
                                }
                                
                                db.flush()
                                annotations_updated += 1
                                logger.info(f"  ✅ Added label '{normalized_label}' to existing annotation for question {question_id}")
                            else:
                                annotations_skipped += 1
                                logger.info(f"  ℹ️ Label '{normalized_label}' already exists for question {question_id}, skipping")
                        else:
                            logger.info(f"🔍 [DEBUG] No existing annotation for question {question_id}, creating new one")
                            # Create new annotation
                            advanced_labels = {
                                "comment_text": comment_text,
                                "anchored_text": anchored_text,
                                "comment_author": author,
                                "comment_date": date,
                                "matching_method": "llm_with_anchored_text",
                                "matching_confidence": 1.0,
                                "original_comment": comment_text,
                                "normalized_label": normalized_label,
                                "backfilled": True,
                                "backfill_date": datetime.now().isoformat()
                            }
                            
                            annotation = QuestionAnnotation(
                                question_id=question_id,
                                survey_id=survey_id,
                                comment=comment_text,
                                labels=[normalized_label],
                                advanced_labels=advanced_labels,
                                annotator_id=author,
                                required=True,
                                quality=3,
                                relevant=3,
                                methodological_rigor=3,
                                content_validity=3,
                                respondent_experience=3,
                                analytical_value=3,
                                business_impact=3,
                                ai_generated=True,
                                ai_confidence=1.0,
                                generation_timestamp=datetime.now()
                            )
                            
                            db.add(annotation)
                            db.flush()  # Get the ID
                            annotation_ids.append(annotation.id)
                            annotations_created += 1
                            logger.info(f"  ✅ Created annotation for question {question_id}: '{comment_text[:50]}...'")
                    
                    except Exception as question_error:
                        # Rollback just this question's changes
                        questions_with_errors += 1
                        logger.warning(f"  ⚠️ Error processing question {question_id}, rolling back: {str(question_error)}")
                        db.rollback()
                        continue
                
                if annotations_created > 0 or annotations_updated > 0:
                    db.commit()
                    stats['annotations_created'] += annotations_created
                    stats['annotations_updated'] += annotations_updated
                    logger.info(f"💾 Committed {annotations_created} new, {annotations_updated} updated, {annotations_skipped} skipped, {questions_with_errors} errors")
                    
                    # Sync to RAG
                    try:
                        sync_service = AnnotationRAGSyncService(db)
                        synced = 0
                        for ann_id in annotation_ids:
                            result = await sync_service.sync_question_annotation(ann_id)
                            if result.get('success'):
                                synced += 1
                        stats['annotations_synced'] += synced
                        logger.info(f"🔗 Synced {synced}/{len(annotation_ids)} annotations to RAG")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to sync annotations to RAG: {str(e)}")
                
            except Exception as e:
                error_msg = f"Error processing golden pair {pair_id}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                stats['errors'].append(error_msg)
                db.rollback()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 MIGRATION COMPLETE")
        logger.info(f"Total golden pairs: {stats['total_golden_pairs']}")
        logger.info(f"Pairs with annotations: {stats['pairs_with_annotations']}")
        logger.info(f"Annotations created: {stats['annotations_created']}")
        logger.info(f"Annotations updated: {stats['annotations_updated']}")
        logger.info(f"Annotations synced to RAG: {stats['annotations_synced']}")
        logger.info(f"Errors: {len(stats['errors'])}")
        
        if stats['errors']:
            logger.error(f"\n❌ Errors encountered:")
            for error in stats['errors']:
                logger.error(f"  - {error}")
        
        return stats
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info(f"🚀 Starting annotation backfill")
    stats = asyncio.run(backfill_all_golden_pair_annotations())
    
    if stats['errors']:
        sys.exit(1)

