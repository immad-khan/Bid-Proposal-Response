from typing import TypedDict, List, Annotated, Dict, Any
import operator

class AgentState(TypedDict):
    """
    State definitions passed between LangGraph agents.
    """
    # Original RFP content or section text
    rfp_text: str
    
    # Parsed structural layout sections
    sections: List[Dict[str, Any]]
    
    # Actionable generation plan / requirements outline
    plan: Dict[str, Any]
    
    # Proposal draft response mapped by section ID or name
    drafts: Annotated[Dict[str, str], operator.ior]
    
    # LLM Judge and Gatekeeper reviews
    reviews: List[Dict[str, Any]]
    
    # Flag to determine if the draft is compliant and approved
    approved: bool
    
    # Current active agent or status info
    status: str
