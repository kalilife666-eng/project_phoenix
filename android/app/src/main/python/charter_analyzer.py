# Copyright project_phoenix
"""
project_phoenix Charter Breach Analysis Engine
Analyzes legal documents for potential Canadian Charter of Rights and Freedoms breaches.
"""

import os
import re
import subprocess
import tempfile
from difflib import SequenceMatcher
from config import (
    CHARTER_SECTIONS, OAKES_TEST, CONFIDENCE_THRESHOLDS,
    MIN_KEYWORD_MATCH, FOCUS_CHARTER_SECTIONS, SPECIFIC_FLAGS
)
from canlii_client import CanLIIClient, CriminalLawNotebookClient
from legal_dictionary import LEGAL_DICTIONARY
from literal_dictionary import LITERAL_DICTIONARY

SECTION_LEGAL_FRAMEWORKS = {
    "7": {
        "governing_test": "Section 7 asks whether state action deprived the person of life, liberty, or security of the person, and if so whether the deprivation occurred contrary to the principles of fundamental justice.",
        "authorities": [
            "Re B.C. Motor Vehicle Act, [1985] 2 SCR 486",
            "R v Morgentaler, [1988] 1 SCR 30",
            "Canada (AG) v Bedford, 2013 SCC 72",
            "Carter v Canada (AG), 2015 SCC 5",
        ],
    },
    "8": {
        "governing_test": "Section 8 asks whether there was a state search or seizure, whether the claimant had a reasonable expectation of privacy, and whether the search or seizure was authorized by law, reasonable, and carried out reasonably.",
        "authorities": [
            "Hunter v Southam Inc, [1984] 2 SCR 145",
            "R v Collins, [1987] 1 SCR 265",
            "R v Grant, 2009 SCC 32",
            "R v Fearon, 2014 SCC 77",
        ],
    },
    "9": {
        "governing_test": "Section 9 asks whether the person was detained or imprisoned and, if so, whether that detention or imprisonment was arbitrary because it lacked lawful authority or objectively reasonable grounds.",
        "authorities": [
            "R v Grant, 2009 SCC 32",
            "R v Mann, 2004 SCC 52",
            "R v Storrey, [1990] 1 SCR 241",
            "R v Whitfield, [1970] SCR 46",
        ],
    },
    "10(a)": {
        "governing_test": "Section 10(a) requires that a detained or arrested person be informed promptly and clearly of the reasons for the detention or arrest.",
        "authorities": [
            "R v Manninen, [1987] 1 SCR 1233",
            "R v Evans, [1991] 1 SCR 869",
        ],
    },

    "11(a)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\binformed of (?:the )?offence\b", r"\bspecific offence\b", r"\bnature of the accusation\b"],
        "require_trigger": True,
    },
    "11(b)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\bdelay\b", r"\breasonable time\b", r"\btrial\b", r"\bjordan\b", r"\bpresumptive ceiling\b", r"\badjournment\b", r"\bstay of proceedings\b"],
        "require_trigger": True,
    },
    "11(d)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\bpresumption of innocence\b", r"\breverse onus\b", r"\bburden on accused\b", r"\bcrown burden\b", r"\bproof beyond a reasonable doubt\b", r"\bbeyond a reasonable doubt\b"],
        "require_trigger": True,
    },
    "10(b)": {
        "governing_test": "Section 10(b) requires immediate advice of the right to counsel and a real opportunity to exercise that right without delay, together with a duty on police to hold off questioning until implementation is complete unless the right is validly waived.",
        "authorities": [
            "R v Bartle, [1994] 3 SCR 173",
            "R v Prosper, [1994] 3 SCR 236",
            "R v Suberu, 2009 SCC 33",
            "R v Sinclair, 2010 SCC 35",
        ],
    },
    "15(1)": {
        "governing_test": "Section 15(1) asks whether the law or state action creates a distinction based on an enumerated or analogous ground and whether that distinction imposes disadvantage by perpetuating prejudice, stereotyping, or discriminatory enforcement.",
        "authorities": [
            "Andrews v Law Society of British Columbia, [1989] 1 SCR 143",
            "Quebec (AG) v A, 2013 SCC 5",
            "Fraser v Canada (AG), 2020 SCC 28",
            "R v Le, 2019 SCC 34",
        ],
    },
    "24": {
        "governing_test": "Section 24 requires an infringement or denial of a Charter right and then asks what remedy is appropriate and just, including exclusion of evidence where admission would bring the administration of justice into disrepute.",
        "authorities": [
            "R v Grant, 2009 SCC 32",
            "Vancouver (City) v Ward, 2010 SCC 27",
            "R v O'Connor, [1995] 4 SCR 411",
        ],
    },
}

BAD_FAITH_FRAMEWORK = {
    "charter_sources": [
        "Canadian Charter of Rights and Freedoms, ss. 7, 8, 9, 10, 15, 24",
        "R v Grant, 2009 SCC 32",
        "R v Storrey, [1990] 1 SCR 241",
        "R v Mann, 2004 SCC 52",
        "R v Le, 2019 SCC 34",
        "R v O'Connor, [1995] 4 SCR 411",
    ],
    "policing_sources": [
        "Ontario Community Safety and Policing Act, 2019, s. 1",
        "Ontario Community Safety and Policing Act, 2019, s. 3(1)(d)(ii)",
    ],
}

CROWN_CONDUCT_FRAMEWORK = {
    "sources": [
        "Canadian Charter of Rights and Freedoms, ss. 7, 11(d), 24",
        "Boucher v The Queen, [1955] SCR 16",
        "R v Stinchcombe, [1991] 3 SCR 326",
        "R v O'Connor, [1995] 4 SCR 411",
        "R v McNeil, 2009 SCC 3",
        "Krieger v Law Society of Alberta, 2002 SCC 65",
        "R v Babos, 2014 SCC 16",
    ],
}

MISCONDUCT_URLS = {
    "police": {
        "arrest": "https://criminalnotebook.ca/index.php?title=Arrest",
        "detention": "https://criminalnotebook.ca/index.php?title=Section_9_of_the_Charter",
        "search": "https://criminalnotebook.ca/index.php?title=Section_8_of_the_Charter",
        "charter_rights": "https://criminalnotebook.ca/index.php?title=Section_10_of_the_Charter",
        "equality": "https://criminalnotebook.ca/index.php?title=Section_15_of_the_Charter",
        "abuse_of_process": "https://criminalnotebook.ca/index.php?title=Abuse_of_Process",
        "ontario_policing": "https://www.ontario.ca/laws/statute/19c01",
    },
    "crown": {
        "disclosure": "https://criminalnotebook.ca/index.php?title=Disclosure",
        "abuse_of_process": "https://criminalnotebook.ca/index.php?title=Abuse_of_Process",
        "remedies": "https://criminalnotebook.ca/index.php?title=Charter_Remedies",
        "exclusion": "https://criminalnotebook.ca/index.php?title=Exclusion_of_Evidence_under_Section_24(2)",
        "stinchcombe_search": "https://www.canlii.org/en/search/#search[0][query]=Stinchcombe%20disclosure%20Crown",
        "babos_search": "https://www.canlii.org/en/search/#search[0][query]=Babos%20abuse%20of%20process%20Crown",
    },
}

HUMAN_RIGHTS_FRAMEWORK = {
    "sources": [
        {
            "layer": "UN",
            "title": "Universal Declaration of Human Rights",
            "url": "https://www.un.org/en/about-us/universal-declaration-of-human-rights",
        },
        {
            "layer": "UN",
            "title": "International Covenant on Civil and Political Rights",
            "url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights",
        },
        {
            "layer": "UN",
            "title": "Convention on the Rights of Persons with Disabilities",
            "url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-rights-persons-disabilities",
        },
        {
            "layer": "National",
            "title": "Canadian Human Rights Act",
            "url": "https://laws.justice.gc.ca/eng/acts/H-6/FullText.html",
        },
        {
            "layer": "Provincial",
            "title": "Ontario Human Rights Code",
            "url": "https://www.ontario.ca/laws/statute/90h19",
        },
    ],
    "cases": [
        {
            "title": "Moore v British Columbia (Education)",
            "citation": "2012 SCC 61",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Moore%20v%20British%20Columbia%20(Education)%202012%20SCC%2061",
        },
        {
            "title": "British Columbia (Public Service Employee Relations Commission) v BCGSEU",
            "citation": "[1999] 3 SCR 3 (Meiorin)",
            "url": "https://www.canlii.org/en/search/#search[0][query]=BCGSEU%20Meiorin%201999%20CanLII%20652",
        },
        {
            "title": "Peel Law Association v Pieters",
            "citation": "2013 ONCA 396",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Peel%20Law%20Association%20v%20Pieters%202013%20ONCA%20396",
        },
        {
            "title": "Quebec (Commission des droits de la personne et des droits de la jeunesse) v Bombardier Inc.",
            "citation": "2015 SCC 39",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Bombardier%202015%20SCC%2039%20human%20rights",
        },
        {
            "title": "British Columbia Human Rights Tribunal v Schrenk",
            "citation": "2017 SCC 62",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Schrenk%202017%20SCC%2062",
        },
        {
            "title": "Robichaud v Canada (Treasury Board)",
            "citation": "[1987] 2 SCR 84",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Robichaud%20v%20Canada%20Treasury%20Board%201987%20CanLII%2073",
        },
        {
            "title": "Janzen v Platy Enterprises Ltd.",
            "citation": "[1989] 1 SCR 1252",
            "url": "https://www.canlii.org/en/search/#search[0][query]=Janzen%20v%20Platy%20Enterprises%201989%20CanLII%2097",
        },
    ],
}

SECTION_TERM_GATES = {
    "2(a)": {
        "dictionary_terms": {"conscience"},
        "trigger_patterns": [r"\breligion\b", r"\breligious\b", r"\bfaith\b", r"\bworship\b", r"\bcreed\b", r"\bconscience\b"],
        "require_trigger": True,
    },
    "2(b)": {
        "dictionary_terms": {"expression"},
        "trigger_patterns": [r"\bexpression\b", r"\bspeech\b", r"\bpress\b", r"\bcensorship\b", r"\bprotest\b", r"\bdemonstration\b", r"\bmedia\b"],
        "require_trigger": True,
    },
    "2(c)": {
        "dictionary_terms": {"association"},
        "trigger_patterns": [r"\bassembly\b", r"\bgathering\b", r"\bprotest\b", r"\bmarch\b", r"\brally\b", r"\bpicket\b"],
        "require_trigger": True,
    },
    "2(d)": {
        "dictionary_terms": {"association"},
        "trigger_patterns": [r"\bassociation\b", r"\bunion\b", r"\bcollective bargaining\b", r"\bmembership\b", r"\borganization\b"],
        "require_trigger": True,
    },
    "7": {
        "dictionary_terms": {"arrest", "detention", "liberty", "security", "fundamental", "justice", "arbitrary"},
        "trigger_patterns": [r"\bdepriv(?:ed|ation)\b", r"\bliberty\b", r"\bsecurity of the person\b", r"\bfundamental justice\b"],
    },
    "8": {
        "dictionary_terms": {"search", "seizure", "warrant", "privacy", "evidence", "unreasonable", "photographic_corroboration", "crime_scene", "scene_nexus", "seized_material"},
        "trigger_patterns": [r"\bsearch(?:ed)?\b", r"\bseiz(?:e|ed|ure)\b", r"\bwarrant(?:less)?\b", r"\bprivacy\b"],
    },
    "9": {
        "dictionary_terms": {"arrest", "detention", "liberty", "arbitrary", "reasonable_grounds", "identification", "scene_nexus"},
        "trigger_patterns": [r"\barrest(?:ed)?\b", r"\bdetain(?:ed|ment)\b", r"\bimprison(?:ed|ment)\b", r"\barbitrary\b"],
    },
    "10(a)": {
        "dictionary_terms": {"arrest", "detention"},
        "trigger_patterns": [r"\breasons? for (?:arrest|detention)\b", r"\bnot informed\b", r"\bprompt(?:ly)?\b"],
        "require_trigger": True,
    },

    "11(a)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\binformed of (?:the )?offence\b", r"\bspecific offence\b", r"\bnature of the accusation\b"],
        "require_trigger": True,
    },
    "11(b)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\bdelay\b", r"\breasonable time\b", r"\btrial\b", r"\bjordan\b", r"\bpresumptive ceiling\b", r"\badjournment\b", r"\bstay of proceedings\b"],
        "require_trigger": True,
    },
    "11(d)": {
        "dictionary_terms": set(),
        "trigger_patterns": [r"\bpresumption of innocence\b", r"\breverse onus\b", r"\bburden on accused\b", r"\bcrown burden\b", r"\bproof beyond a reasonable doubt\b", r"\bbeyond a reasonable doubt\b"],
        "require_trigger": True,
    },
    "10(b)": {
        "dictionary_terms": {"arrest", "detention"},
        "trigger_patterns": [
            r"\bright to counsel\b",
            r"\bright to lawyer\b",
            r"\bdenied counsel\b",
            r"\brefused lawyer\b",
            r"\bno lawyer\b",
            r"\bduty counsel\b",
            r"\blegal aid\b",
            r"\baccess to lawyer\b",
            r"\bconsult(?:ation)? with (?:a )?lawyer\b",
        ],
        "require_trigger": True,
    },
    "11(c)": {
        "dictionary_terms": set(),
        "trigger_patterns": [
            r"\bcompelled witness\b",
            r"\bcompelled testimony\b",
            r"\btestify against (?:himself|herself|themselves|self)\b",
            r"\bself-incrimination\b",
        ],
        "require_trigger": True,
    },
    "15(1)": {
        "dictionary_terms": {"discrimination", "equality", "arbitrary"},
        "trigger_patterns": [r"\bdiscriminat", r"\bequality\b", r"\bprofil(?:e|ing)\b", r"\bbias\b", r"\brace\b", r"\bgender\b", r"\bfemale\b", r"\bmale\b", r"\bwoman\b", r"\bman\b", r"\bmental health\b", r"\banxiety\b", r"\bpanic\b"],
    },
    "24": {
        "dictionary_terms": {"remedy", "breach", "evidence"},
        "trigger_patterns": [
            r"\bremed(?:y|ies)\b",
            r"\b(?:section\s*)?24\s*\(\s*[12]\s*\)",
            r"\bs\.?\s*24\s*\(\s*[12]\s*\)",
            r"\bexclusion of evidence\b",
            r"\bstay of proceedings\b",
            r"\bdamages\b",
        ],
    },
}

TEST_INDICATORS = {
    "deprivation": [r"\bdepriv(?:ed|ation)\b", r"\barrest(?:ed)?\b", r"\bdetain(?:ed|ment)\b", r"\bcustody\b", r"\bimprison(?:ed|ment)\b"],
    "life_liberty_security": [r"\bliberty\b", r"\bsecurity of the person\b", r"\blife\b", r"\bbodily integrity\b"],
    "principles_of_fundamental_justice": [r"\bfundamental justice\b", r"\barbitrary\b", r"\boverbroad\b", r"\bgrossly disproportionate\b", r"\bvague(?:ness)?\b", r"\bunfair\b"],
    "fundamental_justice": [r"\bfundamental justice\b", r"\barbitrary\b", r"\boverbroad\b", r"\bgrossly disproportionate\b", r"\bvague(?:ness)?\b", r"\bunfair\b"],
    "arbitrariness": [r"\barbitrary\b", r"\bno objective grounds\b", r"\bno reasonable grounds\b", r"\bwithout reasonable grounds\b", r"\bwithout cause\b"],
    "overbreadth": [r"\boverbroad\b", r"\bbroader than necessary\b", r"\bsweeping\b"],
    "gross_disproportionality": [r"\bgrossly disproportionate\b", r"\bextreme\b", r"\bexcessive\b"],
    "procedural_fairness": [r"\bduty of fairness\b", r"\bnatural justice\b", r"\bunfair\b", r"\bbias\b", r"\bprocedural\b"],
    "vagueness": [
        r"\bvague\b",
        r"\buncertain\b",
        r"\bimprecise\b",
        r"\bnot clear\b",
        r"\bsuspected to be\b",
        r"\bappears to be\b",
        r"\bpossibly\b",
        r"\bunknown material\b",
        r"\binconsistent(?:ly)? described\b",
        r"\bcopper wire\b.{0,40}\bbell cable\b",
        r"\bbell cable\b.{0,40}\bcopper wire\b",
    ],
    "expectation_of_privacy": [r"\bprivacy\b", r"\bprivate\b", r"\breasonable expectation of privacy\b", r"\bcell phone\b", r"\bhome\b", r"\bcomputer\b"],
    "search_or_seizure": [r"\bsearch(?:ed)?\b", r"\bseiz(?:e|ed|ure)\b", r"\bentry\b", r"\bwarrant\b"],
    "reasonableness": [r"\bunreasonable\b", r"\bwarrantless\b", r"\bwithout warrant\b", r"\bno warrant\b"],
    "warrant_requirement": [r"\bwithout warrant\b", r"\bno warrant\b", r"\bwarrantless\b", r"\blacked warrant\b"],
    "scope": [r"\bstrip search\b", r"\bforced entry\b", r"\bexcessive\b", r"\boverbroad\b"],
    "is_detention": [r"\bdetain(?:ed|ment)\b", r"\barrest(?:ed)?\b", r"\bheld\b", r"\bstopp?ed\b", r"\bcustody\b"],
    "lawful_authority": [r"\bauthorized by law\b", r"\blawful authority\b", r"\bwarrant\b", r"\breasonable grounds\b"],
    "necessity": [r"\bnecessary\b", r"\bproportionate\b", r"\binvestigative detention\b"],
    "was_detained": [r"\bdetain(?:ed|ment)\b", r"\barrest(?:ed)?\b", r"\bcustody\b"],
    "right_imposed": [r"\bright to counsel\b", r"\bright to lawyer\b", r"\blawyer\b", r"\bcounsel\b"],
    "without_delay": [r"\bwithout delay\b", r"\bprompt(?:ly)?\b", r"\bdelayed\b", r"\bnot informed promptly\b"],
    "implementation": [r"\btelephone\b", r"\bduty counsel\b", r"\blegal aid\b", r"\bconsult(?:ation)?\b"],
    "waiver": [r"\bwaiver\b", r"\bwaived\b"],
    "prompt_informing": [r"\bprompt(?:ly)?\b", r"\bnot informed\b", r"\breasons\b"],
    "clarity": [r"\bunderstand\b", r"\bclear(?:ly)?\b", r"\bexplained\b"],
    "enumerated_ground": [r"\brace\b", r"\bethnic\b", r"\bcolour\b", r"\breligion\b", r"\bsex\b", r"\bgender\b", r"\bage\b", r"\bdisabilit"],
    "analogous_ground": [r"\bcitizenship\b", r"\bsexual orientation\b", r"\bmarital status\b"],
    "distinction": [r"\bdiscriminat", r"\bdifferential treatment\b", r"\bprofil(?:e|ing)\b"],
    "discriminatory_effect": [r"\bprejudice\b", r"\bstereotyp", r"\bprofil(?:e|ing)\b", r"\bbias\b", r"\btargeted\b"],
}


def _find_pattern_matches(text, patterns, limit=5):
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found = match.group(0).strip()
            if found and found.lower() not in {m.lower() for m in matches}:
                matches.append(found)
            if len(matches) >= limit:
                return matches
    return matches


def _test_is_supported(test_result):
    return test_result.get("status") == "potential_issue" or bool(test_result.get("identified_issues"))


def _section_is_dictionary_anchored(section_id, text, dictionary_matches, explicit_reference_count=0, grounds_assessment=""):
    gate = SECTION_TERM_GATES.get(section_id)
    if not gate:
        return False
    if explicit_reference_count > 0:
        return True
    if grounds_assessment and section_id in {"7", "9"}:
        return True
    if section_id == "15(1)":
        if grounds_assessment and _has_identity_markers(text):
            return True
        matched_terms = {match["term"] for match in dictionary_matches}
        equality_terms = bool(matched_terms & {"discrimination", "equality"})
        discrimination_signals = bool(_match_any_patterns(text, [
            r"\bdiscriminat",
            r"\bequality\b",
            r"\bprofil(?:e|ing)\b",
            r"\bbias\b",
        ]))
        return equality_terms or discrimination_signals or _has_identity_markers(text)

    matched_terms = {match["term"] for match in dictionary_matches}
    has_dictionary_anchor = bool(matched_terms & gate["dictionary_terms"])
    has_trigger = False

    for pattern in gate["trigger_patterns"]:
        if re.search(pattern, text, re.IGNORECASE):
            has_trigger = True
            break

    if gate.get("require_trigger"):
        return has_trigger

    return has_dictionary_anchor or has_trigger


def _identity_marker_hits(text):
    text_lower = (text or "").lower()
    hits = set()

    explicit_ground_patterns = {
        "race": [r"\brace\b", r"\bracial\b", r"\bindigenous\b"],
        "ancestry / ethnic origin / place of origin": [r"\bethnic\b", r"\bancestry\b", r"\bplace of origin\b", r"\bcitizenship\b"],
        "creed / religion": [r"\breligion\b", r"\bcreed\b", r"\bfaith\b"],
        "disability": [r"\bdisabilit", r"\bmental health\b", r"\billness\b", r"\bmedical\b", r"\banxiety\b", r"\bpanic\b"],
        "age": [r"\bage\b", r"\byouth\b", r"\belderly\b"],
        "family / marital status": [r"\bfamily status\b", r"\bmarital status\b"],
        "sex / gender": [r"\bgender\b", r"\bsex\b"],
    }
    for ground, patterns in explicit_ground_patterns.items():
        if _match_any_patterns(text, patterns):
            hits.add(ground)

    color_clothing_patterns = [
        r"\b(?:black|white)\s+(?:hoodie|jacket|coat|shirt|sweater|pants|trousers|jeans|shorts|dress|skirt|hat|cap|mask|gloves?|shoes?|boots?|clothes?|clothing|uniform)\b",
        r"\b(?:wearing|wore|dressed(?:\s+in)?)\b.{0,20}\b(?:black|white)\b",
        r"\b(?:hoodie|jacket|coat|shirt|sweater|pants|trousers|jeans|shorts|dress|skirt|hat|cap|mask|gloves?|shoes?|boots?|clothes?|clothing|uniform)\b.{0,20}\b(?:black|white)\b",
    ]
    color_person_patterns = [
        r"\b(?:black|white)\s+(?:man|woman|male|female|person|people|individual|suspect|accused|driver|passenger|youth)\b",
        r"\b(?:man|woman|male|female|person|people|individual|suspect|accused|driver|passenger|youth)\b.{0,20}\b(?:black|white)\b",
    ]
    if (
        _match_any_patterns(text, color_person_patterns)
        and not _match_any_patterns(text, color_clothing_patterns)
    ):
        hits.add("race")

    gender_context_patterns = [
        r"\b(?:because|due to|target(?:ed)?|profil(?:e|ing)|bias|stereotyp|discriminat)\b.{0,30}\b(?:woman|man|female|male)\b",
        r"\b(?:woman|man|female|male)\b.{0,30}\b(?:because|due to|target(?:ed)?|profil(?:e|ing)|bias|stereotyp|discriminat)\b",
    ]
    if _match_any_patterns(text, gender_context_patterns):
        hits.add("sex / gender")

    return hits


def _has_identity_markers(text):
    return bool(_identity_marker_hits(text))


def _build_section_legal_articulation(section_id, text, grounds_assessment, applicable_tests, breach_indicators):
    framework = SECTION_LEGAL_FRAMEWORKS.get(section_id)
    if not framework:
        return None

    supported_tests = [test_id for test_id, result in applicable_tests.items() if _test_is_supported(result)]
    indicator_types = {indicator["type"] for indicator in breach_indicators}
    text_lower = text.lower()

    conclusions = []
    if section_id == "7":
        if grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment:
            conclusions.append("Express finding: deprivation of liberty is indicated and the deprivation appears arbitrary, engaging Section 7 through the principles of fundamental justice.")
        elif {"deprivation", "arbitrariness"} & set(supported_tests):
            conclusions.append("Express finding: the facts indicate a deprivation of liberty or security of the person and a live arbitrariness/fundamental justice issue under Section 7.")
    elif section_id == "8":
        if {"without warrant", "no warrant", "warrantless", "searched without"} & indicator_types:
            conclusions.append("Express finding: an unlawful search or seizure is indicated because the text alleges state searching or seizing activity without warrant authority.")
        elif {"search_or_seizure", "expectation_of_privacy", "reasonableness"} <= set(supported_tests) or "search_or_seizure" in supported_tests:
            conclusions.append("Express finding: a Section 8 issue is expressly raised because the document describes a state search or seizure affecting a privacy interest and questions its reasonableness.")
    elif section_id == "9":
        if grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment:
            conclusions.append("Express finding: arbitrary arrest or detention is indicated because the document points to detention without objectively reasonable grounds.")
        elif "is_detention" in supported_tests and ("arbitrariness" in supported_tests or "arbitrary" in indicator_types):
            conclusions.append("Express finding: the facts expressly indicate detention or imprisonment and support a Section 9 arbitrariness analysis.")
    elif section_id == "10(a)":
        if "not informed" in indicator_types or {"was_detained", "prompt_informing"} <= set(supported_tests):
            conclusions.append("Express finding: Section 10(a) is engaged because the document raises whether the detainee was told promptly and clearly why they were being detained or arrested.")
    elif section_id == "10(b)":
        if {"denied counsel", "no lawyer", "refused lawyer"} & indicator_types or "right_imposed" in supported_tests:
            conclusions.append("Express finding: Section 10(b) is engaged because the text raises delay, denial, or non-implementation of the right to counsel.")
    elif section_id == "15(1)":
        identity_markers = _has_identity_markers(text_lower)
        if identity_markers and (grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment):
            conclusions.append("Express finding: the combination of identity-based markers and an apparent lack of objective grounds supports an express Section 15 discriminatory enforcement concern.")
        elif "distinction" in supported_tests and "discriminatory_effect" in supported_tests:
            conclusions.append("Express finding: the document raises both a distinction and a discriminatory effect, which is the core Section 15 inquiry.")
    elif section_id == "24":
        if "infringement" in supported_tests or any(i in indicator_types for i in {"violation", "infringement", "breach"}):
            conclusions.append("Express finding: Charter remedies are live because the document alleges an infringement or denial and raises exclusionary or other remedial consequences.")

    if not conclusions:
        return None

    return {
        "governing_test": framework["governing_test"],
        "authorities": framework["authorities"],
        "conclusion": " ".join(conclusions),
    }


def _match_any_patterns(text, patterns):
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            snippet = match.group(0).strip()
            if snippet and snippet.lower() not in {f.lower() for f in found}:
                found.append(snippet)
    return found


def _has_oakes_justification_context(text):
    """Detect whether the record expressly raises a Section 1 justification context."""
    justification_context_patterns = [
        r"\bsection 1\b",
        r"\bs\.?\s*1\b",
        r"\boakes\b",
        r"\bprescribed by law\b",
        r"\blegislation\b",
        r"\bstatute\b",
        r"\bregulation\b",
        r"\bby-?law\b",
        r"\bpolicy\b",
        r"\bobjective\b",
        r"\bpressing and substantial\b",
        r"\bminimal impairment\b",
        r"\bproportionality\b",
        r"\breasonable limits\b",
    ]

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in justification_context_patterns)


def _generate_recommendations(results):
    """Generate actionable recommendations based on the analysis."""
    recommendations = []

    # Charter recommendations
    for breach in results["potential_breaches"]:
        section = breach["section"]

        if breach["confidence_level"] in ["HIGH", "MEDIUM"]:
            recommendations.append(
                f"[PRIORITY] Charter Section {section} ({breach['title']}): "
                f"Strong indicators of potential breach found. Review the applicable legal tests "
                f"and cross-reference with CanLII authorities."
            )

            # Add test-specific recommendations
            for test_id, test_data in breach.get("applicable_tests", {}).items():
                if test_data["status"] == "potential_issue":
                    recommendations.append(
                        f"  → {section} Test '{test_data['question']}': "
                        f"Issues identified — {', '.join(test_data['identified_issues'][:3])}. "
                        f"Examine evidence carefully for this element."
                    )

        elif breach["confidence_level"] == "LOW":
            recommendations.append(
                f"[REVIEW] Charter Section {section} ({breach['title']}): "
                f"Some indicators present but low confidence. Further factual investigation recommended."
            )

    # Cross-reference recommendations
    for section, refs in results["cross_references"].get("canlii", {}).items():
        if not refs.get("search_results", {}).get("api_configured", True):
            recommendations.append(
                f"[RESEARCH] Section {section}: CanLII API not configured. "
                f"Use the generated search URLs to find supporting case law."
            )

    for section, refs in results["cross_references"].get("criminallawnotebook", {}).items():
        if refs.get("direct_reference"):
            recommendations.append(
                f"[REFERENCE] Section {section}: Criminal Law Notebook reference available — "
                f"review for procedural guidance and case summaries."
            )

    # Dictionary-based recommendations
    for match in results.get("dictionary_matches", []):
        if match["legal_category"] == "constitutional":
            recommendations.append(
                f"[TERM] '{match['matched_as']}' is a constitutional concept. "
                f"Dictionary meaning: {match['legal_definition']}"
            )
        elif match["term"] == "arrest" and any(b["section"] == "9" for b in results["potential_breaches"]):
            recommendations.append(
                f"[LEGAL MEANING] Arrest detected. Under Whitfield (SCC), this requires intention, grounds, "
                f"and notification. Compare this against the provided facts."
            )

    # Specific Case Law Articulation
    if results.get("officer_conduct_assessment"):
        conduct = results["officer_conduct_assessment"]
        if conduct["seriousness"] == "HIGH":
            recommendations.append(
                "[LEGAL ARGUMENT] ABUSIVE STATE CONDUCT: Failure to account for physical impossibilities or manifest factual contradictions mirrors the 'willful blindness' doctrine in R v Briscoe, 2010 SCC 13. This may support a stay of proceedings for Abuse of Process (R v O'Connor)."
            )

    grounds_ass = next((b["description"] for b in results["potential_breaches"] if "GROUNDS ASSESSMENT" in b["description"]), "")
    if "NO OBJECTIVE GROUNDS" in grounds_ass:
        recommendations.append(
            "[LEGAL ARGUMENT] ARBITRARY ARREST: Per R v Storrey, [1990] 1 SCR 241, an arrest is only lawful if the officer has subjectively and objectively reasonable grounds. The absence of primary evidence and the lack of an observed criminal act renders the arrest objectively unreasonable."
        )
    for remedy in results["remedies"]:
        if remedy["type"] == "s24(2)":
            recommendations.append(
                "[REMEDY] If evidence was obtained in breach of Charter rights, apply R v Grant "
                "(2009 SCC 26) three-factor test for exclusion under s.24(2)."
            )
        elif remedy["type"] == "stay":
            recommendations.append(
                "[REMEDY] Consider a stay of proceedings application if delay or abuse of process is established."
            )
        elif remedy["type"] == "damages":
            recommendations.append(
                "[REMEDY] Consider a claim for constitutional damages under the R v Ward framework."
            )

    # Oakes recommendation
    if results["oakes_analysis"] and results["oakes_analysis"]["justification_likely"] is not True:
        recommendations.append(
            "[SECTION 1] The Crown may face difficulty justifying the breach under Section 1. "
            "Focus on minimal impairment and proportionality arguments."
        )

    # Officer Conduct recommendations
    if results.get("officer_conduct_assessment"):
        assessment = results["officer_conduct_assessment"]
        recommendations.append(
            f"[CONDUCT] {assessment['seriousness']} level of state misconduct identified: "
            f"{assessment['legal_basis']}. Consider an Abuse of Process application."
        )

    party_data = results.get("party_narratives", {})
    parties = party_data.get("parties", [])
    if parties:
        recommendations.append(
            f"[PARTIES] Extracted {len(parties)} named/identified parties with role classification and verbatim narrative statements. "
            f"Use these statement excerpts to fact-check exactly who says what happened."
        )
    routing = party_data.get("version_routing", {})
    if routing.get("recommended_version"):
        recommendations.append(
            f"[ROUTING] Suggested version: {routing.get('recommended_version')} — {routing.get('reason', '')}"
        )

    if not recommendations:
        recommendations.append(
            "No specific concerns identified. The document does not appear to raise "
            "significant Charter issues, though this does not constitute legal advice."
        )

    return recommendations


def _generate_overall_assessment(results):
    """
    Generate an assessment that leads with SCC-preferred literal 'Ordinary Meanings'
    before cross-referencing with Charter law and constitutional principles.
    """
    assessment_parts = []

    # Lead with SCC Ordinary Meaning analysis (Literal Dictionary)
    matches = results.get("dictionary_matches", [])
    if matches:
        terms_str = ", ".join([m["matched_as"] for m in matches[:3]])
        assessment_parts.append(
            f"The scan first analyzed the document using the 'Ordinary Meaning' standard preferred by the Supreme Court of Canada. "
            f"Literal English references to {terms_str} were identified. "
        )

        # Highlighting a specific transition from literal to legal
        m = matches[0]
        assessment_parts.append(
            f"For example, the term '{m['matched_as']}' is defined literally as '{m['literal_definition']}' ({m['literal_source']}). "
            f"When cross-referenced with the Charter, this ordinary event takes on {m['legal_category'].replace('_', ' ')} significance."
        )

    # Charter analysis
    breach_count = len(results["potential_breaches"])
    if breach_count > 0:
        sections = ", ".join([b["section"] for b in results["potential_breaches"]])
        assessment_parts.append(
            f"\n\nCONSTITUTIONAL CROSS-REFERENCE: These events implicate {breach_count} potential Charter breach(es) "
            f"under Section(s) {sections}."
        )

        high_confidence = [b for b in results["potential_breaches"] if b["confidence_level"] == "HIGH"]
        if high_confidence:
            assessment_parts.append(
                f" The law requires high-level scrutiny here, particularly for Section(s): {', '.join([b['section'] for b in high_confidence])}."
            )

    # Officer Conduct
    if results.get("officer_conduct_assessment"):
        assessment_parts.append(
            f"\n\nSTATE CONDUCT ASSESSMENT: {results['officer_conduct_assessment']['assessment']}"
        )

    # Oakes / Justification context
    if results.get("oakes_analysis") and results["oakes_analysis"]["justification_likely"] is False:
        assessment_parts.append(
            "\n\nJUSTIFICATION ANALYSIS: Applying the SCC's Oakes Test, these literal infringements "
            "do not currently appear to be saved as 'reasonable limits' under Section 1."
        )

    return " ".join(assessment_parts)


def _identify_remedies(text, breaches):
    """Identify potential Charter remedies based on the analysis."""
    remedies = []
    text_lower = text.lower()

    # Section 24(1) — General remedial authority
    if any(re.findall(r's\.?\s*24\s*\(\s*1\s*\)', text, re.IGNORECASE)):
        remedies.append({
            "type": "s24(1)",
            "description": "Section 24(1) — General Charter Remedy",
            "options": [
                "Stay of proceedings",
                "Exclusion of evidence",
                "Damages",
                "Declaratory relief",
                "Mandamus",
                "Injunction",
            ],
            "relevant": True,
        })

    # Section 24(2) — Exclusion of evidence
    if any(keyword in text_lower for keyword in [
        "exclusion", "exclude", "s. 24(2)", "s24(2)", "illegally obtained",
        "obtained in breach", "admissibility", "bring the administration"
    ]):
        remedies.append({
            "type": "s24(2)",
            "description": "Section 24(2) — Exclusion of Evidence",
            "grant_test": [
                "1. Would admission bring the administration of justice into disrepute?",
                "2. Society's confidence in the rule of law (R v Grant, 2009 SCC 26)",
                "3. Three factors from Grant:",
                "   a. Seriousness of the Charter-infringing conduct (state conduct)",
                "   b. Impact on the accused's Charter-protected interests",
                "   c. Society's interest in adjudication on the merits",
            ],
            "relevant": True,
        })

    # Stay of proceedings
    if any(keyword in text_lower for keyword in [
        "stay of proceedings", "judicial stay", "abuse of process",
        "delay", "jordan", "unreasonable delay"
    ]):
        remedies.append({
            "type": "stay",
            "description": "Stay of Proceedings",
            "grounds": [
                "Section 11(b) — Right to be tried within a reasonable time (R v Jordan, 2016 SCC 27)",
                "Abuse of process",
                "Section 7 — Principles of fundamental justice",
            ],
            "relevant": True,
        })

    # Damages
    if any(keyword in text_lower for keyword in [
        "damages", "constitutional damages", "s. 24(1) damages",
        "compensation", "monetary remedy"
    ]):
        remedies.append({
            "type": "damages",
            "description": "Constitutional Damages (R v Ward, 2010 SCC 27)",
            "principles": [
                "Effective judicial remedy requires damages",
                "No other effective remedy available",
                "Should represent a meaningful remedy",
                "Not punitive in nature (generally)",
            ],
            "relevant": True,
        })

    # If breaches were found but no explicit remedy discussion, add default
    if breaches and not remedies:
        remedies.append({
            "type": "general",
            "description": "General Charter Remedies (Section 24)",
            "options": [
                "Section 24(1) — Appropriate and just remedy",
                "Section 24(2) — Exclusion of evidence (if evidence obtained in breach)",
                "Stay of proceedings (for 11(b) or abuse of process)",
                "Damages (in egregious cases — R v Ward framework)",
            ],
            "relevant": True,
        })

    return remedies


def _analyze_oakes(text, breaches):
    """
    Perform Section 1 Oakes test analysis.
    """
    oakes = OAKES_TEST["1"]
    has_justification_context = _has_oakes_justification_context(text)
    results = {
        "title": oakes["title"],
        "description": oakes["description"],
        "steps": {},
        "breaches_requiring_justification": [b["section"] for b in breaches],
        "justification_likely": False,
        "analysis_summary": "",
        "applicable": has_justification_context,
    }

    text_lower = text.lower()

    for step_id, step_data in oakes["steps"].items():
        step_result = {
            "question": step_data["question"],
            "sub_questions": {},
            "evidence_found": False,
            "analysis": "",
            "satisfied": None,
        }

        sub_questions = step_data["sub_questions"]
        if isinstance(sub_questions, list):
            sq_items = list(enumerate(sub_questions))
        else:
            sq_items = list(sub_questions.items())

        for sq_id, sq_text in sq_items:
            sq_result = {
                "question": sq_text,
                "indicators_found": [],
                "assessment": "",
            }

            # Look for justification language
            justification_patterns = {
                "step1": ["prescribed by law", "enacted", "regulation", "statute", "legislation"],
                "step2": ["pressing and substantial", "important objective", "compelling", "urgent",
                         "public interest", "safety", "security"],
                "step3": ["rational connection", "rational", "carefully designed", "logical",
                         "proportionate means", "means-ends"],
                "step4": ["minimal impairment", "minimally impair", "least intrusive", "no lesser alternative",
                         "narrowly tailored", "tailored", "proportionate"],
                "step5": ["proportionality", "proportionate", "salutary effects", "deleterious effects",
                         "outweigh", "benefits outweigh", "costs and benefits"],
            }

            for key, patterns in justification_patterns.items():
                if key in step_id:
                    for p in patterns:
                        if p in text_lower:
                            sq_result["indicators_found"].append(p)

            if sq_result["indicators_found"]:
                sq_result["assessment"] = "Document contains language suggesting this element may be addressed."
                step_result["evidence_found"] = True
            else:
                sq_result["assessment"] = "No explicit language found addressing this element."

            step_result["sub_questions"][str(sq_id)] = sq_result

        # Set the step analysis
        if step_result["evidence_found"]:
            step_result["analysis"] = "Some indicators present. Further review recommended."
        else:
            if has_justification_context:
                step_result["analysis"] = "No justification indicators found. The Crown may face difficulty meeting this burden."
            else:
                step_result["analysis"] = "Test run for completeness. No Section 1 justification context is expressly raised on the current text."

        results["steps"][step_id] = step_result

    # Overall Oakes assessment
    steps_with_evidence = sum(1 for s in results["steps"].values() if s["evidence_found"])
    total_steps = len(results["steps"])

    if steps_with_evidence == total_steps and has_justification_context:
        results["justification_likely"] = True
        results["analysis_summary"] = (
            "Document contains indicators for all Oakes test steps. "
            "Section 1 justification may be arguable, though the strength of evidence should be evaluated."
        )
    elif steps_with_evidence >= 3 and has_justification_context:
        results["justification_likely"] = None  # Uncertain
        results["analysis_summary"] = (
            "Document contains indicators for some but not all Oakes test steps. "
            "Section 1 justification is uncertain. Particular attention should be paid to "
            "minimal impairment and proportionality analysis."
        )
    else:
        results["justification_likely"] = False
        if has_justification_context:
            results["analysis_summary"] = (
                "Document contains insufficient indicators for Section 1 justification. "
                "The Crown would likely face significant difficulty justifying the Charter infringement."
            )
        else:
            results["analysis_summary"] = (
                "Oakes test run for completeness. The present text does not expressly raise a Section 1 "
                "justification theory, so the result is best read as 'not supported on this record' rather than "
                "'affirmatively justified'."
            )

    return results


def _evaluate_tests(section_id, tests, text):
    """
    Evaluate the legal tests for a Charter section against the document.
    Returns identified issues and concerns for each test element.
    """
    results = {}
    section_framework = SECTION_LEGAL_FRAMEWORKS.get(section_id, {})

    for test_id, test_question in tests.items():
        test_result = {
            "test_id": test_id,
            "question": test_question,
            "identified_issues": [],
            "analysis": "",
            "authorities": section_framework.get("authorities", []),
            "status": "unexamined",
        }

        found_indicators = _find_pattern_matches(text, TEST_INDICATORS.get(test_id, []))

        if found_indicators:
            test_result["status"] = "potential_issue"
            test_result["identified_issues"] = found_indicators
            test_result["analysis"] = (
                f"Expressly engaged. The document contains factual language relevant to this element: "
                f"{', '.join(found_indicators[:4])}."
            )
        else:
            test_result["status"] = "no_indicators_found"
            test_result["analysis"] = (
                "Not expressly supported on the current text. This element requires direct facts or "
                "clear legal articulation in the record."
            )

        results[test_id] = test_result

    return results


def _find_breach_indicators(text, section_id):
    """
    Find language that suggests a Charter breach may have occurred.
    """
    indicators = []

    # General breach indicators
    breach_patterns = [
        ("violation", r'\bviolation\b'),
        ("infringement", r'\binfring(?:ed|ement|ing)\b'),
        ("breach", r'\bbreach\b'),
        ("unreasonable", r'\bunreasonable\b'),
        ("arbitrary", r'\barbitrary\b'),
        ("unconstitutional", r'\bunconstitutional\b'),
        ("unlawful", r'\bunlawful\b'),
        ("without warrant", r'\bwithout\s+(?:a\s+)?warrant\b'),
        ("no warrant", r'\bno\s+warrant\b'),
        ("warrantless", r'\bwarrantless\b'),
        ("forced entry", r'\bforced\s+entry\b'),
        ("kicked in", r'\bkicked\s+in\b'),
        ("without consent", r'\bwithout\s+consent\b'),
        ("searched without", r'\bsearched\s+without\b'),
        ("without cause", r'\bwithout\s+(?:just|probable|reasonable)\s+cause\b'),
        ("without reasonable grounds", r'\bwithout\s+reasonable\s+grounds\b'),
        ("denied", r'\bdenied\b'),
        ("denied counsel", r'\bdenied\s+counsel\b'),
        ("no lawyer", r'\bno\s+lawyer\b'),
        ("refused lawyer", r'\brefused\s+lawyer\b'),
        ("not informed", r'\bnot\s+informed\b'),
        ("failure to inform", r'\bfailure\s+to\s+inform\b'),
        ("excessive", r'\bexcessive\b'),
        ("disproportionate", r'\bdisproportionate\b'),
        ("overbroad", r'\boverbroad\b'),
        ("grossly disproportionate", r'\bgrossly\s+disproportionate\b'),
        ("not advised", r'\bnot\s+advised\b'),
        ("not permitted", r'\bnot\s+permitted\b'),
        ("right violated", r'\bright(?:s)?\s+violate(?:d|s)?\b'),
        ("contrary to", r'\bcontrary\s+to\b'),
        ("failed to", r'\bfailed\s+to\b'),
        ("failure to", r'\bfailure\s+to\b'),
        ("no reasonable grounds", r'\bno\s+reasonable\s+grounds\b'),
        ("lack of disclosure", r'\black\s+(?:of\s+)?disclosure\b'),
        ("delay", r'\b(?:unreasonable\s+)?delay\b'),
        ("coerced", r'\bcoerced?\b'),
        ("compelled", r'\bcompelled?\b'),
    ]

    for label, pattern in breach_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            indicators.append({
                "type": label,
                "count": len(matches),
            })

    return indicators


def _find_charter_references(text):
    """Find explicit Charter section references in the document."""
    references = []
    text_lower = text.lower()

    # Direct section references
    patterns = [
        (r'(?:s(?:ection)?\.?\s*)(\d+(?:\([a-z0-9]+\))?)\s+(?:of\s+)?(?:the\s+)?(?:charter|canadian\s+charter)\b', "explicit"),
        (r'(?:charter|canadian\s+charter)\s+(?:s(?:ection)?\.?\s*)(\d+(?:\([a-z0-9]+\))?)', "explicit"),
        (r'(?:s\.?\s*)(\d+(?:\([a-z0-9]+\))?)\s+(?:of\s+)?(?:the\s+)?(?:charter)\b', "explicit"),
    ]

    seen = set()
    for pattern, ref_type in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            section = match.group(1)
            if section not in seen:
                seen.add(section)
                references.append({
                    "section": section,
                    "context": match.group(0),
                    "type": ref_type,
                })

    # Also check for sections that match our CHARTER_SECTIONS keys
    for section_id in CHARTER_SECTIONS.keys():
        if section_id in text_lower or f"section {section_id}" in text_lower:
            if section_id not in seen:
                seen.add(section_id)
                references.append({
                    "section": section_id,
                    "context": f"section {section_id}",
                    "type": "implicit",
                })

    return references


class CharterAnalyzer:
    """Analyze legal documents for Charter breaches."""

    def __init__(self, canlii_api_key=None, ai_params=None):
        self.canlii = CanLIIClient(canlii_api_key)
        self.cln = CriminalLawNotebookClient()
        
        if ai_params:
            self.ai = AIIntegration(
                api_key=ai_params.get("api_key"),
                model=ai_params.get("model", "gpt-4"),
                provider=ai_params.get("provider", "openai"),
                initial_history=ai_params.get("history")
            )
        else:
            self.ai = None

    def analyze_document(self, text):
        """
        Perform a comprehensive Charter breach analysis on the document.
        
        Args:
            text: The legal document text
            
        Returns:
            dict: Complete analysis results
        """
        dictionary_matches = self._cross_reference_dictionary(text)
        results = {
            "potential_breaches": [],
            "charter_sections_referenced": _find_charter_references(text),
            "oakes_analysis": None,
            "remedies": [],
            "dictionary_matches": dictionary_matches,
            "specific_flags": self._check_specific_flags(text),
            "cross_references": {
                "canlii": {},
                "criminallawnotebook": {},
            },
            "party_narratives": {},
            "overall_assessment": "",
            "recommendations": []
        }

        # Step 1: Analyze each Charter section for potential breaches
        for section_id, section_data in CHARTER_SECTIONS.items():
            # Filter based on user-requested focus sections
            if FOCUS_CHARTER_SECTIONS and section_id not in FOCUS_CHARTER_SECTIONS:
                continue

            breach_result = self._analyze_section(section_id, section_data, text, dictionary_matches)
            if breach_result["flagged"]:
                results["potential_breaches"].append(breach_result)

        # Enforce liberty nexus policy: arbitrary detention/imprisonment (s.9) implies
        # high-priority deprivation-of-liberty analysis under s.7.
        self._enforce_s7_s9_liberty_priority(results["potential_breaches"])
        self._enforce_s15_arbitrary_equality_priority(results["potential_breaches"])

        # Step 2: Run Oakes for completeness whenever breaches exist, but record applicability accurately.
        if results["potential_breaches"]:
            results["oakes_analysis"] = _analyze_oakes(text, results["potential_breaches"])

        # Step 3: Identify potential remedies
        results["remedies"] = _identify_remedies(text, results["potential_breaches"])

        # Step 4: Cross-reference with CanLII
        for breach in results["potential_breaches"]:
            section = breach["section"]
            canlii_results = self.canlii.search_charter_breach_cases(
                section, breach.get("matched_keywords", [])[:3]
            )
            results["cross_references"]["canlii"][section] = {
                "search_results": canlii_results,
                "search_urls": canlii_results.get("search_urls", {}),
                "cln_reference": self.cln.get_charter_section_reference(section),
            }

        # Step 5: Cross-reference with Criminal Law Notebook
        for breach in results["potential_breaches"]:
            section = breach["section"]
            cln_results = self.cln.search_topics(f"section {section} charter")
            results["cross_references"]["criminallawnotebook"][section] = {
                "direct_reference": self.cln.get_charter_section_reference(section),
                "related_topics": cln_results,
                "exclusion_reference": self.cln.get_exclusion_reference() if any(
                    r.get("type") == "exclusion" for r in results["remedies"]
                ) else None,
            }

        # Step 6: Analyze Charter breach interactions
        results["breach_interactions"] = self._analyze_breach_interactions(results["potential_breaches"], text=text)

        # Step 7: Analyze Officer Conduct (Willful Blindness/Negligence)
        results["officer_conduct_assessment"] = self._analyze_officer_conduct(text, results["potential_breaches"])
        results["bad_faith_assessment"] = self._detect_bad_faith_policing(
            text,
            results["potential_breaches"],
            results["officer_conduct_assessment"],
        )
        results["crown_conduct_assessment"] = self._assess_crown_conduct(
            text,
            results["potential_breaches"],
            results["bad_faith_assessment"],
        )
        results["police_misconduct_indicators"] = self._build_police_misconduct_indicators(
            results["potential_breaches"],
            results["officer_conduct_assessment"],
            results["bad_faith_assessment"],
        )
        results["prosecutorial_misconduct_indicators"] = self._build_prosecutorial_misconduct_indicators(
            results["crown_conduct_assessment"]
        )
        results["human_rights_assessment"] = self._assess_human_rights_code(text, results["potential_breaches"])
        results["party_narratives"] = self._extract_party_narratives(text)

        # Step 8: Overall assessment and recommendations
        results["overall_assessment"] = _generate_overall_assessment(results)
        results["recommendations"] = _generate_recommendations(results)

        # Step 7: AI Verification (Optional)
        if self.ai and self.ai.is_configured():
            ai_verify = self.ai.verify_charter_analysis(results, text)
            if not ai_verify.get("error"):
                results["ai_verification"] = ai_verify.get("content")

        return results

    def analyze_human_rights_code(self, text, include_charter_context=True):
        """
        Public helper: analyze raw text against UN/national/provincial human-rights frameworks.

        Args:
            text: Input text to analyze.
            include_charter_context: If True, derives supporting Charter breach signals first.

        Returns:
            dict: {
                "human_rights_assessment": ...,
                "supporting_breaches": [...],
                "charter_sections_referenced": [...]
            }
        """
        safe_text = text if isinstance(text, str) else ""
        supporting_breaches = []

        if include_charter_context and safe_text.strip():
            for section_id, section_data in CHARTER_SECTIONS.items():
                if FOCUS_CHARTER_SECTIONS and section_id not in FOCUS_CHARTER_SECTIONS:
                    continue
                breach_result = self._analyze_section(section_id, section_data, safe_text, [])
                if breach_result.get("flagged"):
                    supporting_breaches.append(breach_result)

            # Keep the same liberty-priority policy used in full analysis.
            self._enforce_s7_s9_liberty_priority(supporting_breaches)

        assessment = self._assess_human_rights_code(safe_text, supporting_breaches)
        return {
            "human_rights_assessment": assessment,
            "supporting_breaches": supporting_breaches,
            "charter_sections_referenced": _find_charter_references(safe_text),
        }

    def _enforce_s7_s9_liberty_priority(self, breaches):
        section_map = {b.get("section"): b for b in breaches}
        s9 = section_map.get("9")
        if not s9:
            return

        policy_note = (
            "PRIORITY RULE: Arbitrary detention/imprisonment (s.9) is treated as a deprivation of liberty "
            "engaging s.7 principles of fundamental justice."
        )

        for sec in ("9", "7"):
            b = section_map.get(sec)
            if not b:
                continue
            b["flagged"] = True
            b["confidence"] = max(float(b.get("confidence", 0) or 0), 0.9)
            b["confidence_level"] = "HIGH"
            desc = b.get("description", "")
            if policy_note not in desc:
                b["description"] = f"{desc}\n\n{policy_note}".strip()

        if "7" not in section_map and "7" in CHARTER_SECTIONS:
            s7 = CHARTER_SECTIONS["7"]
            breaches.append({
                "section": "7",
                "title": s7.get("title", "Life, Liberty and Security of the Person"),
                "description": f"{s7.get('description', '')}\n\n{policy_note}".strip(),
                "flagged": True,
                "confidence": 0.9,
                "confidence_level": "HIGH",
                "matched_keywords": [{"keyword": "liberty nexus (s.9 -> s.7)", "count": 1}],
                "breach_indicators": [{"type": "arbitrary", "count": 1}],
                "explicit_references": 0,
                "applicable_tests": {},
                "legal_articulation": None,
                "dictionary_anchored": True,
                "direct_relevance": True,
            })

    def _enforce_s15_arbitrary_equality_priority(self, breaches):
        """
        Equality-rights policy: if arbitrary detention/imprisonment (s.9) is flagged
        at high priority, promote s.15(1) concern to high priority as a default
        equal-protection safeguard in state-enforcement contexts.
        """
        section_map = {b.get("section"): b for b in breaches}
        s9 = section_map.get("9")
        s15 = section_map.get("15(1)")
        if not s9 or not s15:
            return
        if not s9.get("flagged"):
            return

        s15["flagged"] = True
        s15["confidence"] = max(float(s15.get("confidence", 0) or 0), 0.9)
        s15["confidence_level"] = "HIGH"
        policy_note = (
            "EQUALITY PRIORITY RULE: Where arbitrary detention/imprisonment indicators are present, "
            "s.15(1) is treated as high-priority because unequal and arbitrary enforcement "
            "is incompatible with a free and democratic society."
        )
        desc = s15.get("description", "")
        if policy_note not in desc:
            s15["description"] = f"{desc}\n\n{policy_note}".strip()

    def _extract_party_narratives(self, text):
        """
        Extract likely parties (names), their roles, and exact narrative statements.
        Returns structured data suitable for role-aware routing and UI display.
        """
        sentences = [
            s.strip() for s in re.split(r'(?<=[\.\?!])\s+|\n+', text) if s.strip()
        ]
        role_patterns = {
            "accused": [r"\baccused\b", r"\bdefendant\b"],
            "applicant": [r"\bapplicant\b", r"\bclaimant\b", r"\bpetitioner\b"],
            "respondent": [r"\brespondent\b"],
            "complainant": [r"\bcomplainant\b"],
            "witness": [r"\bwitness\b", r"\beyewitness\b", r"\binformant\b"],
            "officer": [r"\bofficer\b", r"\bconstable\b", r"\bdetective\b", r"\bsergeant\b", r"\bpolice\b"],
            "crown": [r"\bcrown\b", r"\bprosecut(?:or|ion)\b", r"\bcrown counsel\b"],
            "defence_counsel": [r"\bdefen[cs]e counsel\b", r"\bdefen[cs]e lawyer\b", r"\bcounsel for the accused\b"],
            "judge": [r"\bjustice\b", r"\bjudge\b", r"\bcourt\b"],
        }
        statement_verbs = [
            r"\bsaid\b", r"\bstated\b", r"\bsays\b", r"\balleg(?:e|ed|es)\b",
            r"\bclaim(?:s|ed)?\b", r"\breport(?:s|ed)?\b", r"\btestif(?:y|ied|ies)\b",
            r"\bindicat(?:e|ed|es)\b", r"\bnot(?:e|ed|es)\b", r"\bobserv(?:e|ed|es)\b",
            r"\bassert(?:s|ed)?\b", r"\bwrote\b",
        ]
        name_pattern = re.compile(
            r"\b(?:Mr|Ms|Mrs|Dr|Constable|Detective|Sgt|Sergeant|Officer)\.?\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2}\b"
            r"|\b[A-Z][A-Za-z'\-]+,\s*[A-Z][A-Za-z'\-]+\b"
            r"|\b[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,2}\b"
        )
        stop_names = {
            "Canadian Charter", "Charter Rights", "Supreme Court", "Criminal Code",
            "Crown Counsel", "project_phoenix", "Human Rights", "Section", "The Crown",
        }

        parties = {}
        unnamed_counters = {}

        def _normalize_name(name):
            cleaned = re.sub(r"\s+", " ", (name or "").strip(" ,.;:()[]{}\"'"))
            cleaned = re.sub(
                r"^(?:Witness|Accused|Defendant|Applicant|Respondent|Complainant|Officer|Constable|Detective|Sergeant|Sgt)\s+",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            return cleaned

        def _is_name_like(name):
            if not name:
                return False
            if name in stop_names:
                return False
            if len(name) < 3 or len(name) > 80:
                return False
            return True

        def _add_party(name, role, sentence):
            key = name or f"UNNAMED_{role}"
            if key not in parties:
                parties[key] = {
                    "name": name or key,
                    "roles": set(),
                    "what_they_say_happened": [],
                    "source_sentences": [],
                }
            parties[key]["roles"].add(role)
            if sentence and sentence not in parties[key]["source_sentences"]:
                parties[key]["source_sentences"].append(sentence)

        # Case caption extraction (best available explicit naming signal)
        criminal_caption = re.search(
            r"\bR\.?\s*v\.?\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})", text
        )
        civil_caption = re.search(
            r"\b([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})\s+v\.?\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})",
            text
        )
        case_caption = ""
        if criminal_caption:
            accused_name = _normalize_name(criminal_caption.group(1))
            if _is_name_like(accused_name):
                _add_party(accused_name, "accused", "")
                case_caption = f"R v {accused_name}"
        elif civil_caption:
            p1 = _normalize_name(civil_caption.group(1))
            p2 = _normalize_name(civil_caption.group(2))
            if _is_name_like(p1):
                _add_party(p1, "applicant", "")
            if _is_name_like(p2):
                _add_party(p2, "respondent", "")
            if _is_name_like(p1) and _is_name_like(p2):
                case_caption = f"{p1} v {p2}"

        for sentence in sentences:
            matched_roles = []
            for role, patterns in role_patterns.items():
                if any(re.search(p, sentence, re.IGNORECASE) for p in patterns):
                    matched_roles.append(role)
            if not matched_roles:
                continue

            raw_names = [_normalize_name(n) for n in name_pattern.findall(sentence)]
            names = [n for n in raw_names if _is_name_like(n)]

            # If no explicit name, keep role-bound unnamed party so narrative isn't lost.
            if not names:
                for role in matched_roles:
                    unnamed_counters[role] = unnamed_counters.get(role, 0) + 1
                    names.append(f"UNNAMED {role.upper()} {unnamed_counters[role]}")

            has_statement_verb = any(re.search(v, sentence, re.IGNORECASE) for v in statement_verbs)
            has_quote = '"' in sentence or "'" in sentence

            for role in matched_roles:
                for name in names:
                    _add_party(name, role, sentence)
                    if has_statement_verb or has_quote:
                        entry = parties[name]
                        if sentence not in entry["what_they_say_happened"]:
                            entry["what_they_say_happened"].append(sentence)

        role_priority = {
            "accused": 1,
            "applicant": 2,
            "respondent": 3,
            "complainant": 4,
            "witness": 5,
            "officer": 6,
            "crown": 7,
            "defence_counsel": 8,
            "judge": 9,
        }
        party_list = []
        for name, info in parties.items():
            roles_sorted = sorted(info["roles"], key=lambda r: role_priority.get(r, 99))
            primary_role = roles_sorted[0] if roles_sorted else "unknown"
            party_list.append({
                "name": info["name"],
                "primary_role": primary_role,
                "roles": roles_sorted,
                "what_they_say_happened": info["what_they_say_happened"][:25],
                "source_sentences": info["source_sentences"][:40],
                "statement_count": len(info["what_they_say_happened"]),
            })

        party_list.sort(key=lambda p: (-p["statement_count"], role_priority.get(p["primary_role"], 99), p["name"]))

        has_law_license_signals = any(
            any(role in p["roles"] for role in ("crown", "defence_counsel"))
            for p in party_list
        )
        has_public_party_signals = any(
            any(role in p["roles"] for role in ("accused", "applicant", "respondent", "complainant", "witness"))
            for p in party_list
        )
        if has_law_license_signals:
            recommended_version = "licensed_professional"
            route_reason = "Detected counsel/prosecution role signals in the record."
        elif has_public_party_signals:
            recommended_version = "public_self_represented"
            route_reason = "Detected accused/party/witness role signals without clear licensed-counsel signals."
        else:
            recommended_version = "undetermined"
            route_reason = "Could not confidently determine user role from current text."

        return {
            "case_caption": case_caption,
            "parties": party_list,
            "version_routing": {
                "recommended_version": recommended_version,
                "reason": route_reason,
            },
        }

    def _coerce_media_errors(self, extra_media_errors):
        if not extra_media_errors:
            return []
        if isinstance(extra_media_errors, (str, bytes)):
            text = str(extra_media_errors).strip()
            return [text] if text else []

        try:
            return [str(item).strip() for item in extra_media_errors if str(item).strip()]
        except TypeError:
            pass

        to_array = getattr(extra_media_errors, "toArray", None)
        if callable(to_array):
            try:
                return [str(item).strip() for item in to_array() if str(item).strip()]
            except Exception:
                pass

        size = getattr(extra_media_errors, "size", None)
        get = getattr(extra_media_errors, "get", None)
        if callable(size) and callable(get):
            try:
                items = []
                for index in range(size()):
                    text = str(get(index)).strip()
                    if text:
                        items.append(text)
                return items
            except Exception:
                pass

        text = str(extra_media_errors).strip()
        return [text] if text else []

    def analyze_av_against_witness(
        self,
        witness_statement_text,
        video_path=None,
        audio_path=None,
        transcript_text=None,
        extra_media_errors=None,
    ):
        """
        Analyze A/V evidence against a supporting statement.
        - Extracts audio from media (if ffmpeg available)
        - Attempts best-effort transcription
        - Compares witness claims with A/V transcript for matches/contradictions
        """
        witness_statement_text = (witness_statement_text or "").strip()
        transcript_text = (transcript_text or "").strip()
        use_manual_transcript = bool(transcript_text)

        media_info = {"video": None, "audio": None}
        media_errors = self._coerce_media_errors(extra_media_errors)
        gathered_transcripts = []
        transcription_runs = []

        if video_path:
            if not os.path.exists(video_path):
                media_errors.append(f"Video file not found: {video_path}")
            elif use_manual_transcript:
                media_info["video"] = {"path": video_path, "metadata_skipped": "Manual transcript override supplied."}
                transcription_runs.append({
                    "source_type": "video",
                    "path": video_path,
                    "engine": "manual_transcript_override",
                    "quality_score": None,
                    "word_count": len(transcript_text.split()),
                    "segment_count": 0,
                })
            else:
                media_info["video"] = self._probe_media(video_path)
                t = self._transcribe_media_file(video_path, source_type="video")
                transcription_runs.append({
                    "source_type": "video",
                    "path": video_path,
                    "engine": t.get("engine"),
                    "quality_score": t.get("quality_score"),
                    "word_count": t.get("word_count", 0),
                    "segment_count": t.get("segment_count", 0),
                })
                if t.get("text"):
                    gathered_transcripts.append(t["text"])
                if t.get("errors"):
                    media_errors.extend(t["errors"])

        if audio_path:
            if not os.path.exists(audio_path):
                media_errors.append(f"Audio file not found: {audio_path}")
            elif use_manual_transcript:
                media_info["audio"] = {"path": audio_path, "metadata_skipped": "Manual transcript override supplied."}
                transcription_runs.append({
                    "source_type": "audio",
                    "path": audio_path,
                    "engine": "manual_transcript_override",
                    "quality_score": None,
                    "word_count": len(transcript_text.split()),
                    "segment_count": 0,
                })
            else:
                media_info["audio"] = self._probe_media(audio_path)
                t = self._transcribe_media_file(audio_path, source_type="audio")
                transcription_runs.append({
                    "source_type": "audio",
                    "path": audio_path,
                    "engine": t.get("engine"),
                    "quality_score": t.get("quality_score"),
                    "word_count": t.get("word_count", 0),
                    "segment_count": t.get("segment_count", 0),
                })
                if t.get("text"):
                    gathered_transcripts.append(t["text"])
                if t.get("errors"):
                    media_errors.extend(t["errors"])

        if transcript_text:
            gathered_transcripts.append(transcript_text)

        av_transcript = "\n".join(s for s in gathered_transcripts if s.strip()).strip()
        comparison = self._compare_witness_to_transcript(witness_statement_text, av_transcript)
        perjury_risk = self._assess_perjury_risk(witness_statement_text, av_transcript, comparison)
        evidence_conflict = {
            "conflict_detected": bool(comparison.get("contradictions")),
            "conflict_count": len(comparison.get("contradictions", [])),
            "consistency_score": comparison.get("consistency_score", 0.0),
            "summary": comparison.get("summary", ""),
        }

        return {
            "witness_statement_text": witness_statement_text,
            "av_transcript_text": av_transcript,
            "media_info": media_info,
            "media_errors": media_errors,
            "transcription_runs": transcription_runs,
            "comparison": comparison,
            "evidence_conflict_assessment": evidence_conflict,
            "perjury_risk_indicators": perjury_risk,
        }

    def _probe_media(self, media_path):
        """Return lightweight media metadata via ffprobe when available."""
        try:
            proc = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration,bit_rate:stream=index,codec_type,codec_name,width,height,sample_rate,channels",
                    "-of", "default=noprint_wrappers=1",
                    media_path,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                return {"path": media_path, "metadata_error": proc.stderr.strip() or "ffprobe failed"}
            return {"path": media_path, "ffprobe": proc.stdout.strip()}
        except Exception as e:
            return {"path": media_path, "metadata_error": str(e)}

    def _transcribe_media_file(self, media_path, source_type="audio"):
        """
        Best-effort transcription pipeline:
        1) Extract mono WAV with ffmpeg
        2) Try offline ASR engines if installed (faster-whisper, whisper)
        """
        errors = []
        transcript = ""
        engine_used = None
        temp_wav = None
        segment_count = 0
        quality_score = 0.0
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_wav = tmp.name

            ffmpeg_variants = [
                [
                    "ffmpeg", "-y",
                    "-i", media_path,
                    "-vn",
                    "-af", "highpass=f=120,lowpass=f=3800,afftdn=nf=-25",
                    "-ac", "1",
                    "-ar", "16000",
                    temp_wav,
                ],
                [
                    "ffmpeg", "-y",
                    "-i", media_path,
                    "-vn",
                    "-af", "highpass=f=120,lowpass=f=3800",
                    "-ac", "1",
                    "-ar", "16000",
                    temp_wav,
                ],
            ]
            extracted = False
            for ffmpeg_cmd in ffmpeg_variants:
                proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=False)
                if proc.returncode == 0:
                    extracted = True
                    break
                errors.append(f"ffmpeg extraction failed ({'enhanced' if '-af' in ffmpeg_cmd else 'plain'}): {proc.stderr.strip()[:240]}")
            if not extracted:
                return {"text": "", "engine": None, "errors": errors, "source_type": source_type, "quality_score": 0.0}

            try:
                from faster_whisper import WhisperModel  # type: ignore

                # Upgrading to "small" for better accuracy than "base"
                # If memory is an issue on Android, stick with "base" or "tiny"
                model_size = "small" 
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                
                segments, _ = model.transcribe(
                    temp_wav,
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    temperature=0.0,
                )
                parts = []
                logprobs = []
                for seg in segments:
                    text_part = (seg.text or "").strip()
                    if text_part:
                        parts.append(text_part)
                    avg_logprob = getattr(seg, "avg_logprob", None)
                    if isinstance(avg_logprob, (int, float)):
                        logprobs.append(avg_logprob)
                transcript = " ".join(parts).strip()
                transcript = self._polish_transcript(transcript)
                segment_count = len(parts)
                if transcript:
                    engine_used = "faster-whisper(base)"
                    wc = len(re.findall(r"[a-z0-9']+", transcript.lower()))
                    lp_component = 0.0
                    if logprobs:
                        avg_lp = sum(logprobs) / len(logprobs)
                        lp_component = min(max((avg_lp + 2.0) / 2.0, 0.0), 1.0)
                    length_component = min(wc / 120.0, 1.0)
                    quality_score = round((0.55 * lp_component) + (0.45 * length_component), 3)
            except Exception as e:
                errors.append(f"faster-whisper unavailable/failed: {e}")

            if not transcript:
                try:
                    import whisper  # type: ignore

                    model = whisper.load_model("base")
                    out = model.transcribe(temp_wav, fp16=False)
                    transcript = (out.get("text") or "").strip()
                    if transcript:
                        engine_used = "openai-whisper(base)"
                        segment_count = len(re.split(r'(?<=[\.\?!])\s+', transcript))
                        wc = len(re.findall(r"[a-z0-9']+", transcript.lower()))
                        quality_score = round(min(wc / 140.0, 1.0), 3)
                except Exception as e:
                    errors.append(f"openai-whisper unavailable/failed: {e}")
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except OSError:
                    pass

        if not transcript:
            errors.append(
                "No transcript produced. Install faster-whisper/whisper or provide transcript_text manually."
            )

        return {
            "text": transcript,
            "engine": engine_used,
            "errors": errors,
            "source_type": source_type,
            "segment_count": segment_count,
            "word_count": len(re.findall(r"[a-z0-9']+", transcript.lower())),
            "quality_score": quality_score,
        }

    
    def _polish_transcript(self, text):
        if not text:
            return ''
        
        corrections = {
            r'\battention\b': 'detention',
            r'\bsection seven\b': 'Section 7',
            r'\bsection eight\b': 'Section 8',
            r'\bsection nine\b': 'Section 9',
            r'\bcharter reach\b': 'Charter breach',
            r'\bright to council\b': 'right to counsel',
            r'\bsees your\b': 'seizure',
            r'\barrested\b.*\bincident\b': 'arrested incident to arrest',
            r'\boaks test\b': 'Oakes test',
            r'\bjordan ceiling\b': 'Jordan ceiling',
            r'\bdue process\b': 'fundamental justice',
        }
        
        polished = text
        for pattern, replacement in corrections.items():
            polished = re.sub(pattern, replacement, polished, flags=re.IGNORECASE)
            
        return polished

    def _compare_witness_to_transcript(self, witness_text, transcript_text):
        """Claim-level witness-vs-transcript comparison with contradiction flags."""
        def split_claims(text):
            base = [s.strip() for s in re.split(r'(?<=[\.\?!])\s+|\n+', text or "") if s.strip()]
            claims = []
            for sentence in base:
                chunks = [c.strip(" ,;") for c in re.split(r"\b(?:and|but|while|whereas)\b|;", sentence, flags=re.IGNORECASE) if c.strip()]
                claims.extend(chunks if len(chunks) > 1 else [sentence])
            return claims

        def normalize_recording_language(text):
            normalized = (text or "").lower()
            replacements = [
                (r"\bon video\b|\bon camera\b|\bon film\b", " recorded "),
                (r"\bvideo(?:taped|taping)?\b|\bfilmed\b|\bfilm(?:ing)?\b|\btaped\b", " recorded "),
                (r"\bcaptured\b.{0,12}\b(?:video|camera|film)\b", " recorded "),
                (r"\bmic(?:'?d)?\s+up\b|\baudio(?:\s+recorded)?\b", " recorded "),
            ]
            for pattern, replacement in replacements:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            return re.sub(r"\s+", " ", normalized).strip()

        def tokenize(text):
            return [t for t in re.findall(r"[a-z0-9']+", normalize_recording_language(text)) if t]

        def has_negation(text):
            return bool(re.search(r"\b(no|not|never|none|without|didn't|did not|can't|cannot|won't|wasn't|weren't)\b", text.lower()))

        def recording_awareness_state(text):
            lowered = normalize_recording_language(text)
            if not lowered:
                return None

            recording_terms = r"(?:record(?:ed|ing)?|video|camera|taped)"
            unaware_patterns = [
                rf"\b(?:unaware|not aware|wasn't aware|were not aware|did(?: not|n't) know|no idea|did(?: not|n't) realize)\b.{{0,40}}\b{recording_terms}\b",
                rf"\b{recording_terms}\b.{{0,40}}\b(?:without my knowledge|unknown to me|without our knowledge)\b",
                rf"\b(?:without my knowledge|unknown to me|without our knowledge)\b.{{0,40}}\b{recording_terms}\b",
            ]
            aware_patterns = [
                rf"\b(?:i|we)\s+(?:like|liked|love|loved|enjoy|enjoyed|prefer|preferred)\s+being\s+(?:recorded|taped)\b",
                rf"\b(?:knew|know|aware|was aware|were aware)\b.{{0,30}}\b{recording_terms}\b",
                rf"\b{recording_terms}\b.{{0,30}}\b(?:knew|know|aware|was aware|were aware)\b",
                rf"\b(?:consent(?:ed)?|agree(?:d)?|okay|ok|fine|comfortable)\b.{{0,30}}\b(?:to\s+)?(?:being\s+)?(?:recorded|taped)\b",
                rf"\b{recording_terms}\b.{{0,30}}\b(?:consent(?:ed)?|agree(?:d)?|okay|ok|fine|comfortable)\b",
            ]

            if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in unaware_patterns):
                return "unaware"
            if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in aware_patterns):
                return "aware"
            return None

        def has_conflict_pair(a, b):
            pairs = [
                ("inside", "outside"),
                ("daylight", "night"),
                ("day", "night"),
                ("morning", "evening"),
                ("before", "after"),
                ("arrived", "left"),
                ("upstairs", "downstairs"),
                ("front", "back"),
            ]
            al = a.lower()
            bl = b.lower()
            flags = []
            for left, right in pairs:
                if ((re.search(rf"\b{left}\b", al) and re.search(rf"\b{right}\b", bl))
                        or (re.search(rf"\b{right}\b", al) and re.search(rf"\b{left}\b", bl))):
                    flags.append(f"{left}_vs_{right}")
            awareness_a = recording_awareness_state(a)
            awareness_b = recording_awareness_state(b)
            if awareness_a and awareness_b and awareness_a != awareness_b:
                flags.append("recording_awareness_mismatch")
            return flags

        witness_sentences = split_claims(witness_text)
        transcript_sentences = split_claims(transcript_text)
        transcript_awareness_overall = recording_awareness_state(transcript_text)
        matches = []
        contradictions = []
        unverified = []
        matched_transcript_idx = set()

        for ws in witness_sentences:
            witness_awareness = recording_awareness_state(ws)
            if witness_awareness:
                if transcript_awareness_overall and transcript_awareness_overall != witness_awareness:
                    contradictions.append({
                        "witness_sentence": ws,
                        "transcript_sentence": transcript_text.strip(),
                        "similarity_score": round(SequenceMatcher(None, normalize_recording_language(ws), normalize_recording_language(transcript_text)).ratio(), 3),
                        "conflict_flags": ["recording_awareness_mismatch"],
                        "certainty": "high",
                    })
                    matched_transcript_idx.update(range(len(transcript_sentences)))
                    continue
                awareness_candidates = []
                for i, ts in enumerate(transcript_sentences):
                    transcript_awareness = recording_awareness_state(ts)
                    if transcript_awareness and transcript_awareness != witness_awareness:
                        awareness_candidates.append((
                            SequenceMatcher(None, normalize_recording_language(ws), normalize_recording_language(ts)).ratio(),
                            i,
                            ts,
                        ))
                if awareness_candidates:
                    _, best_idx, best_sentence = max(awareness_candidates, key=lambda item: item[0])
                    matched_transcript_idx.add(best_idx)
                    contradictions.append({
                        "witness_sentence": ws,
                        "transcript_sentence": best_sentence,
                        "similarity_score": round(SequenceMatcher(None, normalize_recording_language(ws), normalize_recording_language(best_sentence)).ratio(), 3),
                        "conflict_flags": ["recording_awareness_mismatch"],
                        "certainty": "high",
                    })
                    continue

            wtok = set(tokenize(ws))
            best = {"idx": -1, "score": 0.0, "sentence": ""}
            for i, ts in enumerate(transcript_sentences):
                ttok = set(tokenize(ts))
                if not wtok or not ttok:
                    continue
                overlap = len(wtok & ttok) / max(len(wtok | ttok), 1)
                ratio = SequenceMatcher(None, normalize_recording_language(ws), normalize_recording_language(ts)).ratio()
                score = (0.65 * overlap) + (0.35 * ratio)
                if score > best["score"]:
                    best = {"idx": i, "score": score, "sentence": ts}

            preconflict_flags = has_conflict_pair(ws, best["sentence"])
            recording_awareness_conflict = "recording_awareness_mismatch" in preconflict_flags
            if best["score"] >= 0.28 or (preconflict_flags and best["score"] >= 0.22) or recording_awareness_conflict:
                matched_transcript_idx.add(best["idx"])
                neg_mismatch = has_negation(ws) != has_negation(best["sentence"])
                conflict_flags = preconflict_flags
                item = {
                    "witness_sentence": ws,
                    "transcript_sentence": best["sentence"],
                    "similarity_score": round(best["score"], 3),
                }
                if recording_awareness_conflict:
                    item["conflict_flags"] = conflict_flags
                    item["certainty"] = "high"
                    contradictions.append(item)
                elif neg_mismatch and best["score"] >= 0.35:
                    item["conflict_flags"] = ["negation_mismatch"] + conflict_flags
                    contradictions.append(item)
                elif conflict_flags and best["score"] >= 0.22:
                    item["conflict_flags"] = conflict_flags
                    contradictions.append(item)
                else:
                    matches.append(item)
            else:
                unverified.append(ws)

        additional_av_events = [
            s for i, s in enumerate(transcript_sentences) if i not in matched_transcript_idx
        ]

        denom = max(len(witness_sentences), 1)
        consistency_score = max(0.0, (len(matches) - len(contradictions)) / denom)
        high_certainty_contradictions = sum(1 for item in contradictions if item.get("certainty") == "high")

        return {
            "witness_sentence_count": len(witness_sentences),
            "transcript_sentence_count": len(transcript_sentences),
            "consistency_score": round(consistency_score, 3),
            "matches": matches[:50],
            "contradictions": contradictions[:50],
            "high_certainty_contradictions": high_certainty_contradictions,
            "unverified_witness_claims": unverified[:50],
            "additional_av_events": additional_av_events[:120],
            "summary": (
                f"Compared {len(witness_sentences)} supporting statements against {len(transcript_sentences)} transcript sentences. "
                f"Matches: {len(matches)} | Contradictions: {len(contradictions)} | High-certainty contradictions: {high_certainty_contradictions} | Unverified: {len(unverified)}."
            ),
        }

    def _assess_perjury_risk(self, witness_text, transcript_text, comparison):
        """
        Build a risk-indicator report for potential perjury-related concerns.
        This is not proof of perjury and should not be treated as a legal conclusion.
        """
        witness_text = witness_text or ""
        transcript_text = transcript_text or ""
        contradictions = comparison.get("contradictions", []) if isinstance(comparison, dict) else []
        unverified = comparison.get("unverified_witness_claims", []) if isinstance(comparison, dict) else []
        witness_count = max(int(comparison.get("witness_sentence_count", 0) or 0), 1) if isinstance(comparison, dict) else 1
        consistency_score = float(comparison.get("consistency_score", 0.0) or 0.0) if isinstance(comparison, dict) else 0.0

        evasion_patterns = [
            r"\bi (?:do not|don't) recall\b",
            r"\bi(?:'m| am) not sure\b",
            r"\bmaybe\b",
            r"\bi guess\b",
            r"\bto the best of my knowledge\b",
            r"\bi can(?:not|'t) remember\b",
        ]
        fabrication_patterns = [
            r"\bthat's not true\b",
            r"\bthat is not true\b",
            r"\bmade (?:it|that) up\b",
            r"\bfabricat",
            r"\blied\b",
            r"\bfalse statement\b",
        ]

        evasion_hits = sum(len(re.findall(p, transcript_text, re.IGNORECASE)) for p in evasion_patterns)
        fabrication_hits = sum(len(re.findall(p, transcript_text, re.IGNORECASE)) for p in fabrication_patterns)

        contradiction_ratio = len(contradictions) / witness_count
        unverified_ratio = len(unverified) / witness_count
        score = 0.0
        score += min(0.55, contradiction_ratio * 0.9)
        score += min(0.25, unverified_ratio * 0.35)
        score += min(0.15, evasion_hits * 0.03)
        score += min(0.2, fabrication_hits * 0.05)
        score += max(0.0, 0.1 - max(consistency_score, 0.0) * 0.1)
        score = round(min(score, 1.0), 3)

        if score >= 0.65:
            level = "HIGH"
        elif score >= 0.35:
            level = "MEDIUM"
        else:
            level = "LOW"

        indicators = []
        if contradictions:
            indicators.append(f"{len(contradictions)} witness-vs-evidence contradiction(s) detected.")
        if unverified:
            indicators.append(f"{len(unverified)} witness claim(s) not corroborated by the available transcript.")
        if evasion_hits:
            indicators.append(f"{evasion_hits} potential evasive-language marker(s) detected in transcript.")
        if fabrication_hits:
            indicators.append(f"{fabrication_hits} fabrication/falsehood marker(s) detected in transcript language.")
        if not indicators:
            indicators.append("No strong perjury-risk linguistic indicators detected on current transcript.")

        return {
            "risk_level": level,
            "risk_score": score,
            "consistency_score": consistency_score,
            "indicators": indicators,
            "disclaimer": (
                "Risk indicators only. Automated contradiction/evasion detection is not proof of perjury. "
                "Legal conclusions require full evidentiary context and professional legal assessment."
            ),
        }

    def _analyze_breach_interactions(self, breaches, text=None):
        """
        Analyze how different Charter breaches interact with each other.
        Example: A Section 9 breach often leads to Section 8 or 10(b) issues.
        """
        interactions = []
        sections = [str(b["section"]) for b in breaches]
        text_lower = (text or "").lower()

        def has_section(sec_id):
            return any(sec_id == s or (sec_id + '(') in s for s in sections)

        # Section 9 (Detention) and Section 10(b) (Counsel)
        if has_section("9") and has_section("10(b)"):
            interactions.append({
                "sections": ["9", "10(b)"],
                "description": "Arbitrary detention (s.9) directly impacts the timing and effectiveness of the right to counsel (s.10(b)). If the initial detention was unlawful, any subsequent waiver of counsel may be tainted.",
                "severity": "HIGH"
            })

        # Section 9 (Detention) and Section 8 (Search)
        if has_section("9") and has_section("8"):
            interactions.append({
                "sections": ["9", "8"],
                "description": "An unlawful detention (s.9) typically invalidates a search incident to arrest/detention (s.8). Evidence found during such a search is often subject to exclusion under s.24(2).",
                "severity": "HIGH"
            })

        # Default high-priority liberty/search/fundamental-justice nexus.
        if has_section("7") and has_section("8") and has_section("9"):
            no_observed_crime_signal = bool(re.search(
                r"\b(?:no objective grounds|no reasonable grounds|without reasonable grounds|did not (?:see|observe|witness).{0,40}(?:crime|theft|offence))\b",
                text_lower,
                re.IGNORECASE,
            ))
            if no_observed_crime_signal:
                interactions.append({
                    "sections": ["7", "8", "9"],
                    "description": (
                        "Default interaction engaged: where arrest/detention proceeds despite no observed criminal act or objective grounds, "
                        "the resulting detention appears arbitrary (s.9), related search/seizure appears unlawful unless authorized by law (s.8), "
                        "and the deprivation of liberty engages and may violate fundamental justice (s.7)."
                    ),
                    "severity": "HIGH"
                })
            else:
                interactions.append({
                    "sections": ["7", "8", "9"],
                    "description": (
                        "Core interaction: seizure/search (s.8), arrest/detention (s.9), and fundamental justice (s.7) must be read together. "
                        "If lawful authorization and objective grounds are not established, arbitrariness and liberty-deprivation concerns escalate."
                    ),
                    "severity": "HIGH"
                })

        # Section 7 (Fundamental Justice) as an umbrella
        if has_section("7"):
            for s in sections:
                if s != "7":
                    interactions.append({
                        "sections": ["7", s],
                        "description": f"Section 7 acts as a residual protection. A breach of Section {s} often constitutes a breach of the principles of fundamental justice under Section 7.",
                        "severity": "MEDIUM"
                    })

        # Section 15 (Equality) and other sections
        if has_section("15(1)"):
            for s in sections:
                if s != "15(1)":
                    interactions.append({
                        "sections": ["15(1)", s],
                        "description": f"Potential Discriminatory Interaction: The lack of objective grounds for Section {s} actions, combined with the presence of identity factors, suggests the possibility of discriminatory profiling or bias in the exercise of police discretion.",
                        "severity": "HIGH"
                    })

            if has_section("9"):
                interactions.append({
                    "sections": ["15(1)", "9"],
                    "description": "Arbitrary arrest (s.9) in the absence of evidence often implicates equality rights (s.15) if the decision to arrest appears influenced by identity markers or stereotyping rather than objective proof.",
                    "severity": "HIGH"
                })

        return interactions

    def _analyze_officer_conduct(self, text, breaches):
        """
        Analyzes officer conduct against Criminal Code standards and SCC jurisprudence
        regarding Willful Blindness, Negligence, and Ignorance of Charter standards.
        """
        text_lower = text.lower()
        findings = []
        seriousness_level = "LOW" # Spectrum from Grant test
        
        # 1. Willful Blindness / Reckless Disregard
        # SCC Definition: "Suspicion is aroused to the point where he or she sees the need for further inquiries, 
        # but deliberately declines to make them." (R v Briscoe)
        willful_patterns = [
            r'\bwillful\s+blindness\b', r'\breckless\s+disregard\b', 
            r'\bdeliberate\b.*\bignore\b', r'\bknew\b.*\bbut\b.*\bproceeded\b'
        ]
        
        is_willful = False
        for p in willful_patterns:
            if re.search(p, text_lower):
                is_willful = True
                findings.append("WILLFUL BLINDNESS/RECKLESS DISREGARD: Evidence suggests the officer deliberately ignored facts or legal standards.")
                seriousness_level = "HIGH"
                break

        # 2. Negligence / Ignorance of Charter Standards
        # SCC: "Systemic ignorance of Charter standards" is a serious aggravating factor (R v Grant).
        negligence_patterns = [
            r'\bnegligent\b', r'\bcareless\b', r'\bignorance\b.*\bcharter\b',
            r'\bnot\s+aware\b.*\bprotocol\b', r'\bfailed\s+to\s+check\b'
        ]
        
        is_negligent = False
        for p in negligence_patterns:
            if re.search(p, text_lower):
                is_negligent = True
                findings.append("NEGLIGENCE/IGNORANCE: Officer conduct appears to fall below the required standard of care or basic Charter knowledge.")
                if seriousness_level != "HIGH": seriousness_level = "MEDIUM"
                break

        # 3. Fact-Specific Negligence (Copper Wire Pattern)
        # "wasnt bell cable thats black and covered with multiple layers of rubber it was copper wire which had no insulation"
        if ("copper wire" in text_lower and "insulation" in text_lower) or ("casing" in text_lower and "stripped" in text_lower):
            findings.append("SPECIFIC FACTUAL NEGLECT: Evidence indicates a failure to distinguish between different types of material or utility equipment, which affects the physical feasibility of the alleged act.")
            seriousness_level = "HIGH"

        material_conflict = (
            ("copper wire" in text_lower and "bell cable" in text_lower)
            or bool(re.search(r"\b(?:copper|wire)\b.{0,40}\b(?:bell cable)\b|\b(?:bell cable)\b.{0,40}\b(?:copper|wire)\b", text_lower, re.IGNORECASE))
        )
        vague_material_language = bool(re.search(r"\b(?:suspected to be|appears to be|possibly|unknown material)\b", text_lower, re.IGNORECASE))
        no_photo_documentation = bool(re.search(
            r"\b(?:no|without|absent|missing)\b.{0,20}\b(?:photo|photograph|picture|image)\b",
            text_lower,
            re.IGNORECASE,
        ))

        if material_conflict or vague_material_language:
            findings.append(
                "EVIDENCE-CLASSIFICATION VAGUENESS: Officer narrative uses speculative or conflicting material descriptions "
                "(e.g., copper wire vs Bell cable), indicating failure to assess all available information before arrest/search actions."
            )
            seriousness_level = "HIGH"
        if no_photo_documentation and ("cable" in text_lower or "wire" in text_lower or "material" in text_lower):
            findings.append(
                "DOCUMENTARY OMISSION: No photo/image corroboration for alleged cable/wire material is identified, "
                "supporting a misconduct inference for incomplete evidentiary consideration."
            )
            seriousness_level = "HIGH"

        if "fire" in text_lower and "burn" in text_lower and ("5 minutes" in text_lower or "bag" in text_lower):
            findings.append("FEASIBILITY NEGLECT: Evidence suggests a timeline or physical process that is inconsistent with physical reality or established timeframes, indicating potential willful blindness.")
            seriousness_level = "HIGH"

        if not findings:
            return None

        # User policy: any detected officer misconduct is classified HIGH.
        seriousness_level = "HIGH"

        # Nexus with Charter Breaches (after final seriousness policy is applied)
        if breaches:
            findings.append(f"CONDUCT-BREACH NEXUS: The identified {seriousness_level.lower()} level of misconduct directly facilitated the potential Charter breaches.")

        conclusion = ""
        if seriousness_level == "HIGH":
            conclusion = "⚠️ CONCLUSION: UNACCEPTABLE OFFICER CONDUCT DETECTED. Under the R v Grant framework, 'wilful or reckless disregard' for Charter rights or fundamental factual errors constitute a serious form of state misconduct, making a finding of 'Abuse of Process' likely."
        elif seriousness_level == "MEDIUM":
            conclusion = "⚠️ CONCLUSION: NEGLIGENT STATE ACTION. Systemic or individual ignorance of Charter standards is unacceptable and weighs heavily in favor of a finding of fundamental injustice (Section 7)."

        return {
            "findings": findings,
            "seriousness": seriousness_level,
            "legal_basis": "R v Grant (2009 SCC 26); R v Briscoe (2010 SCC 13); R v O'Connor (Abuse of Process)",
            "assessment": " ".join(findings) + " " + conclusion
        }

    def _detect_bad_faith_policing(self, text, breaches, officer_conduct):
        """
        Detect indicia of police bad faith using both Charter-oriented standards
        and Ontario policing-legislation compliance principles.
        """
        text_lower = text.lower()
        findings = []
        score = 0

        grounds_assessment = self._analyze_grounds_for_arrest(text)
        breach_sections = {breach["section"] for breach in breaches}

        signal_map = [
            {
                "label": "ABSENCE OF OBJECTIVE GROUNDS",
                "patterns": [r"\bno objective grounds\b", r"\bno reasonable grounds\b", r"\bwithout reasonable grounds\b"],
                "points": 3,
                "rationale": "The document indicates detention or arrest without objective grounds, which strongly supports arbitrary state action rather than good-faith policing.",
            },
            {
                "label": "CHARTER DISCLOSURE OR RIGHTS IGNORING",
                "patterns": [r"\bnot informed\b", r"\bdenied counsel\b", r"\bno lawyer\b", r"\brefused lawyer\b", r"\bwithout delay\b"],
                "points": 2,
                "rationale": "The text raises non-compliance with core Charter implementation duties owed at detention or arrest.",
            },
            {
                "label": "WARRANTLESS OR UNJUSTIFIED SEARCH CONDUCT",
                "patterns": [r"\bwithout warrant\b", r"\bno warrant\b", r"\bwarrantless\b", r"\bforced entry\b", r"\bsearched without\b"],
                "points": 2,
                "rationale": "The text alleges state intrusion without lawful authorization or reasonable search procedures.",
            },
            {
                "label": "DISCRIMINATORY ENFORCEMENT / PROFILING",
                "patterns": [r"\bprofil(?:e|ing)\b", r"\bbias\b", r"\bdiscriminat", r"\bstereotyp", r"\btarget(?:ed)?\b"],
                "points": 2,
                "rationale": "The text contains identity-based or profiling language that may indicate unequal and bad-faith enforcement.",
            },
            {
                "label": "FABRICATION / CONCEALMENT / CONTRADICTION",
                "patterns": [r"\bfalse\b", r"\bfabricat", r"\bmislead", r"\bcover up\b", r"\bcontradict", r"\binconsisten", r"\bmanifest\b.*\bno\b", r"\bfailed to check\b"],
                "points": 3,
                "rationale": "The text suggests contradiction, concealment, or possible fabrication inconsistent with honest good-faith policing.",
            },
            {
                "label": "VAGUE OR INCONSISTENT MATERIAL EVIDENCE",
                "patterns": [
                    r"\bsuspected to be\b",
                    r"\bappears to be\b",
                    r"\bunknown material\b",
                    r"\bcopper wire\b.*\bbell cable\b|\bbell cable\b.*\bcopper wire\b",
                    r"\b(?:no|without|missing|absent)\b.{0,20}\b(?:photo|photograph|picture|image)\b",
                ],
                "points": 3,
                "rationale": "Material-evidence vagueness or contradiction (plus absent documentation) suggests unreliable evidentiary grounding and supports bad-faith / arbitrary-enforcement concerns.",
            },
            {
                "label": "RECKLESS DISREGARD OF FACTS OR RIGHTS",
                "patterns": [r"\bwillful\s+blindness\b", r"\breckless\s+disregard\b", r"\bdeliberate\b.*\bignore\b", r"\bknew\b.*\bbut\b.*\bproceeded\b"],
                "points": 3,
                "rationale": "The text suggests a conscious decision to proceed despite obvious factual or legal defects.",
            },
        ]

        for signal in signal_map:
            matches = _match_any_patterns(text, signal["patterns"])
            if signal["label"] == "DISCRIMINATORY ENFORCEMENT / PROFILING":
                identity_matches = sorted(_identity_marker_hits(text))
                if matches and identity_matches:
                    matches = list(dict.fromkeys(matches + identity_matches))
            if not matches:
                continue
            score += signal["points"]
            findings.append({
                "label": signal["label"],
                "matches": matches[:5],
                "rationale": signal["rationale"],
            })

        if grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment:
            score += 3
            findings.append({
                "label": "GROUNDS ANALYSIS SUPPORTS BAD FAITH INFERENCE",
                "matches": ["NO OBJECTIVE GROUNDS FOR ARREST DETECTED"],
                "rationale": "The analyzer's grounds assessment identifies arbitrariness at the arrest stage, which is a central indicator of bad-faith or abusive policing.",
            })

        if officer_conduct and officer_conduct.get("seriousness") == "HIGH":
            score += 2

        if {"8", "9"} <= breach_sections:
            score += 1
        if "15(1)" in breach_sections:
            score += 1

        if score >= 8:
            level = "HIGH"
        elif score >= 4:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not findings:
            return None

        assessment_parts = [
            "Bad faith assessment applies dual standards: Charter compliance and Ontario policing-legislation compliance.",
            "Charter focus: whether police conduct appears arbitrary, discriminatory, warrantless, rights-denying, or abusive.",
            "Policing-legislation focus: whether conduct is inconsistent with the statutory obligation to police in a manner that safeguards Charter rights and supports lawful, legitimate policing.",
        ]
        if level == "HIGH":
            assessment_parts.append(
                "Conclusion: the text contains strong indicators of bad-faith policing rather than a mere good-faith error."
            )
        elif level == "MEDIUM":
            assessment_parts.append(
                "Conclusion: the text contains meaningful indicators of bad-faith or reckless policing and warrants express abuse-of-process review."
            )
        else:
            assessment_parts.append(
                "Conclusion: the text contains limited but reviewable indicators of bad-faith policing."
            )

        return {
            "level": level,
            "score": score,
            "findings": findings,
            "charter_sources": BAD_FAITH_FRAMEWORK["charter_sources"],
            "policing_sources": BAD_FAITH_FRAMEWORK["policing_sources"],
            "legal_basis": (
                "Canadian Charter of Rights and Freedoms, ss. 7, 8, 9, 10, 15 and 24; "
                "Ontario Community Safety and Policing Act, 2019, ss. 1 and 3(1)(d)(ii)."
            ),
            "assessment": " ".join(assessment_parts),
        }

    def _assess_crown_conduct(self, text, breaches, police_bad_faith):
        """
        Assess whether the Crown appears to have ignored a live Charter breach
        or otherwise acted in bad faith in the face of obvious constitutional issues.
        """
        text_lower = text.lower()
        breach_sections = {breach["section"] for breach in breaches}
        high_breach_sections = {
            breach["section"] for breach in breaches if breach.get("confidence_level") == "HIGH"
        }
        findings = []
        concern_score = 0

        signal_map = [
            {
                "label": "IGNORING CHARTER BREACH",
                "patterns": [
                    r"\bcrown\b.*\bignore(?:d|s|ing)?\b.*\bcharter\b",
                    r"\bprosecut(?:or|ion)\b.*\bignore(?:d|s|ing)?\b.*\bcharter\b",
                    r"\bignored?\b.*\bcharter breach\b",
                ],
                "points": 3,
                "rationale": "The text expressly alleges that the Crown ignored a known Charter issue.",
            },
            {
                "label": "NON-DISCLOSURE / DISCLOSURE FAILURE",
                "patterns": [
                    r"\bfail(?:ed)?\s+to\s+disclos",
                    r"\bwithheld\b.*\bdisclos",
                    r"\bnon-?disclos",
                    r"\bStinchcombe\b",
                    r"\bMcNeil\b",
                ],
                "points": 3,
                "rationale": "The text raises a disclosure failure, which is a core Crown obligation and may support bad-faith or abuse-of-process concerns.",
            },
            {
                "label": "PROCEEDING DESPITE KNOWN ILLEGALITY",
                "patterns": [
                    r"\bcrown\b.*\bproceed(?:ed|ing)?\b.*\bdespite\b",
                    r"\bproceed(?:ed|ing)?\b.*\bdespite\b.*\bcharter\b",
                    r"\bcrown\b.*\bknew\b.*\bbut\b.*\bproceed",
                ],
                "points": 2,
                "rationale": "The text suggests the Crown continued despite a known constitutional defect.",
            },
            {
                "label": "OPPOSING REMEDY WITHOUT ANSWERING BREACH",
                "patterns": [
                    r"\bcrown\b.*\boppose(?:d|s|ing)?\b.*\b24\(",
                    r"\bcrown\b.*\boppose(?:d|s|ing)?\b.*\bexclusion\b",
                    r"\bcrown\b.*\bdeny(?:ing|ied)?\b.*\bbreach\b",
                ],
                "points": 2,
                "rationale": "The text suggests the Crown resisted a Charter remedy while failing to confront the underlying breach directly.",
            },
            {
                "label": "MISLEADING OR UNFAIR CROWN POSITION",
                "patterns": [
                    r"\bcrown\b.*\bmislead",
                    r"\bprosecut(?:or|ion)\b.*\bmislead",
                    r"\bcrown\b.*\bbad faith\b",
                    r"\babuse of process\b",
                    r"\bBabos\b",
                ],
                "points": 2,
                "rationale": "The text contains language associated with misleading conduct, unfair litigation conduct, or abuse-of-process allegations against the Crown.",
            },
        ]

        for signal in signal_map:
            matches = _match_any_patterns(text, signal["patterns"])
            if not matches:
                continue
            concern_score += signal["points"]
            findings.append({
                "label": signal["label"],
                "matches": matches[:5],
                "rationale": signal["rationale"],
            })

        crown_present = bool(re.search(r"\b(?:crown|prosecut(?:or|ion)|attorney general)\b", text_lower))
        acknowledgment_patterns = [
            r"\bcrown\b.*\b(?:acknowledge|concede|admit|recognize)\b.*\barbitrary\b",
            r"\bcrown\b.*\b(?:acknowledge|concede|admit|recognize)\b.*\bcharter breach\b",
            r"\bcrown\b.*\b(?:acknowledge|concede|admit|recognize)\b.*\bunlawful search\b",
            r"\bcrown\b.*\b(?:acknowledge|concede|admit|recognize)\b.*\bdiscriminat",
            r"\bcrown\b.*\b(?:acknowledge|concede|admit|recognize)\b.*\bwithout cause\b",
        ]
        has_crown_acknowledgment = any(re.search(pattern, text, re.IGNORECASE) for pattern in acknowledgment_patterns)

        serious_live_breach = bool({"7", "8", "9", "15(1)"} & high_breach_sections)
        arbitrary_arrest_live = "9" in high_breach_sections or (
            police_bad_faith and any(
                finding.get("label") == "ABSENCE OF OBJECTIVE GROUNDS"
                for finding in police_bad_faith.get("findings", [])
            )
        )

        if crown_present and serious_live_breach and not has_crown_acknowledgment:
            concern_score += 4
            findings.append({
                "label": "CROWN NON-ACKNOWLEDGMENT OF LIVE CHARTER DEFECT",
                "matches": sorted(high_breach_sections),
                "rationale": (
                    "The text presents serious live Charter issues, but no Crown-side acknowledgment, concession, or express engagement with those defects. "
                    "Under the non-partisan Crown role described in Boucher and the public-interest role emphasized in Krieger, that silence can support a bad-faith or abuse-of-process concern."
                ),
            })

        if crown_present and arbitrary_arrest_live and not has_crown_acknowledgment:
            concern_score += 3
            findings.append({
                "label": "CROWN FAILURE TO ADDRESS ARBITRARY ARREST",
                "matches": ["s.9 arbitrary arrest/detention concern", "s.7 deprivation of liberty concern"],
                "rationale": (
                    "Where the record indicates arbitrary arrest, deprivation of liberty without cause, or a related unlawful search/discrimination pattern, "
                    "the Crown's failure to acknowledge or engage that constitutional defect is treated here as a serious prosecutorial concern rather than neutral silence."
                ),
            })

        if police_bad_faith and police_bad_faith.get("level") == "HIGH" and any(s in breach_sections for s in {"7", "8", "9", "10(a)", "10(b)", "15(1)"}):
            concern_score += 1
            findings.append({
                "label": "LIVE UNDERLYING CHARTER DEFECT",
                "matches": sorted(breach_sections),
                "rationale": "The document already indicates serious underlying Charter and policing problems, which the Crown would be expected to address rather than ignore.",
            })

        if concern_score >= 6:
            level = "HIGH CONCERN"
        elif concern_score >= 3:
            level = "REVIEW REQUIRED"
        else:
            level = "NO EXPRESS BAD-FAITH INDICATOR"

        if level == "NO EXPRESS BAD-FAITH INDICATOR":
            conclusion = (
                "No express textual indicator shows that the Crown acted in bad faith by ignoring a Charter breach. "
                "That does not establish good faith conclusively; it means the current text does not articulate a prosecutorial bad-faith concern clearly enough."
            )
        elif level == "REVIEW REQUIRED":
            conclusion = (
                "The text raises reviewable concern that the Crown may have ignored or insufficiently addressed a live Charter breach."
            )
        else:
            conclusion = (
                "The text contains strong indicators that the Crown may have acted in bad faith by ignoring, suppressing, or proceeding despite a live Charter breach."
            )

        return {
            "level": level,
            "score": concern_score,
            "findings": findings,
            "sources": CROWN_CONDUCT_FRAMEWORK["sources"],
            "legal_basis": (
                "Canadian Charter of Rights and Freedoms, ss. 7, 11(d), 24; "
                "Boucher v The Queen; Krieger v Law Society of Alberta; R v Stinchcombe; "
                "R v O'Connor; R v McNeil; R v Babos."
            ),
            "assessment": conclusion,
        }

    def _build_police_misconduct_indicators(self, breaches, officer_conduct, bad_faith):
        indicators = []
        seen = set()

        section_url_map = {
            "7": MISCONDUCT_URLS["police"]["abuse_of_process"],
            "8": MISCONDUCT_URLS["police"]["search"],
            "9": MISCONDUCT_URLS["police"]["detention"],
            "10(a)": MISCONDUCT_URLS["police"]["charter_rights"],
            "10(b)": MISCONDUCT_URLS["police"]["charter_rights"],
            "15(1)": MISCONDUCT_URLS["police"]["equality"],
            "24": MISCONDUCT_URLS["police"]["abuse_of_process"],
        }

        for breach in breaches:
            section = breach["section"]
            if section not in section_url_map or section in seen:
                continue
            seen.add(section)
            indicators.append({
                "indicator": f"Section {section} — {breach['title']}",
                "severity": breach.get("confidence_level", "LOW"),
                "summary": (breach.get("legal_articulation") or {}).get("conclusion", breach.get("description", ""))[:220],
                "url": section_url_map[section],
                "source": "Charter / Criminal Law Notebook",
            })

        if officer_conduct:
            indicators.append({
                "indicator": "Officer Conduct Assessment",
                "severity": officer_conduct.get("seriousness", "MEDIUM"),
                "summary": officer_conduct.get("assessment", "")[:220],
                "url": MISCONDUCT_URLS["police"]["abuse_of_process"],
                "source": "State Conduct / Abuse of Process",
            })

        if bad_faith:
            for finding in bad_faith.get("findings", []):
                label = finding["label"]
                if "GROUNDS" in label:
                    url = MISCONDUCT_URLS["police"]["arrest"]
                elif "SEARCH" in label or "WARRANT" in label:
                    url = MISCONDUCT_URLS["police"]["search"]
                elif "DISCRIMINATORY" in label or "PROFILING" in label:
                    url = MISCONDUCT_URLS["police"]["equality"]
                elif "CHARTER" in label:
                    url = MISCONDUCT_URLS["police"]["charter_rights"]
                elif "FABRICATION" in label or "RECKLESS" in label:
                    url = MISCONDUCT_URLS["police"]["abuse_of_process"]
                else:
                    url = MISCONDUCT_URLS["police"]["ontario_policing"]

                indicators.append({
                    "indicator": label.title(),
                    "severity": bad_faith.get("level", "MEDIUM"),
                    "summary": finding.get("rationale", "")[:220],
                    "url": url,
                    "source": "Official Bad Faith / Process Abuse",
                })

        return indicators

    def _build_prosecutorial_misconduct_indicators(self, crown_conduct):
        indicators = []
        if not crown_conduct:
            return indicators

        for finding in crown_conduct.get("findings", []):
            label = finding["label"]
            if "DISCLOSURE" in label:
                url = MISCONDUCT_URLS["crown"]["disclosure"]
            elif "REMEDY" in label:
                url = MISCONDUCT_URLS["crown"]["remedies"]
            elif "ILLEGALITY" in label or "BAD FAITH" in label or "MISLEADING" in label:
                url = MISCONDUCT_URLS["crown"]["babos_search"]
            elif "IGNORING CHARTER BREACH" in label:
                url = MISCONDUCT_URLS["crown"]["exclusion"]
            else:
                url = MISCONDUCT_URLS["crown"]["stinchcombe_search"]

            indicators.append({
                "indicator": label.title(),
                "severity": crown_conduct.get("level", "REVIEW REQUIRED"),
                "summary": finding.get("rationale", "")[:220],
                "url": url,
                "source": "Prosecution Review",
            })

        if not indicators:
            indicators.append({
                "indicator": "Prosecution Review",
                "severity": crown_conduct.get("level", "NO EXPRESS BAD-FAITH INDICATOR"),
                "summary": crown_conduct.get("assessment", "")[:220],
                "url": MISCONDUCT_URLS["crown"]["disclosure"],
                "source": "Prosecution Review",
            })

        return indicators

    def _assess_human_rights_code(self, text, breaches):
        """
        Assess the text against a layered human-rights framework:
        UN instruments, the Canadian Human Rights Act, and provincial human-rights law.
        """
        text_lower = text.lower()
        breach_sections = {breach["section"] for breach in breaches}
        findings = []
        protected_grounds = []
        criteria = []
        score = 0

        protected_grounds.extend(sorted(_identity_marker_hits(text)))

        services_context = bool(_match_any_patterns(text, [
            r"\bpolice\b", r"\barrest\b", r"\bdetain(?:ed|ment)\b", r"\bsearch(?:ed)?\b", r"\bseiz(?:e|ure)\b", r"\bservice\b"
        ]))
        discriminatory_treatment = bool(_match_any_patterns(text, [
            r"\bdiscriminat", r"\bprofil(?:e|ing)\b", r"\bbias\b", r"\bstereotyp", r"\btargeted\b", r"\btreated differently\b"
        ]))
        reprisal_context = bool(_match_any_patterns(text, [
            r"\breprisal\b", r"\bretaliat", r"\bthreat of reprisal\b", r"\bpunished for complaining\b"
        ]))
        indirect_infringement = bool(_match_any_patterns(text, [
            r"\bindirect", r"\bpolicy\b", r"\bpractice\b", r"\bconstructive discrimination\b", r"\badverse effect\b"
        ]))
        association_context = bool(_match_any_patterns(text, [
            r"\bbecause of association\b",
            r"\bassociation with\b",
            r"\bfamily member\b",
            r"\brelated to\b.{0,30}\b(?:family|spouse|partner|friend|associate|group|community)\b",
        ]))
        disability_accommodation = bool(_match_any_patterns(text, [
            r"\baccommodat", r"\bundue hardship\b", r"\bdisability\b", r"\bmental health\b", r"\bmedical\b",
            r"\banxiety\b", r"\bpanic\b", r"\bsymptoms?\b"
        ]))
        no_objective_theft_evidence = bool(_match_any_patterns(text, [
            r"\bno (?:physical )?evidence\b.{0,40}\b(?:theft|steal|stolen|cable|wire|property)\b",
            r"\b(?:theft|steal|stolen|cable|wire|property)\b.{0,40}\b(?:not found|missing|absent|none)\b",
            r"\bno\b.{0,25}\b(?:cable|wire|tool|property)\b",
            r"\bno objective grounds\b",
            r"\binsufficient grounds\b",
        ]))
        innocent_explanation_context = bool(_match_any_patterns(text, [
            r"\banxiety\b",
            r"\bpanic\b",
            r"\bmental health symptom",
            r"\b(?:use|using|used)\b.{0,30}\b(?:bathroom|washroom|restroom|toilet)\b",
            r"\breliev(?:e|ing)\b.{0,25}\b(?:my|their|his|her)?\s*(?:self|anxiety|symptoms?)\b",
            r"\bout of sight\b",
            r"\bbroad daylight\b",
            r"\bdaylight\b",
            r"\bdaytime\b",
        ]))
        privacy_preserving_relief_context = bool(_match_any_patterns(text, [
            r"\bditch\b",
            r"\bout of sight\b",
            r"\bhidden from view\b",
            r"\bprivate(?:ly)?\b",
            r"\bavoid(?:ing)?\b.{0,25}\bindecent exposure\b",
            r"\bnot\b.{0,10}\bcommit\b.{0,25}\bindecent exposure\b",
            r"\breliev(?:e|ing)\b.{0,35}\b(?:anxiety|symptoms?|self)\b",
            r"\b(?:bathroom|washroom|restroom|toilet)\b.{0,25}\bunavailable\b",
        ]))
        suspicious_only_language = bool(_match_any_patterns(text, [
            r"\bsuspicious\b",
            r"\bloiter(?:ing)?\b",
            r"\blurk(?:ing)?\b",
            r"\blooked suspicious\b",
        ]))

        if services_context and protected_grounds and discriminatory_treatment:
            score += 4
            criteria.append("Services discrimination / equal treatment")
            findings.append({
                "criterion": "Services discrimination / equal treatment",
                "summary": "The text indicates services or policing conduct linked to one or more protected grounds and differential treatment.",
                "layers": [
                    "UN: equality, dignity, non-discrimination principles (UDHR / ICCPR)",
                    "National: Canadian Human Rights Act discriminatory practices framework",
                    "Provincial: Human Rights Code services discrimination framework",
                ],
                "cases": [
                    HUMAN_RIGHTS_FRAMEWORK["cases"][0],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][2],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][3],
                ],
            })

        if reprisal_context:
            score += 2
            criteria.append("Reprisal or retaliatory human-rights interference")
            findings.append({
                "criterion": "Reprisal or retaliatory human-rights interference",
                "summary": "The text raises reprisal or retaliatory conduct tied to the assertion of rights.",
                "layers": [
                    "UN: effective protection against retaliation for rights-assertion",
                    "National / Provincial: reprisal protection in human-rights enforcement contexts",
                ],
                "cases": [HUMAN_RIGHTS_FRAMEWORK["cases"][2], HUMAN_RIGHTS_FRAMEWORK["cases"][4]],
            })

        if discriminatory_treatment and services_context:
            score += 1
            criteria.append("Direct or indirect infringement of human-rights protections")

        if indirect_infringement:
            score += 2
            criteria.append("Constructive discrimination / adverse effect discrimination")
            findings.append({
                "criterion": "Constructive discrimination / adverse effect discrimination",
                "summary": "The text suggests a policy, practice, or indirect mechanism causing discriminatory adverse effects.",
                "layers": [
                    "UN: equal protection and substantive equality principles",
                    "National / Provincial: constructive discrimination and accommodation analysis",
                ],
                "cases": [HUMAN_RIGHTS_FRAMEWORK["cases"][1], HUMAN_RIGHTS_FRAMEWORK["cases"][0]],
            })

        if association_context:
            score += 1
            criteria.append("Discrimination because of association")
            findings.append({
                "criterion": "Discrimination because of association",
                "summary": "The text suggests differential treatment because of association with a protected person or group.",
                "layers": [
                    "National / Provincial: association-based discrimination analysis",
                ],
                "cases": [HUMAN_RIGHTS_FRAMEWORK["cases"][3]],
            })

        if disability_accommodation and "disability" in protected_grounds:
            score += 2
            criteria.append("Disability, accommodation, and undue hardship")
            findings.append({
                "criterion": "Disability, accommodation, and undue hardship",
                "summary": "The text raises disability-linked treatment and the accommodation / undue-hardship framework.",
                "layers": [
                    "UN: CRPD equality and accessibility / accommodation principles",
                    "National / Provincial: accommodation and undue-hardship analysis",
                ],
                "cases": [
                    HUMAN_RIGHTS_FRAMEWORK["cases"][1],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][0],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][4],
                ],
            })

        if services_context and "disability" in protected_grounds and privacy_preserving_relief_context:
            score += 2
            criteria.append("Disability-linked privacy-preserving behaviour")
            findings.append({
                "criterion": "Disability-linked privacy-preserving behaviour",
                "summary": "The text indicates behaviour aimed at preserving privacy or avoiding indecent exposure while managing disability-linked symptoms, which strengthens the accommodation and dignity analysis.",
                "layers": [
                    "UN: dignity, privacy, and disability accommodation principles",
                    "National / Provincial: accommodation, dignity, and non-discrimination in services and policing contexts",
                ],
                "cases": [
                    HUMAN_RIGHTS_FRAMEWORK["cases"][0],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][1],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][4],
                ],
            })

        if services_context and "disability" in protected_grounds and no_objective_theft_evidence and innocent_explanation_context:
            score += 4
            criteria.append("Disability-linked policing escalation without objective theft evidence")
            findings.append({
                "criterion": "Disability-linked policing escalation without objective theft evidence",
                "summary": "The text indicates police/service-state intervention despite a disability-linked innocent explanation and no objective theft evidence, which elevates discriminatory-enforcement risk.",
                "layers": [
                    "UN: dignity and non-discrimination in law-enforcement interactions",
                    "National / Provincial: adverse treatment and accommodation duties in services/policing contexts",
                ],
                "cases": [
                    HUMAN_RIGHTS_FRAMEWORK["cases"][0],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][1],
                    HUMAN_RIGHTS_FRAMEWORK["cases"][3],
                ],
            })

        if services_context and protected_grounds and no_objective_theft_evidence and suspicious_only_language:
            score += 2
            criteria.append("Suspicion-based differential enforcement risk")
            findings.append({
                "criterion": "Suspicion-based differential enforcement risk",
                "summary": "The text suggests enforcement based on suspicion labels while objective theft evidence is absent, increasing risk of discriminatory differential treatment.",
                "layers": [
                    "UN: equal protection / non-arbitrariness principles",
                    "National / Provincial: discriminatory services-enforcement screening",
                ],
                "cases": [HUMAN_RIGHTS_FRAMEWORK["cases"][0], HUMAN_RIGHTS_FRAMEWORK["cases"][3]],
            })

        if "15(1)" in breach_sections and protected_grounds and services_context:
            score += 2

        if score >= 6:
            level = "HIGH"
        elif score >= 3:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not findings:
            findings.append({
                "criterion": "Human-rights screening",
                "summary": "No strongly articulated UN / national / provincial human-rights violation is detected on the current text, though protected-ground and services analysis should still be checked manually where policing and discrimination overlap.",
                "layers": [
                    "UN",
                    "National",
                    "Provincial",
                ],
                "cases": [HUMAN_RIGHTS_FRAMEWORK["cases"][0], HUMAN_RIGHTS_FRAMEWORK["cases"][2]],
            })

        return {
            "level": level,
            "score": score,
            "protected_grounds": protected_grounds,
            "criteria": criteria,
            "findings": findings,
            "sources": HUMAN_RIGHTS_FRAMEWORK["sources"],
            "cases": HUMAN_RIGHTS_FRAMEWORK["cases"],
            "assessment": (
                "Human-rights assessment completed across UN, national, and provincial frameworks using equality, non-discrimination, reprisal, constructive discrimination, association, and accommodation criteria."
            ),
        }

    def _cross_reference_dictionary(self, text):
        """
        Cross-reference document text with literal meanings (using dictionaries
        preferred by the Supreme Court of Canada for 'ordinary meaning' analysis)
        before applying constitutional legal context.
        """
        matches = []
        text_lower = text.lower()
        
        # All analysis starts with the 'Ordinary Meaning' dictionary preferred by the SCC
        for key, entry in LEGAL_DICTIONARY.items():
            search_terms = [key.replace("_", " ")]
            if "aliases" in entry:
                search_terms.extend(entry["aliases"])
                
            found_terms = []
            for term in search_terms:
                if term.lower() in text_lower:
                    found_terms.append(term)
            
            if found_terms:
                # Retrieve the SCC-preferred literal definition (Ordinary Meaning)
                literal = LITERAL_DICTIONARY.get(key, {
                    "definition": "Common English meaning varies by usage context.",
                    "source": "General Usage",
                    "etymology": "Unknown"
                })

                matches.append({
                    "term": key,
                    "matched_as": found_terms[0],
                    "literal_definition": literal["definition"],
                    "literal_source": literal.get("source", "N/A"),
                    "literal_etymology": literal.get("etymology", "N/A"),
                    "legal_definition": entry.get("definition") or entry.get("legal_definition", "Definition unavailable."),
                    "legal_source": entry.get("source") or entry.get("legal_source", "N/A"),
                    "legal_category": entry.get("category", "N/A"),
                    "preferred_form": entry.get("preferred_form", key)
                })
        return matches

    def _check_specific_flags(self, text):
        """Check for user-requested specific flags."""
        found_flags = []
        for flag_id, flag_data in SPECIFIC_FLAGS.items():
            matches = []
            for pattern in flag_data["patterns"]:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    matches.extend(found)

            if matches:
                found_flags.append({
                    "id": flag_id,
                    "label": flag_data["label"],
                    "description": flag_data["description"],
                    "count": len(matches),
                    "matches": list(set(matches))[:5]
                })
        return found_flags

    def _analyze_section(self, section_id, section_data, text, dictionary_matches=None):
        """
        Analyze a specific Charter section for potential breach indicators.
        
        Uses keyword matching, context analysis, and breach test frameworks.
        """
        text_lower = text.lower()
        dictionary_matches = dictionary_matches or []

        # Keyword matching
        keywords = section_data["keywords"]
        matched_keywords = []
        keyword_positions = {}

        for kw in keywords:
            if kw.lower() in text_lower:
                count = text_lower.count(kw.lower())
                matched_keywords.append({"keyword": kw, "count": count})
                keyword_positions[kw] = [m.start() for m in re.finditer(re.escape(kw.lower()), text_lower)]

        # Calculate confidence based on keyword density and variety
        keyword_confidence = len(matched_keywords) / max(len(keywords), 1)

        # Check for breach-related language patterns
        breach_indicators = _find_breach_indicators(text, section_id)

        # Special Analysis for Section 9 (Arbitrary Detention), Section 7, and Section 15 (Equality)
        grounds_assessment = self._analyze_grounds_for_arrest(text)

        # Overall confidence score
        total_weight = 0
        max_weight = 0

        # Keyword weight (40%)
        total_weight += 0.4 * keyword_confidence
        max_weight += 0.4

        # Breach indicator weight (40%)
        if breach_indicators:
            indicator_confidence = min(len(breach_indicators) / 5, 1.0)
            total_weight += 0.4 * indicator_confidence
        max_weight += 0.4

        # Explicit reference weight (20%)
        pattern = rf'(?:s(?:ection)?\.?\s*){re.escape(section_id)}\s+(?:of\s+)?(?:the\s+)?(?:charter)'
            
        explicit_refs = re.findall(pattern, text, re.IGNORECASE)
        explicit_confidence = min(len(explicit_refs) / 2, 1.0)
        total_weight += 0.2 * explicit_confidence
        max_weight += 0.2

        # Special Boost for Section 7 Arrest Reports
        if section_id == "7":
            arrest_report_patterns = [r'arrest report', r'police report', r'incident report', r'arrest was made']
            for p in arrest_report_patterns:
                if re.search(p, text, re.IGNORECASE):
                    total_weight += 0.5 # Substantial boost
                    max_weight += 0.5
                    break

        # Boost confidence if "No grounds" logic is triggered
        if grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment:
            # High boost for relevant sections
            if section_id in ["7", "9"]:
                total_weight += 1.5
                max_weight += 1.0 # Guarantee > 100% confidence

            # Special logic for Section 15: If arrest lacks grounds and identity is mentioned,
            # flag potential discriminatory enforcement.
            if section_id == "15(1)":
                if "sex / gender" in _identity_marker_hits(text):
                    total_weight += 0.8
                    max_weight += 0.8

        # Identify applicable tests
        tests = section_data.get("tests", {})
        applicable_tests = _evaluate_tests(section_id, tests, text)

        legal_articulation = _build_section_legal_articulation(
            section_id, text, grounds_assessment, applicable_tests, breach_indicators
        )

        dictionary_anchored = _section_is_dictionary_anchored(
            section_id, text, dictionary_matches, len(explicit_refs), grounds_assessment
        )

        confidence = total_weight / max_weight if max_weight > 0 else 0
        if dictionary_anchored:
            confidence = max(confidence, 0.3)
        if not dictionary_anchored:
            confidence = 0

        supported_test_count = sum(
            1 for test in applicable_tests.values() if test.get("status") == "potential_issue"
        )
        direct_relevance = bool(
            dictionary_anchored and legal_articulation and (
                len(explicit_refs) > 0
                or supported_test_count > 0
                or any(indicator["type"] in {"arbitrary", "without warrant", "no warrant", "warrantless", "not informed", "denied counsel", "no lawyer", "refused lawyer"} for indicator in breach_indicators)
                or (grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment)
            )
        )
        if direct_relevance:
            confidence = max(confidence, 0.9)

        # Confidence level
        if confidence >= CONFIDENCE_THRESHOLDS["high"]:
            confidence_level = "HIGH"
        elif confidence >= CONFIDENCE_THRESHOLDS["medium"]:
            confidence_level = "MEDIUM"
        elif confidence >= CONFIDENCE_THRESHOLDS["low"]:
            confidence_level = "LOW"
        else:
            confidence_level = "MINIMAL"

        is_flagged = dictionary_anchored and confidence >= CONFIDENCE_THRESHOLDS["low"]

        # User policy: flagged Section 9 findings are treated as HIGH priority.
        if section_id == "9" and is_flagged:
            confidence = max(confidence, CONFIDENCE_THRESHOLDS["high"], 0.9)
            confidence_level = "HIGH"

        # User policy: where no objective arrest grounds are detected, related Section 8 search/seizure
        # concerns are treated as high-priority unless the text clearly indicates lawful authorization.
        if section_id == "8" and is_flagged:
            no_objective_grounds = bool(grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment)
            lawful_authorization_signal = bool(re.search(
                r"\b(?:authorized by law|lawful authority|valid warrant|judicial authorization)\b",
                text,
                re.IGNORECASE,
            ))
            if no_objective_grounds and not lawful_authorization_signal:
                confidence = max(confidence, CONFIDENCE_THRESHOLDS["high"], 0.9)
                confidence_level = "HIGH"

        # User policy: flagged Section 15 discriminatory-enforcement findings are HIGH priority.
        if section_id == "15(1)" and is_flagged:
            identity_markers = _has_identity_markers(text)
            discrimination_signals = bool(_match_any_patterns(text, [
                r"\bdiscriminat",
                r"\bprofil(?:e|ing)\b",
                r"\bbias\b",
                r"\bstereotyp",
                r"\btargeted\b",
                r"\btreated differently\b",
            ]))
            arbitrary_arrest_signal = bool(grounds_assessment and "NO OBJECTIVE GROUNDS" in grounds_assessment)
            if arbitrary_arrest_signal and identity_markers:
                # Equality-rights policy: arbitrary arrest/detention is treated as a systemic
                # equal-protection concern only where protected-ground context is actually present.
                confidence = max(confidence, CONFIDENCE_THRESHOLDS["high"], 0.9)
                confidence_level = "HIGH"
            elif (discrimination_signals and identity_markers):
                confidence = max(confidence, CONFIDENCE_THRESHOLDS["high"], 0.9)
                confidence_level = "HIGH"

        # User policy: flagged Section 24 exclusion-of-evidence findings are HIGH priority.
        if section_id == "24" and is_flagged:
            illegal_evidence_signals = bool(_match_any_patterns(text, [
                r"\billegally obtained\b",
                r"\bobtained in breach\b",
                r"\bexclude(?:d|s)?\b.{0,20}\bevidence\b",
                r"\bexclusion of evidence\b",
                r"\badministration of justice\b.{0,30}\bdisrepute\b",
                r"\bs\.?\s*24\s*\(\s*2\s*\)\b",
                r"\b24\s*\(\s*2\s*\)\b",
            ]))
            strong_state_conduct_signal = any(
                indicator.get("type") in {
                    "unlawful",
                    "unconstitutional",
                    "without warrant",
                    "no warrant",
                    "warrantless",
                    "searched without",
                    "without reasonable grounds",
                    "no reasonable grounds",
                    "arbitrary",
                    "violation",
                    "infringement",
                    "breach",
                }
                for indicator in breach_indicators
            )
            if illegal_evidence_signals or strong_state_conduct_signal:
                confidence = max(confidence, CONFIDENCE_THRESHOLDS["high"], 0.9)
                confidence_level = "HIGH"

        # Merge grounds assessment into description or overall notes
        description = section_data["description"]
        if legal_articulation:
            description = (
                f"{description}\n\nGOVERNING TEST: {legal_articulation['governing_test']}\n\n"
                f"EXPRESS FINDING: {legal_articulation['conclusion']}\n\n"
                f"LEADING AUTHORITIES: {'; '.join(legal_articulation['authorities'])}"
            )
        if grounds_assessment:
            description = f"{description}\n\nGROUNDS ASSESSMENT: {grounds_assessment}"

        result = {
            "section": section_id,
            "title": section_data["title"],
            "description": description,
            "flagged": is_flagged,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "matched_keywords": matched_keywords,
            "breach_indicators": breach_indicators,
            "explicit_references": len(explicit_refs),
            "applicable_tests": applicable_tests,
            "legal_articulation": legal_articulation,
            "dictionary_anchored": dictionary_anchored,
            "direct_relevance": direct_relevance,
        }

        return result

    def _analyze_grounds_for_arrest(self, text):
        text_lower = text.lower()
        findings = []
        has_arrest = any(kw in text_lower for kw in ['arrest', 'arrested', 'custody', 'detained'])
        if not has_arrest:
            return ''

        def is_negated_or_absent(target, full_text):
            patterns = [
                rf'\b(?:no|none|without|lack of|beyond|absent)\b.{{0,30}}\b{re.escape(target)}\b',
                rf'\b{re.escape(target)}\b.{{0,30}}\b(?:missing|absent|not present|not found)\b',
                rf'\b(?:doesnt|does not|didnt|did not)\b.{{0,20}}\bsay\b.{{0,30}}\b{re.escape(target)}\b'
            ]
            for p in patterns:
                if re.search(p, full_text, re.IGNORECASE):
                    return True
            return False

        cable_absent = is_negated_or_absent('evidence', text_lower) or is_negated_or_absent('property', text_lower) or is_negated_or_absent('material', text_lower) or is_negated_or_absent('cable', text_lower) or is_negated_or_absent('wire', text_lower) or is_negated_or_absent('tools', text_lower) or ('manifest' in text_lower and 'no' in text_lower)
        if cable_absent:
            findings.append('EVIDENCE ABSENCE: NO PHYSICAL EVIDENCE (CABLE/WIRE/PROPERTY) IDENTIFIED ON MANIFEST.')

        material_conflict = (
            ("copper wire" in text_lower and "bell cable" in text_lower)
            or ("copper" in text_lower and "cable" in text_lower and "suspected" in text_lower)
        )
        vague_material_language = bool(re.search(r"\b(?:suspected to be|appears to be|possibly|unknown material)\b", text_lower, re.IGNORECASE))
        photo_absent = (
            is_negated_or_absent('photo', text_lower)
            or is_negated_or_absent('photograph', text_lower)
            or is_negated_or_absent('picture', text_lower)
            or is_negated_or_absent('image', text_lower)
        )
        seized_material_mismatch = bool(re.search(
            r"\bseized\b.{0,40}\b(?:wire|copper wire)\b",
            text_lower,
            re.IGNORECASE,
        )) and (
            ("bell cable" in text_lower and "copper wire" in text_lower)
            or bool(re.search(r"\bnot present\b.{0,30}\bbell cable\b|\bbell cable\b.{0,30}\bnot present\b", text_lower, re.IGNORECASE))
        )
        scene_link_missing = bool(re.search(
            r"\b(?:no|without|lacks?|missing|absent)\b.{0,35}\b(?:crime scene|scene link|scene nexus|scene evidence|link to scene|linked to scene|source location|pole link|property link)\b",
            text_lower,
            re.IGNORECASE,
        )) or bool(re.search(
            r"\b(?:material|wire|cable)\b.{0,35}\b(?:not linked|not tied|not connected)\b.{0,35}\b(?:scene|pole|property|location|theft)\b",
            text_lower,
            re.IGNORECASE,
        ))
        assumption_driven_theory = bool(re.search(
            r"\b(?:assum(?:e|ed|ption)|suspected|crime in progress)\b.{0,50}\b(?:theft|steal|stolen|wire|cable|offence|crime)\b",
            text_lower,
            re.IGNORECASE,
        )) or bool(re.search(
            r"\b(?:instead of|rather than)\b.{0,35}\b(?:reasonable|probable)\s+grounds\b",
            text_lower,
            re.IGNORECASE,
        )) or bool(re.search(
            r"\boverlook(?:ed|ing)?\b.{0,35}\b(?:relevant evidence|material evidence|available evidence)\b",
            text_lower,
            re.IGNORECASE,
        ))
        no_identification = bool(re.search(
            r"\b(?:could not|couldn't|did not|didn't)\b.{0,20}\bidentify\b.{0,20}\b(?:person|suspect|individual|man|woman)\b",
            text_lower,
            re.IGNORECASE,
        ))

        if material_conflict or vague_material_language:
            findings.append(
                'VAGUENESS / EVIDENCE INCONSISTENCY: MATERIAL DESCRIPTION IS INCONSISTENT OR SPECULATIVE '
                '(E.G., COPPER WIRE IN ONE ACCOUNT, BELL CABLE IN ANOTHER, OR "SUSPECTED TO BE" LANGUAGE).'
            )
        if photo_absent and ("cable" in text_lower or "wire" in text_lower or "material" in text_lower):
            findings.append(
                'DOCUMENTATION GAP: NO PHOTO/IMAGE EVIDENCE OF THE ALLEGED CABLE/WIRE MATERIAL IS IDENTIFIED.'
            )
        if seized_material_mismatch:
            findings.append(
                'SEIZURE / DESCRIPTION MISMATCH: THE MATERIAL DESCRIBED AS SEIZED DOES NOT MATCH THE BELL CABLE THEORY OR THE RECORD INDICATES THE ALLEGED BELL CABLE IS NOT PRESENT.'
            )
        if scene_link_missing:
            findings.append(
                'SCENE NEXUS FAILURE: THE RECORD DOES NOT LINK THE SEIZED MATERIAL TO ANY IDENTIFIED CRIME SCENE, POLE, OR SOURCE LOCATION.'
            )

        witness_mention = re.search(r'\b(?:woman|man|she|he|witness)\b', text_lower)
        saw_crime = re.search(r'\b(?:saw|seen|observed|witnessed)\b.{{0,50}}\b(?:theft|stealing|climbing|cutting|committing)\b', text_lower)
        no_observed_crime = bool(re.search(
            r'\b(?:nobody|no one|none of them)\b.{0,25}\b(?:saw|seen|observed|witnessed)\b.{0,50}\b(?:crime|theft|offence|offense)\b',
            text_lower,
            re.IGNORECASE,
        ))
        if no_observed_crime or (witness_mention and not saw_crime):
            findings.append('WITNESS CREDIBILITY: STATEMENT DOES NOT DESCRIBE OBSERVING A CRIMINAL ACT.')
        if no_identification:
            findings.append('IDENTIFICATION GAP: WITNESS ACCOUNT DOES NOT IDENTIFY THE PERSON AS THE ACTOR OF ANY SPECIFIC OFFENCE.')
        if assumption_driven_theory:
            findings.append('ASSUMPTION-DRIVEN THEORY: THE RECORD SUGGESTS OFFICERS PROCEEDED ON ASSUMPTION OR CRIME-IN-PROGRESS SPECULATION INSTEAD OF OBJECTIVELY VERIFIABLE GROUNDS.')

        pole_missing = is_negated_or_absent('pole', text_lower)
        tools_missing = is_negated_or_absent('tools', text_lower)
        out_of_reach = 'inaccessible' in text_lower or 'reach' in text_lower
        if pole_missing:
            findings.append('PHYSICAL NEXUS: REPORT FAILS TO PLACE SUSPECT ON OR NEAR UTILITY POLE.')
        if tools_missing:
            findings.append('FEASIBILITY: NO TOOLS IDENTIFIED IN SUSPECT POSSESSION.')
        if out_of_reach:
            findings.append('PHYSICAL INACCESSIBILITY: TARGET MATERIAL OR LOCATION INDICATED AS BEYOND REACH.')

        if len(findings) >= 2:
            conclusion = (
                '⚠️ CONCLUSION: NO OBJECTIVE GROUNDS FOR ARREST DETECTED. '
                'LEGAL ARTICULATION: The arrest fails both the subjective and objective tests for '
                'Reasonable Grounds established by the Supreme Court of Canada in R v Storrey. '
                'Specifically: (1) Absence of Stolen Property: No material matching the alleged stolen '
                'items was found on the manifest, meaning the Corpus Delicti is missing. (2) Observation Failure: '
                'The supporting statement fails to describe a criminal act; per R v Chehil, mere presence in a '
                'location is insufficient for arrest grounds. (3) Vague / Contradictory Material Evidence: '
                'where the record alternates between copper wire and Bell cable (or uses speculative "suspected to be" '
                'phrasing) without photographic documentation, evidentiary reliability is materially weakened. '
                '(4) Missing Scene Nexus: the record does not connect the seized material to a defined crime scene or source location. '
                '(5) Assumption Instead of Grounds: the theory of a crime in progress is asserted rather than supported by identified facts. '
                '(6) Physical Impossibility: '
                'The facts suggest physical inaccessibility or logistical impossibilities at the scene. '
                'This constitutes a breach of the Principles of Fundamental Justice (Section 7), '
                'as the states power was exercised in an arbitrary manner. The arrest is therefore '
                'unlawful under Section 9.'
            )
            return ' '.join(findings) + '\n\n' + conclusion
        return ' '.join(findings)
