import Foundation

struct AnalysisHistoryStore {
    private let fileURL: URL
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init() {
        let supportDirectory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        let directory = supportDirectory.appendingPathComponent("ProjectPhoenix", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        fileURL = directory.appendingPathComponent("analysis-history.json")

        encoder = JSONEncoder()
        decoder = JSONDecoder()
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func load() -> [SavedAnalysisRecord] {
        guard let data = try? Data(contentsOf: fileURL) else {
            return []
        }
        return (try? decoder.decode([SavedAnalysisRecord].self, from: data)) ?? []
    }

    func save(_ records: [SavedAnalysisRecord]) {
        guard let data = try? encoder.encode(records) else {
            return
        }
        try? data.write(to: fileURL, options: .atomic)
    }
}
