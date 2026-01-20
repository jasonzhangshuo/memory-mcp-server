#!/usr/bin/env python3
"""Feishu event webhook server (receive group messages)."""

import argparse
import asyncio
import json
import os
import threading
# import queue  # [SSE-REALTIME] Future feature
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

# Load env
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
import sys
sys.path.insert(0, str(project_root))


VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")
IM_TABLE_ID = os.getenv("FEISHU_IM_TABLE_ID", "")
IM_DOC_TOKEN = os.getenv("FEISHU_IM_DOC_TOKEN", "")
SAVE_TO_MEMORY = os.getenv("FEISHU_IM_SAVE_TO_MEMORY", "true").lower() == "true"
READ_API_TOKEN = os.getenv("FEISHU_WEBHOOK_READ_TOKEN", "")
PUSH_API_TOKEN = os.getenv("FEISHU_WEBHOOK_PUSH_TOKEN", "")

DEDUP_PATH = project_root / "storage" / "feishu_event_ids.json"
DEDUP_MAX = 1000
TEMP_INBOX_PATH = project_root / "storage" / "feishu_temp_inbox.jsonl"

# [SSE-REALTIME] Future feature - currently commented out
# SUBSCRIBERS_LOCK = threading.Lock()
# SUBSCRIBERS: set = set()


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


def _load_temp_inbox(limit: int = 20, include_archived: bool = False) -> list:
    """Load messages from temp inbox JSONL file."""
    if not TEMP_INBOX_PATH.exists():
        return []
    
    safe_limit = max(1, min(limit, 100))
    entries = []
    
    try:
        with open(TEMP_INBOX_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if not include_archived and entry.get("archived"):
                        continue
                    entries.append(entry)
                except Exception:
                    continue
        
        # Sort by created_at desc
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return entries[:safe_limit]
    except Exception:
        return []


def _mark_message_archived(message_id: str) -> bool:
    """Mark a message as archived in temp inbox."""
    if not TEMP_INBOX_PATH.exists():
        return False
    
    try:
        lines = []
        updated = False
        with open(TEMP_INBOX_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("message_id") == message_id:
                    entry["archived"] = True
                    updated = True
                lines.append(json.dumps(entry, ensure_ascii=False))
        
        if updated:
            with open(TEMP_INBOX_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        
        return updated
    except Exception:
        return False


# [SSE-REALTIME] Future feature - currently commented out
# def _broadcast_event(payload: Dict[str, Any]) -> None:
#     with SUBSCRIBERS_LOCK:
#         subscribers = list(SUBSCRIBERS)
#     print(f"[DEBUG] _broadcast_event called: {len(subscribers)} subscribers, text={payload.get('text', '')[:50]}")
#     if not subscribers:
#         return
#     for subscriber in subscribers:
#         try:
#             subscriber.put_nowait(payload)
#             print(f"[DEBUG] Sent to subscriber")
#         except Exception as e:
#             print(f"[DEBUG] Failed to send: {e}")
#             continue


async def _store_event(event_payload: Dict[str, Any]) -> None:
    """Store Feishu event to temp inbox (not memory)."""
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

    # Write to temp inbox (JSONL format)
    entry = {
        "message_id": message.get("message_id"),
        "chat_id": message.get("chat_id"),
        "chat_type": message.get("chat_type"),
        "sender_open_id": sender.get("open_id"),
        "sender_union_id": sender.get("union_id"),
        "created_at": created_at,
        "text": text,
        "archived": False,
        "received_at": datetime.now().isoformat(),
    }
    
    TEMP_INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TEMP_INBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # [SSE-REALTIME] Future feature - currently commented out
    # _broadcast_event({
    #     "message_id": message.get("message_id"),
    #     "chat_id": message.get("chat_id"),
    #     "chat_type": message.get("chat_type"),
    #     "sender_open_id": sender.get("open_id"),
    #     "created_at": created_at,
    #     "text": text,
    # })


class FeishuWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_bearer_token(self) -> str:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        return ""

    def _is_authorized(self) -> bool:
        if not READ_API_TOKEN:
            return True
        token = self._get_bearer_token()
        if token:
            return token == READ_API_TOKEN
        parsed = urlparse(self.path)
        token_param = parse_qs(parsed.query).get("token", [""])[0]
        return token_param == READ_API_TOKEN

    def _is_stream_authorized(self) -> bool:
        token = PUSH_API_TOKEN or READ_API_TOKEN
        if not token:
            return True
        auth = self._get_bearer_token()
        if auth:
            return auth == token
        parsed = urlparse(self.path)
        token_param = parse_qs(parsed.query).get("token", [""])[0]
        return token_param == token

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        
        # Health check
        if parsed.path == "/health":
            self._send_json({"ok": True})
            return
        
        # [SSE-REALTIME] Future feature - currently commented out
        # if parsed.path in ("/stream", "/feishu/stream"):
        #     if not self._is_stream_authorized():
        #         self._send_json({"error": "unauthorized"}, status=401)
        #         return
        #     self.send_response(200)
        #     self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        #     self.send_header("Cache-Control", "no-cache")
        #     self.send_header("Connection", "keep-alive")
        #     self.end_headers()
        #     subscriber = queue.Queue(maxsize=100)
        #     with SUBSCRIBERS_LOCK:
        #         SUBSCRIBERS.add(subscriber)
        #     print(f"[DEBUG] New SSE subscriber registered. Total subscribers: {len(SUBSCRIBERS)}")
        #     try:
        #         self.wfile.write(b": ok\n\n")
        #         self.wfile.flush()
        #         while True:
        #             try:
        #                 payload = subscriber.get(timeout=15)
        #                 data = json.dumps(payload, ensure_ascii=False)
        #                 self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
        #                 self.wfile.flush()
        #             except queue.Empty:
        #                 self.wfile.write(b": keep-alive\n\n")
        #                 self.wfile.flush()
        #     except (BrokenPipeError, ConnectionResetError):
        #         pass
        #     finally:
        #         with SUBSCRIBERS_LOCK:
        #             SUBSCRIBERS.discard(subscriber)
        #     return
        
        # Temp inbox endpoint (NEW)
        if parsed.path in ("/temp_inbox", "/feishu/temp_inbox"):
            if not self._is_authorized():
                self._send_json({"error": "unauthorized"}, status=401)
                return
            params = parse_qs(parsed.query)
            try:
                limit = int(params.get("limit", ["20"])[0])
                include_archived = params.get("include_archived", ["false"])[0].lower() == "true"
            except Exception:
                limit = 20
                include_archived = False
            entries = _load_temp_inbox(limit=limit, include_archived=include_archived)
            self._send_json({"ok": True, "count": len(entries), "items": entries})
            return
        
        self._send_json({"error": "not_found"}, status=404)

    def do_PATCH(self) -> None:
        """Handle PATCH requests for archiving messages."""
        parsed = urlparse(self.path)
        
        # PATCH /feishu/temp_inbox/:message_id
        if parsed.path.startswith("/feishu/temp_inbox/") or parsed.path.startswith("/temp_inbox/"):
            if not self._is_authorized():
                self._send_json({"error": "unauthorized"}, status=401)
                return
            
            # Extract message_id from path
            parts = parsed.path.split("/")
            message_id = parts[-1] if len(parts) > 0 else None
            
            if not message_id:
                self._send_json({"error": "message_id_required"}, status=400)
                return
            
            # Read request body
            length = int(self.headers.get("Content-Length", "0"))
            if length > 0:
                raw = self.rfile.read(length)
                try:
                    data = json.loads(raw.decode("utf-8") or "{}")
                except Exception:
                    self._send_json({"error": "invalid_json"}, status=400)
                    return
            else:
                data = {}
            
            # Mark as archived
            if data.get("archived") is True:
                success = _mark_message_archived(message_id)
                if success:
                    self._send_json({"ok": True, "message": "marked_as_archived"})
                else:
                    self._send_json({"error": "message_not_found"}, status=404)
                return
        
        self._send_json({"error": "not_found"}, status=404)

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
