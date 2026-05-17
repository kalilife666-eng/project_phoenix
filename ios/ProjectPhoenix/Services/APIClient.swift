import Foundation

enum APIClientError: LocalizedError {
    case invalidURL
    case server(String)
    case invalidResponse
    case requestFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The API base URL is invalid."
        case .server(let message):
            return message
        case .invalidResponse:
            return "The server returned an unreadable response."
        case .requestFailed(let message):
            return message
        }
    }
}

struct APIClient {
    var baseURL: String
    var accessToken: String?

    func analyzeText(_ text: String) async throws -> AnalysisEnvelope {
        let payload = AnalyzeTextPayload(text: text)
        return try await postJSON(path: "/analyze/text", body: payload)
    }

    func analyzeFile(data: Data, filename: String, mimeType: String) async throws -> AnalysisEnvelope {
        guard let url = URL(string: normalizedBaseURL + "/analyze/file") else {
            throw APIClientError.invalidURL
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = makeRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = makeMultipartBody(
            boundary: boundary,
            data: data,
            filename: filename,
            mimeType: mimeType
        )

        let (responseData, response) = try await session.data(for: request)
        try validate(response: response, data: responseData)
        return try decodeEnvelope(from: responseData)
    }

    func translateText(
        _ text: String,
        targetLanguage: String,
        sourceLanguage: String? = nil
    ) async throws -> TranslationEnvelope {
        let payload = TranslateTextPayload(
            text: text,
            targetLanguage: targetLanguage,
            sourceLanguage: sourceLanguage
        )
        return try await postJSON(path: "/translate", body: payload, decodeAs: TranslationEnvelope.self)
    }

    private var normalizedBaseURL: String {
        baseURL
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    private var session: URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = AppConfig.networkTimeout
        configuration.timeoutIntervalForResource = AppConfig.networkTimeout
        return URLSession(configuration: configuration)
    }

    private func postJSON<T: Encodable>(path: String, body: T) async throws -> AnalysisEnvelope {
        try await postJSON(path: path, body: body, decodeAs: AnalysisEnvelope.self)
    }

    private func postJSON<T: Encodable, R: Decodable>(path: String, body: T, decodeAs: R.Type) async throws -> R {
        guard let url = URL(string: normalizedBaseURL + path) else {
            throw APIClientError.invalidURL
        }

        var request = makeRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)

        let (responseData, response) = try await session.data(for: request)
        try validate(response: response, data: responseData)
        return try decodeResponse(from: responseData, as: decodeAs)
    }

    private func makeRequest(url: URL) -> URLRequest {
        var request = URLRequest(url: url)
        if let accessToken, !accessToken.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            request.setValue(accessToken, forHTTPHeaderField: "X-Project-Phoenix-Token")
        }
        return request
    }

    private func validate(response: URLResponse, data: Data) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ServerErrorResponse.self, from: data),
               let message = errorResponse.error.message {
                throw APIClientError.server(message)
            }
            if let legacyResponse = try? JSONDecoder().decode(LegacyServerErrorResponse.self, from: data) {
                throw APIClientError.server(legacyResponse.detail)
            }
            throw APIClientError.server("Server error.")
        }
    }

    private func decodeEnvelope(from data: Data) throws -> AnalysisEnvelope {
        try decodeResponse(from: data, as: AnalysisEnvelope.self)
    }

    private func decodeResponse<R: Decodable>(from data: Data, as type: R.Type) throws -> R {
        do {
            return try JSONDecoder().decode(type, from: data)
        } catch {
            throw APIClientError.invalidResponse
        }
    }

    private func makeMultipartBody(boundary: String, data: Data, filename: String, mimeType: String) -> Data {
        var body = Data()
        let prefix = "--\(boundary)\r\n"
        body.append(Data(prefix.utf8))
        body.append(Data("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".utf8))
        body.append(Data("Content-Type: \(mimeType)\r\n\r\n".utf8))
        body.append(data)
        body.append(Data("\r\n--\(boundary)--\r\n".utf8))
        return body
    }
}

private struct AnalyzeTextPayload: Encodable {
    let text: String
}

private struct TranslateTextPayload: Encodable {
    let text: String
    let targetLanguage: String
    let sourceLanguage: String?

    enum CodingKeys: String, CodingKey {
        case text
        case targetLanguage = "target_language"
        case sourceLanguage = "source_language"
    }
}

struct TranslationEnvelope: Decodable {
    let meta: ResponseMeta?
    let translation: TranslationBody
}

struct TranslationBody: Decodable {
    let sourceLanguage: String
    let targetLanguage: String
    let translatedText: String

    enum CodingKeys: String, CodingKey {
        case sourceLanguage = "source_language"
        case targetLanguage = "target_language"
        case translatedText = "translated_text"
    }
}

private struct ServerErrorResponse: Decodable {
    let error: ServerErrorBody
}

private struct ServerErrorBody: Decodable {
    let code: String?
    let message: String?
}

private struct LegacyServerErrorResponse: Decodable {
    let detail: String
}
