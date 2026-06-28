"""Manually insert lost scene chat messages into production.

Use when messages were trimmed from scene_state.chat_buffer before scene_messages
persistence existed, or when history must be restored from backups/screenshots.

Required fields per message (JSON object):
  - text (str): message body; required unless type is DICE_ROLL with roll fields
  - sender_id (str): user UUID of the author (campaign member)
  - type (str): SPEAK | ACTION | CONTEXT | MASTER | NARRATIVE | DICE_ROLL

Strongly recommended:
  - id (str): stable message id; generated if omitted (new uuid)
  - timestamp (str): ISO-8601 UTC, e.g. "2026-06-28T14:32:00Z"

Optional (match ChatMessage / live chat payloads):
  - read_by (list[str]): user ids who read the message; default []
  - visibility (str): "all" | "master_only"; default "all"
  - speaker_entity_id, speaker_display_name, speaker_type (MASTER|NPC|PC|NARRATOR)
  - image_url (str)
  - DICE_ROLL: dice_expression, rolls, raw_result, final_result, skill_checked,
    chat_summary, success, entity_id, entity_name, roll_type, roll_details

Per-message control:
  - append_to_buffer (bool): if true, also place in scene_state.chat_buffer for live UI
    (overrides --update-buffer when set)

Example messages file (save as lost_messages.json):

[
  {
    "id": "recovered-msg-1",
    "timestamp": "2026-06-28T14:30:00Z",
    "sender_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "type": "SPEAK",
    "text": "First lost message text here.",
    "speaker_entity_id": "11111111-2222-3333-4444-555555555555",
    "speaker_display_name": "Aldric",
    "speaker_type": "PC",
    "read_by": ["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"],
    "append_to_buffer": true
  },
  {
    "timestamp": "2026-06-28T14:31:15Z",
    "sender_id": "ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj",
    "type": "ACTION",
    "text": "Second lost message.",
    "append_to_buffer": true
  }
]

Dry-run is the default. Pass --apply to commit.

Production example (from repo root, with DATABASE_URL pointing at Neon):

  cd backend
  $env:DATABASE_URL="postgresql+asyncpg://USER:PASS@ep-xxx.neon.tech/neondb?sslmode=require"
  python scripts/insert_scene_messages.py SCENE-UUID-HERE --messages-file lost_messages.json
  python scripts/insert_scene_messages.py SCENE-UUID-HERE --messages-file lost_messages.json --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.campaign import Scene, SceneMessage
from app.schemas.scene import ChatMessage
from app.services.master import utc_now_iso
from app.services.scene_messages import _parse_message_timestamp, persist_scene_message
from app.services.scenes import load_scene_state, save_scene_state

SCRIPT_ONLY_KEYS = frozenset({"append_to_buffer"})


def _load_messages(*, messages_file: Path | None, messages_json: str | None) -> list[dict[str, Any]]:
    if messages_file is not None:
        raw = messages_file.read_text(encoding="utf-8")
    elif messages_json is not None:
        raw = messages_json
    else:
        raise SystemExit("Provide --messages-file or --messages-json")

    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("Messages payload must be a JSON array")
    if not data:
        raise SystemExit("Messages array is empty")
    return data


def _normalize_message(raw: dict[str, Any], *, index: int) -> tuple[dict[str, Any], bool, list[str]]:
    notes: list[str] = []
    entry = dict(raw)

    append_to_buffer = bool(entry.pop("append_to_buffer", False))
    for key in list(entry):
        if key in SCRIPT_ONLY_KEYS:
            entry.pop(key, None)

    if not entry.get("id"):
        entry["id"] = str(uuid.uuid4())
        notes.append(f"message[{index}]: generated id={entry['id']}")

    if not entry.get("timestamp"):
        entry["timestamp"] = utc_now_iso()
        notes.append(f"message[{index}]: missing timestamp; using now()")

    entry.setdefault("read_by", [])
    entry.setdefault("visibility", "all")

    return entry, append_to_buffer, notes


def _message_sort_key(message: ChatMessage) -> datetime:
    return _parse_message_timestamp(message.timestamp)


def _merge_chat_buffer(
    state,
    messages: list[ChatMessage],
) -> int:
    by_id: dict[str, ChatMessage] = {
        message.id: message for message in state.chat_buffer if message.id
    }
    added = 0
    for message in messages:
        if message.id not in by_id:
            added += 1
        by_id[message.id] = message

    combined = sorted(by_id.values(), key=_message_sort_key)
    max_size = state.memory_settings.max_chat_buffer_size
    state.chat_buffer = combined[-max_size:]
    return added


async def run(
    scene_id: uuid.UUID,
    raw_messages: list[dict[str, Any]],
    *,
    apply: bool,
    update_buffer: bool,
) -> int:
    prepared: list[tuple[ChatMessage, bool, list[str]]] = []
    for index, raw in enumerate(raw_messages):
        if not isinstance(raw, dict):
            raise SystemExit(f"message[{index}] must be a JSON object")
        entry, append_to_buffer, notes = _normalize_message(raw, index=index)
        try:
            message = ChatMessage.model_validate(entry)
        except ValidationError as exc:
            raise SystemExit(f"message[{index}] validation failed:\n{exc}") from exc
        if not message.id:
            raise SystemExit(f"message[{index}] id is required after normalization")
        prepared.append((message, append_to_buffer, notes))

    buffer_targets = [
        message
        for message, append_to_buffer, _ in prepared
        if append_to_buffer or update_buffer
    ]

    async with SessionLocal() as db:
        scene = await db.get(Scene, scene_id)
        if scene is None:
            raise SystemExit(f"Scene not found: {scene_id}")

        print(f"Scene: {scene.id} (campaign={scene.campaign_id}, #{scene.scene_number}, {scene.status})")
        print(f"Mode: {'APPLY' if apply else 'DRY RUN'}")
        print(f"Messages to insert/update: {len(prepared)}")
        if buffer_targets:
            print(f"Messages for chat_buffer merge: {len(buffer_targets)}")
        print()

        for message, append_to_buffer, notes in prepared:
            existing = await db.get(SceneMessage, message.id)
            action = "update" if existing is not None else "insert"
            print(f"  [{action}] id={message.id} type={message.type} ts={message.timestamp}")
            if message.text:
                preview = message.text.replace("\n", " ")
                if len(preview) > 80:
                    preview = preview[:77] + "..."
                print(f"           text={preview!r}")
            if append_to_buffer or update_buffer:
                print("           -> chat_buffer")
            for note in notes:
                print(f"           ! {note}")

        buffer_added = 0
        if buffer_targets:
            state = load_scene_state(scene)
            before = len(state.chat_buffer)
            buffer_added = _merge_chat_buffer(state, buffer_targets)
            after = len(state.chat_buffer)
            print()
            print(f"chat_buffer: {before} -> {after} entries ({buffer_added} newly merged)")
            save_scene_state(scene, state)

        for message, _, _ in prepared:
            await persist_scene_message(db, scene.id, message)

        if apply:
            await db.commit()
            print("\nCommitted.")
        else:
            await db.rollback()
            print("\nDry run complete (rolled back). Re-run with --apply to commit.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Insert recovered scene chat messages into scene_messages (and optionally chat_buffer)."
    )
    parser.add_argument("scene_id", help="Scene UUID")
    parser.add_argument(
        "--messages-file",
        type=Path,
        help="Path to JSON file containing an array of message objects",
    )
    parser.add_argument(
        "--messages-json",
        help="Inline JSON array of message objects",
    )
    parser.add_argument(
        "--update-buffer",
        action="store_true",
        help="Merge all messages into scene_state.chat_buffer (chronological, trimmed to max size)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes (default is dry-run rollback)",
    )
    args = parser.parse_args()

    try:
        scene_id = uuid.UUID(args.scene_id)
    except ValueError as exc:
        raise SystemExit(f"Invalid scene_id UUID: {args.scene_id}") from exc

    raw_messages = _load_messages(
        messages_file=args.messages_file,
        messages_json=args.messages_json,
    )
    raise SystemExit(
        asyncio.run(
            run(
                scene_id,
                raw_messages,
                apply=args.apply,
                update_buffer=args.update_buffer,
            )
        )
    )


if __name__ == "__main__":
    main()
