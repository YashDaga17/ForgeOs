"""Deterministic repair and patch application helpers."""

from __future__ import annotations

import asyncio
import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RepairPatch:
    file_path: str
    diff: str
    explanation: str
    confidence: float
    risk: str
    source: str = "deterministic"

    def as_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "diff": self.diff,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "risk": self.risk,
            "source": self.source,
        }


class RepairEngine:
    """Creates and applies safe patches for known MVP failure classes."""

    def plan_deterministic(self, workspace_path: str | Path, failures: list[dict[str, Any]]) -> list[RepairPatch]:
        root = Path(workspace_path)
        patches: list[RepairPatch] = []
        for failure in failures:
            text = f"{failure.get('test', '')} {failure.get('error', '')}".lower()
            if "not_found" in text or "404" in text:
                patch = self._plan_404_patch(root)
                if patch:
                    patches.append(patch)
        return patches

    async def apply(self, workspace_path: str | Path, patch: RepairPatch) -> bool:
        root = Path(workspace_path)
        file_path = root / patch.file_path
        if patch.source in {"deterministic", "demo_ai_fallback"}:
            return await asyncio.to_thread(self._apply_known_patch, file_path, patch)
        return await self._apply_unified_diff(root, patch.diff)

    def demo_user_validation_patch(self, workspace_path: str | Path) -> RepairPatch | None:
        root = Path(workspace_path)
        target = root / "app" / "models.py"
        if not target.exists():
            return None
        original = target.read_text(encoding="utf-8")
        if "def is_valid" in original:
            return None
        updated = original.rstrip() + (
            "\n\n"
            "def _user_is_valid(self: User) -> bool:\n"
            "    if not self.name.strip():\n"
            "        return False\n"
            "    if \"@\" not in self.email:\n"
            "        return False\n"
            "    local, _, domain = self.email.partition(\"@\")\n"
            "    return bool(local and \".\" in domain)\n\n"
            "User.is_valid = _user_is_valid\n"
        )
        return RepairPatch(
            file_path="app/models.py",
            diff=unified_diff("app/models.py", original, updated),
            explanation="Added a User.is_valid method for model validation.",
            confidence=0.76,
            risk="medium",
            source="demo_ai_fallback",
        )

    def _plan_404_patch(self, root: Path) -> RepairPatch | None:
        target = root / "app" / "main.py"
        if not target.exists():
            return None
        original = target.read_text(encoding="utf-8")
        if "HTTPException" in original and "status_code=404" in original:
            return None
        updated = original
        if "from fastapi import FastAPI" in updated:
            updated = updated.replace("from fastapi import FastAPI", "from fastapi import FastAPI, HTTPException")
        updated = updated.replace(
            "    item = get_item(item_id)\n    return item",
            "    item = get_item(item_id)\n    if item is None:\n        raise HTTPException(status_code=404, detail=\"Item not found\")\n    return item",
        )
        if updated == original:
            return None
        return RepairPatch(
            file_path="app/main.py",
            diff=unified_diff("app/main.py", original, updated),
            explanation="Added explicit 404 handling for missing item lookups.",
            confidence=0.97,
            risk="low",
        )

    def _apply_known_patch(self, file_path: Path, patch: RepairPatch) -> bool:
        if not file_path.exists():
            return False
        original = file_path.read_text(encoding="utf-8")
        if patch.file_path == "app/main.py":
            updated = original
            if "from fastapi import FastAPI" in updated and "HTTPException" not in updated:
                updated = updated.replace("from fastapi import FastAPI", "from fastapi import FastAPI, HTTPException")
            updated = updated.replace(
                "    item = get_item(item_id)\n    return item",
                "    item = get_item(item_id)\n    if item is None:\n        raise HTTPException(status_code=404, detail=\"Item not found\")\n    return item",
            )
        elif patch.file_path == "app/models.py" and "def is_valid" not in original:
            updated = original.rstrip() + (
                "\n\n"
                "def _user_is_valid(self: User) -> bool:\n"
                "    if not self.name.strip():\n"
                "        return False\n"
                "    if \"@\" not in self.email:\n"
                "        return False\n"
                "    local, _, domain = self.email.partition(\"@\")\n"
                "    return bool(local and \".\" in domain)\n\n"
                "User.is_valid = _user_is_valid\n"
            )
        else:
            updated = original
        if updated == original:
            return False
        file_path.write_text(updated, encoding="utf-8")
        return True

    async def _apply_unified_diff(self, root: Path, diff: str) -> bool:
        process = await asyncio.create_subprocess_exec(
            "git",
            "apply",
            "--whitespace=nowarn",
            cwd=root,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, _ = await process.communicate(diff.encode())
        return process.returncode == 0


def unified_diff(file_path: str, original: str, updated: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )

