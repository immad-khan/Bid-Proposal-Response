"""
Compliance Schemas — Request and response models for Neo4j compliance tracking
and Go/No-Go bid evaluations.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RequirementCreateSchema(BaseModel):
    requirementId: str = Field(..., example="REQ-001")
    sectionPath: str = Field(..., example="Technical > Section 4.2 > Database")
    description: str = Field(..., example="The system must support Qdrant Cloud for vector index retrieval.")
    isMandatory: bool = Field(default=True)
    pageRef: Optional[int] = Field(default=None)


class ComplianceLinkSchema(BaseModel):
    proposalSectionId: str = Field(..., example="PROP-SEC-1")
    requirementId: str = Field(..., example="REQ-001")
    status: str = Field(default="COMPLIANT", pattern="^(COMPLIANT|PARTIAL|NON_COMPLIANT)$")
    evidence: str = Field(default="")
    score: float = Field(default=1.0, ge=0.0, le=1.0)


class GoNoGoEvaluateSchema(BaseModel):
    capability_score: float = Field(..., ge=0.0, le=1.0, description="Capability match coefficient")
    budget_alignment: float = Field(..., ge=0.0, le=1.0, description="Budget feasibility")
    timeline_feasibility: float = Field(..., ge=0.0, le=1.0, description="Delivery schedule realism")
    past_win_rate: float = Field(..., ge=0.0, le=1.0, description="Historical win rate in this sector")
    competitive_intensity: float = Field(..., ge=0.0, le=1.0, description="1 minus normalized competitor count")
    strategic_value: float = Field(..., ge=0.0, le=1.0, description="Long-term account value")


class GoNoGoResponseSchema(BaseModel):
    decision: str
    win_probability: float
    threshold: float
    model_type: str
    feature_impacts: List[Dict[str, Any]]
    top_factors: List[str]
