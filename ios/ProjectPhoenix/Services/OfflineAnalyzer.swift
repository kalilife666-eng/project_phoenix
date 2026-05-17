import Foundation

struct OfflineAnalyzer {
    func analyze(text: String, sourceName: String, sourceFormat: String) -> AnalysisEnvelope {
        let normalizedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let lowercased = normalizedText.lowercased()
        let breaches = buildBreaches(from: lowercased)
        let recommendations = buildRecommendations(from: breaches)
        let humanRights = buildHumanRightsAssessment(from: lowercased, breaches: breaches)
        let summary = buildSummary(from: breaches, humanRights: humanRights)

        return AnalysisEnvelope(
            meta: ResponseMeta(
                requestID: "offline-\(UUID().uuidString.prefix(8))",
                generatedAt: ISO8601DateFormatter().string(from: Date())
            ),
            source: AnalysisSource(
                kind: "offline",
                metadata: metadata(for: normalizedText, sourceName: sourceName, sourceFormat: sourceFormat),
                citations: [],
                keyLegalTerms: keyLegalTerms(from: lowercased)
            ),
            analysis: AnalysisResult(
                potentialBreaches: breaches,
                charterSectionsReferenced: breaches.map {
                    CharterSectionReference(section: $0.section, context: "offline analyzer", type: "implicit")
                },
                overallAssessment: summary,
                recommendations: recommendations,
                humanRightsAssessment: humanRights,
                oakesAnalysis: OakesAnalysis(
                    justificationLikely: breaches.isEmpty ? nil : false,
                    analysisSummary: breaches.isEmpty
                        ? "No strong Charter issue was detected by the on-device analyzer."
                        : "The offline analyzer treats any flagged breach as requiring manual Section 1 review rather than assuming justification."
                )
            )
        )
    }

    private func metadata(for text: String, sourceName: String, sourceFormat: String) -> DocumentMetadata {
        let paragraphs = text.components(separatedBy: CharacterSet.newlines)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        let sentences = text.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        return DocumentMetadata(
            fileName: sourceName,
            format: sourceFormat,
            charCount: text.count,
            wordCount: text.split(whereSeparator: \.isWhitespace).count,
            paragraphCount: paragraphs.count,
            sentenceCount: sentences.count
        )
    }

    private func buildBreaches(from text: String) -> [PotentialBreach] {
        var breaches: [PotentialBreach] = []

        if let breach = detectSection7(in: text) {
            breaches.append(breach)
        }
        if let breach = detectSection8(in: text) {
            breaches.append(breach)
        }
        if let breach = detectSection9(in: text) {
            breaches.append(breach)
        }
        if let breach = detectSection10b(in: text) {
            breaches.append(breach)
        }
        if let breach = detectSection15(in: text) {
            breaches.append(breach)
        }

        return breaches
    }

    private func detectSection7(in text: String) -> PotentialBreach? {
        let triggers = matchedKeywords(text, [
            "liberty",
            "security of the person",
            "detention",
            "arbitrary",
            "fundamental justice",
            "custody"
        ])
        guard !triggers.isEmpty else { return nil }

        return makeBreach(
            section: "7",
            title: "Life, Liberty and Security of the Person",
            confidenceLevel: triggers.count >= 3 ? "HIGH" : "MEDIUM",
            description: "The offline analyzer found liberty/security language suggesting a Section 7 deprivation and fundamental-justice concern.",
            conclusion: "Offline finding: the text raises a plausible deprivation of liberty or security of the person requiring Section 7 review.",
            governingTest: "Ask whether state action deprived life, liberty, or security of the person and whether the deprivation appears contrary to fundamental justice.",
            keywords: triggers,
            indicators: matchedIndicators(text, [
                "arbitrary",
                "detention",
                "custody",
                "without reasonable grounds"
            ]),
            tests: [
                ApplicableTest(
                    testID: "deprivation",
                    question: "Is there a deprivation of liberty or security of the person?",
                    identifiedIssues: triggers.map(\.keyword),
                    analysis: "The text contains liberty-linked signals that justify manual review.",
                    authorities: [],
                    status: "potential_issue"
                )
            ]
        )
    }

    private func detectSection8(in text: String) -> PotentialBreach? {
        let triggers = matchedKeywords(text, [
            "search",
            "searched",
            "seizure",
            "warrant",
            "warrantless",
            "privacy",
            "bag"
        ])
        guard !triggers.isEmpty else { return nil }

        return makeBreach(
            section: "8",
            title: "Unreasonable Search and Seizure",
            confidenceLevel: triggers.contains(where: { ["warrant", "warrantless"].contains($0.keyword) }) ? "HIGH" : "MEDIUM",
            description: "The offline analyzer found search/seizure and privacy signals consistent with a Section 8 issue.",
            conclusion: "Offline finding: the text describes a possible state search or seizure that may have occurred without lawful authority.",
            governingTest: "Ask whether the state searched or seized, whether a privacy interest existed, and whether the search or seizure was authorized and reasonable.",
            keywords: triggers,
            indicators: matchedIndicators(text, [
                "without warrant",
                "no warrant",
                "warrantless",
                "searched without"
            ]),
            tests: [
                ApplicableTest(
                    testID: "search_or_seizure",
                    question: "Does the text describe a state search or seizure affecting privacy?",
                    identifiedIssues: triggers.map(\.keyword),
                    analysis: "Search-related language is present in the record.",
                    authorities: [],
                    status: "potential_issue"
                )
            ]
        )
    }

    private func detectSection9(in text: String) -> PotentialBreach? {
        let triggers = matchedKeywords(text, [
            "arrest",
            "arrested",
            "detention",
            "detained",
            "arbitrary",
            "grounds"
        ])
        guard !triggers.isEmpty else { return nil }

        return makeBreach(
            section: "9",
            title: "Arbitrary Detention or Imprisonment",
            confidenceLevel: text.contains("without reasonable grounds") || text.contains("no reasonable grounds") ? "HIGH" : "MEDIUM",
            description: "The offline analyzer found arrest/detention language that may indicate arbitrariness.",
            conclusion: "Offline finding: the text raises a live Section 9 issue because detention or arrest language appears alongside arbitrariness or grounds concerns.",
            governingTest: "Ask whether the person was detained or imprisoned and whether that detention appears arbitrary.",
            keywords: triggers,
            indicators: matchedIndicators(text, [
                "arbitrary",
                "without reasonable grounds",
                "no reasonable grounds",
                "arrest"
            ]),
            tests: [
                ApplicableTest(
                    testID: "arbitrariness",
                    question: "Does the record suggest detention without lawful or objectively reasonable grounds?",
                    identifiedIssues: triggers.map(\.keyword),
                    analysis: "Detention language appears with arbitrariness or grounds concerns.",
                    authorities: [],
                    status: "potential_issue"
                )
            ]
        )
    }

    private func detectSection10b(in text: String) -> PotentialBreach? {
        let triggers = matchedKeywords(text, [
            "counsel",
            "lawyer",
            "right to counsel",
            "denied counsel",
            "no lawyer"
        ])
        guard !triggers.isEmpty else { return nil }

        return makeBreach(
            section: "10(b)",
            title: "Right to Retain and Instruct Counsel",
            confidenceLevel: text.contains("denied counsel") || text.contains("no lawyer") ? "HIGH" : "MEDIUM",
            description: "The offline analyzer found right-to-counsel language suggesting Section 10(b) may be engaged.",
            conclusion: "Offline finding: the text suggests delay, denial, or non-implementation of the right to counsel.",
            governingTest: "Ask whether the person was informed promptly of the right to counsel and given a real chance to exercise it.",
            keywords: triggers,
            indicators: matchedIndicators(text, [
                "denied counsel",
                "no lawyer",
                "refused lawyer"
            ]),
            tests: [
                ApplicableTest(
                    testID: "right_imposed",
                    question: "Was the right to counsel triggered and meaningfully implemented?",
                    identifiedIssues: triggers.map(\.keyword),
                    analysis: "Counsel-related language is present in the record.",
                    authorities: [],
                    status: "potential_issue"
                )
            ]
        )
    }

    private func detectSection15(in text: String) -> PotentialBreach? {
        let triggers = matchedKeywords(text, [
            "disability",
            "disabled",
            "race",
            "woman",
            "female",
            "male",
            "profiling",
            "discrimination",
            "targeted"
        ])
        guard !triggers.isEmpty else { return nil }

        return makeBreach(
            section: "15(1)",
            title: "Equality Rights",
            confidenceLevel: text.contains("profiling") || text.contains("discrimination") ? "HIGH" : "MEDIUM",
            description: "The offline analyzer found protected-ground or discriminatory-enforcement language that may raise Section 15 concerns.",
            conclusion: "Offline finding: the text contains markers of protected-ground treatment or discriminatory enforcement requiring equality-rights review.",
            governingTest: "Ask whether the state action draws a distinction on an enumerated or analogous ground and whether it imposes disadvantage.",
            keywords: triggers,
            indicators: matchedIndicators(text, [
                "profiling",
                "discrimination",
                "targeted",
                "bias"
            ]),
            tests: [
                ApplicableTest(
                    testID: "distinction",
                    question: "Does the text suggest differential treatment tied to a protected ground?",
                    identifiedIssues: triggers.map(\.keyword),
                    analysis: "Protected-ground and discrimination markers are present.",
                    authorities: [],
                    status: "potential_issue"
                )
            ]
        )
    }

    private func buildRecommendations(from breaches: [PotentialBreach]) -> [String] {
        guard !breaches.isEmpty else {
            return ["No strong offline Charter signal was found. Review manually if the record is incomplete or highly contextual."]
        }

        var items = ["Treat the on-device result as a screening pass only and verify each flagged section manually."]
        if breaches.contains(where: { $0.section == "8" || $0.section == "9" }) {
            items.append("Check the factual basis for arrest, detention, search authority, and any warrant record.")
        }
        if breaches.contains(where: { $0.section == "10(b)" }) {
            items.append("Confirm the exact timing and implementation of the right to counsel.")
        }
        if breaches.contains(where: { $0.section == "15(1)" }) {
            items.append("Review whether protected-ground markers and differential treatment are expressly supported by the record.")
        }
        return items
    }

    private func buildHumanRightsAssessment(from text: String, breaches: [PotentialBreach]) -> HumanRightsAssessment? {
        let markers = matchedKeywords(text, [
            "disability",
            "disabled",
            "race",
            "religion",
            "sex",
            "gender",
            "profiling",
            "discrimination"
        ])
        guard !markers.isEmpty else { return nil }

        let level = markers.count >= 3 || breaches.contains(where: { $0.section == "15(1)" }) ? "HIGH" : "MEDIUM"
        return HumanRightsAssessment(
            level: level,
            assessment: "The offline analyzer found protected-ground or discriminatory-treatment markers that justify a human-rights review.",
            criteria: markers.map(\.keyword)
        )
    }

    private func buildSummary(from breaches: [PotentialBreach], humanRights: HumanRightsAssessment?) -> String {
        if breaches.isEmpty {
            return "No strong Charter breach was detected by the offline analyzer. This result is heuristic and should not replace manual legal review."
        }

        var summary = "Offline analyzer flagged \(breaches.count) potential Charter issue"
        summary += breaches.count == 1 ? "." : "s."
        let sections = breaches.map { "s. \($0.section)" }.joined(separator: ", ")
        summary += " Flagged sections: \(sections)."
        if humanRights != nil {
            summary += " The text also contains protected-ground or discriminatory-treatment markers."
        }
        return summary
    }

    private func keyLegalTerms(from text: String) -> [String: [KeyLegalTerm]] {
        let categories: [String: [String]] = [
            "detention_arrest": ["arrest", "detention", "custody", "counsel"],
            "evidence": ["search", "seizure", "warrant", "privacy"],
            "equality": ["disability", "profiling", "discrimination", "race", "gender"]
        ]

        var result: [String: [KeyLegalTerm]] = [:]
        for (category, terms) in categories {
            let matches = terms.compactMap { term -> KeyLegalTerm? in
                let count = occurrences(of: term, in: text)
                return count > 0 ? KeyLegalTerm(term: term, count: count) : nil
            }
            if !matches.isEmpty {
                result[category] = matches
            }
        }
        return result
    }

    private func makeBreach(
        section: String,
        title: String,
        confidenceLevel: String,
        description: String,
        conclusion: String,
        governingTest: String,
        keywords: [MatchedKeyword],
        indicators: [BreachIndicator],
        tests: [ApplicableTest]
    ) -> PotentialBreach {
        PotentialBreach(
            section: section,
            title: title,
            description: description,
            confidenceLevel: confidenceLevel,
            confidence: confidenceLevel == "HIGH" ? 0.9 : 0.65,
            matchedKeywords: keywords,
            breachIndicators: indicators,
            applicableTests: Dictionary(uniqueKeysWithValues: tests.map { ($0.testID, $0) }),
            legalArticulation: LegalArticulation(
                governingTest: governingTest,
                authorities: [],
                conclusion: conclusion
            )
        )
    }

    private func matchedKeywords(_ text: String, _ keywords: [String]) -> [MatchedKeyword] {
        keywords.compactMap { keyword in
            let count = occurrences(of: keyword, in: text)
            return count > 0 ? MatchedKeyword(keyword: keyword, count: count) : nil
        }
    }

    private func matchedIndicators(_ text: String, _ indicators: [String]) -> [BreachIndicator] {
        indicators.compactMap { indicator in
            let count = occurrences(of: indicator, in: text)
            return count > 0 ? BreachIndicator(type: indicator, count: count) : nil
        }
    }

    private func occurrences(of needle: String, in haystack: String) -> Int {
        guard !needle.isEmpty else { return 0 }
        var count = 0
        var searchStart = haystack.startIndex
        while searchStart < haystack.endIndex,
              let range = haystack.range(of: needle, options: [.caseInsensitive], range: searchStart..<haystack.endIndex) {
            count += 1
            searchStart = range.upperBound
        }
        return count
    }
}
