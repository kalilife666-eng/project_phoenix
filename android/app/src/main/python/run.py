# Copyright project_phoenix
#!/usr/bin/env python3
"""
project_phoenix — Startup Script
Canadian Charter breach analysis with CanLII, Criminal Law Notebook,
legal dictionary, deflection detection, and AI verification.
"""

import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("═" * 60)
    print("  ⚖️  project_phoenix")
    print("  Charter Breach • CanLII • CLN • AI Verification")
    print("═" * 60)
    print()
    print("Starting GUI...")
    
    from main import main
    main()