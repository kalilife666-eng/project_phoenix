import SwiftUI

private enum InterfaceLanguage: String, CaseIterable, Identifiable {
    case english = "English"
    case french = "Francais"

    var id: String { rawValue }

    var navigationTitle: String {
        switch self {
        case .english: return "Project Phoenix"
        case .french: return "Projet Phoenix"
        }
    }

    var headerTitle: String {
        switch self {
        case .english: return "Canadian Charter analysis on iPhone"
        case .french: return "Analyse de la Charte canadienne sur iPhone"
        }
    }

    var headerSubtitle: String {
        switch self {
        case .english:
            return "Review flagged sections, inspect the supporting tests, and keep a local history of prior analyses while the Python engine runs behind the mobile API."
        case .french:
            return "Travaillez dans une interface francaise distincte et consultez une version francaise traduite automatiquement lorsque l'API de traduction est disponible."
        }
    }
}

struct ContentView: View {
    @StateObject private var viewModel = AnalysisViewModel()
    @State private var interfaceLanguage: InterfaceLanguage = .english

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.95, green: 0.92, blue: 0.86),
                        Color(red: 0.89, green: 0.91, blue: 0.95)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        languagePicker
                        header(for: interfaceLanguage)
                        composer(for: interfaceLanguage)
                        if viewModel.hasResults {
                            results(for: interfaceLanguage)
                        }
                        history(for: interfaceLanguage)
                    }
                    .padding(20)
                }
            }
            .navigationTitle(interfaceLanguage.navigationTitle)
            .toolbar {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    if viewModel.hasResults {
                        ShareLink(item: shareText(for: interfaceLanguage)) {
                            Text(interfaceLanguage == .english ? "Share" : "Partager")
                        }
                    }

                    Button(interfaceLanguage == .english ? "Settings" : "Reglages") {
                        viewModel.isShowingSettings = true
                    }
                }
            }
            .sheet(isPresented: $viewModel.isShowingSettings) {
                SettingsView()
            }
            .fileImporter(
                isPresented: $viewModel.isShowingImporter,
                allowedContentTypes: SupportedDocumentTypes.allowedImportTypes,
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    guard let url = urls.first else { return }
                    Task {
                        await viewModel.importDocument(from: url)
                    }
                case .failure(let error):
                    viewModel.errorMessage = error.localizedDescription
                }
            }
            .alert(alertTitle, isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error.")
            }
        }
        .task(id: interfaceLanguage) {
            if interfaceLanguage == .french {
                await viewModel.ensureFrenchPresentation()
            }
        }
    }

    private var alertTitle: String {
        interfaceLanguage == .english ? "Analysis Error" : "Erreur d'analyse"
    }

    private var languagePicker: some View {
        Picker("Interface", selection: $interfaceLanguage) {
            ForEach(InterfaceLanguage.allCases) { language in
                Text(language.rawValue).tag(language)
            }
        }
        .pickerStyle(.segmented)
    }

    private func header(for language: InterfaceLanguage) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(language.headerTitle)
                .font(.system(size: 30, weight: .bold, design: .serif))
            Text(language.headerSubtitle)
                .font(.body)
                .foregroundStyle(.secondary)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
    }

    private func composer(for language: InterfaceLanguage) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(language == .english ? "Input" : "Entree")
                .font(.headline)

            TextEditor(text: $viewModel.text)
                .frame(minHeight: 220)
                .padding(12)
                .scrollContentBackground(.hidden)
                .background(Color.white.opacity(0.75), in: RoundedRectangle(cornerRadius: 20, style: .continuous))

            HStack(spacing: 12) {
                Button(language == .english ? "Analyze Text" : "Analyser le texte") {
                    Task {
                        await viewModel.runTextAnalysis()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isLoading)

                Button(language == .english ? "Import Document" : "Importer un document") {
                    viewModel.isShowingImporter = true
                }
                .buttonStyle(.bordered)
                .disabled(viewModel.isLoading)

                Button(language == .english ? "Sample" : "Exemple") {
                    viewModel.loadSampleText()
                }
                .buttonStyle(.bordered)
                .disabled(viewModel.isLoading)

                if viewModel.isLoading {
                    ProgressView()
                }
            }

            Text(
                language == .english
                    ? "Simulator default API: http://127.0.0.1:8000"
                    : "API par defaut pour le simulateur : http://127.0.0.1:8000"
            )
            .font(.caption)
            .foregroundStyle(.secondary)

            Text(
                language == .english
                    ? "Supported formats: PDF, DOCX, TXT, RTF, MD"
                    : "Formats pris en charge : PDF, DOCX, TXT, RTF, MD"
            )
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(20)
        .background(Color.white.opacity(0.55), in: RoundedRectangle(cornerRadius: 28, style: .continuous))
    }

    @ViewBuilder
    private func results(for language: InterfaceLanguage) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            if let envelope = viewModel.envelope {
                if language == .english {
                    englishSummaryCard(for: envelope)
                    englishFilters
                    englishResults
                } else {
                    frenchSummaryCard
                    frenchResults
                }
            }
        }
    }

    private var englishFilters: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Review Filters")
                .font(.headline)

            TextField("Search section, title, or reasoning", text: $viewModel.breachSearchText)
                .textFieldStyle(.roundedBorder)

            Picker("Confidence", selection: $viewModel.confidenceFilter) {
                ForEach(BreachConfidenceFilter.allCases) { filter in
                    Text(filter.rawValue).tag(filter)
                }
            }
            .pickerStyle(.segmented)
        }
        .padding(18)
        .background(Color.white.opacity(0.6), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }

    @ViewBuilder
    private var englishResults: some View {
        if viewModel.filteredBreaches.isEmpty {
            Text("No flagged sections match the current filter.")
                .foregroundStyle(.secondary)
                .padding(.top, 6)
        } else {
            Text("Flagged Sections")
                .font(.headline)

            ForEach(viewModel.filteredBreaches) { breach in
                NavigationLink {
                    BreachDetailView(breach: breach)
                } label: {
                    breachCard(
                        sectionLabel: "s. \(breach.section)",
                        title: breach.title,
                        description: breach.legalArticulation?.conclusion ?? breach.description,
                        confidence: breach.confidenceLevel
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    @ViewBuilder
    private var frenchSummaryCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Version francaise automatique")
                .font(.headline)

            if viewModel.isTranslatingFrench {
                HStack(spacing: 10) {
                    ProgressView()
                    Text("Traduction en cours...")
                        .font(.subheadline)
                }
            } else if let presentation = viewModel.frenchPresentation {
                Text(presentation.summary)
                    .font(.subheadline)

                if let notice = presentation.notice {
                    Text(notice)
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.8))
                }

                if !presentation.recommendations.isEmpty {
                    Divider()
                        .overlay(Color.white.opacity(0.25))
                    Text("Recommandations")
                        .font(.headline)
                    ForEach(presentation.recommendations, id: \.self) { recommendation in
                        Text("• \(recommendation)")
                            .font(.subheadline)
                    }
                }
            } else if let error = viewModel.frenchTranslationError {
                Text(error)
                    .font(.subheadline)
            } else {
                Text("Aucune traduction francaise n'est encore disponible.")
                    .font(.subheadline)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.10, green: 0.23, blue: 0.24),
                    Color(red: 0.15, green: 0.30, blue: 0.18)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 28, style: .continuous)
        )
        .foregroundStyle(.white)
    }

    @ViewBuilder
    private var frenchResults: some View {
        if viewModel.isTranslatingFrench {
            EmptyView()
        } else if let presentation = viewModel.frenchPresentation, !presentation.breaches.isEmpty {
            Text("Sections signalees")
                .font(.headline)

            ForEach(presentation.breaches) { breach in
                breachCard(
                    sectionLabel: "art. \(breach.section)",
                    title: breach.title,
                    description: breach.description,
                    confidence: breach.confidenceLabel
                )
            }
        } else {
            Text("Aucune section traduite a afficher.")
                .foregroundStyle(.secondary)
                .padding(.top, 6)
        }
    }

    private func history(for language: InterfaceLanguage) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(language == .english ? "Saved History" : "Historique enregistre")
                .font(.headline)

            if viewModel.savedHistory.isEmpty {
                Text(
                    language == .english
                        ? "Completed analyses will appear here on this device."
                        : "Les analyses terminees apparaitront ici sur cet appareil."
                )
                .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.savedHistory) { record in
                    VStack(alignment: .leading, spacing: 10) {
                        Button {
                            viewModel.loadHistoryRecord(record)
                            if language == .french {
                                Task { await viewModel.ensureFrenchPresentation() }
                            }
                        } label: {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(record.title)
                                        .font(.headline)
                                        .foregroundStyle(.primary)
                                    Spacer()
                                    Text(record.createdAt.formatted(date: .abbreviated, time: .shortened))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Text(record.summary)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(3)
                                Text(historyCountText(record.breachCount, language: language))
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.primary)
                            }
                        }
                        .buttonStyle(.plain)

                        Button(language == .english ? "Delete" : "Supprimer", role: .destructive) {
                            viewModel.deleteHistoryRecord(record)
                        }
                        .font(.caption)
                    }
                    .padding(18)
                    .background(Color.white.opacity(0.6), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
                }
            }
        }
    }

    private func breachCard(sectionLabel: String, title: String, description: String, confidence: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(sectionLabel)
                    .font(.headline)
                Spacer()
                Text(confidence)
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color(red: 0.79, green: 0.29, blue: 0.18).opacity(0.14), in: Capsule())
            }

            Text(title)
                .font(.subheadline.weight(.semibold))
            Text(description)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .lineLimit(5)
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white.opacity(0.7), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }

    private func englishSummaryCard(for envelope: AnalysisEnvelope) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(envelope.displayTitle)
                .font(.headline)

            metadataStrip(for: envelope.source.metadata, language: .english)

            Text(envelope.shortSummary)
                .font(.subheadline)

            if let assessment = envelope.analysis.humanRightsAssessment {
                Text("Human Rights: \(assessment.level)")
                    .font(.subheadline.weight(.semibold))
                Text(assessment.assessment)
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.85))
            }

            if let recommendations = envelope.analysis.recommendations, !recommendations.isEmpty {
                Divider()
                    .overlay(Color.white.opacity(0.25))
                Text("Recommendations")
                    .font(.headline)
                ForEach(recommendations.prefix(4), id: \.self) { recommendation in
                    Text("• \(recommendation)")
                        .font(.subheadline)
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.16, green: 0.22, blue: 0.31),
                    Color(red: 0.40, green: 0.22, blue: 0.16)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 28, style: .continuous)
        )
        .foregroundStyle(.white)
    }

    private func metadataStrip(for metadata: DocumentMetadata, language: InterfaceLanguage) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                metadataPill(label: language == .english ? "Format" : "Format", value: metadata.format?.uppercased() ?? "TEXT")
                if let words = metadata.wordCount {
                    metadataPill(label: language == .english ? "Words" : "Mots", value: "\(words)")
                }
                if let paragraphs = metadata.paragraphCount {
                    metadataPill(label: language == .english ? "Paragraphs" : "Paragraphes", value: "\(paragraphs)")
                }
                if let sentences = metadata.sentenceCount {
                    metadataPill(label: language == .english ? "Sentences" : "Phrases", value: "\(sentences)")
                }
            }
        }
    }

    private func metadataPill(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.7))
            Text(value)
                .font(.caption.weight(.semibold))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.12), in: Capsule())
    }

    private func shareText(for language: InterfaceLanguage) -> String {
        if language == .french, let presentation = viewModel.frenchPresentation {
            var lines = [presentation.summary]
            if !presentation.recommendations.isEmpty {
                lines.append("")
                lines.append("Recommandations")
                lines.append(contentsOf: presentation.recommendations.map { "- \($0)" })
            }
            return lines.joined(separator: "\n")
        }
        return viewModel.shareSummaryText
    }

    private func historyCountText(_ count: Int, language: InterfaceLanguage) -> String {
        if language == .english {
            return "\(count) flagged section\(count == 1 ? "" : "s")"
        }
        return "\(count) section\(count == 1 ? "" : "s") signalee\(count == 1 ? "" : "s")"
    }
}
