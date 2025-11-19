# services/api/app/services/llm_client.py
"""
LLM client supporting multiple backends. Uses HuggingFace local generation if available,
otherwise falls back to a deterministic template generator.

API:
    LLMClient.generate_explanation(structured_input: dict, provider="hf") -> str
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Attempt optional imports lazily to allow repository to be used without heavy deps.
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False


class LLMClient:
    """
    Simple multi-provider LLM client.
    provider: "hf" (HuggingFace local), "template" (fallback)
    """

    _hf_generator = None
    _hf_model_name = os.getenv("HF_LLM_MODEL", "distilgpt2")  # small by default

    @classmethod
    def _init_hf(cls):
        if not HF_AVAILABLE:
            raise RuntimeError("HuggingFace transformers not available")
        if cls._hf_generator is None:
            # create text-generation pipeline
            try:
                # smaller models are quicker; change HF_LLM_MODEL env to a larger model if available
                generator = pipeline(
                    "text-generation", model=cls._hf_model_name, max_length=128
                )
            except Exception as e:
                logger.warning("HF model init error: %s", e)
                raise
            cls._hf_generator = generator
        return cls._hf_generator

    @staticmethod
    def _template_explanation(inp: Dict) -> str:
        # Deterministic human-readable explanation without calling an LLM
        resource = inp.get(
            "selected_resource",
            inp.get("selected_resource_name") or inp.get("name") or "Selected resource",
        )
        work_type = inp.get("work_type", "task")
        priority = inp.get("priority", 1)
        skill = inp.get("skill_level", "N/A")
        cases = inp.get("cases_handled", inp.get("total_cases_handled", "N/A"))
        workload = inp.get("workload", inp.get("current_workload", "N/A"))
        availability = inp.get("availability", "available")

        urgency = "urgent" if int(priority) >= 4 else "routine"
        explanation = (
            f"{resource} was assigned to this {urgency} {work_type} case due to appropriate "
            f"expertise (skill level {skill}), substantial experience ({cases} cases handled), "
            f"and immediate availability ({availability}) with current workload {workload}."
        )
        return explanation

    @classmethod
    def generate_explanation(
        cls, structured_input: Dict, provider: Optional[str] = "hf"
    ) -> str:
        """
        structured_input: dict with keys:
          work_type, priority, selected_resource (or selected_resource_name), skill_level, cases_handled, availability, workload
        provider: "hf" or "template"
        """
        # If provider explicitly set to "template", use deterministic template
        if provider == "template":
            return cls._template_explanation(structured_input)

        # Try HF provider if available
        if provider in (None, "hf"):
            try:
                generator = cls._init_hf()
                # Build prompt
                prompt = (
                    "You are a concise medical workflow assistant. Given the structured data, produce a 2-3 sentence "
                    "professional explanation of why this resource was chosen.\n\n"
                    f"Input: {structured_input}\n\nExplanation:"
                )
                # Generate text
                out = generator(
                    prompt,
                    do_sample=True,
                    top_k=50,
                    temperature=0.7,
                    num_return_sequences=1,
                )
                text = out[0]["generated_text"]
                # Post-process: remove input echo if present
                if "Explanation:" in text:
                    text = text.split("Explanation:", 1)[1].strip()
                # Keep only first 2 sentences
                sentences = text.strip().split(".")
                if len(sentences) > 2:
                    text = ". ".join(sentences[:2]).strip() + "."
                return text
            except Exception as e:
                logger.warning(
                    "HuggingFace generation failed: %s. Falling back to template.", e
                )
                return cls._template_explanation(structured_input)

        # Unknown provider fallback
        return cls._template_explanation(structured_input)
