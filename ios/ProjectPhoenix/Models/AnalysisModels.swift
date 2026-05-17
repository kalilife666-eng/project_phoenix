import Foundation

struct AnalysisEnvelope: Codable {
    let meta: ResponseMeta?
    let source: AnalysisSource
    let analysis: AnalysisResult
}

struct ResponseMeta: Codable {
    let requestID: String?
    let generatedAt: String?

    enum CodingKeys: String, CodingKey {
        case requestID = "request_id"
        case generatedAt = "generated_at"
    }
}

struct AnalysisSource: Codable {
    let kind: String
    let metadata: DocumentMetadata
    let citations: [LegalCitation]?
    let keyLegalTerms: [String: [KeyLegalTerm]]?

    enum CodingKeys: String, CodingKey {
        case kind
        case metadata
        case citations
        case keyLegalTerms = "key_legal_terms"
    }
}

struct DocumentMetadata: Codable {
    let fileName: String?
    let format: String?
    let charCount: Int?
    let wordCount: Int?
    let paragraphCount: Int?
    let sentenceCount: Int?

    enum CodingKeys: String, CodingKey {
        case fileName = "file_name"
        case format
        case charCount = "char_count"
        case wordCount = "word_count"
        case paragraphCount = "paragraph_count"
        case sentenceCount = "sentence_count"
    }
}

struct LegalCitation: Codable, Identifiable {
    let fullCitation: String
    let type: String?
    let section: String?

    var id: String { fullCitation }

    enum CodingKeys: String, CodingKey {
        case fullCitation = "full_citation"
        case type
        case section
    }
}

struct KeyLegalTerm: Codable, Identifiable {
    let term: String
    let count: Int

    var id: String { "\(term)-\(count)" }
}

struct AnalysisResult: Codable {
    let potentialBreaches: [PotentialBreach]
    let charterSectionsReferenced: [CharterSectionReference]?
    let overallAssessment: String?
    let recommendations: [String]?
    let humanRightsAssessment: HumanRightsAssessment?
    let oakesAnalysis: OakesAnalysis?

    enum CodingKeys: String, CodingKey {
        case potentialBreaches = "potential_breaches"
        case charterSectionsReferenced = "charter_sections_referenced"
        case overallAssessment = "overall_assessment"
        case recommendations
        case humanRightsAssessment = "human_rights_assessment"
        case oakesAnalysis = "oakes_analysis"
    }
}

struct CharterSectionReference: Codable, Identifiable {
    let section: String
    let context: String?
    let type: String?

    var id: String { "\(section)-\(context ?? "")-\(type ?? "")" }
}

struct PotentialBreach: Codable, Identifiable {
    let section: String
    let title: String
    let description: String
    let confidenceLevel: String
    let confidence: Double?
    let matchedKeywords: [MatchedKeyword]
    let breachIndicators: [BreachIndicator]
    let applicableTests: [String: ApplicableTest]
    let legalArticulation: LegalArticulation?

    var id: String { section }

    enum CodingKeys: String, CodingKey {
        case section
        case title
        case description
        case confidenceLevel = "confidence_level"
        case confidence
        case matchedKeywords = "matched_keywords"
        case breachIndicators = "breach_indicators"
        case applicableTests = "applicable_tests"
        case legalArticulation = "legal_articulation"
    }
}

struct MatchedKeyword: Codable, Identifiable {
    let keyword: String
    let count: Int

    var id: String { keyword }
}

struct BreachIndicator: Codable, Identifiable {
    let type: String
    let count: Int

    var id: String { type }
}

struct ApplicableTest: Codable, Identifiable {
    let testID: String
    let question: String
    let identifiedIssues: [String]
    let analysis: String
    let authorities: [String]
    let status: String

    var id: String { testID }

    enum CodingKeys: String, CodingKey {
        case testID = "test_id"
        case question
        case identifiedIssues = "identified_issues"
        case analysis
        case authorities
        case status
    }
}

struct LegalArticulation: Codable {
    let governingTest: String
    let authorities: [String]
    let conclusion: String

    enum CodingKeys: String, CodingKey {
        case governingTest = "governing_test"
        case authorities
        case conclusion
    }
}

struct HumanRightsAssessment: Codable {
    let level: String
    let assessment: String
    let criteria: [String]
}

struct OakesAnalysis: Codable {
    let justificationLikely: Bool?
    let analysisSummary: String?

    enum CodingKeys: String, CodingKey {
        case justificationLikely = "justification_likely"
        case analysisSummary = "analysis_summary"
    }
}

struct SavedAnalysisRecord: Codable, Identifiable {
    let id: UUID
    let createdAt: Date
    let title: String
    let summary: String
    let breachCount: Int
    let sourceKind: String
    let envelope: AnalysisEnvelope
}

struct FrenchAnalysisPresentation {
    let summary: String
    let recommendations: [String]
    let breaches: [FrenchBreachPresentation]
    let notice: String?
}

struct FrenchBreachPresentation: Identifiable {
    let section: String
    let title: String
    let description: String
    let confidenceLabel: String

    var id: String { section }
}

extension AnalysisEnvelope {
    var displayTitle: String {
        source.metadata.fileName ?? "Untitled Analysis"
    }

    var shortSummary: String {
        if let overall = analysis.overallAssessment?.trimmingCharacters(in: .whitespacesAndNewlines), !overall.isEmpty {
            return overall
        }
        if let rights = analysis.humanRightsAssessment?.assessment.trimmingCharacters(in: .whitespacesAndNewlines), !rights.isEmpty {
            return rights
        }
        return "No narrative summary available."
    }

    var shareSummaryText: String {
        var lines: [String] = []
        lines.append("Project Phoenix Analysis")
        lines.append(displayTitle)
        lines.append("")
        lines.append("Flagged sections: \(analysis.potentialBreaches.count)")
        if let overall = analysis.overallAssessment, !overall.isEmpty {
            lines.append("")
            lines.append("Overall assessment")
            lines.append(overall)
        }
        if let oakes = analysis.oakesAnalysis?.analysisSummary, !oakes.isEmpty {
            lines.append("")
            lines.append("Section 1 / Oakes")
            lines.append(oakes)
        }
        if !analysis.potentialBreaches.isEmpty {
            lines.append("")
            lines.append("Flagged Charter sections")
            for breach in analysis.potentialBreaches {
                lines.append("s. \(breach.section) \(breach.title) [\(breach.confidenceLevel)]")
            }
        }
        if let recommendations = analysis.recommendations, !recommendations.isEmpty {
            lines.append("")
            lines.append("Recommendations")
            for item in recommendations.prefix(6) {
                lines.append("- \(item)")
            }
        }
        return lines.joined(separator: "\n")
    }
}
