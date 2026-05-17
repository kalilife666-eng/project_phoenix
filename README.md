# project_phoenix (v1.0) - Gemini Version

**Multi-Platform Canadian Charter Breach Analysis with CanLII, AI Verification & Legal Dictionary**

project_phoenix is a comprehensive legal analysis suite designed for both **Android** and **Desktop** environments. It leverages a shared Python-based analysis engine to detect potential Canadian Charter of Rights and Freedoms breaches, providing legal professionals with a powerful aid for case review.

This version (v1.0) is the **Gemini Release**, optimized for Google Gemini 1.5 Pro and incorporating advanced legal reasoning for *R v Tim* and *R v Storrey*.

---

## Platform Capabilities

### Android Application
- **Modern UI:** Built with Jetpack Compose for a native Android experience.
- **Embedded Engine:** Runs the core Python analysis engine locally via Chaquopy.
- **On-the-go Analysis:** Perform legal audits directly from your mobile device.

### Desktop Application
- **Feature-Rich GUI:** Powered by Tkinter for a comprehensive analysis environment.
- **Advanced Reasoning:** Integrated with Gemini-1.5-Pro for deep constitutional analysis.
- **Report Generation:** Export professional HTML and text reports.

---

## Features (Shared Engine)

### Charter Breach Analysis
- Automated detection of potential **Canadian Charter of Rights and Freedoms** breaches.
- Covers Sections 2(a)-15(1) with keyword analysis, breach indicators, and legal test frameworks.
- Confidence scoring (HIGH / MEDIUM / LOW) for each potential breach.
- **Enhanced Logic:** Integrated *R v Tim* (mistake of law) and *R v Storrey* (duty to inquire) reasoning.

### Cross-Reference Integration
- **CanLII** - Search Canadian case law with API integration.
- **Criminal Law Notebook** - Topic browser with direct links for Charter analysis.

### AI Verification (Google Gemini 1.5 Pro)
- AI-powered verification of Charter breach analysis accuracy.
- Advanced reasoning for legal ignorance and failure to investigate innocent explanations.
- Term verification, disambiguation, and executive summary generation.

### Legal Dictionary
- **50+ authoritative Canadian legal definitions** (Criminal Code, SCC jurisprudence).
- Flags misuses, Americanisms, and inconsistent terminology.

### Deflection & Ambiguity Detection
- Identifies vague quantifiers, hedging, passive obfuscation, and weasel words.
- Provides severity ratings and specific suggestions.

---

## Installation & Running

### Desktop
1. **Setup:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch:**
   ```bash
   python main.py
   ```

### Android
1. **Build:** Open the `android/` directory in Android Studio.
2. **Deploy:** Use `./gradlew assembleRelease` to generate artifacts or deploy directly to a device.
3. **Artifacts:** Pre-built `project_phoenix-release.apk` is available in the root directory.

---

## API Configuration

### CanLII (Free - Recommended)
1. Register at https://api.canlii.org/
2. Get your API key
3. In the app: **Settings -> API Keys -> CanLII API Key**

*Without a CanLII key, the app generates direct search URLs you can click.*

### Google Gemini (Required for AI Verification)
1. Get an API key at https://aistudio.google.com/
2. Set env variable: `export GEMINI_API_KEY="AIza..."`
3. Or enter via: **Settings -> API Keys -> Gemini API Key**

*The app works fully without AI - Gemini adds expert verification and enhanced legal reasoning.*

---

## Distribution Notice

Developer contact: **kalilife666@gmail.com**

Publisher-provided access policy:
- Open source software available for free download for all Canadians without a law license.
- This software is intended to remain available for free download permanently.
- Contributions to the developers and their descendants are welcome via e-Transfer to **kalilife666@gmail.com**.
- Any user with a law license requires a paid subscription of **CAD $300/month**.

---

## License
MIT
