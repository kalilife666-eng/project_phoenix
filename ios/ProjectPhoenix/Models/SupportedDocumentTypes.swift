import UniformTypeIdentifiers

enum SupportedDocumentTypes {
    static let docx = UTType(filenameExtension: "docx") ?? .data
    static let markdown = UTType(filenameExtension: "md") ?? .plainText

    static let allowedImportTypes: [UTType] = [
        .pdf,
        docx,
        .plainText,
        .utf8PlainText,
        .rtf,
        markdown
    ]

    static let supportedExtensions: Set<String> = [
        "pdf",
        "docx",
        "txt",
        "rtf",
        "md"
    ]
}
