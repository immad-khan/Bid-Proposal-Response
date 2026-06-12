import logging
from typing import Dict, Any
from services.llm_client import LLMClient

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """\
You are an expert RFP Intelligence Extractor.
Your task is to analyze raw RFP markdown text and extract specific structured data.
You must output ONLY valid JSON without any markdown formatting or explanations.
"""

EXTRACTION_PROMPT_TEMPLATE = """\
Analyze the following RFP text and extract the key intelligence points.

**RFP Text:**
{rfp_text}

Extract the following entities and return them as a JSON object with these exact keys:
- "deadlines_and_dates": List of strings (e.g., submission deadlines, Q&A cutoffs, start dates).
- "mandatory_verbs": List of strings (sentences containing "must", "shall", "required").
- "kpis_and_metrics": List of strings (any performance metrics, SLAs, or required numbers).
- "budget_and_pricing": List of strings (budget caps, pricing structures, financial constraints).
- "compliance_standards": List of strings (e.g., ISO, SOC 2, GDPR, HIPAA, FedRAMP).

If any category has no matches, return an empty list for that key.

Respond with ONLY the JSON object.
"""

class ExtractionService:
    """
    Node 2.0: NER & Schema Extraction
    Extracts structured requirements (Deadlines, Verbs, KPIs, Budget, Compliance) 
    from raw RFP markdown text.
    """
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    def extract_intelligence(self, rfp_text: str) -> Dict[str, Any]:
        """
        Runs the extraction prompt against the LLM to build the JSON preview.
        """
        logger.info("ExtractionService: Starting NER and Schema Extraction (Node 2.0)")
        
        if not rfp_text or not rfp_text.strip():
            logger.warning("ExtractionService: Empty text provided.")
            return self._empty_result()
            
        try:
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                rfp_text=rfp_text[:6000]  # truncate to avoid blowing up context
            )
            
            result = self.llm_client.generate_json(
                prompt=prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                max_tokens=2048,
                temperature=0.1
            )
            
            # Ensure all keys exist
            return {
                "deadlines_and_dates": result.get("deadlines_and_dates", []),
                "mandatory_verbs": result.get("mandatory_verbs", []),
                "kpis_and_metrics": result.get("kpis_and_metrics", []),
                "budget_and_pricing": result.get("budget_and_pricing", []),
                "compliance_standards": result.get("compliance_standards", [])
            }
            
        except Exception as e:
            logger.error(f"ExtractionService: Failed to extract intelligence - {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "deadlines_and_dates": [],
            "mandatory_verbs": [],
            "kpis_and_metrics": [],
            "budget_and_pricing": [],
            "compliance_standards": []
        }
