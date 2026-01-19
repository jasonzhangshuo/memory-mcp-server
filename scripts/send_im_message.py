#!/usr/bin/env python3
"""Send a Feishu IM message (text) via app token."""

import argparse
import asyncio
import os

from sync.feishu_client import FeishuClient


async def send_text(chat_id: str, text: str, use_user_token: bool) -> None:
    client = FeishuClient()
    await client.send_message(
        receive_id_type="chat_id",
        receive_id=chat_id,
        msg_type="text",
        content={"text": text},
        use_user_token=use_user_token,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Feishu IM text message.")
    parser.add_argument(
        "--chat-id",
        default=os.getenv("FEISHU_DEFAULT_CHAT_ID"),
        help="Target chat_id (or set FEISHU_DEFAULT_CHAT_ID).",
    )
    parser.add_argument("--text", required=True, help="Message text to send.")
    parser.add_argument(
        "--use-user-token",
        action="store_true",
        help="Use user token instead of app token.",
    )
    args = parser.parse_args()

    if not args.chat_id:
        raise SystemExit("Missing --chat-id (or set FEISHU_DEFAULT_CHAT_ID).")

    asyncio.run(send_text(args.chat_id, args.text, args.use_user_token))


if __name__ == "__main__":
    main()
