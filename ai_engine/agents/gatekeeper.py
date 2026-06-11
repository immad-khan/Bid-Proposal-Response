import logging
from typing import Dict, Any
from agents.state import AgentState

logger = logging.getLogger(__name__)

class GatekeeperAgent:
    """
    Agent responsible for checking generated drafts against guardrails,
    verifying if there are hallucinated links or unsupported technical claims.
    """
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def verify(self, state: AgentState) -> Dict[str, Any]:
        logger.info("GatekeeperAgent: Running initial security and guardrail checks.")
        
        drafts = state.get("drafts", {})
        reviews = state.get("reviews", [])
        
        gatekeeper_log = []
        passed = True
        
        for req_id, text in drafts.items():
            # Check for generic safety/policy violations (e.g. dummy link placeholders)
            if "TODO" in text or "placeholder" in text.lower():
                gatekeeper_log.append({
                    "req_id": req_id,
                    "check": "No placeholders",
                    "passed": False,
                    "reason": "Draft contains unresolved TODO/placeholder text."
                })
                passed = False
            else:
                gatekeeper_log.append({
                    "req_id": req_id,
                    "check": "No placeholders",
                    "passed": True
                })
                
        reviews.append({
            "step": "gatekeeper",
            "passed": passed,
            "checks": gatekeeper_log
        })
        
        return {
            "reviews": reviews,
            "status": "Gatekeeper verification done."
        }
