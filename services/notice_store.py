"""Atomic, validated storage for per-server notice delivery state."""

from __future__ import annotations

import asyncio
import copy
import json
import os
from pathlib import Path
from typing import Any

from config.settings import MAX_SEEN_NOTICES, NOTICE_STATE_PATH


class NoticeStoreError(RuntimeError):
    """Raised when notice state cannot be read or safely written."""


class NoticeStore:
    def __init__(self, path: str | Path = NOTICE_STATE_PATH) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()

    async def snapshot(self) -> dict[str, dict[str, Any]]:
        async with self._lock:
            state = await asyncio.to_thread(self._read_sync)
            return copy.deepcopy(state["servers"])

    async def configure(self, server_id: int, channel_id: int) -> None:
        async with self._lock:
            state = await asyncio.to_thread(self._read_sync)
            server = state["servers"].setdefault(
                str(server_id), {"notice_channel_id": None, "seen_notices": []}
            )
            server["notice_channel_id"] = channel_id
            await asyncio.to_thread(self._write_sync, state)

    async def disable(self, server_id: int) -> bool:
        async with self._lock:
            state = await asyncio.to_thread(self._read_sync)
            server = state["servers"].get(str(server_id))
            if not server or server.get("notice_channel_id") is None:
                return False
            server["notice_channel_id"] = None
            await asyncio.to_thread(self._write_sync, state)
            return True

    async def mark_seen(self, server_id: int | str, links: list[str]) -> None:
        if not links:
            return
        async with self._lock:
            state = await asyncio.to_thread(self._read_sync)
            server = state["servers"].get(str(server_id))
            if not server:
                return
            existing = server["seen_notices"]
            merged = list(dict.fromkeys([*existing, *links]))[-MAX_SEEN_NOTICES:]
            if merged != existing:
                server["seen_notices"] = merged
                await asyncio.to_thread(self._write_sync, state)

    def _read_sync(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "servers": {}}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise NoticeStoreError("Notice state is unreadable; no changes were written.") from exc
        return self._validate(raw)

    def _validate(self, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict) or not isinstance(raw.get("servers"), dict):
            raise NoticeStoreError("Notice state has an invalid top-level structure.")
        validated: dict[str, Any] = {"version": 1, "servers": {}}
        for server_id, value in raw["servers"].items():
            if not isinstance(server_id, str) or not server_id.isdigit():
                raise NoticeStoreError("Notice state contains an invalid server key.")
            if not isinstance(value, dict):
                raise NoticeStoreError("Notice state contains an invalid server record.")
            channel_id = value.get("notice_channel_id")
            if channel_id is not None and (not isinstance(channel_id, int) or channel_id <= 0):
                raise NoticeStoreError("Notice state contains an invalid channel value.")
            links = value.get("seen_notices", [])
            if not isinstance(links, list) or not all(
                isinstance(link, str) and link.startswith("https://") for link in links
            ):
                raise NoticeStoreError("Notice state contains an invalid seen-notice list.")
            validated["servers"][server_id] = {
                "notice_channel_id": channel_id,
                "seen_notices": list(dict.fromkeys(links))[-MAX_SEEN_NOTICES:],
            }
        return validated

    def _write_sync(self, state: dict[str, Any]) -> None:
        validated = self._validate(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(validated, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise NoticeStoreError("Notice state could not be written atomically.") from exc


notice_store = NoticeStore()
