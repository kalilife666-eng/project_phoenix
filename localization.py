"""
French localization helpers for desktop-visible legal analysis output.
"""

from __future__ import annotations

from copy import deepcopy
import re


URL_KEYS = {
    "url",
    "direct_reference",
    "exclusion_reference",
}

NON_TRANSLATED_KEYS = {
    "confidence_level",
    "level",
    "severity",
    "status",
    "confidence",
    "score",
    "count",
    "section",
    "test_id",
    "type",
    "flagged",
    "explicit_references",
    "evidence_found",
    "satisfied",
    "relevant",
    "estimated_cost_usd",
    "total_tokens",
}

TRANSLATABLE_KEYS = {
    "overall_assessment",
    "analysis_summary",
    "title",
    "description",
    "question",
    "analysis",
    "assessment",
    "summary",
    "rationale",
    "legal_basis",
    "indicator",
    "source",
    "matched_as",
    "literal_definition",
    "literal_source",
    "legal_definition",
    "legal_source",
    "conclusion",
    "governing_test",
    "criterion",
    "layer",
    "message",
    "detail",
    "issue",
    "correct_form",
    "preferred_form",
    "category",
    "name",
}

TRANSLATABLE_LIST_KEYS = {
    "authorities",
    "findings",
    "recommendations",
    "sources",
    "charter_sources",
    "policing_sources",
    "criteria",
    "protected_grounds",
    "layers",
    "options",
    "grounds",
    "principles",
    "grant_test",
    "matches",
}

EXACT_REPLACEMENTS = {
    "Freedom of Conscience and Religion": "Liberte de conscience et de religion",
    "Freedom of Thought, Belief, Opinion and Expression": "Liberte de pensee, de croyance, d'opinion et d'expression",
    "Freedom of Peaceful Assembly": "Liberte de reunion pacifique",
    "Freedom of Association": "Liberte d'association",
    "Democratic Rights — Right to Vote": "Droits democratiques — droit de vote",
    "Life, Liberty and Security of the Person": "Vie, liberte et securite de la personne",
    "Unreasonable Search and Seizure": "Fouille, perquisition ou saisie abusive",
    "Arbitrary Detention or Imprisonment": "Detention ou emprisonnement arbitraire",
    "Right to be Informed of Offence": "Droit d'etre informe de l'infraction",
    "Right to Retain and Instruct Counsel": "Droit de retenir et d'instruire un avocat",
    "Right to Trial Within Reasonable Time": "Droit d'etre juge dans un delai raisonnable",
    "Right Not to Be Compelled as Participant": "Droit de ne pas etre contraint de participer",
    "Right to Be Presumed Innocent": "Droit a la presomption d'innocence",
    "Right Not to Be Subject to Cruel and Unusual Treatment": "Droit de ne pas subir de traitements cruels et inusites",
    "Right Against Self-Incrimination": "Droit contre l'auto-incrimination",
    "Right to an Interpreter": "Droit a un interprete",
    "Equality Rights": "Droits a l'egalite",
    "Remedies for Infringement": "Reparations en cas d'atteinte",
    "Reasonable Limits — Section 1 Oakes Test": "Limites raisonnables — article 1 et test de Oakes",
    "Constructive discrimination / adverse effect discrimination": "Discrimination constructive / discrimination par effet prejudiciable",
    "Suspicion-based differential enforcement risk": "Risque d'application differentielle fondee sur le soupcon",
    "Services discrimination / equal treatment": "Discrimination dans les services / egalite de traitement",
    "Reprisal or retaliatory human-rights interference": "Represailles ou atteinte retaliatoire aux droits de la personne",
    "Direct or indirect infringement of human-rights protections": "Atteinte directe ou indirecte aux protections des droits de la personne",
    "Discrimination because of association": "Discrimination fondee sur l'association",
    "Disability, accommodation, and undue hardship": "Handicap, accommodement et contrainte excessive",
    "Disability-linked privacy-preserving behaviour": "Comportement de protection de la vie privee lie au handicap",
    "Disability-linked policing escalation without objective theft evidence": "Escalade policiere liee au handicap sans preuve objective de vol",
    "No Code criteria strongly triggered": "Aucun critere du Code n'est nettement declenche",
    "None detected": "Aucun element detecte",
    "General Usage": "Usage general",
    "Canadian Legal Usage": "Usage juridique canadien",
    "Terminology Standards": "Normes terminologiques",
    "Official Bad Faith / Process Abuse": "Mauvaise foi officielle / abus de procedure",
    "State Conduct / Abuse of Process": "Conduite de l'Etat / abus de procedure",
    "Charter / Criminal Law Notebook": "Charte / Criminal Law Notebook",
    "Prosecution Review": "Examen de la poursuite",
    "No assessment available.": "Aucune evaluation disponible.",
    "No assessment.": "Aucune evaluation.",
    "No specific concerns identified. The document does not appear to raise significant Charter issues, though this does not constitute legal advice.": "Aucune preoccupation particuliere n'a ete relevee. Le document ne semble pas soulever de questions importantes relatives a la Charte, bien que cela ne constitue pas un avis juridique.",
    "Everyone has the freedom of conscience and religion.": "Chacun a la liberte de conscience et de religion.",
    "Everyone has the freedom of thought, belief, opinion and expression, including freedom of the press.": "Chacun a la liberte de pensee, de croyance, d'opinion et d'expression, y compris la liberte de la presse.",
    "Everyone has the freedom of peaceful assembly.": "Chacun a la liberte de reunion pacifique.",
    "Everyone has the freedom of association.": "Chacun a la liberte d'association.",
    "Every citizen of Canada has the right to vote in an election and to be qualified for membership in Parliament.": "Toute citoyenne et tout citoyen du Canada a le droit de voter a une election et d'etre admissible a un siege au Parlement.",
    "Everyone has the right to life, liberty and security of the person and the right not to be deprived thereof except in accordance with the principles of fundamental justice.": "Chacun a droit a la vie, a la liberte et a la securite de sa personne et ne peut en etre prive qu'en conformite avec les principes de justice fondamentale.",
    "Everyone has the right to be secure against unreasonable search or seizure.": "Chacun a droit a la protection contre les fouilles, perquisitions ou saisies abusives.",
    "Everyone has the right not to be arbitrarily detained or imprisoned.": "Chacun a le droit de ne pas etre detenu ou emprisonne arbitrairement.",
    "Everyone has the right on arrest or detention to be informed promptly of the reasons therefor.": "Chacun a le droit, en cas d'arrestation ou de detention, d'etre informe sans delai des motifs de celle-ci.",
    "Everyone has the right on arrest or detention to retain and instruct counsel without delay and to be informed of that right.": "Chacun a le droit, en cas d'arrestation ou de detention, d'avoir recours sans delai a l'assistance d'un avocat et d'etre informe de ce droit.",
    "Any person charged with an offence has the right to be informed without unreasonable delay of the specific offence.": "Toute personne inculpee d'une infraction a le droit d'etre informee sans delai deraisonnable de l'infraction precise qui lui est reprochee.",
    "Any person charged with an offence has the right to be tried within a reasonable time.": "Toute personne inculpee d'une infraction a le droit d'etre jugee dans un delai raisonnable.",
    "Any person charged with an offence has the right not to be compelled to participate as a source party in proceedings against that person.": "Toute personne inculpee d'une infraction a le droit de ne pas etre contrainte de participer comme partie source dans des procedures dirigees contre elle.",
    "Any person charged with an offence has the right to be presumed innocent until proven guilty according to law in a fair and public hearing by an independent and impartial tribunal.": "Toute personne inculpee d'une infraction a le droit d'etre presumee innocente jusqu'a preuve du contraire, selon la loi, au cours d'une audience publique et equitable devant un tribunal independant et impartial.",
    "Everyone has the right not to be subjected to any cruel and unusual treatment or punishment.": "Chacun a le droit de ne pas subir de traitements ou peines cruels et inusites.",
    "A source party shall not be incriminated by any evidence given in proceedings.": "Une partie source ne peut etre incriminee par une preuve fournie dans une procedure.",
    "A participant in any proceedings who does not understand or speak the language in which the proceedings are conducted has the right to the assistance of an interpreter.": "Toute partie a une procedure qui ne comprend pas ou ne parle pas la langue dans laquelle elle se deroule a droit a l'assistance d'un interprete.",
    "Every individual is equal before and under the law and has the right to the equal protection and equal benefit of the law without discrimination based on race, national or ethnic origin, colour, religion, sex, age or mental or physical disability.": "Toute personne est egale devant la loi et a droit a la meme protection et au meme benefice de la loi, independamment de toute discrimination, notamment des discriminations fondees sur la race, l'origine nationale ou ethnique, la couleur, la religion, le sexe, l'age ou les deficiences mentales ou physiques.",
    "Anyone whose rights or freedoms, as guaranteed by this Charter, have been infringed or denied may apply to a court of competent jurisdiction to obtain such remedy as the court considers appropriate and just in the circumstances.": "Quiconque, victime de violation ou de negation des droits ou libertes garantis par la presente Charte, peut s'adresser a un tribunal competent pour obtenir la reparation que le tribunal estime convenable et juste eu egard aux circonstances.",
    "The rights and freedoms guaranteed are subject to such reasonable limits prescribed by law as can be demonstrably justified in a free and democratic society.": "Les droits et libertes qui y sont enonces ne peuvent etre restreints que par une regle de droit, dans des limites qui soient raisonnables et dont la justification puisse se demontrer dans le cadre d'une societe libre et democratique.",
    "Is there a deprivation of life, liberty, or security of the person?": "Y a-t-il privation de vie, de liberte ou de securite de la personne ?",
    "Is the limit prescribed by law (is there a valid law/rule)?": "La limite est-elle prevue par la loi (existe-t-il une regle ou une loi valide) ?",
    "Is there a validly enacted law or rule?": "Existe-t-il une loi ou une regle valablement adoptee ?",
    "Is the law sufficiently precise and accessible?": "La loi est-elle suffisamment precise et accessible ?",
    "Is the objective of the law pressing and substantial?": "L'objectif de la loi est-il urgent et reel ?",
    "Is the objective important enough to justify overriding a Charter right?": "L'objectif est-il suffisamment important pour justifier la restriction d'un droit garanti par la Charte ?",
    "Is the objective consistent with the values of a free and democratic society?": "L'objectif est-il conforme aux valeurs d'une societe libre et democratique ?",
    "Is there a rational connection between the objective and the means?": "Existe-t-il un lien rationnel entre l'objectif et les moyens ?",
    "Are the measures carefully designed to achieve the objective?": "Les mesures sont-elles soigneusement concues pour atteindre l'objectif ?",
    "Is there a causal connection between the law and the objective?": "Existe-t-il un lien causal entre la loi et l'objectif ?",
    "Is the law arbitrary?": "La loi est-elle arbitraire ?",
    "Does the law minimally impair the Charter right?": "La loi porte-t-elle une atteinte minimale au droit garanti par la Charte ?",
    "Are there less intrusive means available that would achieve the objective?": "Existe-t-il des moyens moins intrusifs permettant d'atteindre l'objectif ?",
    "Does the law sweep more broadly than necessary?": "La loi va-t-elle au-dela de ce qui est necessaire ?",
    "Oakes test run for completeness. The present text does not expressly raise a Section 1 justification theory, so the result is best read as 'not supported on this record' rather than 'affirmatively justified'.": "Le test de Oakes a ete execute par souci d'exhaustivite. Le texte actuel ne souleve pas explicitement une theorie de justification au titre de l'article 1; il faut donc lire ce resultat comme « non appuye au dossier » plutot que comme « positivement justifie ».",
    "Test run for completeness. No Section 1 justification context is expressly raised on the current text.": "Test effectue par souci d'exhaustivite. Aucun contexte explicite de justification au titre de l'article 1 n'est souleve dans le texte actuel.",
    "Some indicators present. Further review recommended.": "Certains indicateurs sont presents. Un examen complementaire est recommande.",
}

REGEX_REPLACEMENTS = [
    (r"\bThe scan first analyzed the document using the 'Ordinary Meaning' standard preferred by the Supreme Court of Canada\.", "L'analyse a d'abord examine le document selon la norme du « sens ordinaire » privilegiee par la Cour supreme du Canada."),
    (r"\bLiteral English references to (.+?) were identified\.", r"Des references litterales anglaises a \1 ont ete relevees."),
    (r"\bFor example, the term '(.+?)' is defined literally as '(.+?)' \((.+?)\)\.", r"Par exemple, le terme « \1 » est defini litteralement comme « \2 » (\3)."),
    (r"\bWhen cross-referenced with the Charter, this ordinary event takes on (.+?) significance\.", r"Lorsqu'il est recoupe avec la Charte, cet evenement ordinaire prend une portee \1."),
    (r"\bcriminal procedure\.", "en procedure penale."),
    (r"\bCONSTITUTIONAL CROSS-REFERENCE:", "RENVOI CONSTITUTIONNEL :"),
    (r"\bThese events implicate (\d+) potential Charter breach\(es\) under Section\(s\) (.+?)\.", r"Ces evenements mettent en cause \1 violation(s) potentielle(s) de la Charte au titre des articles \2."),
    (r"\bThe law requires high-level scrutiny here, particularly for Section\(s\): (.+?)\.", r"Une verification juridique approfondie s'impose ici, en particulier pour les articles \1."),
    (r"\bJUSTIFICATION ANALYSIS:", "ANALYSE DE LA JUSTIFICATION :"),
    (r"\bApplying the SCC's Oakes Test, these literal infringements do not currently appear to be saved as 'reasonable limits' under Section 1\.", "En appliquant le test de Oakes de la CSC, ces atteintes litterales ne semblent pas actuellement pouvoir etre sauvees comme « limites raisonnables » au regard de l'article 1."),
    (r"\bApplying the SCC's Oakes Test, these literal infringements do not currently appear to be saved as 'reasonable limits' under Article 1\.", "En appliquant le test de Oakes de la CSC, ces atteintes litterales ne semblent pas actuellement pouvoir etre sauvees comme « limites raisonnables » au regard de l'article 1."),
    (r"\bSTATE CONDUCT ASSESSMENT:", "EVALUATION DE LA CONDUITE DE L'ETAT :"),
    (r"\bGOVERNING TEST:", "TEST APPLICABLE :"),
    (r"\bEXPRESS FINDING:", "CONSTAT EXPLICITE :"),
    (r"\bLEADING AUTHORITIES:", "AUTORITES PRINCIPALES :"),
    (r"\bGROUNDS ASSESSMENT:", "EVALUATION DES MOTIFS :"),
    (r"\bPRIORITY RULE:", "REGLE DE PRIORITE :"),
    (r"\bExpress finding:", "Constat explicite :"),
    (r"\bConfidence\b", "Confiance"),
    (r"\bDescription\b", "Description"),
    (r"\bSummary\b", "Resume"),
    (r"\bLegal Basis\b", "Fondement juridique"),
    (r"\bFindings\b", "Constats"),
    (r"\bMatches\b", "Correspondances"),
    (r"\bCharter Sources\b", "Sources de la Charte"),
    (r"\bReference Sources\b", "Sources de reference"),
    (r"\bProtected grounds\b", "Motifs proteges"),
    (r"\bProtected Grounds\b", "Motifs proteges"),
    (r"\bHuman-rights assessment completed across UN, national, and provincial frameworks using equality, non-discrimination, reprisal, constructive discrimination, association, and accommodation criteria\.", "L'evaluation en droits de la personne a ete effectuee selon les cadres de l'ONU, nationaux et provinciaux en utilisant des criteres d'egalite, de non-discrimination, de represailles, de discrimination constructive, d'association et d'accommodement."),
    (r"\bBad faith assessment applies dual standards: Charter compliance and Ontario policing-legislation compliance\.", "L'evaluation de la mauvaise foi applique une double norme : conformite a la Charte et conformite a la legislation ontarienne en matiere de police."),
    (r"\bCharter focus: whether police conduct appears arbitrary, discriminatory, warrantless, rights-denying, or abusive\.", "Volet Charte : verifier si la conduite policiere parait arbitraire, discriminatoire, sans mandat, attentatoire aux droits ou abusive."),
    (r"\bPolicing-legislation focus: whether conduct is inconsistent with the statutory obligation to police in a manner that safeguards Charter rights and supports lawful, legitimate policing\.", "Volet legislation policiere : verifier si la conduite est incompatible avec l'obligation statutaire d'assurer un maintien de l'ordre qui protege les droits garantis par la Charte et appuie un exercice legal et legitime des fonctions policieres."),
    (r"\bConclusion: the text contains meaningful indicators of bad-faith or reckless policing and warrants express abuse-of-process review\.", "Conclusion : le texte contient des indicateurs significatifs de mauvaise foi policiere ou de conduite temeraire et justifie un examen explicite pour abus de procedure."),
    (r"\bThe text contains strong indicators that the Crown may have acted in bad faith by ignoring, suppressing, or proceeding despite a live Charter breach\.", "Le texte contient de forts indicateurs selon lesquels la Couronne pourrait avoir agi de mauvaise foi en ignorant, en supprimant ou en poursuivant malgre une violation actuelle de la Charte."),
    (r"\bThe text suggests a policy, practice, or indirect mechanism causing discriminatory adverse effects\.", "Le texte suggere une politique, une pratique ou un mecanisme indirect causant des effets discriminatoires prejudiciables."),
    (r"\bThe text suggests enforcement based on suspicion labels while objective theft evidence is absent, increasing risk of discriminatory differential treatment\.", "Le texte suggere une intervention fondee sur des etiquettes de soupcon alors qu'aucune preuve objective de vol n'est presente, ce qui accroît le risque d'un traitement discriminatoire differentiel."),
    (r"\bNo strongly articulated UN / national / provincial human-rights violation is detected on the current text, though protected-ground and services analysis should still be checked manually where policing and discrimination overlap\.", "Aucune violation fortement formulee des droits de la personne au niveau onusien, national ou provincial n'est detectee dans le texte actuel, bien qu'une verification manuelle demeure necessaire lorsque le maintien de l'ordre et la discrimination se recoupent."),
    (r"\bNo explicit language found addressing this element\.", "Aucun libelle explicite ne traite de cet element."),
    (r"\bDocument contains language suggesting this element may be addressed\.", "Le document contient un libelle suggerant que cet element pourrait etre present."),
    (r"\bTest run for completeness\. No Section 1 justification context is expressly raised on the current text\.", "Test effectue par souci d'exhaustivite. Aucun contexte explicite de justification au titre de l'article 1 n'est souleve dans le texte actuel."),
    (r"\bSome indicators present\. Further review recommended\.", "Certains indicateurs sont presents. Un examen complementaire est recommande."),
    (r"\bSection (\d+(?:\([a-z0-9]+\))?) asks whether", r"L'article \1 examine si"),
    (r"\bSection (\d+(?:\([a-z0-9]+\))?) requires", r"L'article \1 exige"),
    (r"\bSection (\d+(?:\([a-z0-9]+\))?) is engaged because", r"L'article \1 est en cause parce que"),
    (r"\bSection (\d+(?:\([a-z0-9]+\))?)", r"Article \1"),
    (r"\bdeprived the person of life, liberty, or security of the person\b", "a prive la personne de sa vie, de sa liberte ou de sa securite"),
    (r"\band if so whether the deprivation occurred contrary to the principles of fundamental justice\.", "et, dans l'affirmative, si cette privation est survenue contrairement aux principes de justice fondamentale."),
    (r"\bthe facts indicate a deprivation of liberty or security of the person and a live arbitrariness/fundamental justice issue under Article 7\.", "les faits indiquent une privation de liberte ou de securite de la personne ainsi qu'une question actuelle d'arbitraire et de justice fondamentale au regard de l'article 7."),
    (r"\bArbitrary detention/imprisonment \(s\.9\) is treated as a deprivation of liberty engaging s\.7 principles of fundamental justice\.", "La detention ou l'emprisonnement arbitraire (art. 9) est traite comme une privation de liberte engageant les principes de justice fondamentale de l'art. 7."),
    (r"\bstate action\b", "l'action de l'Etat"),
    (r"\bstate search or seizure\b", "une fouille ou saisie etatique"),
    (r"\breasonable expectation of privacy\b", "attente raisonnable en matiere de vie privee"),
    (r"\bwithout objectively reasonable grounds\b", "sans motifs objectivement raisonnables"),
    (r"\blive Charter breach\b", "violation actuelle de la Charte"),
    (r"\bobjective theft evidence\b", "preuve objective de vol"),
    (r"\bdiscriminatory differential treatment\b", "traitement discriminatoire differentiel"),
    (r"\bStrong indicators of potential breach found\. Review the applicable legal tests and cross-reference with CanLII authorities\.", "De forts indicateurs d'une violation potentielle ont ete releves. Examinez les tests juridiques applicables et recoupez-les avec les autorites de CanLII."),
    (r"\[PRIORITY\]", "[PRIORITE]"),
    (r"\[REVIEW\]", "[REVISION]"),
    (r"\[RESEARCH\]", "[RECHERCHE]"),
    (r"\[REFERENCE\]", "[REFERENCE]"),
    (r"\[TERM\]", "[TERME]"),
    (r"\[LEGAL MEANING\]", "[SENS JURIDIQUE]"),
    (r"\[LEGAL ARGUMENT\]", "[ARGUMENT JURIDIQUE]"),
    (r"\[REMEDY\]", "[REPARATION]"),
    (r"\[SECTION 1\]", "[ARTICLE 1]"),
    (r"\[CONDUCT\]", "[CONDUITE]"),
    (r"\[PARTIES\]", "[PARTIES]"),
    (r"\[ROUTING\]", "[AIGUILLAGE]"),
    (r"\bCharter Article (\d+(?:\([a-z0-9]+\))?)", r"Article \1 de la Charte"),
    (r"\bTest '(.+?)': Issues identified — (.+?)\. Examine evidence carefully for this element\.", r"Test « \1 » : points releves — \2. Examinez attentivement la preuve relative a cet element."),
    (r"\bSome indicators present but low confidence\. Further factual investigation recommended\.", "Certains indicateurs sont presents, mais le niveau de confiance demeure faible. Une verification factuelle supplementaire est recommandee."),
    (r"\bCanLII API not configured\. Use the generated search URLs to find supporting case law\.", "L'API CanLII n'est pas configuree. Utilisez les URL de recherche generees pour trouver la jurisprudence pertinente."),
    (r"\bCriminal Law Notebook reference available — review for procedural guidance and case summaries\.", "Une reference Criminal Law Notebook est disponible — consultez-la pour l'orientation procedurale et les resumes jurisprudentiels."),
    (r"\bDictionary meaning:", "Sens du dictionnaire :"),
    (r"\bArrest detected\. Under Whitfield \(SCC\), this requires intention, grounds, and notification\. Compare this against the provided facts\.", "Arrestation detectee. Selon Whitfield (CSC), cela exige une intention, des motifs et un avis donne. Comparez cela aux faits fournis."),
    (r"\bIf evidence was obtained in breach of Charter rights, apply R v Grant \(2009 SCC 26\) three-factor test for exclusion under s\.24\(2\)\.", "Si une preuve a ete obtenue en violation des droits garantis par la Charte, appliquez le test en trois volets de R c Grant (2009 CSC 26) pour l'exclusion en vertu de l'art. 24(2)."),
    (r"\bConsider a stay of proceedings application if delay or abuse of process is established\.", "Envisagez une demande d'arret des procedures si un delai abusif ou un abus de procedure est etabli."),
    (r"\bConsider a claim for constitutional damages under the R v Ward framework\.", "Envisagez une demande de dommages-interets constitutionnels selon le cadre de R c Ward."),
    (r"\bThe Crown may face difficulty justifying the breach under Section 1\. Focus on minimal impairment and proportionality arguments\.", "La Couronne pourrait avoir du mal a justifier la violation au regard de l'article 1. Mettez l'accent sur l'atteinte minimale et la proportionnalite."),
    (r"\blevel of state misconduct identified:", "niveau d'inconduite etatique releve :"),
    (r"\bConsider an Abuse of Process application\.", "Envisagez une demande pour abus de procedure."),
    (r"\bExtracted (\d+) named/identified parties with role classification and verbatim narrative statements\.", r"\1 parties nommees ou identifiees ont ete extraites avec classification des roles et declarations narratives verbatim."),
    (r"\bUse these statement excerpts to fact-check exactly who says what happened\.", "Utilisez ces extraits de declaration pour verifier precisement qui affirme quoi."),
    (r"\bSuggested version:", "Version suggeree :"),
    (r"\bWITNESS CREDIBILITY: STATEMENT DOES NOT DESCRIBE OBSERVING A CRIMINAL ACT\.", "CREDIBILITE DU TEMOIN : LA DECLARATION NE DECRIT PAS L'OBSERVATION D'UN ACTE CRIMINEL."),
    (r"\bIDENTIFICATION GAP: WITNESS ACCOUNT DOES NOT IDENTIFY THE PERSON AS THE ACTOR OF ANY SPECIFIC OFFENCE\.", "LACUNE D'IDENTIFICATION : LE RECIT DU TEMOIN N'IDENTIFIE PAS LA PERSONNE COMME L'AUTEUR D'UNE INFRACTION PRECISE."),
    (r"\bASSUMPTION-DRIVEN THEORY: THE RECORD SUGGESTS OFFICERS PROCEEDED ON ASSUMPTION OR CRIME-IN-PROGRESS SPECULATION INSTEAD OF OBJECTIVELY VERIFIABLE GROUNDS\.", "THEORIE FONDEE SUR UNE HYPOTHESE : LE DOSSIER SUGGERE QUE LES AGENTS ONT PROCEDE SUR LA BASE D'UNE HYPOTHESE OU D'UNE SPECULATION DE CRIME EN COURS PLUTOT QUE SUR DES MOTIFS OBJECTIVEMENT VERIFIABLES."),
    (r"\bPHYSICAL NEXUS: REPORT FAILS TO PLACE SUSPECT ON OR NEAR UTILITY POLE\.", "LIEN PHYSIQUE : LE RAPPORT NE SITUE PAS LE SUSPECT SUR OU PRES DU POTEAU DE SERVICE PUBLIC."),
    (r"\bFEASIBILITY: NO TOOLS IDENTIFIED IN SUSPECT POSSESSION\.", "FAISABILITE : AUCUN OUTIL N'EST IDENTIFIE EN POSSESSION DU SUSPECT."),
    (r"\bPHYSICAL INACCESSIBILITY: TARGET MATERIAL OR LOCATION INDICATED AS BEYOND REACH\.", "INACCESSIBILITE PHYSIQUE : LE MATERIEL OU L'EMPLACEMENT CIBLE EST INDIQUE COMME HORS DE PORTEE."),
    (r"\bEVIDENCE ABSENCE: NO PHYSICAL EVIDENCE \(CABLE/WIRE/PROPERTY\) IDENTIFIED ON MANIFEST\.", "ABSENCE DE PREUVE : AUCUNE PREUVE PHYSIQUE (CABLE/FIL/BIEN) N'EST IDENTIFIEE DANS L'INVENTAIRE."),
    (r"\bNO OBJECTIVE GROUNDS\b", "ABSENCE DE MOTIFS OBJECTIFS"),
    (r"\bHIGH CONCERN\b", "PREOCCUPATION ELEVEE"),
    (r"\bREVIEW REQUIRED\b", "REVISION REQUISE"),
    (r"\bHIGH\b", "ELEVE"),
    (r"\bMEDIUM\b", "MOYEN"),
    (r"\bLOW\b", "FAIBLE"),
]


def translate_text_to_french(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    if text.startswith("http://") or text.startswith("https://") or text.startswith("file://"):
        return text

    translated = EXACT_REPLACEMENTS.get(text, text)
    for source, target in sorted(EXACT_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    for pattern, replacement in REGEX_REPLACEMENTS:
        translated = re.sub(pattern, replacement, translated)
    return translated


def localize_analysis_results_to_french(results):
    localized = deepcopy(results)
    return _localize_value(localized, key=None)


def _localize_value(value, key):
    if isinstance(value, dict):
        localized = {}
        for child_key, child_value in value.items():
            localized[child_key] = _localize_value(child_value, child_key)
        return localized

    if isinstance(value, list):
        if key in TRANSLATABLE_LIST_KEYS:
            return [_localize_value(item, None) for item in value]
        return [_localize_value(item, key) for item in value]

    if not isinstance(value, str):
        return value

    if key in URL_KEYS or key in NON_TRANSLATED_KEYS:
        return value

    if key in TRANSLATABLE_KEYS or key in TRANSLATABLE_LIST_KEYS or key is None:
        return translate_text_to_french(value)

    return value
