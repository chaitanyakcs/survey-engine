#!/usr/bin/env python3
"""
Script to find the survey with the most annotations and comments using the API.

Usage:
    python scripts/find_survey_with_most_annotations.py [--api-url <url>] [--limit <n>]
    
Examples:
    # Check production
    python scripts/find_survey_with_most_annotations.py --api-url https://survey-engine-production.up.railway.app
    
    # Check local
    python scripts/find_survey_with_most_annotations.py --api-url http://localhost:8000
"""

import sys
import argparse
import requests
from typing import Dict, List, Tuple
from urllib.parse import urljoin


def get_all_surveys(api_url: str, limit: int = 1000) -> List[Dict]:
    """Fetch all surveys from the API"""
    surveys = []
    skip = 0
    batch_size = 50
    
    print(f"📋 Fetching surveys from {api_url}...")
    
    while True:
        url = urljoin(api_url, "/api/v1/survey/list")
        params = {"skip": skip, "limit": batch_size}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            batch = response.json()
            
            if not batch:
                break
                
            surveys.extend(batch)
            print(f"   Fetched {len(surveys)} surveys so far...")
            
            if len(batch) < batch_size:
                break
                
            skip += batch_size
            
            if len(surveys) >= limit:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching surveys: {e}")
            break
    
    print(f"✅ Found {len(surveys)} surveys total")
    return surveys


def get_survey_annotations(api_url: str, survey_id: str) -> Dict:
    """Fetch annotations for a specific survey"""
    url = urljoin(api_url, f"/api/v1/surveys/{survey_id}/annotations")
    params = {"include_ai_annotations": "true"}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 404:
            return {
                "question_annotations": [],
                "section_annotations": [],
                "overall_comment": None
            }
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Error fetching annotations for {survey_id}: {e}")
        return {
            "question_annotations": [],
            "section_annotations": [],
            "overall_comment": None
        }


def is_human_annotation(ann: Dict) -> bool:
    """Check if annotation is human-generated (not AI)"""
    # Filter out AI-generated annotations
    if ann.get("ai_generated") is True:
        return False
    # Filter out annotations from ai_system
    if ann.get("annotator_id") == "ai_system":
        return False
    # Include all others as human annotations
    return True


def count_annotations_and_comments(annotations_data: Dict, human_only: bool = True) -> Tuple[int, int]:
    """Count total annotations and comments, optionally filtering for human-only"""
    question_anns = annotations_data.get("question_annotations", [])
    section_anns = annotations_data.get("section_annotations", [])
    overall_comment = annotations_data.get("overall_comment")
    
    # Filter for human annotations only if requested
    if human_only:
        question_anns = [qa for qa in question_anns if is_human_annotation(qa)]
        section_anns = [sa for sa in section_anns if is_human_annotation(sa)]
        # Survey-level comments are typically human, but we'll include them
    
    # Count annotations
    total_annotations = len(question_anns) + len(section_anns)
    if overall_comment:
        total_annotations += 1
    
    # Count comments (non-empty comment fields)
    comment_count = 0
    
    # Question annotation comments
    for qa in question_anns:
        if qa.get("comment") and qa.get("comment").strip():
            comment_count += 1
    
    # Section annotation comments
    for sa in section_anns:
        if sa.get("comment") and sa.get("comment").strip():
            comment_count += 1
    
    # Survey-level comment
    if overall_comment and overall_comment.strip():
        comment_count += 1
    
    return total_annotations, comment_count


def find_survey_with_most_annotations(api_url: str, limit: int = 1000) -> None:
    """Find and display the survey with the most annotations and comments"""
    
    # Get all surveys
    surveys = get_all_surveys(api_url, limit)
    
    if not surveys:
        print("❌ No surveys found")
        return
    
    print(f"\n🔍 Checking HUMAN annotations only for {len(surveys)} surveys...\n")
    
    survey_stats = []
    
    for i, survey in enumerate(surveys, 1):
        survey_id = survey.get("id")
        survey_title = survey.get("title", "Untitled Survey")
        
        if not survey_id:
            continue
        
        print(f"[{i}/{len(surveys)}] Checking {survey_id[:8]}... - {survey_title[:50]}")
        
        # Get annotations (fetch all, then filter for human-only)
        annotations_data = get_survey_annotations(api_url, survey_id)
        
        # Count annotations and comments (human-only)
        total_annotations, comment_count = count_annotations_and_comments(annotations_data, human_only=True)
        
        # Get filtered human annotations for accurate counts
        question_anns = [qa for qa in annotations_data.get("question_annotations", []) if is_human_annotation(qa)]
        section_anns = [sa for sa in annotations_data.get("section_annotations", []) if is_human_annotation(sa)]
        
        if total_annotations > 0 or comment_count > 0:
            survey_stats.append({
                "survey_id": survey_id,
                "title": survey_title,
                "total_annotations": total_annotations,
                "comment_count": comment_count,
                "question_annotations": len(question_anns),
                "section_annotations": len(section_anns),
                "has_overall_comment": bool(annotations_data.get("overall_comment")),
                "annotations_data": {
                    "question_annotations": question_anns,
                    "section_annotations": section_anns,
                    "overall_comment": annotations_data.get("overall_comment")
                }
            })
            print(f"   ✅ Found {total_annotations} annotations, {comment_count} comments")
        else:
            print(f"   ⚪ No annotations")
    
    if not survey_stats:
        print("\n❌ No surveys with annotations found")
        return
    
    # Sort by total annotations (descending), then by comment count
    survey_stats.sort(key=lambda x: (x["total_annotations"], x["comment_count"]), reverse=True)
    
    # Display results
    print("\n" + "="*80)
    print("📊 SURVEYS WITH MOST HUMAN ANNOTATIONS AND COMMENTS")
    print("="*80)
    print()
    
    # Show all surveys with human annotations
    print(f"All {len(survey_stats)} surveys with human annotations:\n")
    
    for i, stats in enumerate(survey_stats, 1):
        survey_url = urljoin(api_url, f'/surveys/{stats["survey_id"]}')
        print(f"{i}. {survey_url}")
        print(f"   Title: {stats['title']}")
        print(f"   Annotations: {stats['total_annotations']} ({stats['question_annotations']} questions, {stats['section_annotations']} sections), Comments: {stats['comment_count']}")
        print()
    
    # Show all links in a simple list
    print("="*80)
    print("🔗 ALL SURVEYS WITH HUMAN ANNOTATIONS - LINKS")
    print("="*80)
    print()
    
    for stats in survey_stats:
        survey_url = urljoin(api_url, f'/surveys/{stats["survey_id"]}')
        print(survey_url)
    
    print()
    print(f"Total: {len(survey_stats)} surveys with human annotations")


def main():
    parser = argparse.ArgumentParser(
        description="Find the survey with the most annotations and comments using the API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check production
  python scripts/find_survey_with_most_annotations.py --api-url https://survey-engine-production.up.railway.app
  
  # Check local
  python scripts/find_survey_with_most_annotations.py --api-url http://localhost:8000
  
  # Limit to first 100 surveys
  python scripts/find_survey_with_most_annotations.py --limit 100
        """
    )
    parser.add_argument(
        "--api-url",
        default="https://survey-engine-production.up.railway.app",
        help="API base URL (default: production)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of surveys to check (default: 1000)"
    )
    
    args = parser.parse_args()
    
    find_survey_with_most_annotations(args.api_url, args.limit)


if __name__ == "__main__":
    main()

