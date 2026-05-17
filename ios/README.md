# iPhone App Scaffold

This folder contains the iPhone client scaffold for `project_phoenix`.

## Architecture

- `mobile_api.py` stays responsible for all Python-based legal analysis.
- `ios/ProjectPhoenix/` contains a native SwiftUI client.
- The iPhone app sends either raw text or uploaded documents to the API and renders a mobile-friendly subset of the analysis.

## Why this shape

The current Android app uses Chaquopy to embed Python directly inside Android. That runtime is Android-only, so the iPhone path is to expose the existing analyzer over HTTP and keep the iOS client native.

## Generate the Xcode project

On macOS:

```bash
brew install xcodegen
cd ios
xcodegen generate
open ProjectPhoenix.xcodeproj
```

## Run the backend API

From the repository root:

```bash
python -m uvicorn mobile_api:app --host 0.0.0.0 --port 8000 --reload
```

## App configuration

Set the API base URL in the app's Settings screen.

- iOS Simulator can usually reach a local Mac server at `http://127.0.0.1:8000`.
- A physical iPhone needs a LAN URL, tunnel, or deployed API.
- If the backend sets `PROJECT_PHOENIX_MOBILE_API_TOKEN`, enter the same token in the app's Settings screen.

## Current scope

- Paste text and run Charter analysis
- Import `.pdf`, `.docx`, `.txt`, `.rtf`, or `.md`
- Filter flagged sections by confidence and search text
- Open section detail screens with supporting tests and indicators
- Share an exported text summary from the current analysis
- Keep a local saved-history list on device
- Switch between an English workspace and a separate French interface
- Generate an automatic French version of the analysis when offline mode is disabled and the backend translation API is available

## Not done yet

- Signing, provisioning, and App Store packaging
- Offline on-device analysis on iOS
- Richer offline caching beyond saved analysis snapshots
