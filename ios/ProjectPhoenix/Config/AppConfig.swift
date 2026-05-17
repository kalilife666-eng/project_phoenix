import Foundation

enum AppConfig {
    static let defaultAPIBaseURL = "http://127.0.0.1:8000"
    static let networkTimeout: TimeInterval = 90
    static let maxImportBytes = 15 * 1024 * 1024
    static let maxHistoryItems = 20
}
