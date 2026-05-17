import Foundation
import SwiftUI
import UniformTypeIdentifiers

enum BreachConfidenceFilter: String, CaseIterable, Identifiable {
    case all = "All"
    case high = "HIGH"
    case medium = "MEDIUM"
    case low = "LOW"
    case minimal = "MINIMAL"

    var id: String { rawValue }
}

@MainActor
final class AnalysisViewModel: ObservableObject {
    @Published var text = ""
    @Published var envelope: AnalysisEnvelope?
    @Published var frenchPresentation: FrenchAnalysisPresentation?
    @Published var isLoading = false
    @Published var isTranslatingFrench = false
    @Published var errorMessage: String?
    @Published var frenchTranslationError: String?
    @Published var isShowingImporter = false
    @Published var isShowingSettings = false
    @Published var breachSearchText = ""
    @Published var confidenceFilter: BreachConfidenceFilter = .all
    @Published var savedHistory: [SavedAnalysisRecord]

    @AppStorage("apiBaseURL") var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("apiToken") var apiToken = ""
    @AppStorage("offlineModeEnabled") var offlineModeEnabled = true

    private let historyStore = AnalysisHistoryStore()
    private let offlineAnalyzer = OfflineAnalyzer()
    private let localDocumentReader = LocalDocumentReader()

    init() {
        savedHistory = historyStore.load()
    }

    var hasResults: Bool {
        envelope != nil
    }

    var filteredBreaches: [PotentialBreach] {
        guard let breaches = envelope?.analysis.potentialBreaches else {
            return []
        }

        return breaches.filter { breach in
            let matchesConfidence = confidenceFilter == .all || breach.confidenceLevel == confidenceFilter.rawValue
            let search = breachSearchText.trimmingCharacters(in: .whitespacesAndNewlines)
            let matchesSearch: Bool
            if search.isEmpty {
                matchesSearch = true
            } else {
                let haystack = [
                    breach.section,
                    breach.title,
                    breach.description,
                    breach.legalArticulation?.conclusion ?? ""
                ].joined(separator: " ").lowercased()
                matchesSearch = haystack.contains(search.lowercased())
            }
            return matchesConfidence && matchesSearch
        }
    }

    var shareSummaryText: String {
        envelope?.shareSummaryText ?? "No analysis available."
    }

    func loadSampleText() {
        text = """
        Police arrested me without a warrant, denied me access to counsel, and searched my bag before explaining the grounds for detention.
        """
    }

    func runTextAnalysis() async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            errorMessage = "Enter or paste text first."
            return
        }

        if offlineModeEnabled {
            envelope = offlineAnalyzer.analyze(
                text: trimmed,
                sourceName: "inline_text.txt",
                sourceFormat: "text"
            )
            if let envelope {
                breachSearchText = ""
                confidenceFilter = .all
                persistHistory(for: envelope)
                Task { await refreshFrenchPresentation(for: envelope) }
            }
            return
        }

        await performRequest {
            try await makeClient().analyzeText(trimmed)
        }
    }

    func importDocument(from url: URL) async {
        let didAccess = url.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                url.stopAccessingSecurityScopedResource()
            }
        }

        let pathExtension = url.pathExtension.lowercased()
        guard SupportedDocumentTypes.supportedExtensions.contains(pathExtension) else {
            errorMessage = "Unsupported file type. Use pdf, docx, txt, rtf, or md."
            return
        }

        do {
            if offlineModeEnabled {
                let localResult = try localDocumentReader.readText(from: url)
                let localEnvelope = offlineAnalyzer.analyze(
                    text: localResult.text,
                    sourceName: localResult.sourceName,
                    sourceFormat: localResult.sourceFormat
                )
                envelope = localEnvelope
                breachSearchText = ""
                confidenceFilter = .all
                persistHistory(for: localEnvelope)
                Task { await refreshFrenchPresentation(for: localEnvelope) }
                return
            }

            let fileValues = try url.resourceValues(forKeys: [.fileSizeKey])
            if let fileSize = fileValues.fileSize, fileSize > AppConfig.maxImportBytes {
                errorMessage = "This file is too large for the current mobile import limit."
                return
            }

            let data = try Data(contentsOf: url)
            let filename = url.lastPathComponent
            let mimeType = mimeTypeForURL(url)

            await performRequest {
                try await makeClient().analyzeFile(
                    data: data,
                    filename: filename,
                    mimeType: mimeType
                )
            }
        } catch {
            errorMessage = userFacingErrorMessage(for: error)
        }
    }

    func loadHistoryRecord(_ record: SavedAnalysisRecord) {
        envelope = record.envelope
        breachSearchText = ""
        confidenceFilter = .all
        frenchPresentation = nil
        frenchTranslationError = nil
    }

    func ensureFrenchPresentation() async {
        guard let envelope else { return }
        if frenchPresentation != nil || isTranslatingFrench {
            return
        }
        await refreshFrenchPresentation(for: envelope)
    }

    func deleteHistoryRecord(_ record: SavedAnalysisRecord) {
        savedHistory.removeAll { $0.id == record.id }
        historyStore.save(savedHistory)
    }

    private func makeClient() -> APIClient {
        APIClient(
            baseURL: apiBaseURL,
            accessToken: apiToken.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : apiToken
        )
    }

    private func performRequest(_ operation: @escaping () async throws -> AnalysisEnvelope) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let responseEnvelope = try await operation()
            envelope = responseEnvelope
            breachSearchText = ""
            confidenceFilter = .all
            persistHistory(for: responseEnvelope)
            Task { await refreshFrenchPresentation(for: responseEnvelope) }
        } catch {
            errorMessage = userFacingErrorMessage(for: error)
        }
    }

    private func refreshFrenchPresentation(for envelope: AnalysisEnvelope) async {
        frenchPresentation = nil
        frenchTranslationError = nil

        if offlineModeEnabled {
            frenchPresentation = FrenchAnalysisPresentation(
                summary: "Le mode hors ligne est actif. La version francaise automatique des resultats exige l'API de traduction en ligne.",
                recommendations: [],
                breaches: [],
                notice: "Desactivez le mode hors ligne dans Reglages pour obtenir une traduction francaise automatique."
            )
            return
        }

        isTranslatingFrench = true
        defer { isTranslatingFrench = false }

        let client = makeClient()

        do {
            async let summaryTranslation = client.translateText(
                envelope.shortSummary,
                targetLanguage: "french",
                sourceLanguage: "english"
            )

            async let recommendationTranslations: [String] = translateRecommendations(
                envelope.analysis.recommendations ?? [],
                client: client
            )

            async let breachTranslations: [FrenchBreachPresentation] = translateBreaches(
                envelope.analysis.potentialBreaches,
                client: client
            )

            let translatedSummary = try await summaryTranslation
            let translatedRecommendations = try await recommendationTranslations
            let translatedBreaches = try await breachTranslations

            frenchPresentation = FrenchAnalysisPresentation(
                summary: translatedSummary.translation.translatedText,
                recommendations: translatedRecommendations,
                breaches: translatedBreaches,
                notice: "Version francaise traduite automatiquement a partir de l'analyse anglaise."
            )
        } catch {
            frenchTranslationError = userFacingErrorMessage(for: error)
        }
    }

    private func translateRecommendations(_ recommendations: [String], client: APIClient) async throws -> [String] {
        var translated: [String] = []
        for recommendation in recommendations {
            let response = try await client.translateText(
                recommendation,
                targetLanguage: "french",
                sourceLanguage: "english"
            )
            translated.append(response.translation.translatedText)
        }
        return translated
    }

    private func translateBreaches(_ breaches: [PotentialBreach], client: APIClient) async throws -> [FrenchBreachPresentation] {
        var translated: [FrenchBreachPresentation] = []
        for breach in breaches {
            let translatedDescription = try await client.translateText(
                breach.legalArticulation?.conclusion ?? breach.description,
                targetLanguage: "french",
                sourceLanguage: "english"
            )

            translated.append(
                FrenchBreachPresentation(
                    section: breach.section,
                    title: Self.frenchTitle(for: breach.title),
                    description: translatedDescription.translation.translatedText,
                    confidenceLabel: Self.frenchConfidenceLabel(for: breach.confidenceLevel)
                )
            )
        }
        return translated.sorted { $0.section < $1.section }
    }

    private static func frenchConfidenceLabel(for level: String) -> String {
        switch level.uppercased() {
        case "HIGH":
            return "ELEVEE"
        case "MEDIUM":
            return "MOYENNE"
        case "LOW":
            return "FAIBLE"
        case "MINIMAL":
            return "MINIMALE"
        default:
            return level
        }
    }

    private static func frenchTitle(for englishTitle: String) -> String {
        let mapping: [String: String] = [
            "Life, Liberty and Security of the Person": "Vie, liberte et securite de la personne",
            "Unreasonable Search and Seizure": "Fouilles, perquisitions ou saisies abusives",
            "Arbitrary Detention or Imprisonment": "Detention ou emprisonnement arbitraire",
            "Right to Retain and Instruct Counsel": "Droit de retenir et de consulter un avocat",
            "Equality Rights": "Droits a l'egalite"
        ]
        return mapping[englishTitle] ?? englishTitle
    }

    private func persistHistory(for envelope: AnalysisEnvelope) {
        let record = SavedAnalysisRecord(
            id: UUID(),
            createdAt: Date(),
            title: envelope.displayTitle,
            summary: envelope.shortSummary,
            breachCount: envelope.analysis.potentialBreaches.count,
            sourceKind: envelope.source.kind,
            envelope: envelope
        )

        savedHistory.removeAll { existing in
            existing.title == record.title && existing.summary == record.summary
        }
        savedHistory.insert(record, at: 0)
        if savedHistory.count > AppConfig.maxHistoryItems {
            savedHistory = Array(savedHistory.prefix(AppConfig.maxHistoryItems))
        }
        historyStore.save(savedHistory)
    }

    private func userFacingErrorMessage(for error: Error) -> String {
        if let apiError = error as? APIClientError, let message = apiError.errorDescription {
            return message
        }
        if let urlError = error as? URLError {
            switch urlError.code {
            case .timedOut:
                return "The request timed out. Check whether the API is running and reachable."
            case .notConnectedToInternet, .cannotFindHost, .cannotConnectToHost:
                return "Cannot reach the API. Verify the base URL and that the server is running."
            default:
                return urlError.localizedDescription
            }
        }
        return error.localizedDescription
    }

    private func mimeTypeForURL(_ url: URL) -> String {
        if let type = UTType(filenameExtension: url.pathExtension),
           let mimeType = type.preferredMIMEType {
            return mimeType
        }
        return "application/octet-stream"
    }
}
