# Copyright project_phoenix
import os
import sys
from ai_integration import AIIntegration

def test_gemini_connection(api_key):
    """
    Test Gemini API connection within the Android environment.
    """
    try:
        # Check if the library is available
        try:
            import google.generativeai as genai
        except ImportError:
            return "Error: google-generativeai library not installed in the Python environment."

        ai = AIIntegration(api_key=api_key, model="gemini-1.5-flash", provider="gemini")
        if not ai.is_configured():
            return "Error: AI not configured. Check API key."
            
        result = ai.ask_custom_question("Hello, are you working correctly?")
        
        if result.get("error"):
            return f"API Error: {result['error']}"
        
        return f"Success: {result['content']}"
    except Exception as e:
        return f"Exception: {str(e)}\nTraceback: {sys.exc_info()}"

if __name__ == "__main__":
    # For local testing if needed
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        print(test_gemini_connection(key))
    else:
        print("Set GEMINI_API_KEY env var to test.")
