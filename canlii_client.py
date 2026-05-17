# Copyright project_phoenix
"""
CanLII API Integration Module
Handles searching and retrieving cases from the CanLII database.
"""

import requests
import json
import urllib.parse
from datetime import datetime


def generate_citation_list(results):
    """Generate a formatted citation list from search results."""
    citations = []
    if not results or "results" not in results:
        return citations
        
    for case in results.get("results", []):
        citation = {
            "title": case.get("title", "Unknown"),
            "citation": case.get("citation", ""),
            "database_id": case.get("databaseId", ""),
            "case_id": case.get("caseId", ""),
            "url": case.get("url", f"https://www.canlii.org{case.get('path', '')}"),
            "date": case.get("decisionDate", ""),
            "jurisdiction": case.get("jurisdiction", "")
        }
        citations.append(citation)
    
    return citations


def _fallback_search(query):
    """
    Provide fallback search URLs when API key is not available.
    Generates direct CanLII search URLs the user can click.
    """
    encoded_query = urllib.parse.quote(query, safe="")
    
    return {
        "api_configured": False,
        "message": "CanLII API key not configured. Use the generated URLs to search directly.",
        "search_urls": {
            "general": f"https://www.canlii.org/en/search/#search[0][query]={encoded_query}",
            "charter_cases": f"https://www.canlii.org/en/search/#search[0][query]={encoded_query}+charter+breach",
            "constitutional": f"https://www.canlii.org/en/search/#search[0][query]={encoded_query}+constitutional+law",
        },
        "results": [],
        "tip": "Get a free API key at https://api.canlii.org/ for direct integration."
    }


class CanLIIClient:
    """Client for the CanLII API v1"""

    def __init__(self, api_key=None):
        from config import CANLII_API_BASE, CANLII_API_KEY
        self.api_key = api_key or CANLII_API_KEY
        self.base_url = CANLII_API_BASE
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"API-Key": self.api_key})

    def is_configured(self):
        return bool(self.api_key)

    def search_cases(self, query, database_id=None, jurisdiction=None, legislation=None, 
                     decision_date_start=None, decision_date_end=None, page=1, 
                     result_count=50):
        """
        Search CanLII for cases matching the query.
        
        Args:
            query: Search term(s)
            database_id: Specific CanLII database ID
            jurisdiction: Jurisdiction filter (e.g., 'on', 'bc', 'federal')
            legislation: Legislation reference filter
            decision_date_start: Start date (YYYY-MM-DD)
            decision_date_end: End date (YYYY-MM-DD)
            page: Page number for pagination
            result_count: Number of results per page
            
        Returns:
            dict: Search results
        """
        if not self.is_configured():
            return _fallback_search(query)

        endpoint = f"{self.base_url}/caseSearch/{self.api_key}"
        
        params = {
            "query": urllib.parse.quote(query, safe=""),
            "pageNum": page,
            "resultCount": result_count
        }

        if database_id:
            params["dbId"] = database_id
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        if legislation:
            params["legislation"] = legislation
        if decision_date_start:
            params["decisionDateFrom"] = decision_date_start
        if decision_date_end:
            params["decisionDateFrom"] = decision_date_end

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "results": [],
                "message": f"CanLII API error: {e}. Try using the web search fallback."
            }

    def get_case_metadata(self, database_id, case_id):
        """Retrieve metadata for a specific case."""
        if not self.is_configured():
            return {"error": "API key not configured"}

        endpoint = f"{self.base_url}/caseBrowse/{self.api_key}/{database_id}/{case_id}"
        
        try:
            response = self.session.get(endpoint, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_legislation(self, database_id, legislation_id):
        """Retrieve legislation from CanLII."""
        if not self.is_configured():
            return {"error": "API key not configured"}

        endpoint = f"{self.base_url}/legislationBrowse/{self.api_key}/{database_id}/{legislation_id}"
        
        try:
            response = self.session.get(endpoint, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def search_charter_breach_cases(self, section, keywords=None):
        """
        Search for cases involving a specific Charter section breach.
        
        Args:
            section: Charter section (e.g., "8", "2(b)")
            keywords: Additional keywords to refine the search (list of strings or dicts with 'keyword' key)
            
        Returns:
            dict: Search results
        """
        # Build a targeted search query
        search_terms = [f'"section {section}"', '"Canadian Charter of Rights"']
        
        if keywords:
            for kw in keywords[:3]:
                if isinstance(kw, dict) and 'keyword' in kw:
                    search_terms.append(f'"{kw["keyword"]}"')
                elif isinstance(kw, str):
                    search_terms.append(f'"{kw}"')
        
        query = " AND ".join(search_terms)
        return self.search_cases(query)


class CriminalLawNotebookClient:
    """Client for accessing Criminal Law Notebook content"""

    def __init__(self):
        pass

    BASE_URL = "https://criminalnotebook.ca"

    # Key topic areas from Criminal Law Notebook
    TOPICS = {
        "charter": {
            "name": "Charter of Rights",
            "url": f"{BASE_URL}/index.php?title=Canadian_Charter_of_Rights_and_Freedoms",
            "subtopics": {
                "s2_fundamental": f"{BASE_URL}/index.php?title=Fundamental_Freedoms_(Section_2)",
                "s7_liberty": f"{BASE_URL}/index.php?title=Section_7_of_the_Charter",
                "s8_search": f"{BASE_URL}/index.php?title=Section_8_of_the_Charter",
                "s9_detention": f"{BASE_URL}/index.php?title=Section_9_of_the_Charter",
                "s10_rights": f"{BASE_URL}/index.php?title=Section_10_of_the_Charter",
                "s11_trial": f"{BASE_URL}/index.php?title=Section_11_of_the_Charter",
                "s12_cruel": f"{BASE_URL}/index.php?title=Section_12_of_the_Charter",
                "s13_incrimination": f"{BASE_URL}/index.php?title=Section_13_of_the_Charter",
                "s14_interpreter": f"{BASE_URL}/index.php?title=Section_14_of_the_Charter",
                "s15_equality": f"{BASE_URL}/index.php?title=Section_15_of_the_Charter",
                "s1_oakes": f"{BASE_URL}/index.php?title=Section_1_and_the_Oakes_Test",
                "remedies": f"{BASE_URL}/index.php?title=Charter_Remedies",
                "exclusion": f"{BASE_URL}/index.php?title=Exclusion_of_Evidence_under_Section_24(2)",
            }
        },
        "evidence": {
            "name": "Evidence Law",
            "url": f"{BASE_URL}/index.php?title=Evidence",
            "subtopics": {
                "admissibility": f"{BASE_URL}/index.php?title=Admissibility_of_Evidence",
                "hearsay": f"{BASE_URL}/index.php?title=Hearsay",
                "confessions": f"{BASE_URL}/index.php?title=Confessions",
                "character": f"{BASE_URL}/index.php?title=Character_Evidence",
                "privilege": f"{BASE_URL}/index.php?title=Privilege",
                "similar_fact": f"{BASE_URL}/index.php?title=Similar_Fact_Evidence",
            }
        },
        "procedure": {
            "name": "Criminal Procedure",
            "url": f"{BASE_URL}/index.php?title=Criminal_Procedure",
            "subtopics": {
                "arrest": f"{BASE_URL}/index.php?title=Arrest",
                "bail": f"{BASE_URL}/index.php?title=Bail",
                "disclosure": f"{BASE_URL}/index.php?title=Disclosure",
                "arraignment": f"{BASE_URL}/index.php?title=Arraignment",
                "trial": f"{BASE_URL}/index.php?title=Trial_Process",
                "sentencing": f"{BASE_URL}/index.php?title=Sentencing",
                "appeals": f"{BASE_URL}/index.php?title=Appeals",
            }
        },
        "offences": {
            "name": "Criminal Offences",
            "url": f"{BASE_URL}/index.php?title=Criminal_Offences",
            "subtopics": {
                "homicide": f"{BASE_URL}/index.php?title=Homicide",
                "assault": f"{BASE_URL}/index.php?title=Assault_Offences",
                "sexual_offences": f"{BASE_URL}/index.php?title=Sexual_Offences",
                "property": f"{BASE_URL}/index.php?title=Property_Offences",
                "fraud": f"{BASE_URL}/index.php?title=Fraud_Offences",
                "drug_offences": f"{BASE_URL}/index.php?title=Drug_Offences",
            }
        },
        "defences": {
            "name": "Defences",
            "url": f"{BASE_URL}/index.php?title=Defences",
            "subtopics": {
                "self_defence": f"{BASE_URL}/index.php?title=Self-Defence",
                "necessity": f"{BASE_URL}/index.php?title=Necessity",
                "duress": f"{BASE_URL}/index.php?title=Duress",
                "intoxication": f"{BASE_URL}/index.php?title=Intoxication",
                "mental_disorder": f"{BASE_URL}/index.php?title=Mental_Disorder",
                "entrapment": f"{BASE_URL}/index.php?title=Entrapment",
                "abuse_of_process": f"{BASE_URL}/index.php?title=Abuse_of_Process",
            }
        }
    }

    def search_topics(self, keyword):
        """Search Criminal Law Notebook topics for matching content."""
        results = []
        keyword_lower = keyword.lower()
        
        for topic_id, topic in self.TOPICS.items():
            if keyword_lower in topic["name"].lower():
                results.append({
                    "type": "topic",
                    "topic_id": topic_id,
                    "name": topic["name"],
                    "url": topic["url"],
                    "relevance": "high"
                })
            
            for sub_id, sub_url in topic.get("subtopics", {}).items():
                sub_name = sub_id.replace("_", " ").title()
                if keyword_lower in sub_name.lower() or keyword_lower in topic["name"].lower():
                    results.append({
                        "type": "subtopic",
                        "topic_id": topic_id,
                        "subtopic_id": sub_id,
                        "name": f"{topic['name']} — {sub_name}",
                        "url": sub_url,
                        "relevance": "medium"
                    })
        
        return results

    def get_charter_section_reference(self, section):
        """Get the Criminal Law Notebook reference for a specific Charter section."""
        section_map = {
            "1": self.TOPICS["charter"]["subtopics"]["s1_oakes"],
            "2(a)": self.TOPICS["charter"]["subtopics"]["s2_fundamental"],
            "2(b)": self.TOPICS["charter"]["subtopics"]["s2_fundamental"],
            "2(c)": self.TOPICS["charter"]["subtopics"]["s2_fundamental"],
            "2(d)": self.TOPICS["charter"]["subtopics"]["s2_fundamental"],
            "7": self.TOPICS["charter"]["subtopics"]["s7_liberty"],
            "8": self.TOPICS["charter"]["subtopics"]["s8_search"],
            "9": self.TOPICS["charter"]["subtopics"]["s9_detention"],
            "10(a)": self.TOPICS["charter"]["subtopics"]["s10_rights"],
            "10(b)": self.TOPICS["charter"]["subtopics"]["s10_rights"],
            "11(a)": self.TOPICS["charter"]["subtopics"]["s11_trial"],
            "11(b)": self.TOPICS["charter"]["subtopics"]["s11_trial"],
            "11(c)": self.TOPICS["charter"]["subtopics"]["s11_trial"],
            "11(d)": self.TOPICS["charter"]["subtopics"]["s11_trial"],
            "12": self.TOPICS["charter"]["subtopics"]["s12_cruel"],
            "13": self.TOPICS["charter"]["subtopics"]["s13_incrimination"],
            "14": self.TOPICS["charter"]["subtopics"]["s14_interpreter"],
            "15(1)": self.TOPICS["charter"]["subtopics"]["s15_equality"],
        }
        
        return section_map.get(section, self.TOPICS["charter"]["url"])

    def get_remedy_reference(self):
        """Get Criminal Law Notebook reference for Charter remedies (s.24)."""
        return self.TOPICS["charter"]["subtopics"]["remedies"]

    def get_exclusion_reference(self):
        """Get Criminal Law Notebook reference for s.24(2) exclusion of evidence."""
        return self.TOPICS["charter"]["subtopics"]["exclusion"]