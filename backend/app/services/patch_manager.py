"""Manages backups and transactional updates for codebase patches."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict
from app.services.repair_engine import RepairPatch

logger = logging.getLogger(__name__)

class PatchManager:
    """Manages transactional application of patches, backing up original contents."""

    def __init__(self, workspace_path: str | Path) -> None:
        self.workspace_path = Path(workspace_path)
        self._backups: Dict[str, str] = {}

    def backup(self, patch: RepairPatch) -> bool:
        """Backs up the target file of a patch in memory before it is written to."""
        target_file = self.workspace_path / patch.file_path
        if not target_file.exists():
            # If the file is new/doesn't exist, we track that it needs to be deleted on rollback
            self._backups[patch.file_path] = ""
            return True

        try:
            content = target_file.read_text(encoding="utf-8")
            self._backups[patch.file_path] = content
            logger.info(f"[PatchManager] Backed up {patch.file_path} (length: {len(content)})")
            return True
        except Exception as exc:
            logger.error(f"[PatchManager] Failed to back up {patch.file_path}: {exc}")
            return False

    def get_backups(self) -> Dict[str, str]:
        """Returns the current backup map."""
        return self._backups

    def clear(self) -> None:
        """Clears the backup map after a successful commit."""
        self._backups.clear()
