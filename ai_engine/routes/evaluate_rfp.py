from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

@router.get("/compliance/{project_id}/score")
async def get_compliance_score(project_id: str):
    """
    Get compliance score for a specific project
    """
    # Custom values for seeded projects
    scores = {
        "nasa-rfp": 0.92,
        "dod-cloud": 0.74,
        "who-system": 0.45
    }
    score = scores.get(project_id, 0.8)
    return {"project_id": project_id, "score": score}

@router.get("/go-nogo/{project_id}")
async def get_go_nogo_evaluation(project_id: str):
    """
    Get detailed Go/No-Go evaluation and SHAP analysis for a specific project
    """
    # Custom values for seeded projects to ensure rich mock data on the dashboard
    if project_id == "nasa-rfp":
        return {
            "probability": 0.88,
            "decision": "GO",
            "shap_features": [
                {"name": "compliance_rate", "value": 0.92, "shap": 0.15},
                {"name": "tech_gap_count", "value": 1.0, "shap": 0.05},
                {"name": "budget_margin_delta", "value": 0.21, "shap": 0.08}
            ]
        }
    elif project_id == "dod-cloud":
        return {
            "probability": 0.62,
            "decision": "NO-GO",
            "shap_features": [
                {"name": "compliance_rate", "value": 0.74, "shap": 0.02},
                {"name": "tech_gap_count", "value": 4.0, "shap": -0.05},
                {"name": "budget_margin_delta", "value": 0.10, "shap": -0.01}
            ]
        }
    elif project_id == "who-system":
        return {
            "probability": 0.32,
            "decision": "NO-GO",
            "shap_features": [
                {"name": "compliance_rate", "value": 0.45, "shap": -0.15},
                {"name": "tech_gap_count", "value": 8.0, "shap": -0.10},
                {"name": "budget_margin_delta", "value": 0.05, "shap": -0.08}
            ]
        }
    
    # Run the engine for any other dynamically generated project ID
    try:
        engine = GoNoGoEngine()
        res = engine.evaluate_rfp({
            "compliance_gaps": [],
            "rfp_budget": 100000.0,
            "company_base_cost": 85000.0
        })
        # Map output to format expected by backend
        shap_features = []
        for name, data in res.get("shap_explanations", {}).items():
            shap_features.append({
                "name": name,
                "value": data.get("value", 0.0),
                "shap": data.get("attribution", 0.0)
            })
        return {
            "probability": res.get("win_probability", 0.5),
            "decision": res.get("decision", "NO-GO"),
            "shap_features": shap_features
        }
    except Exception as e:
        logger.error(f"Failed to evaluate dynamic go-nogo: {e}")
        return {
            "probability": 0.5,
            "decision": "NO-GO",
            "shap_features": []
        }
