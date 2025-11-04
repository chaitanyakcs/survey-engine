"""
Survey comparison utilities using SOTA hybrid approach without LLM calls.
Combines TF-IDF, structural analysis, and metadata comparison for fast, accurate similarity.
"""
from typing import Dict, List, Any, Optional, Set
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)

SKLEARN_AVAILABLE = False
try:
    # Lazy import to avoid scipy/numpy compatibility issues at module import time
    # Import only when actually needed
    import sklearn.feature_extraction.text
    import sklearn.metrics.pairwise
    SKLEARN_AVAILABLE = True
except (ImportError, TypeError) as e:
    SKLEARN_AVAILABLE = False
    logger.warning(f"sklearn not available, falling back to basic similarity: {e}")


def _extract_actual_survey(survey: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the actual survey from potentially nested structures.
    
    Handles cases where survey might be:
    - Direct survey object: {"title": ..., "sections": ...}
    - Nested in final_output: {"final_output": {"title": ..., "sections": ...}}
    - Nested in raw_output: {"raw_output": {"title": ..., "sections": ...}}
    
    Args:
        survey: Survey dictionary, potentially nested
        
    Returns:
        Dict: The actual survey object
    """
    if not survey or not isinstance(survey, dict):
        return survey
    
    # Check for nested structures
    if "final_output" in survey:
        nested = survey["final_output"]
        if isinstance(nested, dict):
            return nested
    
    if "raw_output" in survey:
        nested = survey["raw_output"]
        if isinstance(nested, dict):
            return nested
    
    if "survey_json" in survey:
        nested = survey["survey_json"]
        if isinstance(nested, dict):
            return nested
    
    # Return as-is if no nesting found
    return survey


def compare_surveys(survey1: Dict[str, Any], survey2: Dict[str, Any]) -> float:
    """
    Compare two surveys and return a similarity score (0.0-1.0).
    
    Uses hybrid SOTA approach:
    - TF-IDF semantic similarity (40% - increased for better text matching)
    - Structural similarity (20% - decreased since format may differ)
    - Metadata similarity (25% - increased for methodology matching)
    - Content similarity (15% - decreased)
    
    Args:
        survey1: First survey JSON (can have nested final_output)
        survey2: Second survey JSON (can have nested final_output)
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not survey1 or not survey2:
        return 0.0
    
    # Handle nested structures - extract actual survey from final_output if present
    survey1 = _extract_actual_survey(survey1)
    survey2 = _extract_actual_survey(survey2)
    
    if not survey1 or not survey2:
        return 0.0
    
    # If surveys are identical (same object reference)
    if survey1 is survey2:
        return 1.0
    
    try:
        # Extract text representations
        text1 = _survey_to_rich_text(survey1)
        text2 = _survey_to_rich_text(survey2)
        
        # 1. Semantic Similarity (50% weight - PRIMARY factor, what actually matters)
        semantic_score = _compute_tfidf_similarity(text1, text2)
        
        # 2. Structural Similarity (20% weight - format differences don't mean content is different)
        structural_score = _compare_structure(survey1, survey2)
        
        # 3. Metadata Similarity (15% weight - methodology tags are metadata, not content)
        #    Methodology tags help when they match, but don't heavily penalize when different
        metadata_score = _compare_metadata(survey1, survey2)
        
        # 4. Content Similarity (15% weight - question text similarity)
        content_score = _compare_content(survey1, survey2)
        
        # Weighted combination - prioritize actual content similarity
        weighted_score = (
            semantic_score * 0.50 +
            structural_score * 0.20 +
            metadata_score * 0.15 +
            content_score * 0.15
        )
        
        return round(weighted_score, 3)
        
    except Exception as e:
        logger.error(f"Error comparing surveys: {e}", exc_info=True)
        return 0.0


def compare_surveys_detailed(survey1: Dict[str, Any], survey2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detailed comparison returning component scores and question-level match stats.

    Returns dictionary with:
    - semantic_similarity
    - structural_similarity
    - metadata_similarity
    - content_similarity
    - overall_similarity (weighted combination used by compare_surveys)
    - methodology_similarity (explicit jaccard of methodology tags)
    - question_match: { match_rate, precision, recall, f1, total_a, total_b, matched_pairs: [ {a_index,b_index,score} ] }
    """
    if not survey1 or not survey2:
        return {
            "semantic_similarity": 0.0,
            "structural_similarity": 0.0,
            "metadata_similarity": 0.0,
            "content_similarity": 0.0,
            "overall_similarity": 0.0,
            "methodology_similarity": 0.0,
            "question_match": {
                "match_rate": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "total_a": 0,
                "total_b": 0,
                "matched_pairs": []
            }
        }

    # Normalize
    s1 = _extract_actual_survey(survey1)
    s2 = _extract_actual_survey(survey2)

    text1 = _survey_to_rich_text(s1)
    text2 = _survey_to_rich_text(s2)

    semantic = _compute_tfidf_similarity(text1, text2)
    structural = _compare_structure(s1, s2)
    metadata = _compare_metadata(s1, s2)
    content = _compare_content(s1, s2)

    overall = round(semantic * 0.50 + structural * 0.20 + metadata * 0.15 + content * 0.15, 3)

    # Methodology similarity as explicit Jaccard
    tags1 = set(s1.get("metadata", {}).get("methodology_tags", []) or [])
    tags2 = set(s2.get("metadata", {}).get("methodology_tags", []) or [])
    if tags1 or tags2:
        inter = len(tags1.intersection(tags2))
        union = len(tags1.union(tags2))
        methodology_sim = (inter / union) if union else 0.0
    else:
        methodology_sim = 0.0

    # Question-level matching
    question_match = _compute_question_match_stats(s1, s2)

    return {
        "semantic_similarity": round(semantic, 3),
        "structural_similarity": round(structural, 3),
        "metadata_similarity": round(metadata, 3),
        "content_similarity": round(content, 3),
        "overall_similarity": overall,
        "methodology_similarity": round(methodology_sim, 3),
        "question_match": question_match,
    }


def compute_question_match_across_all_golden_pairs(
    generated_survey: Dict[str, Any],
    all_golden_surveys: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Match questions in generated survey against ALL golden pairs (not just best match).
    
    This is more like human evaluation: "Can you find a similar question 
    anywhere in the reference examples?"
    
    Args:
        generated_survey: The generated survey to match
        all_golden_surveys: List of all golden survey JSONs to match against
        
    Returns:
        Dict with match statistics across all golden pairs
    """
    from src.utils.survey_utils import extract_all_questions
    
    gen_questions = extract_all_questions(generated_survey)
    gen_q_texts = [q.get("text", "").strip() for q in gen_questions if q.get("text", "").strip()]
    
    if not gen_q_texts:
        return {
            "match_rate": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "total_generated": 0,
            "total_golden_questions": 0,
            "matched_pairs": [],
            "matches_by_golden": {}
        }
    
    # Collect all questions from all golden pairs
    all_golden_questions = []
    golden_survey_index = []  # Track which golden survey each question comes from
    
    for golden_idx, golden_survey in enumerate(all_golden_surveys):
        golden_qs = extract_all_questions(golden_survey)
        for q in golden_qs:
            if q.get("text", "").strip():
                all_golden_questions.append(q)
                golden_survey_index.append(golden_idx)
    
    if not all_golden_questions:
        return {
            "match_rate": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "total_generated": len(gen_q_texts),
            "total_golden_questions": 0,
            "matched_pairs": [],
            "matches_by_golden": {}
        }
    
    # Match each generated question against all golden questions
    matched_pairs = []
    used_golden = set()
    
    if SKLEARN_AVAILABLE:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Create TF-IDF vectors for all questions
            all_texts = gen_q_texts + [q.get("text", "").strip() for q in all_golden_questions]
            vectorizer = TfidfVectorizer(lowercase=True, stop_words=None, ngram_range=(1, 2), min_df=1, max_df=1.0)
            tfidf = vectorizer.fit_transform(all_texts)
            
            gen_mat = tfidf[0:len(gen_q_texts)]
            golden_mat = tfidf[len(gen_q_texts):]
            sim_matrix = cosine_similarity(gen_mat, golden_mat)
            
            # For each generated question, find best match across all golden questions
            # Lower threshold to 0.25 to catch more semantic similarities
            candidates = []
            for i in range(len(gen_q_texts)):
                for j in range(len(all_golden_questions)):
                    score = float(sim_matrix[i, j])
                    if score >= 0.25:  # Lowered from 0.4 to catch more matches
                        candidates.append((i, j, score, golden_survey_index[j]))
            
            # Sort by similarity and match greedily
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            matches_by_golden = {}
            for i, j, score, golden_idx in candidates:
                if i not in [mp["a_index"] for mp in matched_pairs] and j not in used_golden:
                    # Check option similarity
                    option_similarity = None
                    gen_q = gen_questions[i]
                    golden_q = all_golden_questions[j]
                    opts1 = gen_q.get("options", [])
                    opts2 = golden_q.get("options", [])
                    
                    if opts1 and opts2 and isinstance(opts1, list) and isinstance(opts2, list):
                        opts1_set = set(str(o).lower().strip() for o in opts1)
                        opts2_set = set(str(o).lower().strip() for o in opts2)
                        if opts1_set or opts2_set:
                            inter = len(opts1_set & opts2_set)
                            union = len(opts1_set | opts2_set)
                            option_similarity = inter / union if union > 0 else 0.0
                    
                    matched_pairs.append({
                        "a_index": i,
                        "b_index": j,
                        "score": round(score, 3),
                        "golden_survey_index": golden_idx,
                        "option_similarity": round(option_similarity, 3) if option_similarity is not None else None
                    })
                    used_golden.add(j)
                    matches_by_golden[golden_idx] = matches_by_golden.get(golden_idx, 0) + 1
        except Exception:
            # Fallback to token matching
            pass
    
    # If TF-IDF failed or not available, use token matching
    if not matched_pairs:
        def _tok(text: str) -> set:
            return set(w.lower() for w in text.split() if len(w) > 2)
        
        candidates = []
        for i, t1 in enumerate(gen_q_texts):
            tokens1 = _tok(t1)
            for j, golden_q in enumerate(all_golden_questions):
                t2 = golden_q.get("text", "").strip()
                tokens2 = _tok(t2)
                if tokens1 and tokens2:
                    sim = len(tokens1 & tokens2) / len(tokens1 | tokens2) if (tokens1 | tokens2) else 0.0
                    if sim >= 0.25:  # Lowered from 0.4 to catch more matches
                        candidates.append((i, j, sim, golden_survey_index[j]))
        
        candidates.sort(key=lambda x: x[2], reverse=True)
        matches_by_golden = {}
        used_golden = set()
        
        for i, j, sim, golden_idx in candidates:
            if i not in [mp["a_index"] for mp in matched_pairs] and j not in used_golden:
                # Check option similarity
                option_similarity = None
                gen_q = gen_questions[i]
                golden_q = all_golden_questions[j]
                opts1 = gen_q.get("options", [])
                opts2 = golden_q.get("options", [])
                
                if opts1 and opts2 and isinstance(opts1, list) and isinstance(opts2, list):
                    opts1_set = set(str(o).lower().strip() for o in opts1)
                    opts2_set = set(str(o).lower().strip() for o in opts2)
                    if opts1_set or opts2_set:
                        inter = len(opts1_set & opts2_set)
                        union = len(opts1_set | opts2_set)
                        option_similarity = inter / union if union > 0 else 0.0
                
                matched_pairs.append({
                    "a_index": i,
                    "b_index": j,
                    "score": round(sim, 3),
                    "golden_survey_index": golden_idx,
                    "option_similarity": round(option_similarity, 3) if option_similarity is not None else None
                })
                used_golden.add(j)
                matches_by_golden[golden_idx] = matches_by_golden.get(golden_idx, 0) + 1
    
    matches = len(matched_pairs)
    total_gen = len(gen_q_texts)
    total_golden = len(all_golden_questions)
    
    recall = matches / total_gen if total_gen else 0.0
    precision = matches / total_golden if total_golden else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    match_rate = matches / max(total_gen, total_golden)
    
    return {
        "match_rate": round(match_rate, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "total_a": total_gen,  # Generated questions (for UI compatibility)
        "total_b": total_golden,  # Golden questions (for UI compatibility)
        "total_generated": total_gen,  # Also keep for clarity
        "total_golden_questions": total_golden,  # Also keep for clarity
        "matched_pairs": matched_pairs,
        "matches_by_golden": matches_by_golden  # How many matches came from each golden pair
    }


def _compute_question_match_stats(s1: Dict[str, Any], s2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute question-level matching using TF-IDF similarity across question texts.
    Returns match rate and basic IR-style metrics.
    
    Uses multiple strategies for better matching:
    - TF-IDF cosine similarity (primary)
    - Keyword overlap (fallback for short questions)
    - Question type matching (boost)
    """
    def _normalize_question_text(text: str) -> str:
        """Normalize question text for better matching"""
        if not text:
            return ""
        # Remove extra whitespace, normalize case
        text = " ".join(text.split())
        return text.lower().strip()
    
    qs1_raw = _extract_all_questions(s1)
    qs2_raw = _extract_all_questions(s2)
    
    # Extract texts with normalization
    qs1 = [_normalize_question_text(q.get("text", "")) for q in qs1_raw if isinstance(q.get("text", ""), str) and q.get("text", "").strip()]
    qs2 = [_normalize_question_text(q.get("text", "")) for q in qs2_raw if isinstance(q.get("text", ""), str) and q.get("text", "").strip()]

    total_a = len(qs1)
    total_b = len(qs2)

    if total_a == 0 or total_b == 0:
        return {
            "match_rate": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "total_a": total_a,
            "total_b": total_b,
            "matched_pairs": []
        }

    if not SKLEARN_AVAILABLE:
        # Fallback: simple token overlap matching with improved algorithm
        def _tok(text: str) -> set:
            return set(w.lower() for w in text.split() if len(w) > 2)
        
        # Collect all candidate matches
        candidates = []
        for i, t1 in enumerate(qs1):
            tokens1 = _tok(t1)
            for j, t2 in enumerate(qs2):
                tokens2 = _tok(t2)
                if tokens1 and tokens2:
                    sim = len(tokens1 & tokens2) / len(tokens1 | tokens2)
                    if sim >= 0.25:  # Lowered threshold to catch more matches
                        candidates.append((i, j, sim))
        
        # Sort by similarity (best first) and match greedily
        candidates.sort(key=lambda x: x[2], reverse=True)
        matched_pairs = []
        used_a = set()
        used_b = set()
        for i, j, sim in candidates:
            if i not in used_a and j not in used_b:
                # Calculate option similarity if both questions have options
                option_similarity = None
                q1_full = qs1_raw[i] if i < len(qs1_raw) else {}
                q2_full = qs2_raw[j] if j < len(qs2_raw) else {}
                opts1 = q1_full.get("options", [])
                opts2 = q2_full.get("options", [])
                
                if opts1 and opts2 and isinstance(opts1, list) and isinstance(opts2, list):
                    # Compare options using Jaccard similarity
                    opts1_set = set(str(o).lower().strip() for o in opts1)
                    opts2_set = set(str(o).lower().strip() for o in opts2)
                    if opts1_set or opts2_set:
                        inter = len(opts1_set & opts2_set)
                        union = len(opts1_set | opts2_set)
                        option_similarity = inter / union if union > 0 else 0.0
                
                match_entry = {
                    "a_index": i,
                    "b_index": j,
                    "score": round(sim, 3),
                    "option_similarity": round(option_similarity, 3) if option_similarity is not None else None
                }
                matched_pairs.append(match_entry)
                used_a.add(i)
                used_b.add(j)
    else:
        # Use TF-IDF cosine similarity matrix to greedily match
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vectorizer = TfidfVectorizer(lowercase=True, stop_words=None, ngram_range=(1, 2), min_df=1, max_df=1.0)
            tfidf = vectorizer.fit_transform(qs1 + qs2)
            a_mat = tfidf[0:total_a]
            b_mat = tfidf[total_a:total_a + total_b]
            sim_matrix = cosine_similarity(a_mat, b_mat)
            matched_pairs = []
            used_a = set()
            used_b = set()
            
            # Collect all potential matches above threshold
            candidates = []
            for i in range(total_a):
                for j in range(total_b):
                    score = float(sim_matrix[i, j])
                    if score >= 0.25:  # Lowered threshold to catch more matches
                        candidates.append((i, j, score))
            
            # Sort by similarity score (highest first) - ensures best matches are made first
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            # Greedy matching from best matches first
            for i, j, score in candidates:
                if i not in used_a and j not in used_b:
                    # Calculate option similarity if both questions have options
                    option_similarity = None
                    q1_full = qs1_raw[i] if i < len(qs1_raw) else {}
                    q2_full = qs2_raw[j] if j < len(qs2_raw) else {}
                    opts1 = q1_full.get("options", [])
                    opts2 = q2_full.get("options", [])
                    
                    if opts1 and opts2 and isinstance(opts1, list) and isinstance(opts2, list):
                        # Compare options using Jaccard similarity
                        opts1_set = set(str(o).lower().strip() for o in opts1)
                        opts2_set = set(str(o).lower().strip() for o in opts2)
                        if opts1_set or opts2_set:
                            inter = len(opts1_set & opts2_set)
                            union = len(opts1_set | opts2_set)
                            option_similarity = inter / union if union > 0 else 0.0
                    
                    match_entry = {
                        "a_index": i,
                        "b_index": j,
                        "score": round(score, 3),
                        "option_similarity": round(option_similarity, 3) if option_similarity is not None else None
                    }
                    matched_pairs.append(match_entry)
                    used_a.add(i)
                    used_b.add(j)
        except Exception:
            # Fallback to token method on any failure
            return _compute_question_match_stats({"questions": [{"text": t} for t in qs1]}, {"questions": [{"text": t} for t in qs2]})

    matches = len(matched_pairs)
    recall = matches / total_a if total_a else 0.0
    precision = matches / total_b if total_b else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    match_rate = matches / max(total_a, total_b)

    return {
        "match_rate": round(match_rate, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "total_a": total_a,
        "total_b": total_b,
        "matched_pairs": matched_pairs
    }


def _survey_to_rich_text(survey: Dict[str, Any]) -> str:
    """
    Convert survey to rich text representation for TF-IDF analysis.
    Includes title, description, metadata, sections, and questions.
    
    Args:
        survey: Survey JSON object
        
    Returns:
        str: Rich text representation
    """
    parts = []
    
    # Title and description
    if "title" in survey:
        parts.append(f"Title: {survey['title']}")
    
    if "description" in survey:
        parts.append(f"Description: {survey['description']}")
    
    # Metadata - methodology tags are important
    metadata = survey.get("metadata", {})
    if "methodology_tags" in metadata and metadata["methodology_tags"]:
        parts.append(f"Methodologies: {' '.join(metadata['methodology_tags'])}")
    
    if "industry_category" in metadata and metadata["industry_category"]:
        parts.append(f"Industry: {metadata['industry_category']}")
    
    # Extract all questions text
    all_questions = _extract_all_questions(survey)
    
    if survey.get("sections"):
        # New sections format
        for section in survey["sections"]:
            section_title = section.get("title", f"Section {section.get('id', '')}")
            parts.append(f"Section: {section_title}")
            
            if "description" in section:
                parts.append(f"Section Description: {section['description']}")
            
            for question in section.get("questions", []):
                qtext = question.get("text", "")
                qtype = question.get("type", "")
                if qtext:
                    parts.append(f"Question: {qtext}")
                if qtype:
                    parts.append(f"Type: {qtype}")
                if question.get("options"):
                    parts.append(f"Options: {' '.join(question['options'])}")
    elif survey.get("questions"):
        # Legacy format
        parts.append("Questions:")
        for question in survey["questions"]:
            qtext = question.get("text", "")
            qtype = question.get("type", "")
            if qtext:
                parts.append(f"Question: {qtext}")
            if qtype:
                parts.append(f"Type: {qtype}")
            if question.get("options"):
                parts.append(f"Options: {' '.join(question['options'])}")
    
    return " ".join(parts)


def _extract_all_questions(survey: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all questions from survey regardless of format."""
    if survey.get("sections"):
        all_questions = []
        for section in survey["sections"]:
            all_questions.extend(section.get("questions", []))
        return all_questions
    elif survey.get("questions"):
        return survey["questions"]
    return []


def _compute_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Compute TF-IDF cosine similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Cosine similarity score (0.0-1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    if text1 == text2:
        return 1.0
    
    if not SKLEARN_AVAILABLE:
        # Fallback to simple word overlap
        return _simple_word_similarity(text1, text2)
    
    try:
        # Lazy import sklearn here to avoid import-time scipy/numpy issues
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Create TF-IDF vectors with better defaults for short documents
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,  # Don't remove stop words for short text
            ngram_range=(1, 1),  # Just unigrams for now
            max_features=1000,  # Lower limit for small docs
            min_df=1,  # Allow all terms
            max_df=1.0,  # Allow all terms
            norm='l2'  # Use L2 normalization
        )
        
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return float(similarity)
        
    except Exception as e:
        logger.warning(f"TF-IDF failed, using fallback: {e}")
        return _simple_word_similarity(text1, text2)


def _simple_word_similarity(text1: str, text2: str) -> float:
    """
    Simple word-based similarity as fallback.
    Uses Jaccard similarity of word sets.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Jaccard similarity (0.0-1.0)
    """
    words1 = set(word.lower() for word in text1.split() if len(word) > 2)
    words2 = set(word.lower() for word in text2.split() if len(word) > 2)
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def _compare_structure(survey1: Dict[str, Any], survey2: Dict[str, Any]) -> float:
    """
    Compare structural similarity between two surveys.
    
    Factors:
    - Number of sections
    - Section IDs matching
    - Question types distribution
    - Number of questions per section
    
    Args:
        survey1: First survey
        survey2: Second survey
        
    Returns:
        float: Structural similarity (0.0-1.0)
    """
    # Check if both use sections format or legacy format
    has_sections1 = "sections" in survey1
    has_sections2 = "sections" in survey2
    
    # Different formats = different structure
    if has_sections1 != has_sections2:
        return 0.3  # Some similarity but different structure
    
    scores = []
    
    # Compare number of sections
    sections1 = survey1.get("sections", [])
    sections2 = survey2.get("sections", [])
    
    if sections1 and sections2:
        # Section count similarity
        count_diff = abs(len(sections1) - len(sections2))
        max_sections = max(len(sections1), len(sections2))
        if max_sections > 0:
            count_score = 1.0 - (count_diff / max_sections)
            scores.append(count_score)
        else:
            scores.append(0.0)
        
        # Section ID matching
        ids1 = {s.get("id") for s in sections1 if s.get("id") is not None}
        ids2 = {s.get("id") for s in sections2 if s.get("id") is not None}
        
        if ids1 and ids2:
            id_overlap = len(ids1.intersection(ids2))
            id_union = len(ids1.union(ids2))
            if id_union > 0:
                id_score = id_overlap / id_union
                scores.append(id_score)
        
        # Question type distribution
        qtypes1 = Counter(q.get("type", "") for s in sections1 for q in s.get("questions", []))
        qtypes2 = Counter(q.get("type", "") for s in sections2 for q in s.get("questions", []))
        
        if qtypes1 or qtypes2:
            type_similarity = _compare_distributions(qtypes1, qtypes2)
            scores.append(type_similarity)
    
    # Compare total question counts
    questions1 = _extract_all_questions(survey1)
    questions2 = _extract_all_questions(survey2)
    
    if questions1 or questions2:
        total1 = len(questions1)
        total2 = len(questions2)
        max_total = max(total1, total2)
        if max_total > 0:
            question_count_similarity = 1.0 - abs(total1 - total2) / max_total
            scores.append(question_count_similarity)
    
    # Average all structural scores
    if scores:
        return sum(scores) / len(scores)
    
    return 0.5  # Neutral if no structure to compare


def _compare_distributions(dist1: Counter, dist2: Counter) -> float:
    """
    Compare two distributions using Jaccard similarity.
    
    Args:
        dist1: First distribution as Counter
        dist2: Second distribution as Counter
        
    Returns:
        float: Similarity between 0.0 and 1.0
    """
    if not dist1 and not dist2:
        return 1.0
    if not dist1 or not dist2:
        return 0.0
    
    # All keys
    all_keys = set(dist1.keys()).union(set(dist2.keys()))
    
    if not all_keys:
        return 1.0
    
    # Normalized counts
    total1 = sum(dist1.values())
    total2 = sum(dist2.values())
    
    if total1 == 0 or total2 == 0:
        return 0.0
    
    # Compare normalized distributions
    differences = []
    for key in all_keys:
        val1 = dist1.get(key, 0) / total1
        val2 = dist2.get(key, 0) / total2
        differences.append(abs(val1 - val2))
    
    return 1.0 - (sum(differences) / len(all_keys))


def _compare_metadata(survey1: Dict[str, Any], survey2: Dict[str, Any]) -> float:
    """
    Compare metadata similarity between surveys.
    
    Factors:
    - Methodology tags overlap (Jaccard)
    - Industry category match
    - Research goal keywords
    
    Args:
        survey1: First survey
        survey2: Second survey
        
    Returns:
        float: Metadata similarity (0.0-1.0)
    """
    metadata1 = survey1.get("metadata", {})
    metadata2 = survey2.get("metadata", {})
    
    scores = []
    
    # Methodology tags similarity (Jaccard)
    # Note: Methodology tags are metadata labels - missing/incorrect tags shouldn't heavily penalize
    # If surveys are similar in content, methodology tags might just be wrong labels
    tags1 = set(metadata1.get("methodology_tags", []))
    tags2 = set(metadata2.get("methodology_tags", []))
    
    if tags1 or tags2:
        if not tags1 or not tags2:
            # One missing - give baseline score (tags are just metadata)
            methodology_score = 0.5
        else:
            intersection = len(tags1.intersection(tags2))
            union = len(tags1.union(tags2))
            if union > 0:
                jaccard = intersection / union
                # Map Jaccard to 0.5-1.0 range: no overlap = 0.5, full overlap = 1.0
                # This way methodology only boosts when it matches, doesn't heavily penalize when different
                methodology_score = 0.5 + (jaccard * 0.5)
            else:
                methodology_score = 0.5
        scores.append(methodology_score)
    
    # Industry category match
    industry1 = metadata1.get("industry_category")
    industry2 = metadata2.get("industry_category")
    
    if industry1 or industry2:
        if industry1 == industry2:
            industry_score = 1.0
        elif not industry1 or not industry2:
            industry_score = 0.5  # One missing
        else:
            industry_score = 0.0
        scores.append(industry_score)
    
    # Average metadata scores
    if scores:
        return sum(scores) / len(scores)
    
    return 0.5  # Neutral if no metadata


def _compare_content(survey1: Dict[str, Any], survey2: Dict[str, Any]) -> float:
    """
    Compare content similarity between questions.
    
    Factors:
    - Question text similarity (TF-IDF)
    - Question type matching
    - Option similarity
    
    Args:
        survey1: First survey
        survey2: Second survey
        
    Returns:
        float: Content similarity (0.0-1.0)
    """
    questions1 = _extract_all_questions(survey1)
    questions2 = _extract_all_questions(survey2)
    
    if not questions1 or not questions2:
        return 0.5  # Neutral if no questions
    
    # Combine all question texts
    texts1 = [q.get("text", "") for q in questions1]
    texts2 = [q.get("text", "") for q in questions2]
    
    combined_text1 = " ".join(texts1)
    combined_text2 = " ".join(texts2)
    
    # Use TF-IDF similarity on question texts
    if combined_text1 and combined_text2:
        content_similarity = _compute_tfidf_similarity(combined_text1, combined_text2)
    else:
        content_similarity = 0.0
    
    return content_similarity

