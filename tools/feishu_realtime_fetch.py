"""Fetch recent realtime Feishu inbox events."""

import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import FeishuRealtimeFetchInput


def _get_queue_path() -> Path:
    env_path = os.getenv("FEISHU_REALTIME_QUEUE_PATH", "").strip()
    if env_path:
        return Path(env_path)
    return project_root / "storage" / "feishu_realtime_queue.jsonl"


async def feishu_realtime_fetch(params: FeishuRealtimeFetchInput) -> str:
    """Fetch recent realtime Feishu messages from local queue."""
    queue_path = _get_queue_path()
    limit = max(1, min(params.limit or 5, 100))
    if not queue_path.exists():
        return json.dumps({
            "status": "success",
            "count": 0,
            "items": [],
            "message": "queue file not found"
        }, ensure_ascii=False, indent=2)

    items = []
    try:
        with queue_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    continue
    except Exception as exc:
        return json.dumps({
            "status": "error",
            "message": f"failed to read queue: {exc}"
        }, ensure_ascii=False, indent=2)

    recent = items[-limit:]
    return json.dumps({
        "status": "success",
        "count": len(recent),
        "items": recent
    }, ensure_ascii=False, indent=2)
