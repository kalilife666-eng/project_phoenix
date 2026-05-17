import SwiftUI

struct SettingsView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("apiToken") private var apiToken = ""
    @AppStorage("offlineModeEnabled") private var offlineModeEnabled = true
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Backend") {
                    TextField("API Base URL", text: $apiBaseURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        .autocorrectionDisabled()

                    Button("Use Simulator Default") {
                        apiBaseURL = AppConfig.defaultAPIBaseURL
                    }

                    Text("Example: http://192.168.1.10:8000")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Authentication") {
                    SecureField("Optional API Token", text: $apiToken)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()

                    Text("Only needed if `PROJECT_PHOENIX_MOBILE_API_TOKEN` is set on the backend.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Mode") {
                    Toggle("Offline Mode", isOn: $offlineModeEnabled)

                    Text("Turn this off when you want the French interface to generate automatic translated results through the backend translation API.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}
