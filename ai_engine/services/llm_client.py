import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Unified client wrapper for multiple LLM providers (Groq, OpenAI, Anthropic).
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        logger.info(f"LLMClient: Sending prompt to provider: {self.provider}")
        
        if self.provider == "openai":
            if not self.openai_key:
                return f"[Mock OpenAI Response] (API Key missing) - Response to: {prompt[:30]}"
            # Actual OpenAI API call would go here
            return f"[OpenAI Response] for: {prompt[:30]}"
            
        elif self.provider == "groq":
            if not self.groq_key:
                return f"[Mock Groq Response] (API Key missing) - Response to: {prompt[:30]}"
            # Actual Groq API call would go here
            return f"[Groq Response] for: {prompt[:30]}"
            
        elif self.provider == "anthropic":
            if not self.anthropic_key:
                return f"[Mock Anthropic Response] (API Key missing) - Response to: {prompt[:30]}"
            # Actual Anthropic API call would go here
            return f"[Anthropic Response] for: {prompt[:30]}"
            
        else:
            return f"[Mock Default Response] for: {prompt[:30]}"
