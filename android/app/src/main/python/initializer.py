# Copyright project_phoenix
"""
NLP Initializer Module
Handles downloading and configuring NLP resources (NLTK, SpaCy) at runtime.
"""

import os
import nltk

def initialize_nlp(data_dir):
    """
    Initialize NLP data.

    Args:
        data_dir: Path to the directory where NLTK data should be stored.
    """
    print(f"Initializing NLP with data directory: {data_dir}")

    # Create the directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Configure NLTK to use the specified directory
    nltk.data.path.append(data_dir)

    # Required NLTK resources
    resources = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
    ]

    for resource_path, resource_name in resources:
        try:
            # Check if resource is already downloaded
            nltk.data.find(resource_path)
            print(f"NLTK resource '{resource_name}' already exists.")
        except LookupError:
            print(f"Downloading NLTK resource: {resource_name}")
            nltk.download(resource_name, download_dir=data_dir)

    print("NLP initialization complete.")
    return True
