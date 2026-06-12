from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from services.go_nogo_engine import GoNoGoEngine

logger = logging.getLogger(__name__)

router = APIRouter()

class EvaluateRFPRequest(BaseModel):
    compliance_gaps: List[str] = []
    rfp_budget: float = 100000.0
    company_base_cost: float = 80000.0

@router.post("/api/v1/evaluate-rfp")
async def evaluate_rfp(request: EvaluateRFPRequest):
    """
    Module 5.0: Evaluate RFP probability of winning.
    """
    try:
        # Convert request to LangGraph state dict expected by engine
        state = {
            "compliance_gaps": request.compliance_gaps,
            "rfp_budget": request.rfp_budget,
            "company_base_cost": request.company_base_cost
        }
        
        engine = GoNoGoEngine()
        result = engine.evaluate_rfp(state)
        
        return result
    except Exception as e:
        logger.error(f"Error evaluating RFP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
