"""Handles reverting workspace files and discarding failed patch attempts."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class RollbackManager:
    """Manages restoring workspace files to original state using memory backups and git fallback."""

    def __init__(self, workspace_path: str | Path) -> None:
        self.workspace_path = Path(workspace_path)

    def rollback(self, backups: Dict[str, str]) -> bool:
        """Restores modified files from backup strings and falls back to git cleanups."""
        success = True

        # Step 1: Restore files from memory backup dictionary
        for rel_path, original_content in backups.items():
            target_file = self.workspace_path / rel_path
            try:
                if original_content == "":
                    # The file was created by the patch, so we remove it during rollback
                    if target_file.exists():
                        target_file.unlink()
                        logger.info(f"[RollbackManager] Removed newly created patch file: {rel_path}")
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(original_content, encoding="utf-8")
                    logger.info(f"[RollbackManager] Restored original content for: {rel_path}")
            except Exception as exc:
                logger.error(f"[RollbackManager] Failed to restore file {rel_path}: {exc}")
                success = False

        # Step 2: Fall back to Git discard utilities if .git directory exists
        git_dir = self.workspace_path / ".git"
        if git_dir.exists():
            try:
                logger.info("[RollbackManager] Invoking git checkout to clean remaining unstaged changes")
                subprocess.run(
                    ["git", "checkout", "--", "."],
                    cwd=self.workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                subprocess.run(
                    ["git", "clean", "-fd"],
                    cwd=self.workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                logger.info("[RollbackManager] Git workspace reset and cleaned successfully")
            except Exception as exc:
                logger.error(f"[RollbackManager] Git checkout/clean failed: {exc}")
                success = False

        return success
