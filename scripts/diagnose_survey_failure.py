#!/usr/bin/env python3
"""
Diagnostic script to investigate why a survey generation failed.

Usage:
    python scripts/diagnose_survey_failure.py <survey_id> [--api-url <url>] [--db]
    
Examples:
    # Query via API
    python scripts/diagnose_survey_failure.py edc1dd30-3f29-4469-b6df-0cd0ee5afac5 --api-url https://survey-engine-production.up.railway.app
    
    # Query directly from database (local or remote)
    python scripts/diagnose_survey_failure.py edc1dd30-3f29-4469-b6df-0cd0ee5afac5 --db
"""

import sys
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

# Add src to path for local database access
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

try:
    from src.database.connection import get_db_session
    from src.database.models import Survey, LLMAudit, RFQ
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  Database access not available (will use API only)")


def format_timestamp(ts: Optional[str]) -> str:
    """Format timestamp for display"""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return ts


def query_via_api(survey_id: str, api_url: str) -> Dict[str, Any]:
    """Query LLM audit records via API"""
    base_url = api_url.rstrip('/')
    
    print(f"\n🔍 Querying LLM audit records for survey: {survey_id}")
    print(f"   API URL: {base_url}")
    
    # Get LLM audit records
    audit_url = f"{base_url}/api/v1/llm-audit/interactions"
    params = {
        "parent_survey_id": survey_id,
        "page": 1,
        "page_size": 100
    }
    
    try:
        response = requests.get(audit_url, params=params, timeout=30)
        response.raise_for_status()
        audit_data = response.json()
        
        records = audit_data.get("records", [])
        total_count = audit_data.get("total_count", 0)
        
        print(f"   ✅ Found {total_count} LLM audit record(s)")
        return {"records": records, "total_count": total_count}
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to query API: {e}")
        return {"records": [], "total_count": 0}
    
    # Get survey info
    try:
        survey_url = f"{base_url}/api/v1/survey/{survey_id}"
        response = requests.get(survey_url, timeout=30)
        if response.status_code == 200:
            survey_data = response.json()
            return {"records": records, "total_count": total_count, "survey": survey_data}
    except:
        pass
    
    return {"records": records, "total_count": total_count}


def query_via_db(survey_id: str) -> Dict[str, Any]:
    """Query LLM audit records directly from database"""
    if not DB_AVAILABLE:
        print("❌ Database access not available")
        return {"records": [], "total_count": 0}
    
    print(f"\n🔍 Querying database for survey: {survey_id}")
    
    db = get_db_session()
    try:
        # Get survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        
        survey_info = None
        if survey:
            survey_info = {
                "id": str(survey.id),
                "status": survey.status,
                "created_at": survey.created_at.isoformat() if survey.created_at else None,
                "rfq_id": str(survey.rfq_id) if survey.rfq_id else None
            }
        
        # Get LLM audit records
        audit_records = db.query(LLMAudit).filter(
            LLMAudit.parent_survey_id == survey_id
        ).order_by(LLMAudit.created_at.desc()).all()
        
        records = []
        for record in audit_records:
            records.append({
                "id": str(record.id),
                "interaction_id": record.interaction_id,
                "parent_workflow_id": record.parent_workflow_id,
                "parent_survey_id": record.parent_survey_id,
                "model_name": record.model_name,
                "model_provider": record.model_provider,
                "purpose": record.purpose,
                "sub_purpose": record.sub_purpose,
                "context_type": record.context_type,
                "success": record.success,
                "error_message": record.error_message,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "response_time_ms": record.response_time_ms,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "tags": record.tags,
                "interaction_metadata": record.interaction_metadata
            })
        
        return {
            "records": records,
            "total_count": len(records),
            "survey": survey_info
        }
        
    finally:
        db.close()


def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze LLM audit records to identify failures"""
    if not records:
        return {"error": "No records found"}
    
    # Group by purpose and check success/failure
    by_purpose = {}
    failed_records = []
    successful_records = []
    
    for record in records:
        purpose = record.get("purpose", "unknown")
        sub_purpose = record.get("sub_purpose", "")
        key = f"{purpose}" + (f"::{sub_purpose}" if sub_purpose else "")
        
        if key not in by_purpose:
            by_purpose[key] = {"total": 0, "success": 0, "failed": 0, "records": []}
        
        by_purpose[key]["total"] += 1
        by_purpose[key]["records"].append(record)
        
        if record.get("success", True):
            by_purpose[key]["success"] += 1
            successful_records.append(record)
        else:
            by_purpose[key]["failed"] += 1
            failed_records.append(record)
    
    # Find the first failure in chronological order
    sorted_records = sorted(records, key=lambda r: r.get("created_at", ""))
    first_failure = None
    for record in sorted_records:
        if not record.get("success", True):
            first_failure = record
            break
    
    return {
        "total_records": len(records),
        "by_purpose": by_purpose,
        "failed_records": failed_records,
        "successful_records": successful_records,
        "first_failure": first_failure,
        "failure_count": len(failed_records),
        "success_count": len(successful_records)
    }


def print_analysis(analysis: Dict[str, Any], survey_info: Optional[Dict[str, Any]] = None):
    """Print detailed analysis"""
    print("\n" + "="*80)
    print("📊 SURVEY GENERATION FAILURE ANALYSIS")
    print("="*80)
    
    if survey_info:
        print(f"\n📋 Survey Information:")
        print(f"   ID: {survey_info.get('id', 'N/A')}")
        print(f"   Status: {survey_info.get('status', 'N/A')}")
        if survey_info.get('created_at'):
            print(f"   Created: {format_timestamp(survey_info['created_at'])}")
        if survey_info.get('rfq_id'):
            print(f"   RFQ ID: {survey_info['rfq_id']}")
    
    print(f"\n📈 LLM Interaction Summary:")
    print(f"   Total Interactions: {analysis['total_records']}")
    print(f"   ✅ Successful: {analysis['success_count']}")
    print(f"   ❌ Failed: {analysis['failure_count']}")
    
    if analysis['failure_count'] == 0:
        print("\n⚠️  No explicit failures found in LLM audit records.")
        print("   The failure may have occurred at a different stage (validation, parsing, etc.)")
        return
    
    # Show first failure (root cause)
    first_failure = analysis.get('first_failure')
    if first_failure:
        print(f"\n🔴 ROOT CAUSE - First Failure:")
        print(f"   Interaction ID: {first_failure.get('interaction_id', 'N/A')}")
        print(f"   Purpose: {first_failure.get('purpose', 'N/A')}")
        if first_failure.get('sub_purpose'):
            print(f"   Sub-Purpose: {first_failure.get('sub_purpose')}")
        print(f"   Model: {first_failure.get('model_name', 'N/A')} ({first_failure.get('model_provider', 'N/A')})")
        print(f"   Created: {format_timestamp(first_failure.get('created_at'))}")
        print(f"   Error Message: {first_failure.get('error_message', 'No error message')}")
        
        if first_failure.get('interaction_metadata'):
            metadata = first_failure.get('interaction_metadata')
            if isinstance(metadata, dict) and metadata:
                print(f"   Metadata: {json.dumps(metadata, indent=2)[:200]}...")
    
    # Show all failures grouped by purpose
    if analysis['failed_records']:
        print(f"\n❌ All Failed Interactions ({len(analysis['failed_records'])}):")
        for i, record in enumerate(analysis['failed_records'], 1):
            print(f"\n   {i}. {record.get('purpose', 'unknown')}")
            if record.get('sub_purpose'):
                print(f"      Sub-Purpose: {record.get('sub_purpose')}")
            print(f"      Model: {record.get('model_name', 'N/A')}")
            print(f"      Time: {format_timestamp(record.get('created_at'))}")
            error_msg = record.get('error_message', 'No error message')
            print(f"      Error: {error_msg[:200]}")
            if len(error_msg) > 200:
                print(f"             ... (truncated)")
    
    # Show interactions by purpose
    print(f"\n📊 Interactions by Purpose:")
    for purpose, stats in analysis['by_purpose'].items():
        status = "✅" if stats['failed'] == 0 else "❌"
        print(f"   {status} {purpose}: {stats['success']} success, {stats['failed']} failed (total: {stats['total']})")
    
    # Show workflow timeline
    print(f"\n⏱️  Workflow Timeline:")
    sorted_by_time = sorted(analysis.get('successful_records', []) + analysis.get('failed_records', []), 
                           key=lambda r: r.get('created_at', ''))
    for i, record in enumerate(sorted_by_time[:10], 1):  # Show first 10
        status = "✅" if record.get('success', True) else "❌"
        purpose = record.get('purpose', 'unknown')
        if record.get('sub_purpose'):
            purpose += f"::{record.get('sub_purpose')}"
        time_str = format_timestamp(record.get('created_at'))
        print(f"   {i}. {status} {time_str} - {purpose}")
    
    if len(sorted_by_time) > 10:
        print(f"   ... and {len(sorted_by_time) - 10} more interactions")


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose survey generation failure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query via API (production)
  python scripts/diagnose_survey_failure.py edc1dd30-3f29-4469-b6df-0cd0ee5afac5 --api-url https://survey-engine-production.up.railway.app
  
  # Query directly from database
  python scripts/diagnose_survey_failure.py edc1dd30-3f29-4469-b6df-0cd0ee5afac5 --db
        """
    )
    parser.add_argument("survey_id", help="Survey ID to diagnose")
    parser.add_argument("--api-url", default="https://survey-engine-production.up.railway.app",
                       help="API base URL (default: production)")
    parser.add_argument("--db", action="store_true",
                       help="Query directly from database instead of API")
    
    args = parser.parse_args()
    
    survey_id = args.survey_id
    
    # Query data
    if args.db:
        if not DB_AVAILABLE:
            print("❌ Database access not available. Use --api-url instead.")
            sys.exit(1)
        data = query_via_db(survey_id)
    else:
        data = query_via_api(survey_id, args.api_url)
    
    records = data.get("records", [])
    survey_info = data.get("survey")
    
    if not records:
        print(f"\n❌ No LLM audit records found for survey: {survey_id}")
        print("   Possible reasons:")
        print("   - Survey was never generated (no workflow started)")
        print("   - Audit records were not created (check audit logging)")
        print("   - Wrong survey ID")
        sys.exit(1)
    
    # Analyze records
    analysis = analyze_records(records)
    
    # Print analysis
    print_analysis(analysis, survey_info)
    
    print("\n" + "="*80)
    print("✅ Analysis complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

