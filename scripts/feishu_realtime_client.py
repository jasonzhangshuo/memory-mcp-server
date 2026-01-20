#!/usr/bin/env python3
"""Realtime Feishu inbox client (SSE)."""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def _default_output_path() -> Path:
    project_root = Path(__file__).parent.parent
    return project_root / "storage" / "feishu_realtime_queue.jsonl"


def _write_event(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with output_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _notify_mac(title: str, body: str) -> None:
    if sys.platform != "darwin":
        return
    safe_title = title.replace('"', '\\"')
    safe_body = body.replace('"', '\\"')
    os.system(
        f'osascript -e \'display notification "{safe_body}" with title "{safe_title}"\''
    )


def _parse_sse_stream(response, output_path: Path, notify: bool) -> None:
    buffer_lines = []
    for raw in response:
        try:
            line = raw.decode("utf-8").strip()
        except Exception:
            continue
        if not line:
            if buffer_lines:
                data = "\n".join(buffer_lines)
                buffer_lines = []
                try:
                    payload = json.loads(data)
                except Exception:
                    continue
                payload.setdefault("received_at", datetime.now().isoformat())
                _write_event(output_path, payload)
                if notify:
                    _notify_mac("Feishu message", payload.get("text", "")[:200])
            continue
        if line.startswith("data:"):
            buffer_lines.append(line[len("data:"):].strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Feishu realtime SSE client.")
    parser.add_argument("--url", default=os.getenv("FEISHU_REALTIME_STREAM_URL", "").strip())
    parser.add_argument("--token", default=os.getenv("FEISHU_WEBHOOK_PUSH_TOKEN", "").strip())
    parser.add_argument("--output", default=os.getenv("FEISHU_REALTIME_QUEUE_PATH", "").strip())
    parser.add_argument("--notify", action="store_true", help="Enable macOS notifications")
    args = parser.parse_args()

    if not args.url:
        print("Missing --url or FEISHU_REALTIME_STREAM_URL", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else _default_output_path()
    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    backoff = 2
    while True:
        try:
            request = Request(args.url, headers=headers)
            with urlopen(request, timeout=60) as response:
                backoff = 2
                _parse_sse_stream(response, output_path, args.notify)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"[realtime] connect failed: {exc}", file=sys.stderr)
        time.sleep(min(backoff, 30))
        backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    main()
