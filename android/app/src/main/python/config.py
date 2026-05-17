# Copyright project_phoenix
"""
Configuration for the Legal Document Analyzer
"""

# CanLII API Configuration
CANLII_API_BASE = "https://api.canlii.org/v1"
# Get your free API key at https://api.canlii.org/
CANLII_API_KEY = ""  # User must provide their own key

# Criminal Law Notebook
CLN_BASE_URL = "https://criminalnotebook.ca"

# Charter Sections for Breach Analysis
CHARTER_SECTIONS = {
    "2(a)": {
        "title": "Freedom of Conscience and Religion",
        "description": "Everyone has the freedom of conscience and religion.",
        "keywords": ["religion", "conscience", "belief", "faith", "worship", "religious freedom",
                      "creed", "spiritual", "sacred", "prayer", "religious practice"],
        "tests": {
            "sincere_belief": "Is the claimant's belief sincere and deeply held?",
            "interference": "Is there interference with the ability to act on the belief?",
            "causation": "Is the interference causally connected to the belief?",
            "severity": "Is the interference more than trivial or insubstantial?"
        }
    },
    "2(b)": {
        "title": "Freedom of Thought, Belief, Opinion and Expression",
        "description": "Everyone has the freedom of thought, belief, opinion and expression, including freedom of the press.",
        "keywords": ["expression", "speech", "opinion", "press", "media", "censorship",
                      "protest", "demonstration", "symbolic expression", "artistic expression",
                      "commercial expression", "hate speech", "defamation", "internet"],
        "tests": {
            "is_expression": "Does the activity convey a meaning (expressive content)?",
            "purpose": "Does the law or action target the content or form of expression?",
            "effect": "Does the law or action have a chilling effect on expression?",
            "press_freedom": "Is press freedom or journalistic source protection implicated?"
        }
    },
    "2(c)": {
        "title": "Freedom of Peaceful Assembly",
        "description": "Everyone has the freedom of peaceful assembly.",
        "keywords": ["assembly", "gathering", "protest", "demonstration", "march", "rally",
                      "picket", "public meeting", "freedom of association"],
        "tests": {
            "is_assembly": "Is there a gathering of persons for a common purpose?",
            "peaceful": "Is the assembly peaceful in nature?",
            "interference": "Is there state interference with the assembly?"
        }
    },
    "2(d)": {
        "title": "Freedom of Association",
        "description": "Everyone has the freedom of association.",
        "keywords": ["association", "union", "collective bargaining", "membership",
                      "group", "organization", "labour", "trade union", "professional association"],
        "tests": {
            "is_association": "Is the activity a collective one involving association?",
            "purpose": "Does the law prevent the formation of associations or their activities?",
            "collective_action": "Is collective bargaining or collective action at issue?"
        }
    },
    "3": {
        "title": "Democratic Rights — Right to Vote",
        "description": "Every citizen of Canada has the right to vote in an election and to be qualified for membership in Parliament.",
        "keywords": ["vote", "election", "electoral", "ballot", "citizen", "parliament",
                      "legislature", "franchise", "suffrage", "riding", "constituency"],
        "tests": {
            "is_citizen": "Is the claimant a Canadian citizen?",
            "election_context": "Does the matter relate to a federal or provincial election?",
            "denial": "Has the right to vote or stand for office been denied?"
        }
    },
    "7": {
        "title": "Life, Liberty and Security of the Person",
        "description": "Everyone has the right to life, liberty and security of the person and the right not to be deprived thereof except in accordance with the principles of fundamental justice.",
        "keywords": ["life", "liberty", "security of the person", "fundamental justice",
                      "arbitrary", "overbreadth", "grossly disproportionate", "procedural fairness",
                      "duty of fairness", "natural justice", "deprivation", "detention",
                      "imprisonment", "bodily integrity", "medical treatment", "mental health",
                      "risk of harm", "stigma", "serious illness", "custody record", "incident record",
                      "intake record", "case record", "event record", "statement"],
        "tests": {
            "deprivation": "Is there a deprivation of life, liberty, or security of the person?",
            "life_liberty_security": "Which interest is engaged — life, liberty, or security of the person?",
            "principles_of_fundamental_justice": "Is the deprivation in accordance with the principles of fundamental justice?",
            "arbitrariness": "Is the law or action arbitrary (no rational connection)?",
            "overbreadth": "Is the law overbroad (goes further than necessary)?",
            "gross_disproportionality": "Is the law or action grossly disproportionate?",
            "procedural_fairness": "Are procedures fair (duty of fairness/natural justice)?",
            "vagueness": "Is the law or decision vague or uncertain?",
            "arrest_report_present": "Does the document contain a custody or incident record tied to the event?",
            "liberty_impact": "Does the record demonstrate a direct impact on the individual's liberty?",
            "grounds_for_arrest": "Are there objectively reasonable grounds described in the record?"
        }
    },
    "8": {
        "title": "Unreasonable Search and Seizure",
        "description": "Everyone has the right to be secure against unreasonable search or seizure.",
        "keywords": ["search", "seizure", "warrant", "privacy", "reasonable expectation of privacy",
                      "probable cause", "reasonable grounds", "informant", "wiretap", "surveillance",
                      "cell phone", "computer", "vehicle", "home", "detention search", "strip search",
                      "DNA", "blood sample", "breath sample", "entry", "inspection", "border"],
        "tests": {
            "expectation_of_privacy": "Does the claimant have a reasonable expectation of privacy in the subject matter?",
            "search_or_seizure": "Was there a search or seizure by the state?",
            "reasonableness": "Was the search or seizure reasonable?",
            "warrant_requirement": "Was a warrant obtained? If not, was the warrantless search justified?",
            "scope": "Was the search conducted in a reasonable manner?"
        }
    },
    "9": {
        "title": "Arbitrary Detention or Imprisonment",
        "description": "Everyone has the right not to be arbitrarily detained or imprisoned.",
        "keywords": ["detention", "arrest", "imprisonment", "arbitrary", "lawful",
                      "police stop", "border detention", "investigative detention",
                      "psychiatric detention", "immigration hold", "protective custody",
                      " roadside stop", "RIDE program", "checkpoint"],
        "tests": {
            "is_detention": "Was the person detained (physical or psychological restraint)?",
            "lawful_authority": "Was the detention authorized by law?",
            "arbitrariness": "Was the detention arbitrary (no reasonable grounds)?",
            "necessity": "Was the detention necessary and proportionate?"
        }
    },
    "10(a)": {
        "title": "Right to be Informed of Offence",
        "description": "Everyone has the right on arrest or detention to be informed promptly of the reasons therefor.",
        "keywords": ["informed of reasons", "right to know", "arrest reasons",
                      "notification of charges", "prompt information", "charges explained"],
        "tests": {
            "was_detained": "Was the person arrested or detained?",
            "prompt_informing": "Was the person promptly informed of the reason for arrest/detention?",
            "clarity": "Were the reasons communicated in a way the person could understand?"
        }
    },
    "10(b)": {
        "title": "Right to Retain and Instruct Counsel",
        "description": "Everyone has the right on arrest or detention to retain and instruct counsel without delay and to be informed of that right.",
        "keywords": ["counsel", "lawyer", "right to a lawyer", "legal advice",
                      "duty counsel", "legal aid", "without delay", "inform of right",
                      "waiver", "access to lawyer", "telephone", "consultation"],
        "tests": {
            "was_detained": "Was the person arrested or detained?",
            "right_imposed": "Was the person informed of the right to counsel?",
            "without_delay": "Was the person given the opportunity to exercise the right without delay?",
            "implementation": "Were reasonable steps taken to implement the right?",
            "waiver": "Was there a valid waiver of the right to counsel?"
        }
    },
    "11(a)": {
        "title": "Right to be Informed of Offence",
        "description": "Any person charged with an offence has the right to be informed without unreasonable delay of the specific offence.",
        "keywords": ["informed of offence", "specific offence", "notification of charges", "nature of the accusation", "charges explained"],
        "tests": {
            "is_charged": "Has the person been charged with an offence?",
            "delay": "Was the person informed without unreasonable delay?",
            "specificity": "Was the information provided specific enough to allow for a full answer and defence?"
        }
    },
    "11(b)": {
        "title": "Right to Trial Within Reasonable Time",
        "description": "Any person charged with an offence has the right to be tried within a reasonable time.",
        "keywords": ["delay", "reasonable time", "trial within reasonable time", "Jordan",
                      "Jordan framework", "presumptive ceiling", "institutional delay",
                      "adjournment", "continuation", "stay of proceedings"],
        "tests": {
            "is_charged": "Has the person been charged with an offence?",
            "jordan_framework": "Does the delay exceed the Jordan presumptive ceiling (18 months provincial / 30 months superior)?",
            "defence_delay": "Was the delay caused by the defence?",
            "exceptional_circumstances": "Are there exceptional circumstances justifying the delay?"
        }
    },
    "11(c)": {
        "title": "Right Not to Be Compelled as Witness",
        "description": "Any person charged with an offence has the right not to be compelled to be a witness in proceedings against that person.",
        "keywords": ["compelled witness", "testify against self", "self-incrimination",
                      "right to silence", "compelled testimony", "immunity"],
        "tests": {
            "is_charged": "Has the person been charged with an offence?",
            "compelled": "Is the person being compelled to be a witness against themselves?",
            "use_immunity": "Is adequate use immunity or derivative use immunity provided?"
        }
    },
    "11(d)": {
        "title": "Right to Be Presumed Innocent",
        "description": "Any person charged with an offence has the right to be presumed innocent until proven guilty according to law in a fair and public hearing by an independent and impartial tribunal.",
        "keywords": ["independent tribunal", "impartial tribunal", "judicial independence",
                      "fair hearing", "public hearing", "bias", "reasonable apprehension of bias"],
        "tests": {
            "impartiality": "Is the tribunal independent and impartial?",
            "fair_hearing": "Is the hearing fair and public?",
            "bias": "Is there a reasonable apprehension of bias?"
        }
    },
    "12": {
        "title": "Right Not to Be Subject to Cruel and Unusual Treatment",
        "description": "Everyone has the right not to be subjected to any cruel and unusual treatment or punishment.",
        "keywords": ["cruel", "unusual", "punishment", "treatment", "excessive", "disproportionate",
                      "solitary confinement", "mandatory minimum", "grossly disproportionate",
                      "degrading", "torture", "inhuman", "sentencing"],
        "tests": {
            "is_punishment": "Is there a punishment or treatment imposed by the state?",
            "gross_disproportionality": "Is the punishment or treatment grossly disproportionate to the offence?",
            "degrading": "Is the treatment degrading or inhumane?",
            "mandatory_minimum": "Is a mandatory minimum sentence at issue (does it allow for individualized justice)?",
            "standards": "Does the punishment exceed what is acceptable in a free and democratic society?"
        }
    },
    "13": {
        "title": "Right Against Self-Incrimination",
        "description": "A witness shall not be incriminated by any evidence given in proceedings.",
        "keywords": ["self-incrimination", "incriminating evidence", "subsequent prosecution",
                      "use immunity", "derivative use immunity", "testimony used against"],
        "tests": {
            "is_witness": "Was the person a witness in proceedings?",
            "incriminated": "Is the evidence given being used to incriminate the witness in other proceedings?",
            "use_immunity": "Is adequate protection against self-incrimination provided?"
        }
    },
    "14": {
        "title": "Right to an Interpreter",
        "description": "A party or witness in any proceedings who does not understand or speak the language in which the proceedings are conducted has the right to the assistance of an interpreter.",
        "keywords": ["interpreter", "translation", "language", "understanding",
                      "deaf", "sign language", "proceedings", "communication", "comprehension"],
        "tests": {
            "language_barrier": "Does the person not understand or speak the language of the proceedings?",
            "need_for_interpreter": "Is an interpreter necessary for the person to participate meaningfully?",
            "provided": "Was an interpreter provided?"
        }
    },
    "15(1)": {
        "title": "Equality Rights",
        "description": "Every individual is equal before and under the law and has the right to the equal protection and equal benefit of the law without discrimination based on race, national or ethnic origin, colour, religion, sex, age or mental or physical disability.",
        "keywords": ["equality", "discrimination", "race", "national origin", "ethnic origin",
                      "colour", "religion", "sex", "gender", "age", "disability", "sexual orientation",
                      "equal protection", "equal benefit", "analogous ground", "substantive equality",
                      "adverse effects discrimination", "direct discrimination", "woman", "female", "man", "male"],
        "tests": {
            "distinction": "Does the law create a distinction based on an enumerated or analogous ground?",
            "discriminatory_effect": "Does the distinction create a disadvantage by perpetuating prejudice or stereotyping?",
            "enumerated_ground": "Is the ground enumerated in s.15(1) (race, national origin, ethnicity, colour, religion, sex, age, disability)?",
            "analogous_ground": "Is the ground analogous to those enumerated (e.g., sexual orientation, marital status, citizenship)?"
        }
    },
    "24": {
        "title": "Remedies for Infringement",
        "description": "Anyone whose rights or freedoms, as guaranteed by this Charter, have been infringed or denied may apply to a court of competent jurisdiction to obtain such remedy as the court considers appropriate and just in the circumstances.",
        "keywords": ["remedy", "24(1)", "24(2)", "exclusion of evidence", "appropriate and just",
                      "stay of proceedings", "damages", "judicial stay", "abuse of process"],
        "tests": {
            "competent_jurisdiction": "Is the court one of competent jurisdiction to grant the remedy?",
            "infringement": "Has a Charter right or freedom been infringed or denied?",
            "appropriate_and_just": "Is the requested remedy appropriate and just in the circumstances?",
            "disrepute": "For s.24(2), would admission of the evidence bring the administration of justice into disrepute?"
        }
    }
}

# Section 1 Oakes Test (Justification)
OAKES_TEST = {
    "1": {
        "title": "Reasonable Limits — Section 1 Oakes Test",
        "description": "The rights and freedoms guaranteed are subject to such reasonable limits prescribed by law as can be demonstrably justified in a free and democratic society.",
        "steps": {
            "step1_prescribed_by_law": {
                "question": "Is the limit prescribed by law (is there a valid law/rule)?",
                "sub_questions": [
                    "Is there a validly enacted law or rule?",
                    "Is the law sufficiently precise and accessible?"
                ]
            },
            "step2_pressing_objective": {
                "question": "Is the objective of the law pressing and substantial?",
                "sub_questions": [
                    "Is the objective important enough to justify overriding a Charter right?",
                    "Is the objective consistent with the values of a free and democratic society?"
                ]
            },
            "step3_rational_connection": {
                "question": "Is there a rational connection between the objective and the means?",
                "sub_questions": [
                    "Are the measures carefully designed to achieve the objective?",
                    "Is there a causal connection between the law and the objective?",
                    "Is the law arbitrary?"
                ]
            },
            "step4_minimal_impairment": {
                "question": "Does the law minimally impair the Charter right?",
                "sub_questions": [
                    "Are there less intrusive means available that would achieve the objective?",
                    "Does the law sweep more broadly than necessary?",
                    "Is the impairment proportionate to the benefit?"
                ]
            },
            "step5_proportionality": {
                "question": "Is there proportionality between the effects and the objective?",
                "sub_questions": [
                    "Do the salutary effects outweigh the deleterious effects?",
                    "Is the law proportionate in its impact?",
                    "Does the benefit outweigh the harm to the individual?"
                ]
            }
        }
    }
}
OAKS_TEST = OAKES_TEST  # Compatibility alias for misspelling in main.py

# Application Settings
APP_TITLE = "Project Phoenix — Authoritative Charter Analysis"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# Analysis thresholds
MIN_KEYWORD_MATCH = 1  # Minimum keyword matches to flag potential breach
CONFIDENCE_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25
}

# User-specific focus sections (Set to empty list to analyze entire Charter)
FOCUS_CHARTER_SECTIONS = []

# Specific User Flags
SPECIFIC_FLAGS = {
    "health_explanation_ignored": {
        "patterns": [r'\b(anxiety|medical|joint|cannabis|pot|weed|smoke|smoked)\b.*' + 
                        r'\b(arrested|detained|searched|RTC|cautioned)\b',
                        r'\b(stated|claimed|said)\b.*\b(anxiety|medical|health)\b'],
        "label": "Health-Based Explanation Ignored",
        "description": "The document indicates the individual provided a health-related explanation (e.g., anxiety, medical use) for their behavior, but was arrested regardless. Under R v Chehil, suspicion must be objectively reasonable; ignoring a plausible lawful explanation may undermine grounds for arrest (s.9) and equality rights (s.15)."
    },

    
    "lack_of_photos": {
        "patterns": [r'\black\s+of\s+(?:photos?|photographs?|images?|pictures?)\b', r'\bno\s+(?:photos?|photographs?|images?|pictures?)\s+(?:taken|available|provided)\b'],
        "label": "Lack of Photos",
        "description": "The document indicates a lack of photographic evidence, which may affect the reliability of observations or searches."
    }
}

# CanLII Database IDs
CANLII_DATABASES = {
    "scc": "csc-scc",
    "federal_court": "cf",
    "federal_court_appeal": "caf",
    "ontario_scj": "onsc",
    "ontario_caj": "onca",
    "bc_scj": "bcsc",
    "bc_caj": "bcca",
    "alberta_qb": "abqb",
    "alberta_ab": "abca",
    "quebec_sc": "qccs",
    "quebec_ca": "qcca",
}
