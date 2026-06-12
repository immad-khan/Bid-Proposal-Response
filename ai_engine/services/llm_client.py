"""
LLM Client — Unified wrapper for OpenAI, Groq, and Anthropic providers.
Routes prompt completion requests to the configured provider with proper
error handling and structured output support.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified client wrapper for multiple LLM providers (Groq, OpenAI, Anthropic).
    Lazily initializes the provider SDK on first use to avoid import errors
    when optional provider packages are not installed.
    """

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, backup_api_key: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()
        self.api_key = api_key
        self.backup_api_key = backup_api_key
        self._client = None
        self._backup_client = None
        self._model = None
        logger.info(f"LLMClient: Configured for provider '{self.provider}'")

    def _get_client(self, use_backup: bool = False):
        """Lazy-initialize the provider client on first call."""
        if use_backup:
            if self._backup_client is not None:
                return self._backup_client
            api_key_to_use = self.backup_api_key
        else:
            if self._client is not None:
                return self._client
            api_key_to_use = self.api_key

        if self.provider == "openai":
            from openai import OpenAI
            api_key = api_key_to_use or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            client = OpenAI(api_key=api_key)
            self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif self.provider == "groq":
            from groq import Groq
            api_key = api_key_to_use or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set.")
            client = Groq(api_key=api_key)
            self._model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        elif self.provider == "anthropic":
            import anthropic
            api_key = api_key_to_use or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
            client = anthropic.Anthropic(api_key=api_key)
            self._model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        else:
            raise ValueError(f"Unsupported LLM provider: '{self.provider}'. Use 'openai', 'groq', or 'anthropic'.")

        if use_backup:
            self._backup_client = client
            return self._backup_client
        else:
            self._client = client
            return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant specializing in RFP proposal writing.",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Send a prompt to the configured LLM provider and return the text response.

        Args:
            prompt: The user prompt / instruction.
            system_prompt: System-level instruction setting the assistant's role.
            max_tokens: Maximum tokens in the completion.
            temperature: Sampling temperature (0 = deterministic, 1 = creative).

        Returns:
            The generated text string.

        Raises:
            ValueError: If the provider API key is missing.
            Exception: On network or provider errors.
        """
    def _execute_generation(self, client, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> str:
        if self.provider in ("openai", "groq"):
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()

        elif self.provider == "anthropic":
            response = client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
            return response.content[0].text.strip()

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant specializing in RFP proposal writing.",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        client = self._get_client(use_backup=False)
        logger.info(f"LLMClient: Generating response via {self.provider}/{self._model} (temp={temperature})")

        try:
            return self._execute_generation(client, prompt, system_prompt, max_tokens, temperature)
        except Exception as e:
            logger.warning(f"LLMClient: Primary generation failed ({self.provider}) — {type(e).__name__}: {e}")
            
            # 1. First try same-provider backup key if provided
            if self.backup_api_key:
                logger.info("LLMClient: Attempting fallback with backup API key on same provider...")
                try:
                    backup_client = self._get_client(use_backup=True)
                    return self._execute_generation(backup_client, prompt, system_prompt, max_tokens, temperature)
                except Exception as backup_e:
                    logger.error(f"LLMClient: Same-provider fallback also failed — {type(backup_e).__name__}: {backup_e}")
            
            # 2. Try cross-provider fallback to OpenAI
            if self.provider != "openai" and os.getenv("OPENAI_API_KEY"):
                logger.info("LLMClient: Cross-provider fallback -> Attempting OpenAI...")
                try:
                    fallback_llm = LLMClient(provider="openai")
                    return fallback_llm.generate(prompt, system_prompt, max_tokens, temperature)
                except Exception as fallback_e:
                    logger.error(f"LLMClient: OpenAI fallback failed — {type(fallback_e).__name__}: {fallback_e}")

            # 3. Try cross-provider fallback to Anthropic
            if self.provider != "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
                logger.info("LLMClient: Cross-provider fallback -> Attempting Anthropic...")
                try:
                    fallback_llm = LLMClient(provider="anthropic")
                    return fallback_llm.generate(prompt, system_prompt, max_tokens, temperature)
                except Exception as fallback_e:
                    logger.error(f"LLMClient: Anthropic fallback failed — {type(fallback_e).__name__}: {fallback_e}")

            logger.error("LLMClient: All fallback attempts exhausted. Failing.")
            raise e

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant. Always respond with valid JSON only.",
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate a response and parse it as JSON.
        Useful for structured outputs (plans, evaluations, scores).
        """
        raw = self.generate(prompt, system_prompt, max_tokens, temperature)

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (the ``` markers)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"LLMClient: Failed to parse JSON response — {e}. Raw: {raw[:200]}")
            return {"raw_response": raw, "parse_error": str(e)}
