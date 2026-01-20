#!/usr/bin/env python3
"""Feishu poller: periodically check temp inbox and send notifications."""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

# Load env
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
import sys
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


TEMP_INBOX_PATH = project_root / "storage" / "feishu_temp_inbox.jsonl"
NOTIFICATION_CHAT_ID = os.getenv("FEISHU_NOTIFICATION_CHAT_ID", "")
POLLER_INTERVAL = int(os.getenv("FEISHU_POLLER_INTERVAL", "300"))  # Default 5 minutes
LAST_NOTIFIED_PATH = project_root / "storage" / "feishu_poller_state.json"


def _load_unarchived_messages() -> List[Dict[str, Any]]:
    """Load unarchived messages from temp inbox."""
    if not TEMP_INBOX_PATH.exists():
        return []
    
    messages = []
    try:
        with open(TEMP_INBOX_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if not entry.get("archived", False):
                        messages.append(entry)
                except Exception:
                    continue
        return messages
    except Exception:
        return []


def _load_last_notified_count() -> int:
    """Load last notified message count."""
    if not LAST_NOTIFIED_PATH.exists():
        return 0
    try:
        data = json.loads(LAST_NOTIFIED_PATH.read_text(encoding="utf-8"))
        return data.get("count", 0)
    except Exception:
        return 0


def _save_last_notified_count(count: int) -> None:
    """Save last notified message count."""
    LAST_NOTIFIED_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "count": count,
        "timestamp": datetime.now().isoformat()
    }
    LAST_NOTIFIED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def _send_notification(count: int) -> bool:
    """Send Feishu notification about new messages."""
    if not NOTIFICATION_CHAT_ID:
        print(f"⚠️  FEISHU_NOTIFICATION_CHAT_ID 未配置，跳过通知")
        return False
    
    try:
        client = FeishuClient()
        text = f"📬 您有 {count} 条新的飞书消息待处理\n\n💡 在 Claude 中使用 feishu_fetch_inbox 查看详情"
        
        content = {"text": text}
        
        await client.send_message(
            receive_id_type="chat_id",
            receive_id=NOTIFICATION_CHAT_ID,
            msg_type="text",
            content=content,
            use_user_token=False
        )
        
        print(f"✅ 已发送通知：{count} 条新消息")
        return True
    
    except Exception as e:
        print(f"❌ 发送通知失败: {e}")
        return False


async def _poll_once() -> None:
    """Poll temp inbox once and send notification if needed."""
    messages = _load_unarchived_messages()
    current_count = len(messages)
    last_count = _load_last_notified_count()
    
    print(f"[{datetime.now().isoformat()}] 未归档消息: {current_count} 条（上次通知: {last_count} 条）")
    
    # Only notify if count increased
    if current_count > last_count and current_count > 0:
        success = await _send_notification(current_count)
        if success:
            _save_last_notified_count(current_count)
    elif current_count == 0:
        # Reset counter when inbox is empty
        if last_count > 0:
            _save_last_notified_count(0)


async def _poll_loop(interval: int) -> None:
    """Main polling loop."""
    print(f"🚀 Feishu poller started (interval: {interval}s)")
    print(f"   Temp inbox: {TEMP_INBOX_PATH}")
    print(f"   Notification chat: {NOTIFICATION_CHAT_ID or '(未配置)'}")
    
    while True:
        try:
            await _poll_once()
        except Exception as e:
            print(f"❌ 轮询出错: {e}")
        
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Feishu message poller.")
    parser.add_argument("--interval", type=int, default=POLLER_INTERVAL, help="轮询间隔（秒），默认 300")
    args = parser.parse_args()
    
    asyncio.run(_poll_loop(args.interval))


if __name__ == "__main__":
    main()
