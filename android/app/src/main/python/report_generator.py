# Copyright project_phoenix
"""
Report Generator Module
Generates analysis reports in various formats (HTML, PDF, TXT).
"""

import os
from datetime import datetime


class ReportGenerator:
    """Generate formatted analysis reports."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_html_report(self, analysis_results, document_metadata, output_path):
        """Generate a detailed HTML report."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>project_phoenix — Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
            color: white;
            padding: 30px 40px;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 5px;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 30px 40px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #1a237e;
            border-bottom: 2px solid #e8eaf6;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .section h3 {{
            color: #283593;
            margin: 15px 0 10px;
        }}
        .alert {{
            padding: 15px 20px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .alert-high {{
            background: #ffebee;
            border-left: 4px solid #c62828;
            color: #b71c1c;
        }}
        .alert-medium {{
            background: #fff3e0;
            border-left: 4px solid #e65100;
            color: #bf360c;
        }}
        .alert-low {{
            background: #e8f5e9;
            border-left: 4px solid #2e7d32;
            color: #1b5e20;
        }}
        .alert-info {{
            background: #e3f2fd;
            border-left: 4px solid #1565c0;
            color: #0d47a1;
        }}
        .breach-card {{
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
        }}
        .breach-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-high {{ background: #ffcdd2; color: #c62828; }}
        .badge-medium {{ background: #ffe0b2; color: #e65100; }}
        .badge-low {{ background: #c8e6c9; color: #2e7d32; }}
        .confidence-bar {{
            background: #e0e0e0;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .confidence-fill {{
            height: 100%;
            border-radius: 10px;
        }}
        .confidence-fill.high {{ background: #c62828; }}
        .confidence-fill.medium {{ background: #e65100; }}
        .confidence-fill.low {{ background: #2e7d32; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #e8eaf6;
            color: #283593;
            font-weight: 600;
        }}
        .keyword-tag {{
            display: inline-block;
            background: #e8eaf6;
            color: #283593;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin: 2px;
        }}
        .test-item {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px 15px;
            margin: 8px 0;
        }}
        .test-issue {{
            border-left: 3px solid #c62828;
        }}
        .test-ok {{
            border-left: 3px solid #2e7d32;
        }}
        .oakes-step {{
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        }}
        .recommendation {{
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 4px;
            background: #fff9c4;
            border-left: 3px solid #f9a825;
        }}
        .recommendation.priority {{
            border-left-color: #c62828;
            background: #ffebee;
        }}
        .url-link {{
            color: #1565c0;
            text-decoration: none;
            word-break: break-all;
        }}
        .url-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 20px 40px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}
        .meta-item {{
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 4px;
        }}
        .meta-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .meta-value {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        .remedy-card {{
            background: #e8f5e9;
            border: 1px solid #a5d6a7;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        }}
        .disclaimer {{
            background: #fff3e0;
            border: 1px solid #ffe0b2;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            font-size: 13px;
            color: #e65100;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ project_phoenix — Analysis Report</h1>
            <p>Authoritative Canadian Charter Analysis</p>
            <p>Generated: {self.timestamp}</p>
        </div>
        <div class="content">
"""

        # Document Metadata
        meta = document_metadata
        html += f"""
            <div class="section">
                <h2>📋 Document Information</h2>
                <div class="meta-grid">
                    <div class="meta-item">
                        <div class="meta-label">File Name</div>
                        <div class="meta-value">{meta.get('file_name', 'N/A')}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Format</div>
                        <div class="meta-value">{meta.get('format', 'N/A')}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Words</div>
                        <div class="meta-value">{meta.get('word_count', 'N/A'):,}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Paragraphs</div>
                        <div class="meta-value">{meta.get('paragraph_count', 'N/A')}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Characters</div>
                        <div class="meta-value">{meta.get('char_count', 'N/A'):,}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Sentences</div>
                        <div class="meta-value">{meta.get('sentence_count', 'N/A')}</div>
                    </div>
                </div>
            </div>
"""

        # Disclaimer
        html += """
            <div class="disclaimer">
                <strong>⚠️ DISCLAIMER:</strong> This analysis is generated by an automated tool and does not constitute legal advice.
                All findings should be reviewed by a qualified Canadian legal professional. Keyword matching and automated
                analysis cannot replace the exercise of legal judgment.
            </div>
"""

        # Overall Assessment
        html += f"""
            <div class="section">
                <h2>📊 Overall Assessment</h2>
                <div class="alert alert-info">
                    {analysis_results.get('overall_assessment', 'No assessment available.')}
                </div>
                <p><strong>Potential breaches identified:</strong> {len(analysis_results.get('potential_breaches', []))}</p>
                <p><strong>Charter sections referenced in document:</strong> {len(analysis_results.get('charter_sections_referenced', []))}</p>
                <p><strong>Remedies identified:</strong> {len(analysis_results.get('remedies', []))}</p>
            </div>
"""

        # Potential Breaches Detail
        html += """
            <div class="section">
                <h2>🔍 Potential Charter Breaches</h2>
"""
        breaches = analysis_results.get("potential_breaches", [])
        if breaches:
            for breach in breaches:
                conf_level = breach.get("confidence_level", "LOW").lower()
                conf_pct = int(breach.get("confidence", 0) * 100)

                html += f"""
                <div class="breach-card">
                    <div class="breach-header">
                        <h3>Section {breach['section']} — {breach['title']}</h3>
                        <span class="badge badge-{conf_level}">{breach.get('confidence_level', 'LOW')}</span>
                    </div>
                    <p><em>{breach.get('description', '')}</em></p>
                    <div class="confidence-bar">
                        <div class="confidence-fill {conf_level}" style="width: {conf_pct}%"></div>
                    </div>
                    <p>Confidence: {conf_pct}%</p>
"""

                # Keywords
                if breach.get("matched_keywords"):
                    html += "                    <p><strong>Matched keywords:</strong> "
                    for kw in breach["matched_keywords"]:
                        html += f'<span class="keyword-tag">{kw["keyword"]} ({kw["count"]})</span> '
                    html += "</p>\n"

                # Breach indicators
                if breach.get("breach_indicators"):
                    html += "                    <p><strong>Breach indicators:</strong></p><ul>"
                    for ind in breach["breach_indicators"]:
                        html += f"<li>{ind['type']}: {ind['count']} occurrences</li>"
                    html += "</ul>"

                # Applicable tests
                if breach.get("applicable_tests"):
                    html += "                    <p><strong>Legal Tests:</strong></p>"
                    for test_id, test in breach["applicable_tests"].items():
                        css_class = "test-issue" if test["status"] == "potential_issue" else "test-ok"
                        html += f"""
                    <div class="test-item {css_class}">
                        <strong>{test['question']}</strong><br>
                        <em>Status: {test['status'].replace('_', ' ').title()}</em>
"""
                        if test.get("identified_issues"):
                            html += "<br>Issues found: " + ", ".join(test["identified_issues"])
                        html += "                    </div>\n"

                html += "                </div>\n"
        else:
            html += '            <div class="alert alert-low">No potential Charter breaches identified in this document.</div>\n'

        html += "            </div>\n"

        # Oakes Analysis
        oakes = analysis_results.get("oakes_analysis")
        if oakes:
            just_status = "N/A"
            just_color = "alert-info"
            if oakes.get("justification_likely") is True:
                just_status = "JUSTIFICATION LIKELY"
                just_color = "alert-low"
            elif oakes.get("justification_likely") is False:
                just_status = "JUSTIFICATION UNLIKELY"
                just_color = "alert-high"
            else:
                just_status = "JUSTIFICATION UNCERTAIN"
                just_color = "alert-medium"

            html += f"""
            <div class="section">
                <h2>⚖️ Section 1 — Oakes Test Analysis</h2>
                <div class="alert {just_color}">
                    <strong>{just_status}</strong><br>
                    {oakes.get('analysis_summary', '')}
                </div>
                <p><strong>Breaches requiring justification:</strong> {', '.join(oakes.get('breaches_requiring_justification', []))}</p>
"""
            for step_id, step in oakes.get("steps", {}).items():
                html += f"""
                <div class="oakes-step">
                    <h4>{step['question']}</h4>
                    <p>{step.get('analysis', '')}</p>
"""
                for sq_id, sq in step.get("sub_questions", {}).items():
                    html += f"""
                    <div class="test-item">
                        <strong>{sq['question']}</strong><br>
                        {sq.get('assessment', '')}
"""
                    if sq.get("indicators_found"):
                        html += "<br>Indicators: " + ", ".join(sq["indicators_found"])
                    html += "                    </div>\n"

                html += "                </div>\n"

            html += "            </div>\n"

        # Remedies
        remedies = analysis_results.get("remedies", [])
        if remedies:
            html += """
            <div class="section">
                <h2>💊 Potential Remedies</h2>
"""
            for remedy in remedies:
                html += f"""
                <div class="remedy-card">
                    <h3>{remedy['description']}</h3>
"""
                if remedy.get("options"):
                    html += "<ul>"
                    for opt in remedy["options"]:
                        html += f"<li>{opt}</li>"
                    html += "</ul>"
                if remedy.get("grant_test"):
                    html += "<ul>"
                    for item in remedy["grant_test"]:
                        html += f"<li>{item}</li>"
                    html += "</ul>"
                if remedy.get("grounds"):
                    html += "<ul>"
                    for g in remedy["grounds"]:
                        html += f"<li>{g}</li>"
                    html += "</ul>"
                if remedy.get("principles"):
                    html += "<ul>"
                    for p in remedy["principles"]:
                        html += f"<li>{p}</li>"
                    html += "</ul>"
                html += "                </div>\n"

            html += "            </div>\n"

        # Cross References
        cross_refs = analysis_results.get("cross_references", {})
        canlii_refs = cross_refs.get("canlii", {})
        cln_refs = cross_refs.get("criminallawnotebook", {})

        if canlii_refs or cln_refs:
            html += """
            <div class="section">
                <h2>📚 Cross-References</h2>
"""
            if canlii_refs:
                html += "                <h3>CanLII — Case Law Search</h3>"
                for section, refs in canlii_refs.items():
                    html += f"""
                <div class="breach-card">
                    <h4>Section {section}</h4>
"""
                    if refs.get("search_urls"):
                        html += "<p><strong>Search URLs:</strong></p><ul>"
                        for label, url in refs["search_urls"].items():
                            html += f'<li><a class="url-link" href="{url}" target="_blank">{label.title()}: {url}</a></li>'
                        html += "</ul>"
                    html += "                </div>\n"

            if cln_refs:
                html += "                <h3>Criminal Law Notebook</h3>"
                for section, refs in cln_refs.items():
                    html += f"""
                <div class="breach-card">
                    <h4>Section {section}</h4>
"""
                    if refs.get("direct_reference"):
                        html += f'<p><strong>Direct reference:</strong> <a class="url-link" href="{refs["direct_reference"]}" target="_blank">{refs["direct_reference"]}</a></p>'
                    if refs.get("related_topics"):
                        html += "<p><strong>Related topics:</strong></p><ul>"
                        for topic in refs["related_topics"]:
                            html += f'<li><a class="url-link" href="{topic["url"]}" target="_blank">{topic["name"]}</a></li>'
                        html += "</ul>"
                    if refs.get("exclusion_reference"):
                        html += f'<p><strong>Exclusion of Evidence:</strong> <a class="url-link" href="{refs["exclusion_reference"]}" target="_blank">{refs["exclusion_reference"]}</a></p>'
                    html += "                </div>\n"

            html += "            </div>\n"

        # Recommendations
        recommendations = analysis_results.get("recommendations", [])
        if recommendations:
            html += """
            <div class="section">
                <h2>✅ Recommendations</h2>
"""
            for rec in recommendations:
                is_priority = rec.startswith("[PRIORITY]") or rec.startswith("[REMEDY]")
                css_class = "priority" if is_priority else ""
                html += f'                <div class="recommendation {css_class}">{rec}</div>\n'

            html += "            </div>\n"

        # Footer
        html += f"""
            <div class="footer">
                <p>Generated by project_phoenix v{os.environ.get("APP_VERSION", "1.0")} — {self.timestamp}</p>
                <p>This report does not constitute legal advice. Consult a qualified Canadian legal professional.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        # Write report
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def generate_text_report(self, analysis_results, document_metadata, output_path):
        """Generate a plain text report."""
        lines = ["=" * 80, "PROJECT PHOENIX — ANALYSIS REPORT",
                 "Authoritative Canadian Charter Analysis",
                 f"Generated: {self.timestamp}", "=" * 80]

        # Document Info
        meta = document_metadata
        lines.append(f"\nDOCUMENT INFORMATION")
        lines.append("-" * 40)
        lines.append(f"  File:     {meta.get('file_name', 'N/A')}")
        lines.append(f"  Format:   {meta.get('format', 'N/A')}")
        lines.append(f"  Words:    {meta.get('word_count', 'N/A'):,}")
        lines.append(f"  Paragraphs: {meta.get('paragraph_count', 'N/A')}")

        # Disclaimer
        lines.append(f"\nDISCLAIMER: This analysis does not constitute legal advice.")

        # Overall Assessment
        lines.append(f"\nOVERALL ASSESSMENT")
        lines.append("-" * 40)
        lines.append(analysis_results.get("overall_assessment", "No assessment available."))

        # Breaches
        breaches = analysis_results.get("potential_breaches", [])
        lines.append(f"\nPOTENTIAL CHARTER BREACHES ({len(breaches)} found)")
        lines.append("=" * 60)
        for breach in breaches:
            lines.append(f"\n  Section {breach['section']} — {breach['title']}")
            lines.append(f"  Confidence: {breach.get('confidence_level', 'N/A')} ({int(breach.get('confidence', 0)*100)}%)")
            lines.append(f"  Description: {breach.get('description', '')}")
            if breach.get("matched_keywords"):
                lines.append(f"  Keywords: {', '.join([k['keyword'] for k in breach['matched_keywords']])}")
            if breach.get("applicable_tests"):
                lines.append(f"  Legal Tests:")
                for tid, test in breach["applicable_tests"].items():
                    status_icon = "⚠️" if test["status"] == "potential_issue" else "✓"
                    lines.append(f"    {status_icon} {test['question']} — {test['status']}")

        # Oakes
        oakes = analysis_results.get("oakes_analysis")
        if oakes:
            lines.append(f"\nSECTION 1 — OAKES TEST")
            lines.append("-" * 40)
            lines.append(oakes.get("analysis_summary", ""))
            for step_id, step in oakes.get("steps", {}).items():
                lines.append(f"  {step['question']}")
                lines.append(f"  → {step.get('analysis', '')}")

        # Remedies
        remedies = analysis_results.get("remedies", [])
        if remedies:
            lines.append(f"\nREMEDIES")
            lines.append("-" * 40)
            for r in remedies:
                lines.append(f"  {r['description']}")

        # Cross-refs
        cross_refs = analysis_results.get("cross_references", {})
        canlii_refs = cross_refs.get("canlii", {})
        if canlii_refs:
            lines.append(f"\nCANLII CROSS-REFERENCES")
            lines.append("-" * 40)
            for section, refs in canlii_refs.items():
                lines.append(f"  Section {section}:")
                if refs.get("search_urls"):
                    for label, url in refs["search_urls"].items():
                        lines.append(f"    {label.title()}: {url}")

        # Recommendations
        recommendations = analysis_results.get("recommendations", [])
        if recommendations:
            lines.append(f"\nRECOMMENDATIONS")
            lines.append("-" * 40)
            for rec in recommendations:
                lines.append(f"  • {rec}")

        lines.append(f"\n{'=' * 80}")
        lines.append(f"End of Report — {self.timestamp}")
        lines.append("=" * 80)

        report_text = "\n".join(lines)
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        return output_path