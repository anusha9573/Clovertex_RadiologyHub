"""Shared LLM client with HuggingFace + template providers."""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline

    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False


class LLMClient:
    _hf_generator = None
    _hf_model_name = os.getenv("HF_LLM_MODEL", "distilgpt2")

    @classmethod
    def _init_hf(cls):
        if not HF_AVAILABLE:
            raise RuntimeError("HuggingFace transformers not available")
        if cls._hf_generator is None:
            cls._hf_generator = pipeline(
                "text-generation", model=cls._hf_model_name, max_length=160
            )
        return cls._hf_generator

    @staticmethod
    def _template_explanation(payload: Dict) -> str:
        resource = payload.get(
            "selected_resource",
            payload.get("selected_resource_name")
            or payload.get("name")
            or "Selected resource",
        )
        work_type = payload.get("work_type", "case")
        priority = int(payload.get("priority", 1))
        skill = payload.get("skill_level", "N/A")
        cases = payload.get("cases_handled", payload.get("total_cases_handled", "N/A"))
        workload = payload.get("workload", payload.get("current_workload", "N/A"))
        availability = payload.get("availability", "available")

        urgency = "urgent" if priority >= 4 else "routine"
        return (
            f"{resource} was assigned to this {urgency} {work_type} request because of "
            f"their skill level {skill}, experience across {cases} similar studies, "
            f"and availability window {availability} with workload {workload}."
        )

    @classmethod
    def generate_explanation(
        cls, structured_input: Dict, provider: Optional[str] = "hf"
    ) -> str:
        if provider == "template":
            return cls._template_explanation(structured_input)

        if provider in (None, "hf"):
            try:
                generator = cls._init_hf()
                prompt = (
                    "You are a concise medical workflow allocator. Given the structured data, "
                    "produce a professional 2-3 sentence explanation for the assignment.\n"
                    f"Input: {structured_input}\nExplanation:"
                )
                output = generator(
                    prompt,
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    num_return_sequences=1,
                )
                text = output[0]["generated_text"]
                if "Explanation:" in text:
                    text = text.split("Explanation:", 1)[1].strip()
                sentences = [s.strip() for s in text.split(".") if s.strip()]
                if len(sentences) > 2:
                    text = ". ".join(sentences[:2]) + "."
                return text
            except Exception as exc:
                logger.warning("HF generation failed (%s); falling back to template.", exc)

        return cls._template_explanation(structured_input)

