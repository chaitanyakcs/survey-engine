#!/usr/bin/env python3
"""
Batch recompute golden similarity and breakdown for existing surveys.

For each survey with used_golden_examples and final_output:
 - Recalculate per-example similarity using compare_surveys
 - Compute best match detailed breakdown
 - Store into survey.pillar_scores['golden_similarity_analysis']

Safe to run multiple times.
"""
from __future__ import annotations

import sys
from typing import Dict, Any, List

from src.database import get_db
from src.database.models import Survey, GoldenRFQSurveyPair
from src.utils.survey_comparison import compare_surveys, compare_surveys_detailed


def main(limit: int | None = None) -> None:
    db = next(get_db())
    try:
        q = db.query(Survey)
        if limit:
            surveys: List[Survey] = q.limit(limit).all()
        else:
            surveys = q.all()

        updated = 0
        skipped = 0
        for survey in surveys:
            try:
                if not survey.final_output or not survey.used_golden_examples:
                    skipped += 1
                    continue

                golden_ids = survey.used_golden_examples or []
                golden_pairs = (
                    db.query(GoldenRFQSurveyPair)
                    .filter(GoldenRFQSurveyPair.id.in_(golden_ids))
                    .all()
                )
                if not golden_pairs:
                    skipped += 1
                    continue

                individual_similarities: List[Dict[str, Any]] = []
                for pair in golden_pairs[:10]:
                    golden_survey = pair.survey_json
                    if isinstance(golden_survey, dict) and "final_output" in golden_survey:
                        golden_survey = golden_survey["final_output"]
                    elif isinstance(golden_survey, dict) and "survey_json" in golden_survey:
                        golden_survey = golden_survey["survey_json"]

                    # Ensure metadata from DB is available
                    if isinstance(golden_survey, dict) and pair.methodology_tags:
                        golden_survey.setdefault("metadata", {})
                        golden_survey["metadata"].setdefault(
                            "methodology_tags", pair.methodology_tags
                        )
                        if pair.industry_category and not golden_survey["metadata"].get(
                            "industry_category"
                        ):
                            golden_survey["metadata"][
                                "industry_category"
                            ] = pair.industry_category

                    sim = compare_surveys(survey.final_output, golden_survey)
                    individual_similarities.append(
                        {
                            "golden_id": str(pair.id),
                            "similarity": float(sim),
                            "title": pair.title or "Untitled Golden Example",
                            "methodology_tags": pair.methodology_tags or [],
                            "industry_category": pair.industry_category,
                        }
                    )

                if not individual_similarities:
                    skipped += 1
                    continue

                avg_similarity = sum(s["similarity"] for s in individual_similarities) / len(
                    individual_similarities
                )
                best_idx = max(
                    range(len(individual_similarities)),
                    key=lambda i: individual_similarities[i]["similarity"],
                )
                best_pair = golden_pairs[best_idx]
                best_survey = best_pair.survey_json
                if isinstance(best_survey, dict) and "final_output" in best_survey:
                    best_survey = best_survey["final_output"]
                breakdown = compare_surveys_detailed(survey.final_output, best_survey)

                # Store into pillar_scores
                if survey.pillar_scores is None or not isinstance(
                    survey.pillar_scores, dict
                ):
                    survey.pillar_scores = {}
                survey.pillar_scores["golden_similarity_analysis"] = {
                    "overall_average": float(avg_similarity),
                    "best_match": {
                        "golden_id": individual_similarities[best_idx]["golden_id"],
                        "title": individual_similarities[best_idx]["title"],
                        "similarity": float(individual_similarities[best_idx]["similarity"]),
                        "match_type": "overall",
                        "match_reason": "Recalculated using SOTA hybrid comparison",
                    },
                    "best_industry_match": None,
                    "best_methodology_match": None,
                    "best_combined_match": None,
                    "individual_similarities": individual_similarities,
                    "methodology_alignment": {"score": 0.0},
                    "industry_alignment": {"score": 0.0},
                    "total_golden_examples_analyzed": len(individual_similarities),
                    "similarity_breakdown": breakdown,
                    "note": "Recalculated using SOTA hybrid approach",
                }

                db.commit()
                updated += 1
            except Exception:
                db.rollback()
                skipped += 1
                continue

        print(f"Updated: {updated}, Skipped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)


