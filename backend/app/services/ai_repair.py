"""
OpenAI-backed AI repair service with an explicit credential gate.

The service never pretends a model was called. If `OPENAI_API_KEY` is absent,
callers receive a blocked result and can choose a deterministic fallback.
"""

from __future__ import annotations

import ast
import json
from pathlib import PurePosixPath
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings, get_settings
from app.services.repair_engine import unified_diff


RepairRisk = Literal["low", "medium", "high"]
RepairStatus = Literal["completed", "blocked", "failed"]


class AIRepairPatch(BaseModel):
    """Structured patch returned by the AI repair model."""

    file_path: str
    explanation: str
    unified_diff: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk: RepairRisk


class AIRepairProposal(BaseModel):
    """Model response before ForgeOS deterministically constructs the patch diff."""

    file_path: str
    explanation: str
    updated_content: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    risk: RepairRisk


class AIRepairResult(BaseModel):
    """AI repair outcome with truthful gate status."""

    status: RepairStatus
    message: str
    model: str
    patch: AIRepairPatch | None = None
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class AIRegressionTest(BaseModel):
    """A new pytest file generated after a verified repair."""

    file_path: str
    content: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)


class AIRegressionResult(BaseModel):
    status: RepairStatus
    message: str
    model: str
    regression_test: AIRegressionTest | None = None
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class AIRepairService:
    """Builds repair prompts and calls OpenAI Responses API when configured."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    async def repair(
        self,
        *,
        repository_name: str,
        failures: list[dict[str, Any]],
        test_output: str,
        file_context: dict[str, str],
        test_context: dict[str, str] | None = None,
        _retry_attempt: bool = False,
    ) -> AIRepairResult:
        """Return one structured repair patch for the highest-value failure."""
        if not self.settings.openai_api_key:
            return AIRepairResult(
                status="blocked",
                model=self.settings.openai_repair_model,
                message="OPENAI_API_KEY is not configured. AI repair is gated until credentials are provided.",
            )

        try:
            client = self._client()
            response = await client.responses.create(
                model=self.settings.openai_repair_model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are ForgeOS Repair. Return the complete updated content for exactly one supplied Python file "
                            "that fixes the failing Python/FastAPI/pytest repository. "
                            "Prefer minimal changes and preserve unrelated code. The file_path must be one of the supplied files. "
                            "Repair only the failure objects provided; "
                            "ignore unrelated historical traceback text. The tests are read-only behavior evidence and must never be edited. "
                            "If a test invokes a missing method, implement that behavior rather than adding unrelated required fields. Do not include markdown."
                            + (
                                " This is a corrective retry: return syntactically valid Python source for the supplied target and preserve unrelated code."
                                if _retry_attempt
                                else ""
                            )
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "repository_name": repository_name,
                                "failures": failures,
                                "test_output": test_output[-6000:],
                                "files": file_context,
                                "tests": test_context or {},
                            },
                            indent=2,
                        ),
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "forgeos_ai_repair_content",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "file_path": {"type": "string"},
                                "explanation": {"type": "string"},
                                "updated_content": {"type": "string", "minLength": 1},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "risk": {"type": "string", "enum": ["low", "medium", "high"]},
                            },
                            "required": [
                                "file_path",
                                "explanation",
                                "updated_content",
                                "confidence",
                                "risk",
                            ],
                        },
                    }
                },
            )
            payload = json.loads(self._extract_output_text(response))
            proposal = AIRepairProposal.model_validate(payload)
            proposal = resolve_repair_target(proposal, file_context)
            input_tokens, output_tokens = _usage_tokens(response)
            safety_reason = repair_content_safety_reason(proposal, file_context)
            if safety_reason:
                if not _retry_attempt:
                    return await self.repair(
                        repository_name=repository_name,
                        failures=failures,
                        test_output=test_output,
                        file_context=file_context,
                        test_context=test_context,
                        _retry_attempt=True,
                    )
                return AIRepairResult(
                    status="failed",
                    model=self.settings.openai_repair_model,
                    message=f"AI repair content was rejected by the workspace safety gate: {safety_reason}.",
                    request_id=_response_id(response),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            patch = AIRepairPatch(
                file_path=proposal.file_path,
                explanation=proposal.explanation,
                unified_diff=unified_diff(
                    proposal.file_path,
                    file_context[proposal.file_path],
                    proposal.updated_content,
                ),
                confidence=proposal.confidence,
                risk=proposal.risk,
            )
            if not is_safe_repair_patch(patch, file_context):
                return AIRepairResult(
                    status="failed",
                    model=self.settings.openai_repair_model,
                    message="AI repair patch was rejected by the workspace safety gate.",
                    request_id=_response_id(response),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            return AIRepairResult(
                status="completed",
                model=self.settings.openai_repair_model,
                message="AI repair returned a structured patch.",
                patch=patch,
                request_id=_response_id(response),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            return AIRepairResult(
                status="failed",
                model=self.settings.openai_repair_model,
                message=f"AI repair returned invalid structured output: {exc}",
            )
        except Exception as exc:
            return AIRepairResult(
                status="failed",
                model=self.settings.openai_repair_model,
                message=f"AI repair request failed: {exc}",
            )

    async def generate_regression_test(
        self,
        *,
        repository_name: str,
        failures: list[dict[str, Any]],
        file_context: dict[str, str],
        test_paths: list[str],
    ) -> AIRegressionResult:
        """Create one constrained pytest regression test for a verified repair."""
        if not self.settings.openai_api_key:
            return AIRegressionResult(
                status="blocked",
                model=self.settings.openai_repair_model,
                message="OPENAI_API_KEY is not configured. Regression-test generation is gated.",
            )
        if not failures or not test_paths:
            return AIRegressionResult(
                status="blocked",
                model=self.settings.openai_repair_model,
                message="No verified failure and pytest target are available for regression-test generation.",
            )

        try:
            response = await self._client().responses.create(
                model=self.settings.openai_repair_model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are ForgeOS Regression Proof. Return exactly one new, minimal pytest test file for a repair that already passed. "
                            "Use only the supplied repository context. Do not change production code, do not use network or subprocess calls, "
                            "and do not include markdown. The test must live under an existing pytest target."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "repository_name": repository_name,
                                "verified_failures": failures,
                                "pytest_targets": test_paths,
                                "files": file_context,
                            },
                            indent=2,
                        ),
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "forgeos_regression_test",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "file_path": {"type": "string"},
                                "content": {"type": "string"},
                                "explanation": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                            "required": ["file_path", "content", "explanation", "confidence"],
                        },
                    }
                },
            )
            regression_test = AIRegressionTest.model_validate(json.loads(self._extract_output_text(response)))
            if not is_safe_regression_test(regression_test, test_paths):
                return AIRegressionResult(
                    status="failed",
                    model=self.settings.openai_repair_model,
                    message="AI regression test was rejected by the workspace safety gate.",
                )
            input_tokens, output_tokens = _usage_tokens(response)
            return AIRegressionResult(
                status="completed",
                model=self.settings.openai_repair_model,
                message="AI generated a bounded regression test candidate.",
                regression_test=regression_test,
                request_id=_response_id(response),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            return AIRegressionResult(
                status="failed",
                model=self.settings.openai_repair_model,
                message=f"AI regression test returned invalid structured output: {exc}",
            )
        except Exception as exc:
            return AIRegressionResult(
                status="failed",
                model=self.settings.openai_repair_model,
                message=f"AI regression test request failed: {exc}",
            )

    def _client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.openai_timeout_seconds,
            max_retries=1,
        )

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        """Extract text from the SDK response without relying on one shape only."""
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


FORBIDDEN_TEST_TOKENS = ("subprocess", "os.system", "shutil.rmtree", "requests.", "httpx.")


def is_safe_repair_patch(patch: AIRepairPatch, file_context: dict[str, str]) -> bool:
    """Allow one relative Python patch only when its target was supplied to the model."""
    path = PurePosixPath(patch.file_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        return False
    normalized_path = path.as_posix()
    if normalized_path not in file_context:
        return False
    diff = patch.unified_diff.lstrip()
    return (
        bool(diff)
        and f"--- a/{normalized_path}" in diff
        and f"+++ b/{normalized_path}" in diff
        and "\x00" not in diff
    )


def is_safe_repair_content(proposal: AIRepairProposal, file_context: dict[str, str]) -> bool:
    """Constrain an AI replacement to a provided, syntactically valid Python file."""
    return repair_content_safety_reason(proposal, file_context) is None


def resolve_repair_target(
    proposal: AIRepairProposal,
    file_context: dict[str, str],
) -> AIRepairProposal:
    """Expand an unambiguous model basename to its supplied repository path."""
    path = PurePosixPath(proposal.file_path)
    if path.is_absolute() or ".." in path.parts or path.as_posix() in file_context:
        return proposal
    matches = [
        candidate
        for candidate in file_context
        if PurePosixPath(candidate).name == path.name
    ]
    return proposal.model_copy(update={"file_path": matches[0]}) if len(matches) == 1 else proposal


def repair_content_safety_reason(
    proposal: AIRepairProposal,
    file_context: dict[str, str],
) -> str | None:
    """Return a safe diagnostic for an AI replacement rejected before execution."""
    path = PurePosixPath(proposal.file_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        return "target path must be a relative Python source file"
    normalized_path = path.as_posix()
    original = file_context.get(normalized_path)
    if original is None or not proposal.updated_content.strip() or "\x00" in proposal.updated_content:
        return "target content is not in the supplied repair scope"
    if proposal.updated_content == original:
        return "candidate did not change the supplied source"
    minimum_size = max(24, int(len(original) * 0.5))
    maximum_size = max(len(original) * 3, len(original) + 1200)
    if not minimum_size <= len(proposal.updated_content) <= maximum_size:
        return "candidate size exceeds the bounded source-change limit"
    try:
        ast.parse(proposal.updated_content)
    except SyntaxError:
        return "candidate is not valid Python syntax"
    return None


def normalize_unified_diff_headers(patch: AIRepairPatch) -> AIRepairPatch:
    """Canonicalize no-prefix unified-diff headers before handing them to git apply."""
    path = PurePosixPath(patch.file_path).as_posix()
    normalized_lines: list[str] = []
    for line in patch.unified_diff.splitlines(keepends=True):
        ending = "\n" if line.endswith("\n") else ""
        body = line[:-1] if ending else line
        if body == f"--- {path}" or body.startswith(f"--- {path}\t"):
            normalized_lines.append(f"--- a/{path}{ending}")
        elif body == f"+++ {path}" or body.startswith(f"+++ {path}\t"):
            normalized_lines.append(f"+++ b/{path}{ending}")
        else:
            normalized_lines.append(line)
    return patch.model_copy(update={"unified_diff": "".join(normalized_lines)})


def is_safe_regression_test(regression_test: AIRegressionTest, test_paths: list[str]) -> bool:
    """Limit generated tests to new pytest files inside existing test targets."""
    path = PurePosixPath(regression_test.file_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        return False
    if not (path.name.startswith("test_") or path.name.endswith("_test.py")):
        return False
    allowed_directories = {
        (PurePosixPath(test_path) if PurePosixPath(test_path).suffix == "" else PurePosixPath(test_path).parent)
        for test_path in test_paths
    }
    if not any(path.is_relative_to(directory) for directory in allowed_directories):
        return False
    lowered = regression_test.content.lower()
    return bool(regression_test.content.strip()) and not any(token in lowered for token in FORBIDDEN_TEST_TOKENS)


def _usage_tokens(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    return (
        int(getattr(usage, "input_tokens", 0) or 0),
        int(getattr(usage, "output_tokens", 0) or 0),
    )


def _response_id(response: Any) -> str:
    return str(getattr(response, "_request_id", "") or getattr(response, "id", ""))
