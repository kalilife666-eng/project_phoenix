import Foundation
import PDFKit
import UniformTypeIdentifiers

enum LocalDocumentReaderError: LocalizedError {
    case unsupportedOfflineFormat(String)
    case unreadableDocument

    var errorDescription: String? {
        switch self {
        case .unsupportedOfflineFormat(let ext):
            return "Offline import currently supports pdf, txt, md, and rtf. The '\(ext)' format still needs the backend."
        case .unreadableDocument:
            return "The document could not be read locally."
        }
    }
}

struct LocalDocumentReader {
    func readText(from url: URL) throws -> (text: String, sourceName: String, sourceFormat: String) {
        let ext = url.pathExtension.lowercased()

        switch ext {
        case "txt", "md":
            let text = try String(contentsOf: url, encoding: .utf8)
            return (text, url.lastPathComponent, ext)
        case "rtf":
            let data = try Data(contentsOf: url)
            let attributed = try NSAttributedString(
                data: data,
                options: [.documentType: NSAttributedString.DocumentType.rtf],
                documentAttributes: nil
            )
            return (attributed.string, url.lastPathComponent, ext)
        case "pdf":
            guard let document = PDFDocument(url: url) else {
                throw LocalDocumentReaderError.unreadableDocument
            }
            let pages = (0..<document.pageCount).compactMap { document.page(at: $0)?.string }
            let text = pages.joined(separator: "\n")
            guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw LocalDocumentReaderError.unreadableDocument
            }
            return (text, url.lastPathComponent, ext)
        case "docx":
            throw LocalDocumentReaderError.unsupportedOfflineFormat(ext)
        default:
            throw LocalDocumentReaderError.unsupportedOfflineFormat(ext.isEmpty ? "unknown" : ext)
        }
    }
}
