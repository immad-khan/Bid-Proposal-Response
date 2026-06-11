import logging
from typing import Dict, Any
from agents.state import AgentState

logger = logging.getLogger(__name__)

class JudgeAgent:
    """
    Agent acting as an LLM Judge, scoring the generated response
    for compliance accuracy, clarity, and completeness against the RFP.
    """
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def score(self, state: AgentState) -> Dict[str, Any]:
        logger.info("JudgeAgent: Scoring drafts for compliance and clarity.")
        
        drafts = state.get("drafts", {})
        reviews = state.get("reviews", [])
        
        total_score = 0
        scored_count = 0
        judge_log = []
        
        for req_id, text in drafts.items():
            # Mock LLM evaluation score
            # A real implementation would compare the text with the actual RFP requirements
            score = 8.5  # mock score out of 10
            
            judge_log.append({
                "req_id": req_id,
                "score": score,
                "feedback": "Strong structure, clearly addresses user's scaling question."
            })
            total_score += score
            scored_count += 1
            
        avg_score = (total_score / scored_count) if scored_count > 0 else 0
        approved = avg_score >= 7.0
        
        reviews.append({
            "step": "llm_judge",
            "average_score": avg_score,
            "passed": approved,
            "details": judge_log
        })
        
        return {
            "reviews": reviews,
            "approved": approved,
            "status": f"Judge scoring complete. Approved: {approved} (Score: {avg_score}/10)"
        }
