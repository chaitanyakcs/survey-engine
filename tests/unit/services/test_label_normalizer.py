import pytest
from src.services.label_normalizer import LabelNormalizer


def test_normalize_abbreviations():
    normalizer = LabelNormalizer()
    
    assert normalizer.normalize("addl_demographics") == "Additional_Demographics"
    assert normalizer.normalize("adnl_demographics") == "Additional_Demographics"
    assert normalizer.normalize("demog_basic") == "Demographics_Basic"
    assert normalizer.normalize("coi_check") == "Conflict_Of_Interest_Check"


def test_normalize_separators():
    normalizer = LabelNormalizer()
    
    assert normalizer.normalize("brand-awareness") == "Brand_Awareness"
    assert normalizer.normalize("brand.awareness") == "Brand_Awareness"
    assert normalizer.normalize("brand awareness") == "Brand_Awareness"


def test_fuzzy_match():
    normalizer = LabelNormalizer()
    candidates = ["Additional_Demographics", "Basic_Demographics", "Category_Usage"]
    
    assert normalizer.fuzzy_match("addl_demog", candidates) == "Additional_Demographics"
    assert normalizer.fuzzy_match("adnl_demographics", candidates) == "Additional_Demographics"


def test_normalize_batch():
    normalizer = LabelNormalizer()
    labels = ["addl_demographics", "coi_check", "brand-awareness"]
    
    normalized = normalizer.normalize_batch(labels)
    assert normalized == ["Additional_Demographics", "Conflict_Of_Interest_Check", "Brand_Awareness"]


def test_normalize_edge_cases():
    normalizer = LabelNormalizer()
    
    # Test empty string
    assert normalizer.normalize("") == ""
    
    # Test single word
    assert normalizer.normalize("demographics") == "Demographics"
    
    # Test multiple underscores
    assert normalizer.normalize("addl___demographics") == "Additional_Demographics"
    
    # Test leading/trailing underscores
    assert normalizer.normalize("_addl_demographics_") == "Additional_Demographics"


def test_normalize_case_insensitive():
    normalizer = LabelNormalizer()
    
    assert normalizer.normalize("ADDL_DEMOGRAPHICS") == "Additional_Demographics"
    assert normalizer.normalize("Addl_Demographics") == "Additional_Demographics"
    assert normalizer.normalize("addl_DEMOGRAPHICS") == "Additional_Demographics"


def test_fuzzy_match_threshold():
    normalizer = LabelNormalizer()
    candidates = ["Additional_Demographics", "Basic_Demographics"]
    
    # Should match with high threshold
    assert normalizer.fuzzy_match("addl_demog", candidates, threshold=0.8) == "Additional_Demographics"
    
    # Should not match with very high threshold
    assert normalizer.fuzzy_match("completely_different", candidates, threshold=0.9) == "Completely_Different"

