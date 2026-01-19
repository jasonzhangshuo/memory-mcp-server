#!/usr/bin/env python3
"""Feishu event webhook server (receive group messages)."""

import argparse
import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load env
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
import sys
sys.path.insert(0, str(project_root))

from models import MemoryAddInput
from storage.db import init_db, add_memory
from sync.feishu_client import FeishuClient


VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")
IM_TABLE_ID = os.getenv("FEISHU_IM_TABLE_ID", "")
IM_DOC_TOKEN = os.getenv("FEISHU_IM_DOC_TOKEN", "")
SAVE_TO_MEMORY = os.getenv("FEISHU_IM_SAVE_TO_MEMORY", "true").lower() == "true"

DEDUP_PATH = project_root / "storage" / "feishu_event_ids.json"
DEDUP_MAX = 1000


def _load_dedup_ids() -> set:
    if not DEDUP_PATH.exists():
        return set()
    try:
        data = json.loads(DEDUP_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(data)
    except Exception:
        pass
    return set()


def _save_dedup_ids(ids: set) -> None:
    ids_list = list(ids)[-DEDUP_MAX:]
    DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEDUP_PATH.write_text(json.dumps(ids_list, ensure_ascii=False, indent=2), encoding="utf-8")


DEDUP_IDS = _load_dedup_ids()


def _parse_text_message(message: Dict[str, Any]) -> str:
    content = message.get("content", "")
    message_type = message.get("message_type", "")
    if message_type == "text":
        try:
            return json.loads(content).get("text", "")
        except Exception:
            return content or ""
    return f"[{message_type}] {content}"


async def _store_event(event_payload: Dict[str, Any]) -> None:
    await init_db()

    event = event_payload.get("event", {})
    header = event_payload.get("header", {})
    message = event.get("message", {})
    sender = event.get("sender", {}).get("sender_id", {})

    event_id = header.get("event_id") or message.get("message_id")
    if event_id in DEDUP_IDS:
        return
    DEDUP_IDS.add(event_id)
    _save_dedup_ids(DEDUP_IDS)

    text = _parse_text_message(message).strip()
    if not text:
        text = "[empty]"

    create_time_ms = message.get("create_time")
    try:
        created_at = datetime.fromtimestamp(int(create_time_ms) / 1000.0).isoformat()
    except Exception:
        created_at = datetime.now().isoformat()

    content = {
        "text": text,
        "chat_id": message.get("chat_id"),
        "chat_type": message.get("chat_type"),
        "message_id": message.get("message_id"),
        "sender_open_id": sender.get("open_id"),
        "sender_union_id": sender.get("union_id"),
        "created_at": created_at,
        "raw": message,
    }

    # 1) Save to memory (local DB)
    if SAVE_TO_MEMORY:
        title = text[:50] + ("..." if len(text) > 50 else "")
        await add_memory(
            memory_id=str(header.get("event_id") or message.get("message_id") or os.urandom(8).hex()),
            category="conversation",
            title=title or "Feishu message",
            content=json.dumps(content, ensure_ascii=False, indent=2),
            project="feishu-inbox",
            importance=3,
            source_type="feishu_im",
            tags=["feishu", "im", message.get("chat_type", "unknown")],
        )

    # 2) Optional: write to separate Feishu table
    if IM_TABLE_ID:
        client = FeishuClient()
        fields = {
            "标题": title or "Feishu message",
            "内容": text,
            "记忆ID": message.get("message_id") or header.get("event_id"),
            "项目": "feishu-inbox",
            "标签": ["feishu", "im", message.get("chat_type", "unknown")],
        }
        try:
            await client.create_record(fields=fields, table_id=IM_TABLE_ID)
        except Exception:
            pass

    # 3) Optional: append to Feishu document
    if IM_DOC_TOKEN:
        client = FeishuClient()
        line = f"- {created_at} | {sender.get('open_id','')} | {text}\n"
        try:
            await client.append_document_content(IM_DOC_TOKEN, line)
        except Exception:
            pass


class FeishuWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send_json({"error": "invalid_json"}, status=400)
            return

        # URL verification
        if data.get("type") == "url_verification" and data.get("challenge"):
            self._send_json({"challenge": data.get("challenge")})
            return

        # Encrypted payload (not supported unless ENCRYPT_KEY is configured)
        if "encrypt" in data:
            if not ENCRYPT_KEY:
                self._send_json({"error": "encrypt_key_missing"}, status=400)
                return
            # Placeholder: encryption not implemented in this script
            self._send_json({"error": "encrypt_not_supported"}, status=400)
            return

        # Token validation
        token = data.get("token") or data.get("header", {}).get("token")
        if VERIFICATION_TOKEN and token != VERIFICATION_TOKEN:
            self._send_json({"error": "token_invalid"}, status=401)
            return

        # Event type check
        event_type = data.get("header", {}).get("event_type") or data.get("event", {}).get("type")
        if event_type != "im.message.receive_v1":
            self._send_json({"ok": True})
            return

        # Return immediately; process in background
        self._send_json({"ok": True})
        threading.Thread(target=lambda: asyncio.run(_store_event(data)), daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Feishu event webhook server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), FeishuWebhookHandler)
    print(f"Feishu webhook listening on http://{args.host}:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
