# Copyright project_phoenix
"""
AI Integration Module
Connects to OpenAI and Google Gemini APIs for enhanced legal analysis accuracy,  
term verification, ambiguity resolution, and cross-reference validation.
"""

import json
import os
import requests
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIIntegration:
    """
    AI-powered legal analysis enhancement.
    Supports OpenAI GPT-4 and Google Gemini for:
    - Legal term verification and disambiguation
    - Charter breach analysis accuracy review
    - Deflection/ambiguity detection enhancement
    - Case law cross-reference suggestions
    - Terminology consistency enforcement
    """

    # System prompts tailored for Canadian legal analysis
    SYSTEM_PROMPTS = {
        "charter_analysis": (
            "You are an expert Canadian constitutional law analyst. You have deep knowledge of the "
            "Canadian Charter of Rights and Freedoms, Supreme Court of Canada jurisprudence, and "
            "the criminal justice system. Your role is to:\n"
            "1. Verify Charter breach analysis for accuracy\n"
            "2. Identify any Charter issues the automated system may have missed\n"
            "3. Validate the confidence levels assigned to potential breaches\n"
            "4. Suggest specific SCC authorities that support or refute the analysis\n"
            "5. Ensure the Oakes test analysis is correctly applied\n"
            "6. Verify that the correct legal tests are cited for each Charter section\n\n"
            "Always cite specific cases with proper Canadian legal citation format. "
            "Be precise about legal tests and their requirements per SCC authority. "
            "If the analysis contains errors, correct them with authority."
        ),
        "term_verification": (
            "You are a Canadian legal terminology expert. Your role is to:\n"
            "1. Verify that legal terms are used correctly in their Canadian legal context\n"
            "2. Identify any terms used inconsistently or ambiguously\n"
            "3. Distinguish between similar but distinct legal concepts\n"
            "4. Flag any American or other foreign legal terminology incorrectly used in a Canadian context\n"
            "5. Ensure terminology aligns with Criminal Code definitions and SCC jurisprudence\n\n"
            "Be precise. Identify the specific misuse and provide the correct Canadian usage with authority."
        ),
        "deflection_detection": (
            "You are an expert in analytical legal reasoning and rhetoric. Your role is to:\n"
            "1. Identify instances where language is used to deflect, obscure, or avoid addressing legal issues\n"
            "2. Detect ambiguity that could be exploited to create unreasonable doubt\n"
            "3. Flag equivocation, circular reasoning, or question-begging in legal arguments\n"
            "4. Identify weasel words and unsupported assertions\n"
            "5. Detect when legal tests are described imprecisely to avoid their consequences\n"
            "6. Flag when the standard of proof or onus is described incorrectly or imprecisely\n\n"
            "For each instance found, explain WHY it is deflection or ambiguity, what the precise "
            "legal position should be, and the potential consequence of the ambiguity."
        ),
        "cross_reference_validation": (
            "You are a Canadian legal research expert with comprehensive knowledge of SCC and appellate "
            "court decisions. Your role is to:\n"
            "1. Validate that cited authorities actually stand for the propositions claimed\n"
            "2. Identify missing key authorities that should be referenced\n"
            "3. Suggest the most on-point SCC decisions for each Charter issue identified\n"
            "4. Flag any overruled or limited authority\n"
            "5. Suggest CanLII search terms that would locate the most relevant authorities\n\n"
            "Provide specific case names, citations, and the ratio/holding relevant to the issue."
        ),
        "summary": (
            "You are an expert Canadian criminal and constitutional law analyst. Summarize the "
            "following legal document analysis in clear, precise language. Identify:\n"
            "1. The key Charter issues\n"
            "2. The strength of each breach claim\n"
            "3. The likely Section 1 justification analysis\n"
            "4. The most appropriate remedies\n"
            "5. Any critical gaps in the analysis\n\n"
            "Write for a legal professional. Be concise and authoritative."
        ),
    }

    def __init__(
        self,
        api_key=None,
        model="gpt-4",
        base_url=None,
        provider="openai",
        initial_history=None,
        analysis=None,
        reasoning=None,
        **kwargs
    ):
        self.provider = provider
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if self.provider == "gemini":
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
            if GEMINI_AVAILABLE and self.api_key:
                genai.configure(api_key=self.api_key)

        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        chosen_reasoning = reasoning if reasoning is not None else analysis
        if chosen_reasoning is None and "analysis" in kwargs:
            chosen_reasoning = kwargs.get("analysis")
        self.reasoning = self._normalize_reasoning(chosen_reasoning)
        self.session = requests.Session()
        if self.provider == "openai" and self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
        self.conversation_history = initial_history if isinstance(initial_history, list) else []
        self.cost_tracker = {"total_tokens": 0, "requests": 0}

    def is_configured(self):
        return bool(self.api_key)

    def _call_api(self, system_prompt, user_message, temperature=0.2, max_tokens=2000):
        """Make an API call to the configured provider."""
        if not self.is_configured():
            provider_name = "Gemini" if self.provider == "gemini" else "OpenAI"
            return {
                "error": f"{provider_name} API key not configured. Set appropriate environment variable or provide key in settings.",
                "content": None,
                "fallback": True,
            }

        if self.provider == "gemini":
            return self._call_gemini(system_prompt, user_message, temperature, max_tokens)
        else:
            return self._call_openai(system_prompt, user_message, temperature, max_tokens)

    def _call_openai(self, system_prompt, user_message, temperature, max_tokens):
        """Make an API call to OpenAI."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        endpoint_order = ["/responses", "/chat/completions"] if self._should_prefer_responses() else ["/chat/completions", "/responses"]
        last_http_error = None

        try:
            for endpoint in endpoint_order:
                payload = self._build_openai_payload(endpoint, messages, temperature, max_tokens)
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=60,
                )
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    last_http_error = e
                    if response.status_code == 400:
                        continue
                    raise

                result = response.json()
                usage = result.get("usage", {})
                tokens_used = self._extract_token_usage(usage)
                self.cost_tracker["total_tokens"] += tokens_used
                self.cost_tracker["requests"] += 1
                content = self._extract_openai_text(result)

                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "provider": "openai",
                    "system_prompt": system_prompt,
                    "user_message": user_message,
                    "response": content,
                    "tokens_used": tokens_used,
                    "endpoint": endpoint,
                })

                return {"content": content, "error": None, "fallback": False}

            if last_http_error:
                return {
                    "error": f"OpenAI API error: {last_http_error.response.status_code} — {last_http_error.response.text[:200]}",
                    "content": None,
                    "fallback": True
                }
            return {"error": "OpenAI API error: request failed.", "content": None, "fallback": True}

        except requests.exceptions.Timeout:
            return {"error": "OpenAI API request timed out.", "content": None, "fallback": True}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to OpenAI API.", "content": None, "fallback": True}
        except requests.exceptions.HTTPError as e:
            return {"error": f"OpenAI API error: {e.response.status_code} — {e.response.text[:200]}", "content": None, "fallback": True}
        except Exception as e:
            return {"error": f"Unexpected OpenAI error: {str(e)}", "content": None, "fallback": True}

    def _is_reasoning_model(self):
        model_lower = (self.model or "").lower()
        return model_lower.startswith("o") or model_lower.startswith("gpt-5")

    def _normalize_reasoning(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            v = value.strip().lower()
            if not v:
                return None
            return {"effort": v}
        if isinstance(value, dict):
            normalized = {}
            effort = value.get("effort") or value.get("analysis") or value.get("level")
            if isinstance(effort, str) and effort.strip():
                normalized["effort"] = effort.strip().lower()
            summary = value.get("summary")
            if isinstance(summary, str) and summary.strip():
                normalized["summary"] = summary.strip().lower()
            return normalized or None
        return None

    def _should_prefer_responses(self):
        return self.reasoning is not None or self._is_reasoning_model()

    def _build_openai_payload(self, endpoint, messages, temperature, max_tokens):
        if endpoint == "/responses":
            payload = {
                "model": self.model,
                "input": messages,
                "max_output_tokens": max_tokens,
            }
            if self.reasoning:
                payload["reasoning"] = self.reasoning
            if (not self._is_reasoning_model()) and temperature is not None:
                payload["temperature"] = temperature
            return payload

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return payload

    def _extract_openai_text(self, result):
        if isinstance(result.get("output_text"), str):
            return result.get("output_text")

        if result.get("choices"):
            return result["choices"][0]["message"].get("content", "")

        parts = []
        for item in result.get("output", []) or []:
            if item.get("type") != "message":
                continue
            for content_item in item.get("content", []) or []:
                if content_item.get("type") == "output_text":
                    parts.append(content_item.get("text", ""))
                elif content_item.get("type") == "text":
                    parts.append(content_item.get("text", ""))
        return "\n".join([p for p in parts if p]).strip()

    def _extract_token_usage(self, usage):
        if not isinstance(usage, dict):
            return 0
        total = usage.get("total_tokens")
        if isinstance(total, int):
            return total
        input_tokens = usage.get("input_tokens", 0) or 0
        output_tokens = usage.get("output_tokens", 0) or 0
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            return input_tokens + output_tokens
        return 0

    def _call_gemini(self, system_prompt, user_message, temperature, max_tokens):
        """Make an API call to Google Gemini."""
        if not GEMINI_AVAILABLE:
            return {"error": "google-generativeai library not installed.", "content": None, "fallback": True}

        try:
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                system_instruction=system_prompt
            )

            response = model.generate_content(user_message)
            content = response.text

            # Track usage
            self.cost_tracker["requests"] += 1

            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "provider": "gemini",
                "system_prompt": system_prompt,
                "user_message": user_message,
                "response": content,
                "tokens_used": 0,
            })

            return {"content": content, "error": None, "fallback": False}

        except Exception as e:
            return {"error": f"Gemini API error: {str(e)}", "content": None, "fallback": True}

    def verify_charter_analysis(self, automated_results, document_excerpt):
        """
        Have AI verify and enhance the automated Charter breach analysis.
        """
        # Prepare a focused excerpt (first 3000 chars to stay within token limits)
        excerpt = document_excerpt[:3000] if len(document_excerpt) > 3000 else document_excerpt

        breaches_summary = []
        for breach in automated_results.get("potential_breaches", []):
            breaches_summary.append({
                "section": breach["section"],
                "title": breach["title"],
                "confidence": breach.get("confidence_level", "N/A"),
                "confidence_pct": int(breach.get("confidence", 0) * 100),
                "keywords_matched": [k["keyword"] for k in breach.get("matched_keywords", [])[:5]],
                "indicators": [i["type"] for i in breach.get("breach_indicators", [])[:5]],
            })

        user_msg = (
            f"DOCUMENT EXCERPT:\n---\n{excerpt}\n---\n\n"
            f"AUTOMATED CHARTER BREACH ANALYSIS RESULTS:\n"
            f"{json.dumps(breaches_summary, indent=2)}\n\n"
            f"OAKES ANALYSIS:\n"
            f"Justification likely: {automated_results.get('oakes_analysis', {}).get('justification_likely', 'N/A')}\n"
            f"Summary: {automated_results.get('oakes_analysis', {}).get('analysis_summary', 'N/A')}\n\n"
            f"Please review this analysis for:\n"
            f"1. Accuracy — Are the Charter issues correctly identified? Are any missed?\n"
            f"2. Confidence levels — Do you agree with HIGH/MEDIUM/LOW designations?\n"
            f"3. Legal tests — Are the correct tests cited for each section?\n"
            f"4. Missing issues — What Charter issues might the keyword-based system have missed?\n"
            f"5. Key authorities — What are the most important SCC cases for each breach identified?\n"
            f"6. Oakes analysis — Is the Section 1 assessment accurate?\n\n"
            f"Respond in structured JSON format with keys: 'verified_breaches', 'missed_issues', "
            f"'confidence_adjustments', 'key_authorities', 'oakes_assessment', 'overall_assessment'."
        )

        return self._call_api(self.SYSTEM_PROMPTS["charter_analysis"], user_msg, temperature=0.15, max_tokens=2500)

    def verify_legal_terms(self, document_text, flagged_terms):
        """
        Have AI verify legal terminology usage and flag misuses.
        """
        excerpt = document_text[:3000] if len(document_text) > 3000 else document_text

        user_msg = (
            f"DOCUMENT EXCERPT:\n---\n{excerpt}\n---\n\n"
            f"FLAGGED TERMINOLOGY ISSUES (from automated scan):\n"
            f"{json.dumps(flagged_terms[:20], indent=2)}\n\n"
            f"Please review:\n"
            f"1. Are the flagged misuses correctly identified?\n"
            f"2. Are there additional terminology errors the automated system missed?\n"
            f"3. Are any terms used in an American legal context when a Canadian term should apply?\n"
            f"4. Are any terms used ambiguously — where the meaning could shift depending on interpretation?\n"
            f"5. Are there instances where a defined legal term is used inconsistently?\n\n"
            f"For each issue, provide: the term, the problematic usage, the correct Canadian usage, "
            f"and the legal authority or source supporting the correction."
        )

        return self._call_api(self.SYSTEM_PROMPTS["term_verification"], user_msg, temperature=0.15, max_tokens=2500)

    def detect_deflection(self, document_text, automated_deflections):
        """
        Have AI detect and analyze deflection, ambiguity, and obfuscation.
        """
        excerpt = document_text[:4000] if len(document_text) > 4000 else document_text

        user_msg = (
            f"DOCUMENT EXCERPT:\n---\n{excerpt}\n---\n\n"
            f"AUTOMATED DEFLECTION/AMBIGUITY FLAGS:\n"
            f"{json.dumps(automated_deflections[:15], indent=2)}\n\n"
            f"Please perform a deeper analysis of deflection and ambiguity in this document:\n"
            f"1. Review the automated flags — are they genuine concerns or false positives?\n"
            f"2. Identify any deflection techniques the pattern-matching system would miss:\n"
            f"   - Subtle reframing of legal issues\n"
            f"   - Mischaracterization of the applicable legal test\n"
            f"   - Inaccurate description of the burden or onus\n"
            f"   - Strategic ambiguity about who bears the burden of proof\n"
            f"   - Presenting a higher standard of proof than required\n"
            f"   - Conflating distinct legal concepts (e.g., 'detention' vs 'arrest')\n"
            f"3. Identify any places where legal reasoning appears to avoid a necessary conclusion\n"
            f"4. Flag any instances where the document's language could be interpreted in multiple ways\n\n"
            f"For each finding, specify: the text at issue, the deflection/ambiguity type, "
            f"the precise legal position, the potential consequence, and a recommended clarification."
        )

        return self._call_api(self.SYSTEM_PROMPTS["deflection_detection"], user_msg, temperature=0.2, max_tokens=3000)

    def validate_cross_references(self, automated_results, document_text):
        """
        Have AI validate and enhance CanLII cross-reference suggestions.
        """
        excerpt = document_text[:2000] if len(document_text) > 2000 else document_text

        breaches = [b["section"] for b in automated_results.get("potential_breaches", [])]

        user_msg = (
            f"DOCUMENT EXCERPT:\n---\n{excerpt}\n---\n\n"
            f"CHARTER BREACHES IDENTIFIED: {', '.join(breaches) if breaches else 'None'}\n\n"
            f"Please suggest the most relevant SCC and appellate court authorities for each "
            f"Charter breach identified. For each authority, provide:\n"
            f"1. Full case citation (neutral and reporter)\n"
            f"2. The ratio or holding relevant to the specific Charter section\n"
            f"3. Suggested CanLII search terms\n"
            f"4. Whether the case is good law or has been limited/overruled\n"
            f"5. Any recent SCC decisions that may affect the analysis\n\n"
            f"Also identify any legislation (Criminal Code sections, etc.) directly relevant to each breach."
        )

        return self._call_api(self.SYSTEM_PROMPTS["cross_reference_validation"], user_msg, temperature=0.15, max_tokens=2500)

    def generate_summary(self, analysis_results):
        """
        Generate an AI-powered executive summary of the complete analysis.
        """
        user_msg = (
            f"COMPLETE ANALYSIS RESULTS:\n"
            f"{json.dumps(analysis_results, indent=2, default=str)[:5000]}\n\n"
            f"Please provide a concise executive summary covering:\n"
            f"1. Key Charter issues and their strength\n"
            f"2. The Section 1 justification outlook\n"
            f"3. Recommended remedies\n"
            f"4. Critical next steps for the legal professional\n"
            f"5. Any significant risks or gaps in the analysis"
        )

        return self._call_api(self.SYSTEM_PROMPTS["summary"], user_msg, temperature=0.3, max_tokens=1500)

    def ask_custom_question(self, question, document_context=""):
        """
        Ask a custom legal question with optional document context.
        """
        system = (
            "You are an expert Canadian criminal and constitutional law analyst. "
            "Answer the following question with precision, citing relevant authorities, "
            "legal tests, and Charter provisions as applicable. Use Canadian legal terminology."
        )

        user_msg = question
        if document_context:
            user_msg = f"DOCUMENT CONTEXT:\n---\n{document_context[:2000]}\n---\n\nQUESTION:\n{question}"

        return self._call_api(system, user_msg, temperature=0.3, max_tokens=2000)

    def get_usage_stats(self):
        """Get API usage statistics."""
        return {
            "total_tokens": self.cost_tracker["total_tokens"],
            "total_requests": self.cost_tracker["requests"],
            "estimated_cost_usd": round(self.cost_tracker["total_tokens"] * 0.00003, 4),  # rough GPT-4 estimate
        }

    def save_history(self, filepath):
        """Save conversation history to a JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False

    def load_history(self, filepath):
        """Load conversation history from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            if isinstance(history, list):
                self.conversation_history = history
                return True
            return False
        except Exception as e:
            print(f"Error loading history: {e}")
            return False

    def import_history(self, json_data):
        """Import conversation history from a JSON string or list."""
        try:
            if isinstance(json_data, str):
                import json
                history = json.loads(json_data)
            else:
                history = json_data

            if isinstance(history, list):
                self.conversation_history.extend(history)
                return True
            return False
        except Exception as e:
            print(f"Error importing history: {e}")
            return False
