# Routes package initializer

from .parsing import router as parsing_router
from .compliance import router as compliance_router
from .proposal import router as proposal_router

__all__ = ["parsing_router", "compliance_router", "proposal_router"]
