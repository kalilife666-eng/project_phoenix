#!/usr/bin/env python3
# Copyright project_phoenix
"""
Disclosure Analysis Tool — Startup Script
Simple report/disclosure analysis using dictionary-backed checks.
"""

import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

if __name__ == "__main__":
    print("═" * 60)
    print("  Disclosure Analysis Tool")
    print("  Report checks • dictionary definitions • plain-language output")
    print("═" * 60)
    print()
    print("Starting GUI...")
    
    from main import main
    main()
