# Copyright project_phoenix

from charter_analyzer import CharterAnalyzer
from config import CHARTER_SECTIONS

def validate():
    analyzer = CharterAnalyzer()
    
    # 1. Positive Test: 3+ keywords AND 1+ indicator
    # Keywords: wiretap, warrant, privacy (3 keywords)
    # Indicator: violation
    test_text_positive = """
    The police conducted a wiretap on the suspect's phone without a warrant.
    This action violated their reasonable expectation of privacy.
    """
    
    results_pos = analyzer.analyze_document(test_text_positive)
    section_8_pos = next((b for b in results_pos["potential_breaches"] if b["section"] == "8"), None)
    
    if section_8_pos:
        print("PASS: Section 8 flagged in positive test (3+ keywords, 1+ indicator).")
    else:
        print("FAIL: Section 8 NOT flagged in positive test.")
        res = analyzer._analyze_section("8", CHARTER_SECTIONS["8"], test_text_positive)
        print(f"  Debug: keywords={len(res['matched_keywords'])}, indicators={len(res['breach_indicators'])}")

    # 2. Negative Test: 2 keywords, 1 indicator. Should NOT be flagged.
    # Keywords: wiretap, warrant (2 keywords)
    # Indicator: violation
    test_text_negative = "The police used a wiretap and a warrant. It was a violation."
    results_neg = analyzer.analyze_document(test_text_negative)
    
    section_8_neg = next((b for b in results_neg["potential_breaches"] if b["section"] == "8"), None)
    if not section_8_neg:
        print("PASS: Section 8 NOT flagged in negative test (2 keywords, 1 indicator).")
    else:
        print("FAIL: Section 8 flagged in negative test (should require 3+ keywords).")
        res = analyzer._analyze_section("8", CHARTER_SECTIONS["8"], test_text_negative)
        print(f"  Debug: keywords={len(res['matched_keywords'])}, indicators={len(res['breach_indicators'])}")

    # 3. Explicit Reference Test: 1 keyword, 0 indicators, but EXPLICIT reference. Should be flagged.
    test_text_explicit = "This relates to Section 8 of the Charter."
    results_exp = analyzer.analyze_document(test_text_explicit)
    section_8_exp = next((b for b in results_exp["potential_breaches"] if b["section"] == "8"), None)
    
    if section_8_exp:
        print("PASS: Section 8 flagged due to explicit reference.")
    else:
        print("FAIL: Section 8 NOT flagged despite explicit reference.")

if __name__ == "__main__":
    validate()
