"""Bounded OpenAI enrichment for evidence-backed business intelligence."""

from __future__ import annotations

import json
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings, get_settings


InsightStatus = Literal["completed", "blocked", "failed"]


class BusinessBrief(BaseModel):
    """AI interpretation constrained to facts collected by ForgeOS."""

    executive_summary: str = Field(min_length=20, max_length=700)
    product_thesis: str = Field(min_length=8, max_length=320)
    engineering_risk: str = Field(min_length=8, max_length=320)
    next_move: str = Field(min_length=8, max_length=320)
    confidence: float = Field(ge=0.0, le=1.0)


class AIInsightResult(BaseModel):
    status: InsightStatus
    message: str
    model: str
    brief: BusinessBrief | None = None
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class AIInsightsService:
    """Produces concise product briefs from deterministic repository facts."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    async def summarize_business_intelligence(self, facts: dict[str, Any]) -> AIInsightResult:
        if not self.settings.openai_api_key:
            return AIInsightResult(
                status="blocked",
                model=self.settings.openai_bi_model,
                message="OPENAI_API_KEY is not configured. The deterministic business summary remains active.",
            )

        try:
            client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.openai_timeout_seconds,
                max_retries=1,
            )
            response = await client.responses.create(
                model=self.settings.openai_bi_model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are ForgeOS Business Intelligence. Interpret only the repository facts supplied. "
                            "Do not invent users, revenue, market share, security findings, test coverage, or unsupported metrics. "
                            "Make uncertainty explicit. Return concise decision-ready language, never markdown."
                        ),
                    },
                    {"role": "user", "content": json.dumps(facts, indent=2)},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "forgeos_business_brief",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "executive_summary": {"type": "string", "minLength": 20, "maxLength": 700},
                                "product_thesis": {"type": "string", "minLength": 8, "maxLength": 320},
                                "engineering_risk": {"type": "string", "minLength": 8, "maxLength": 320},
                                "next_move": {"type": "string", "minLength": 8, "maxLength": 320},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                            "required": [
                                "executive_summary",
                                "product_thesis",
                                "engineering_risk",
                                "next_move",
                                "confidence",
                            ],
                        },
                    }
                },
            )
            brief = BusinessBrief.model_validate(json.loads(_extract_output_text(response)))
            input_tokens, output_tokens = _usage_tokens(response)
            return AIInsightResult(
                status="completed",
                model=self.settings.openai_bi_model,
                message="OpenAI generated an evidence-constrained business brief.",
                brief=brief,
                request_id=str(getattr(response, "_request_id", "") or getattr(response, "id", "")),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            return AIInsightResult(
                status="failed",
                model=self.settings.openai_bi_model,
                message="AI business brief did not satisfy the structured response contract; the deterministic summary remains active.",
            )
        except Exception as exc:
            return AIInsightResult(
                status="failed",
                model=self.settings.openai_bi_model,
                message=f"AI business brief request failed: {exc}",
            )


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(str(text))
    if chunks:
        return "".join(chunks)
    raise ValueError("OpenAI response did not contain output text")


def _usage_tokens(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    return (
        int(getattr(usage, "input_tokens", 0) or 0),
        int(getattr(usage, "output_tokens", 0) or 0),
    )
