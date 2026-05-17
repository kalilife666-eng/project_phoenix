# Copyright project_phoenix
LEGAL_DICTIONARY = {
    "anxiety": {
        "legal_definition": "A recognized mental health condition that constitutes a disability under Section 15 of the Charter. Where an individual's behavior (e.g., medical cannabis use for symptom management) is a direct manifestation of a disability, the state has a duty to accommodate to the point of undue hardship. Arresting an individual for behavior that is a non-criminal manifestation of a disability may constitute discrimination and an arbitrary detention (s.9) if the health-based explanation was plausible and ignored.",
        "legal_source": "R v Chehil, 2013 SCC 49; Charter s. 15(1)",
        "matched_as": "anxiety / mental health disability"
    },

    "charter": {
        "definition": "The Canadian Charter of Rights and Freedoms, being Part I of the Constitution Act, 1982 (Schedule B to the Canada Act 1982 (UK), 1982, c. 11).",
        "source": "Constitution Act, 1982",
        "category": "constitutional",
        "aliases": ["canadian charter", "canadian charter of rights and freedoms", "the charter"],
        "misuses": ["charter of rights", "rights charter", "charter of freedoms"],
        "preferred_form": "Canadian Charter of Rights and Freedoms",
    },
    "breach": {
        "definition": "A violation or infringement of a right guaranteed under the Canadian Charter of Rights and Freedoms. Established when the claimant demonstrates, on a balance of probabilities, that a Charter right has been violated (R v Oakes, 1986 SCC 66).",
        "source": "R v Oakes, [1986] 1 SCR 103; Charter s.24",
        "category": "constitutional",
        "aliases": ["violation", "infringement", "charter breach", "charter violation"],
        "misuses": ["charter break", "breaking the charter", "charter offense"],
        "preferred_form": "breach",
    },
    "infringement": {
        "definition": "A contravention or violation of a Charter right or freedom. Used interchangeably with 'breach' in Canadian constitutional law. See 'breach'.",
        "source": "Charter of Rights and Freedoms; R v Oakes",
        "category": "constitutional",
        "aliases": ["violation", "breach"],
        "misuses": ["infringement", "infraction"],
        "preferred_form": "infringement",
    },
    "oakes_test": {
        "definition": "The two-step proportionality test established in R v Oakes, [1986] 1 SCR 103, for determining whether a limit on a Charter right can be justified under Section 1. Step 1: Is the limit prescribed by law and is the objective pressing and substantial? Step 2: Proportionality — (a) rational connection, (b) minimal impairment, (c) proportionality of effects.",
        "source": "R v Oakes, [1986] 1 SCR 103",
        "category": "constitutional",
        "aliases": ["section 1 analysis", "s.1 analysis", "s.1 test", "oakes proportionality test"],
        "misuses": ["oaks test", "oak's test", "the oakes", "s1 test"],
        "preferred_form": "Oakes test",
    },
    "reasonable_limits": {
        "definition": "Limits on Charter rights that are prescribed by law and can be demonstrably justified in a free and democratic society, pursuant to Section 1 of the Charter. See Oakes test.",
        "source": "Charter, s.1; R v Oakes",
        "category": "constitutional",
        "aliases": ["s.1 limits", "section 1 limits", "justified limits", "prescribed by law"],
        "misuses": ["reasonable restrictions", "reasonable limitations"],
        "preferred_form": "reasonable limits prescribed by law",
    },
    "prescribed_by_law": {
        "definition": "A requirement under Section 1 of the Charter that a limit on a right must have a legal basis — enacted by valid legislation or regulation — and must be sufficiently precise and accessible (Ontario v Canadian Pacific Ltd, [1995] 2 SCR 1035).",
        "source": "Charter, s.1; Ontario v Canadian Pacific Ltd",
        "category": "constitutional",
        "aliases": [], "misuses": ["set by law", "written in law"],
        "preferred_form": "prescribed by law",
    },
    "principles_of_fundamental_justice": {
        "definition": "The core principles against which deprivations of life, liberty, or security of the person under Section 7 of the Charter are measured. These are not merely procedural; they include substantive norms that are: (1) a legal principle, (2) fundamental to our justice system, (3) identifiable with precision (R v Malmo-Levine, 2003 SCC 74).",
        "source": "R v Malmo-Levine, 2003 SCC 74; Charter s.7",
        "category": "constitutional",
        "aliases": ["fundamental justice", "pfj"],
        "misuses": ["fundamental principles of justice", "basic justice"],
        "preferred_form": "principles of fundamental justice",
    },
    "remedy": {
        "definition": "A court-ordered means of redress for a Charter breach, pursuant to Section 24(1) of the Charter. Remedies include: stay of proceedings, exclusion of evidence, damages, declaratory relief, injunctions, and mandamus. The remedy must be 'appropriate and just' in the circumstances (R v 974649 Ontario Inc, 2001 SCC 81).",
        "source": "Charter s.24(1); R v 974649 Ontario Inc",
        "category": "constitutional",
        "aliases": ["charter remedy", "relief"],
        "misuses": ["charter reward", "compensation (when not referring to damages remedy specifically)"],
        "preferred_form": "remedy",
    },
    "exclusion_of_evidence": {
        "definition": "A remedy under Section 24(2) of the Charter whereby evidence obtained in a manner that infringed a Charter right is excluded if its admission would bring the administration of justice into disrepute. The three-factor Grant test applies (R v Grant, 2009 SCC 26).",
        "source": "Charter s.24(2); R v Grant, 2009 SCC 26",
        "category": "constitutional",
        "aliases": ["s.24(2) exclusion", "exclusion under s.24(2)", "24(2) remedy"],
        "misuses": ["suppression of evidence", "throwing out evidence"],
        "preferred_form": "exclusion of evidence",
    },
    "arrest": {
        "definition": "The taking or keeping of a person in custody by legal authority, especially in response to a criminal charge. Under the Criminal Code, an arrest requires: (1) intention to arrest, (2) grounds for arrest, and (3) notification that the person is under arrest (R v Whitfield, [1967] 1 SCR 25).",
        "source": "Criminal Code, RSC 1985, c. C-46, s.495; R v Whitfield",
        "category": "criminal_procedure",
        "aliases": ["taken into custody", "placed under arrest"],
        "misuses": ["apprehension (unless under Youth Criminal Justice Act)", "detainment"],
        "preferred_form": "arrest",
    },
    "detention": {
        "definition": "A suspension of liberty, whether physical or psychological. Physical detention occurs when police use physical constraint. Psychological detention occurs when a reasonable person would conclude they are not free to leave (R v Therens, [1985] 1 SCR 613; R v Grant, 2009 SCC 26). Includes investigative detention.",
        "source": "R v Grant, 2009 SCC 26; R v Therens",
        "category": "criminal_procedure",
        "aliases": ["investigative detention", "being detained", "held for questioning"],
        "misuses": ["arrest (when no formal arrest made)", "custody (distinct concept)", "holding"],
        "preferred_form": "detention",
    },
    "custody": {
        "definition": "The state of being under the control or guardianship of the state. Distinct from arrest and detention. Pre-trial custody refers to time spent in detention before trial; post-conviction custody refers to imprisonment after conviction.",
        "source": "Criminal Code; Corrections and Conditional Release Act",
        "category": "criminal_procedure",
        "aliases": ["pre-trial custody", "remand custody", "custodial", "in custody"],
        "misuses": ["holding", "jail time (informal)"],
        "preferred_form": "custody",
    },
    "bail": {
        "definition": "The conditional release of an accused person pending trial pursuant to Section 515 of the Criminal Code. The constitutional right to reasonable bail is protected by Section 11(e) of the Charter. The default position is release on the least onerous conditions (R v Antic, 2017 SCC 27).",
        "source": "Criminal Code, s.515; Charter s.11(e); R v Antic",
        "category": "criminal_procedure",
        "aliases": ["judicial interim release", "release", "bail hearing"],
        "misuses": ["bond (criminal law)", "parole (distinct concept)"],
        "preferred_form": "judicial interim release (formal) / bail (general)",
    },
    "search_warrant": {
        "definition": "A written order issued by a justice or judge under Section 487 of the Criminal Code authorizing a peace officer to search a place or thing and seize evidence. Must be based on information under oath establishing reasonable grounds to believe an offence has been committed and evidence will be found.",
        "source": "Criminal Code, ss.487, 487.01-487.09",
        "category": "criminal_procedure",
        "aliases": ["warrant", "search and seizure warrant", "telewarrant (for telewarrants)"],
        "misuses": ["warrant of arrest (distinct)", "court order (too general)"],
        "preferred_form": "search warrant",
    },
    "wiretap": {
        "definition": "Authorization for interception of private communications under Part VI of the Criminal Code (ss.183-196). Requires prior judicial authorization based on reasonable grounds, though Part VI authorization is not always required.",
        "source": "Criminal Code, Part VI; Charter s.8",
        "category": "criminal_procedure",
        "aliases": ["interception of communications", "electronic surveillance", "part VI authorization"],
        "misuses": ["wire tapping", "phone tap", "bugging"],
        "preferred_form": "authorization for interception of private communications",
    },
    "disclosure": {
        "definition": "The Crown's obligation to provide the defence with all relevant, non-privileged information in its possession or control, subject to statutory and common law exceptions. A constitutional duty under Section 7 of the Charter (R v Stinchcombe, [1991] 3 SCR 326).",
        "source": "R v Stinchcombe, [1991] 3 SCR 326; Charter s.7",
        "category": "criminal_procedure",
        "aliases": ["crown disclosure", "stinchcombe disclosure", "first-party disclosure"],
        "misuses": ["discovery (civil procedure concept)", "production"],
        "preferred_form": "disclosure",
    },
    "stay_of_proceedings": {
        "definition": "A judicial remedy that permanently terminates proceedings against an accused, available as a Charter remedy under Section 24(1) for breaches of Section 11(b) (unreasonable delay per R v Jordan, 2016 SCC 27) or for abuse of process. A permanent stay is an exceptional remedy only for the clearest of cases.",
        "source": "Charter s.24(1); R v Jordan, 2016 SCC 27; R v O'Connor",
        "category": "criminal_procedure",
        "aliases": ["judicial stay", "stay", "staying the proceedings"],
        "misuses": ["dismissal (provincial offences context)", "acquittal (distinct)"],
        "preferred_form": "stay of proceedings",
    },
    "acquittal": {
        "definition": "A finding of not guilty following a trial on the merits. The accused is entitled to the benefit of any reasonable doubt — the presumption of innocence requires proof beyond a reasonable doubt.",
        "source": "Criminal Code; Charter s.11(d)",
        "category": "criminal_procedure",
        "aliases": ["not guilty finding", "finding of not guilty"],
        "misuses": ["dismissal (distinct — no finding on merits)", "exoneration (informal)"],
        "preferred_form": "acquittal",
    },
    "voir_dire": {
        "definition": "A hearing within a trial, typically to determine the admissibility of evidence (e.g., confessions, Charter-affected evidence) or the competence of a witness. Conducted in the absence of the jury.",
        "source": "Criminal Code; common law",
        "category": "criminal_procedure",
        "aliases": ["trial within a trial", "admissibility hearing", "voir dire hearing"],
        "misuses": ["voir dire trial", "voir dire hearing (strictly, it IS within a trial)"],
        "preferred_form": "voir dire",
    },
    "beyond_reasonable_doubt": {
        "definition": "The standard of proof required for a criminal conviction. It falls much closer to absolute certainty than to proof on a balance of probabilities. It is based on reason and common sense, logically connected to the evidence and not based on sympathy or prejudice (R v Lifchus, [1997] 3 SCR 320).",
        "source": "R v Lifchus; Charter s.11(d)",
        "category": "evidence",
        "aliases": ["brd", "reasonable doubt standard", "criminal standard of proof"],
        "misuses": ["beyond a shadow of a doubt", "100% certainty", "preponderance of doubt"],
        "preferred_form": "beyond a reasonable doubt",
    },
    "balance_of_probabilities": {
        "definition": "The civil standard of proof. The party bearing the burden must establish that it is more likely than not (greater than 50%) that the fact in question is true. Also applies to Charter breach claims (R v Oakes) and certain evidentiary burdens on the accused.",
        "source": "R v Oakes; civil jurisprudence",
        "category": "evidence",
        "aliases": ["civil standard", "preponderance of evidence", "more likely than not"],
        "misuses": ["balance of doubt", "probability balance"],
        "preferred_form": "balance of probabilities",
    },
    "reasonable_expectation_of_privacy": {
        "definition": "The threshold for establishing a Section 8 Charter claim. A claimant must demonstrate: (1) they subjectively expected privacy in the subject matter, and (2) that expectation was objectively reasonable in the circumstances (R v Hunter v Southam, [1984] 2 SCR 145; R v Tessling, 2004 SCC 5).",
        "source": "Hunter v Southam; R v Tessling; Charter s.8",
        "category": "evidence",
        "aliases": ["rep", "privacy expectation", "expectation of privacy"],
        "misuses": ["right to privacy", "privacy right (Charter doesn't create a free-standing right to privacy)"],
        "preferred_form": "reasonable expectation of privacy",
    },
    "reasonable_grounds": {
        "definition": "An objective standard: whether a reasonable person standing in the shoes of the officer would have had grounds to believe the relevant fact. More than mere suspicion but less than proof on a balance of probabilities (R v Storrey, [1990] 1 SCR 241).",
        "source": "Criminal Code; R v Storrey",
        "category": "evidence",
        "aliases": ["reasonable and probable grounds", "objective grounds", "objective basis", "rpg", "grounds", "probable cause (US term)"],
        "misuses": ["probable cause (American standard — not Canadian)", "reasonable suspicion (lower standard)"],
        "preferred_form": "reasonable grounds",
    },
    "photographic_corroboration": {
        "definition": "Photographs or images tendered to confirm a material fact, preserve the condition of an exhibit, or provide objective corroboration for an officer's narrative. The absence of expected photographs may weaken reliability, continuity, or the objective basis for a search, seizure, detention, or arrest.",
        "source": "R v Nikolovski, [1996] 3 SCR 1197; Charter ss.8-9",
        "category": "evidence",
        "aliases": ["photo corroboration", "photographic corroboration", "picture corroboration", "photos", "pictures", "images", "no photos", "no pictures"],
        "misuses": ["proof by picture alone", "automatic verification"],
        "preferred_form": "photographic corroboration",
    },
    "identification": {
        "definition": "Evidence tending to show that a particular person is the actor involved in the alleged event. Identification evidence must be approached cautiously because of the risk of honest but mistaken identification; weak or absent identification undermines grounds and trial reliability.",
        "source": "R v Hibbert, 2002 SCC 39; R v Tat, 1997 CanLII 2235 (ON CA)",
        "category": "evidence",
        "aliases": ["identify", "identified", "identification", "could not identify", "unable to identify", "no identification"],
        "misuses": ["identity proof by assumption", "identification by hunch"],
        "preferred_form": "identification evidence",
    },
    "crime_scene": {
        "definition": "The physical location where the alleged offence is said to have occurred or where material evidence is said to originate. A missing or undefined crime scene can weaken the inference that seized property is connected to a specific offence.",
        "source": "Criminal evidence principles; Charter ss.8-9",
        "category": "evidence",
        "aliases": ["crime scene", "theft scene", "scene of the offence", "scene of offence", "offence scene"],
        "misuses": ["scene assumed without proof"],
        "preferred_form": "crime scene",
    },
    "scene_nexus": {
        "definition": "The evidentiary link connecting a person, place, or seized item to a specific offence location or criminal event. Without a demonstrated nexus, police suspicion may remain speculative and fall short of reasonable and probable grounds.",
        "source": "R v Mann, 2004 SCC 52; R v Tim, 2022 SCC 12; Charter ss.8-9",
        "category": "evidence",
        "aliases": ["scene nexus", "scene linkage", "linked to the scene", "linked to any crime scene", "linked to any theft scene", "source location nexus", "crime scene nexus", "linked to a crime scene", "linked to the crime scene", "no crime scene that the material was linked to"],
        "misuses": ["nexus inferred from possession alone"],
        "preferred_form": "scene nexus",
    },
    "seized_material": {
        "definition": "The physical property taken by police during a search or seizure and relied on as evidence. Accurate description, continuity, and linkage to the alleged offence are essential; material inconsistencies in description can undermine grounds and reliability.",
        "source": "Criminal evidence principles; Charter s.8",
        "category": "evidence",
        "aliases": ["seized material", "material seized", "seized property", "bell cable", "copper wire", "seized wire", "seized cable"],
        "misuses": ["generic property description without particulars"],
        "preferred_form": "seized material",
    },
    "reasonable_suspicion": {
        "definition": "A standard lower than reasonable grounds, requiring only an objectively discernible basis for suspicion. Insufficient for arrest or search warrant authorization but may suffice for investigative detention (R v Chehil, 2013 SCC 49).",
        "source": "R v Chehil, 2013 SCC 49",
        "category": "evidence",
        "aliases": ["suspicion", "articulable cause"],
        "misuses": ["reasonable grounds (higher standard)", "hunch (no objective basis)"],
        "preferred_form": "reasonable suspicion",
    },
    "confession": {
        "definition": "A statement made by an accused person acknowledging guilt of an offence. To be admissible, the Crown must prove beyond a reasonable doubt that the confession was voluntary, applying the Ibrahim rule and its common law extensions (R v Oickle, 2000 SCC 38).",
        "source": "R v Oickle; R v Ibrahim",
        "category": "evidence",
        "aliases": ["voluntary statement", "admission of guilt", "self-incriminating statement"],
        "misuses": ["admission (not all admissions are confessions to the offence)"],
        "preferred_form": "confession (for statements acknowledging guilt) / voluntary statement (for admissibility context)",
    },
    "hearsay": {
        "definition": "An out-of-court statement adduced to prove the truth of its contents. Generally inadmissible unless it falls within a recognized exception or satisfies the principled approach to admissibility (R v Khelawon, 2006 SCC 57). The principled exception requires necessity and reliability.",
        "source": "R v Khelawon; R v Starr",
        "category": "evidence",
        "aliases": ["hearsay statement", "out-of-court statement", "double hearsay (hearsay within hearsay)"],
        "misuses": ["second-hand information (imprecise)", "rumour"],
        "preferred_form": "hearsay",
    },
    "derivative_evidence": {
        "definition": "Evidence discovered as a result of an initial Charter breach. Under s.24(2), derivative evidence may be excluded if its admission would bring the administration of justice into disrepute. Distinguished from non-derivative evidence.",
        "source": "Charter s.24(2); R v Grant",
        "category": "evidence",
        "aliases": ["fruit of the poisonous tree (US doctrine — not Canadian)", "discovered evidence"],
        "misuses": ["fruit of the poisonous tree (American doctrine not adopted in Canada)"],
        "preferred_form": "derivative evidence",
    },
    "mandatory_minimum": {
        "definition": "A statutory minimum sentence that a court must impose upon conviction for a specified offence, removing judicial discretion to impose a lesser sentence. Subject to Charter challenge under Section 12 (cruel and unusual punishment) or Section 7 (overbreadth/arbitrariness) (R v Nur, 2015 SCC 15; R v Lloyd, 2016 SCC 13).",
        "source": "Criminal Code; Charter ss.7, 12; R v Nur; R v Lloyd",
        "category": "sentencing",
        "aliases": ["mandatory minimum sentence", "mms", "minimum sentence", "statutory minimum"],
        "misuses": ["mandatory sentence (imprecise)", "minimum penalty"],
        "preferred_form": "mandatory minimum sentence",
    },
    "proportionality": {
        "definition": "The fundamental principle of sentencing in Canada (Criminal Code s.718.1): a sentence must be proportionate to the gravity of the offence and the degree of responsibility of the offender. Also a requirement under Section 1 Oakes test and Section 12 of the Charter.",
        "source": "Criminal Code s.718.1; Charter ss.1, 12",
        "category": "sentencing",
        "aliases": ["proportionate sentence", "proportionality principle"],
        "misuses": ["proportional (Canadian legal usage prefers 'proportionate')", "balanced sentence"],
        "preferred_form": "proportionality",
    },
    "conditional_sentence": {
        "definition": "A sentence of imprisonment that may be served in the community under strict conditions (Criminal Code s.742.1). Available only where: (1) the offence has no mandatory minimum, (2) the term is less than two years, and (3) serving in the community does not endanger safety.",
        "source": "Criminal Code s.742.1; R v Proulx, 2000 SCC 5",
        "category": "sentencing",
        "aliases": ["house arrest", "cs", "conditional sentence order", "cso"],
        "misuses": ["probation (distinct order)", "suspended sentence"],
        "preferred_form": "conditional sentence",
    },
    "credit_for_pre-trial_custody": {
        "definition": "Enhanced credit for time spent in pre-trial custody prior to sentencing. Under Criminal Code s.719(3), the court may credit up to 1.5 days for each day of pre-trial custody, absent circumstances justifying a different ratio (R v Summers, 2014 SCC 36).",
        "source": "Criminal Code s.719(3); R v Summers",
        "category": "sentencing",
        "aliases": ["pre-trial custody credit", "enhanced credit", "1.5:1 credit", "dead time"],
        "misuses": ["time served (informal and imprecise)", "dead time credit"],
        "preferred_form": "credit for pre-trial custody",
    },
    "actus_reus": {
        "definition": "The physical or external element of an offence. Consists of: (1) a voluntary act (or omission where there is a legal duty to act), (2) that causes (3) the prohibited consequence or result. Must be voluntary — automatism negates actus reus.",
        "source": "Criminal Code; R v Parks; common law",
        "category": "offences",
        "aliases": ["guilty act", "physical element", "external element", "prohibited act"],
        "misuses": ["the act", "the crime itself"],
        "preferred_form": "actus reus",
    },
    "mens_rea": {
        "definition": "The mental element of an offence. The minimum requirement is awareness of the factual circumstances giving rise to the offence or, for crimes of negligence, objective failure to meet a standard of care. Includes subjective intent (intent, knowledge, recklessness, willful blindness) and objective fault (criminal negligence, etc.).",
        "source": "Criminal Code; R v Sansregret; R v City of Sault Ste Marie",
        "category": "offences",
        "aliases": ["guilty mind", "mental element", "fault element", "subjective fault", "objective fault"],
        "misuses": ["intent (only one form of mens rea)", "motive (distinct concept)"],
        "preferred_form": "mens rea",
    },
    "strict_liability": {
        "definition": "An offence where the Crown need not prove mens rea, but the accused may avoid liability by establishing on a balance of probabilities that they exercised due diligence (R v City of Sault Ste Marie, [1978] 2 SCR 1299).",
        "source": "R v City of Sault Ste Marie",
        "category": "offences",
        "aliases": ["strict liability offence", "due diligence offence"],
        "misuses": ["absolute liability (no due diligence defence)", "no-fault liability"],
        "preferred_form": "strict liability",
    },
    "absolute_liability": {
        "definition": "An offence where conviction follows proof of actus reus alone, with no due diligence defence available. Conviction of an absolute liability offence subject to imprisonment violates Section 7 of the Charter (R v City of Sault Ste Marie; Reference re s.94(2) Motor Vehicle Act).",
        "source": "R v City of Sault Ste Marie; Charter s.7",
        "category": "offences",
        "aliases": ["absolute liability offence", "no-fault offence"],
        "misuses": ["strict liability (due diligence available)", "no mens rea offence (overgeneral)"],
        "preferred_form": "absolute liability",
    },
    "self_defence": {
        "definition": "A defence under Section 34 of the Criminal Code permitting the use of force to defend against an assault. Requires: (1) the accused reasonably believed force was being used against them, (2) the act was committed for the purpose of defending, and (3) the act was reasonable in the circumstances.",
        "source": "Criminal Code s.34; R v Lavallée",
        "category": "defences",
        "aliases": ["defence of the person", "defence of self"],
        "misuses": ["self protection", "standing your ground (American concept)"],
        "preferred_form": "self-defence",
    },
    "necessity": {
        "definition": "A common law defence where an accused commits an offence to avoid an urgent peril. Requirements (R v Latimer, 2001 SCC 1): (1) imminent peril, (2) no reasonable legal alternative, and (3) proportionality. Extremely narrow.",
        "source": "R v Latimer; R v Perka",
        "category": "defences",
        "aliases": ["defence of necessity", "choice of evils", "competing harms"],
        "misuses": ["emergency defence", "duress (distinct — threat from another person)"],
        "preferred_form": "defence of necessity",
    },
    "entrapment": {
        "definition": "An abuse of process defence where the state induces the commission of an offence that would not otherwise have occurred. Two approaches in Canada: (1) the 'random virtue testing' approach (offering opportunity only), and (2) the 'susceptible person' approach (providing the means and instigation). If established, a stay of proceedings is the only remedy (R v Mack, [1988] 2 SCR 903).",
        "source": "R v Mack; R v Barnes",
        "category": "defences",
        "aliases": ["trap", "police entrapment"],
        "misuses": ["sting operation (lawful if not entrapment)", "setup"],
        "preferred_form": "entrapment",
    },
    "abuse_of_process": {
        "definition": "A common law doctrine allowing a stay of proceedings where state conduct is so prejudicial to the accused's right to a fair trial, or so offensive to the administration of justice, that the proceedings should be terminated. Includes entrapment, delay, non-disclosure, and misconduct.",
        "source": "R v O'Connor; R v Keyowski; Charter s.7, s.11(d), s.24(1)",
        "category": "defences",
        "aliases": ["process abuse", "abuse"],
        "misuses": ["unfair trial (imprecise)", "prosecutorial misconduct (subset)"],
        "preferred_form": "abuse of process",
    },
    "accused": {
        "definition": "A person charged with an offence under the Criminal Code or other federal statute. Entitled to the presumption of innocence, the right to a fair trial, and all Charter protections applicable to persons charged with offences (Charter s.11).",
        "source": "Criminal Code; Charter s.11",
        "category": "parties",
        "aliases": ["defendant (criminal — though technically correct)", "respondent (appeal context)", "appellant (when appealing)"],
        "misuses": ["defendant (civil law term preferred in that context)", "perpetrator (prejudges guilt)", "offender (distinct — convicted)"],
        "preferred_form": "accused",
    },
    "crown": {
        "definition": "The state as represented by the prosecutor in criminal proceedings. The Crown bears the burden of proving the accused's guilt beyond a reasonable doubt. Includes the Attorney General and their delegates.",
        "source": "Criminal Code; Constitution Act, 1867",
        "category": "parties",
        "aliases": ["the crown", "prosecution", "prosecutor", "the state"],
        "misuses": ["the government (too general)", "the people (Americanism)"],
        "preferred_form": "the Crown (formal) / Crown (adjectival)",
    },
    "peace_officer": {
        "definition": "A person defined in Criminal Code s.2 as a peace officer, including police officers, customs officers, and others designated by statute. Entitled to exercise powers conferred on peace officers by law.",
        "source": "Criminal Code s.2",
        "category": "parties",
        "aliases": ["police officer", "officer", "law enforcement"],
        "misuses": ["cop (informal)", "law enforcement officer (US term)"],
        "preferred_form": "peace officer (statutory) / police officer (specific) / officer (contextual)",
    },
    "informant": {
        "definition": "A person who provides information to police, including confidential informants whose identity is protected by privilege (Legal Services Society v BC, 2002 SCC 29; R v Barros, 2019 SCC 66). Informant privilege is a class privilege.",
        "source": "Criminal Code; R v Barros; Legal Services Society v BC",
        "category": "parties",
        "aliases": ["confidential informant", "ci", "source"],
        "misuses": ["spy", "snitch (informal)", "tipster (informal)"],
        "preferred_form": "informant / confidential informant",
    },
    "duty_of_fairness": {
        "definition": "The common law duty requiring procedural fairness in administrative and governmental decision-making. Applies when an individual's rights, privileges, or interests are at stake. Content varies with context (Baker v Canada, [1999] 2 SCR 817). Distinct from, but related to, natural justice.",
        "source": "Baker v Canada; Knight v Indian Head School Division",
        "category": "procedural",
        "aliases": ["procedural fairness", "fairness duty"],
        "misuses": ["due process (American term)", "natural justice (subset — audi alteram partem and nemo judex)"],
        "preferred_form": "duty of fairness",
    },
    "natural_justice": {
        "definition": "The two common law procedural fairness rules: (1) audi alteram partem (the right to be heard), and (2) nemo judex in causa sua (the rule against bias). A subset of the broader duty of fairness.",
        "source": "Common law; Nicholson v Haldimand-Norfolk",
        "category": "procedural",
        "aliases": ["rules of natural justice"],
        "misuses": ["due process (American)", "fairness (broader)"],
        "preferred_form": "natural justice",
    },
    "reasonable_apprehension_of_bias": {
        "definition": "The test for bias: would a reasonable, informed person, viewing the matter realistically and practically, apprehend that the decision-maker might not bring an impartial mind to the proceedings? (Committee for Justice and Liberty v Canada, [1978] 1 SCR 369; R v S(RD), [1997] 3 SCR 484).",
        "source": "Committee for Justice and Liberty; R v S(RD)",
        "category": "procedural",
        "aliases": ["bias", "apprehension of bias", "reasonable apprehension"],
        "misuses": ["appearance of bias (not the Canadian test)", "actual bias (higher threshold)"],
        "preferred_form": "reasonable apprehension of bias",
    },
    "onus": {
        "definition": "The burden of proving a fact or set of facts. In criminal law, the prosecution bears the onus of proving guilt beyond a reasonable doubt (Woolmington v DPP). A reverse onus places the evidentiary or persuasive burden on the accused.",
        "source": "Woolmington v DPP; Charter s.11(d)",
        "category": "procedural",
        "aliases": ["burden of proof", "burden"],
        "misuses": ["onus of proof (redundant but accepted)"],
        "preferred_form": "onus (or 'burden' depending on context)",
    },
    "reverse_onus": {
        "definition": "A provision that shifts the legal burden of proof from the Crown to the accused. Reverse onus provisions must be justified under Section 1 of the Charter, as they engage the presumption of innocence (R v Oakes; R v Vaillancourt).",
        "source": "R v Oakes; Charter s.11(d), s.1",
        "category": "procedural",
        "aliases": ["shifted burden", "burden on the accused"],
        "misuses": ["presumption of guilt", "guilty until proven innocent"],
        "preferred_form": "reverse onus",
    },
    "jordan": {
        "definition": "R v Jordan, 2016 SCC 27 established the framework for Section 11(b) unreasonable delay. Presumptive ceilings: 18 months for provincial courts, 30 months for superior courts. Exceeding the ceiling is presumptively unreasonable. Defence delay and exceptional circumstances may extend or reduce the ceiling.",
        "source": "R v Jordan, 2016 SCC 27",
        "category": "key_cases",
        "aliases": ["jordan framework", "jordan test", "jordan ceiling", "jordan delay"],
        "misuses": ["jordan rule", "jordan timeline"],
        "preferred_form": "Jordan framework (methodology) / Jordan (case short form)",
    },
    "grant": {
        "definition": "R v Grant, 2009 SCC 26 established the three-factor framework for Section 24(2) exclusion of evidence: (1) seriousness of the Charter-infringing state conduct, (2) impact on the accused's Charter-protected interests, and (3) society's interest in adjudication on the merits.",
        "source": "R v Grant, 2009 SCC 26",
        "category": "key_cases",
        "aliases": ["grant test", "grant framework", "24(2) grant test"],
        "misuses": ["grant doctrine"],
        "preferred_form": "Grant test (for s.24(2) analysis) / R v Grant (case citation)",
    },
    "stinchcombe": {
        "definition": "R v Stinchcombe, [1991] 3 SCR 326. Established the Crown's constitutional duty of disclosure under Section 7 of the Charter. The Crown must disclose all relevant information to the defence, whether inculpatory or exculpatory.",
        "source": "R v Stinchcombe, [1991] 3 SCR 326",
        "category": "key_cases",
        "aliases": ["stinchcombe disclosure", "stinchcombe duty", "disclosure duty"],
        "misuses": ["stinchberg", "stinchcomb"],
        "preferred_form": "Stinchcombe disclosure (for the duty) / R v Stinchcombe (case citation)",
    },
}


TERMINOLOGY_RULES = {
    "judgment": {
        "correct": "judgment",
        "incorrect": ["judgement"],
        "note": "In Canadian legal writing, 'judgment' (without the 'e') is the preferred spelling, consistent with SCC practice."
    },
    "offence": {
        "correct": "offence",
        "incorrect": ["offense"],
        "note": "Canadian spelling uses 'offence'. 'Offense' is American."
    },
    "defence": {
        "correct": "defence",
        "incorrect": ["defense"],
        "note": "Canadian spelling uses 'defence'. 'Defense' is American."
    },
    "licence": {
        "correct": "licence",
        "incorrect": ["license (as noun)"],
        "note": "In Canadian usage, 'licence' is the noun and 'license' is the verb."
    },
    "Crown": {
        "correct": "the Crown",
        "incorrect": ["crown", "the crown", "THE CROWN"],
        "note": "When referring to the prosecuting authority, 'the Crown' must be capitalized."
    },
    "Charter": {
        "correct": "the Charter",
        "incorrect": ["the charter", "Charter (without article in sentence context)"],
        "note": "'Charter' must be capitalized when referring to the Canadian Charter of Rights and Freedoms."
    },
    "section_reference": {
        "correct": "s.",
        "incorrect": ["sec.", "sect.", "S.", "section (when abbreviating)"],
        "note": "Canadian legal citation uses 's.' for section and 'ss.' for sections."
    },
    "subsection_reference": {
        "correct": "ss.",
        "incorrect": ["ss", "s-s", "sub-s"],
        "note": "Use 'ss.' for multiple sections. For subsection, use 's. X(y)'."
    },
    "proportionate": {
        "correct": "proportionate",
        "incorrect": ["proportional"],
        "note": "Canadian jurisprudence uses 'proportionate' rather than 'proportional' (e.g., 'proportionate response')."
    },
    "recognize": {
        "correct": "recognize",
        "incorrect": ["recognise"],
        "note": "Canadian legal writing typically uses the '-ize' form, consistent with the Canadian Oxford Dictionary."
    },
    "organize": {
        "correct": "organize",
        "incorrect": ["organise"],
        "note": "Canadian legal writing uses '-ize' forms."
    },
    "accused_reference": {
        "correct": "the accused",
        "incorrect": ["the Accused", "The Accused", "the defendant (in criminal proceedings)"],
        "note": "'The accused' (lowercase) is correct. 'The Accused' is used only at the start of a sentence or in a defined term."
    },
    "court_reference": {
        "correct": "the court / the Court",
        "incorrect": ["The Court (mid-sentence unless referring to SCC)", "the ct."],
        "note": "Capitalize 'Court' when referring to the Supreme Court of Canada or in a party's own writings.",
    },
    "versus": {
        "correct": "v.",
        "incorrect": ["vs.", "vs", "v", "versus"],
        "note": "In Canadian legal citations, use 'v.' (with period, no period after if in case name)."
    },
    "reasonable_doubt": {
        "correct": "beyond a reasonable doubt",
        "incorrect": ["beyond reasonable doubt", "beyond any doubt", "beyond all doubt", "beyond shadow of a doubt"],
        "note": "The exact phrase is 'beyond a reasonable doubt' — the indefinite article 'a' is required."
    },
    "onus_phrase": {
        "correct": "onus",
        "incorrect": ["onous", "onus of proof (redundant but acceptable)"],
        "note": "Use 'onus' or 'burden of proof'. 'Onus of proof' is common but technically redundant."
    },
}

# ============================================================================
# DEFLECTION / AMBIGUITY PATTERNS
# Patterns that indicate deliberate vagueness, equivocation, or deflection
# ============================================================================

DEFLECTION_PATTERNS = {
    "vague_quantifiers": {
        "patterns": [
            r'\b(?:a number of|several|various|some|certain|numerous|multiple|a few|many)\b',
        ],
        "description": "Vague quantifiers that lack specificity. Legal documents should specify exact numbers or ranges where possible.",
        "severity": "medium",
        "suggestion": "Replace with specific numbers or defined ranges."
    },
    "hedging_language": {
        "patterns": [
            r'\b(?:maybe|perhaps|possibly|it seems|it appears|arguably|one might say|it could be argued)\b',
            r'\b(?:somewhat|rather|kind of|sort of|more or less|to some extent|in a way)\b',
        ],
        "description": "Hedging language that weakens assertions. While some hedging is appropriate in legal analysis, excessive hedging can indicate ambiguity or lack of confidence.",
        "severity": "medium",
        "suggestion": "Determine whether the assertion can be stated with greater certainty or requires qualification with proper legal standards."
    },
    "undefined_references": {
        "patterns": [
            r'\b(?:the aforementioned|the aforementioned|the above-mentioned|said [a-z]+|such [a-z]+)\b',
            r'\b(?:the following|hereinafter|herein|therein|wherein)\b(?!.*defined)',
        ],
        "description": "References to undefined antecedents. Ensure all references clearly identify their subject. 'Said' and 'such' are often used to avoid specificity.",
        "severity": "high",
        "suggestion": "Replace with specific defined terms or repeat the specific reference for clarity."
    },
    "passive_obfuscation": {
        "patterns": [
            r'\b(?:it was determined|it was decided|it was found|it was concluded|it is noted|it is submitted)\b',
            r'\bwas (?:found|determined|decided|concluded|noted|observed|considered)\b(?! by)',
        ],
        "description": "Passive constructions that omit the decision-maker. Legal documents should identify who made the decision, finding, or conclusion.",
        "severity": "high",
        "suggestion": "Identify the actor: 'The trial judge determined...', 'This Court found...', 'The officer decided...'"
    },
    "equivocation": {
        "patterns": [
            r'\b(?:on one hand|on the other hand|at the same time|be that as it may|nevertheless|notwithstanding)\b',
            r'\b(?:while it is true|although|albeit|inasmuch as)\b',
        ],
        "description": "Equivocal language that presents contradictory positions without resolution. While nuance is important, unresolved contradictions undermine clarity.",
        "severity": "medium",
        "suggestion": "Acknowledge both positions but clearly state which prevails and why, or articulate the legal framework for resolution."
    },
    "circular_references": {
        "patterns": [
            r'\b(?:as (?:noted|stated|mentioned|set out|described) (?:above|below|earlier|previously|elsewhere))(?:\s*,\s*(?:see|cf\.|compare)\s*\S+)?\b',
            r'\b(?:see\s+(?:above|below|supra|infra|ibid))\b',
        ],
        "description": "Cross-references without specificity. Ensure references identify the exact location (paragraph number, page, footnote).",
        "severity": "medium",
        "suggestion": "Specify the exact reference: 'as noted at paragraph 14', 'see supra, footnote 7', 'see below, Part III'."
    },
    "weasel_words": {
        "patterns": [
            r'\b(?:clearly|obviously|undoubtedly|certainly|unquestionably|self-evidently|patently|manifestly)\b',
            r'\b(?:it goes without saying|it is axiomatic|as is well known|as everyone knows)\b',
        ],
        "description": "Assertive language without supporting authority. If something is 'clear' or 'obvious,' cite the authority that makes it so. These terms often mask weak analysis.",
        "severity": "high",
        "suggestion": "Either remove the intensifier or replace it with supporting authority: 'As stated in R v Oakes...', 'Section 7 of the Charter provides...'"
    },
    "undefined_terms": {
        "patterns": [
            r'\b(?:appropriate|reasonable|suitable|adequate|proper|sufficient|necessary)\b(?!\s+(?:and\s+)?(?:just|cause|grounds|doubt|notice|time|care|person|steps|precision|opportunity|means))',
        ],
        "description": "Context-dependent legal terms used without definition or contextual anchor. Terms like 'reasonable', 'appropriate', and 'necessary' have specific legal meanings that vary by context.",
        "severity": "high",
        "suggestion": "Define the applicable legal standard: 'reasonable' per what test? 'Appropriate and just' per s.24(1)? 'Necessary' per the principled exception to the hearsay rule?"
    },
    "legalese_obfuscation": {
        "patterns": [
            r'\b(?:notwithstanding|provided that|subject to|without prejudice to|save as|except as)\b.*(?:aforementioned|foregoing|hereinafter)\b',
            r'\b(?:ipse dixit|inter alia|mutatis mutandis|pendente lite|sub judice)\b',
        ],
        "description": "Excessive use of Latin maxims or archaic legal phrasing that obscures meaning. Plain language is preferred in modern Canadian legal writing.",
        "severity": "low",
        "suggestion": "Replace with plain English equivalents: 'inter alia' → 'among other things'; 'mutatis mutandis' → 'with the necessary changes'."
    },
}
