import SwiftUI

struct BreachDetailView: View {
    let breach: PotentialBreach

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("s. \(breach.section)")
                            .font(.headline)
                        Spacer()
                        Text(breach.confidenceLevel)
                            .font(.caption.weight(.semibold))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.accentColor.opacity(0.14), in: Capsule())
                    }

                    Text(breach.title)
                        .font(.title3.weight(.semibold))
                    Text(breach.description)
                        .font(.body)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }

            if let articulation = breach.legalArticulation {
                Section("Legal Articulation") {
                    Text(articulation.conclusion)
                    Text(articulation.governingTest)
                        .foregroundStyle(.secondary)

                    if !articulation.authorities.isEmpty {
                        ForEach(articulation.authorities, id: \.self) { authority in
                            Text(authority)
                                .font(.subheadline)
                        }
                    }
                }
            }

            if !breach.matchedKeywords.isEmpty {
                Section("Matched Keywords") {
                    ForEach(breach.matchedKeywords) { keyword in
                        HStack {
                            Text(keyword.keyword)
                            Spacer()
                            Text("\(keyword.count)")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }

            if !breach.breachIndicators.isEmpty {
                Section("Indicators") {
                    ForEach(breach.breachIndicators) { indicator in
                        HStack {
                            Text(indicator.type)
                            Spacer()
                            Text("\(indicator.count)")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }

            if !breach.applicableTests.isEmpty {
                Section("Applicable Tests") {
                    ForEach(breach.applicableTests.values.sorted(by: { $0.testID < $1.testID })) { test in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(test.question)
                                .font(.headline)
                            Text(test.analysis)
                                .foregroundStyle(.secondary)
                            Text(test.status.replacingOccurrences(of: "_", with: " ").capitalized)
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.primary)

                            if !test.identifiedIssues.isEmpty {
                                Text(test.identifiedIssues.joined(separator: ", "))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .navigationTitle("Section \(breach.section)")
        .navigationBarTitleDisplayMode(.inline)
    }
}
