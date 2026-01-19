#!/usr/bin/env python3
"""自动同步服务 - 定时同步记忆数据到飞书"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sync.sync_to_feishu import sync_all_memories
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取同步间隔（秒）
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "3600"))  # 默认1小时


async def sync_loop():
    """同步循环"""
    print("=" * 60)
    print("🔄 自动同步服务启动")
    print("=" * 60)
    print(f"同步间隔: {SYNC_INTERVAL} 秒 ({SYNC_INTERVAL // 60} 分钟)")
    print(f"按 Ctrl+C 停止")
    print()
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始同步...")
            await sync_all_memories(dry_run=False)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 同步完成，等待 {SYNC_INTERVAL} 秒...")
            print()
            
            # 等待指定时间
            await asyncio.sleep(SYNC_INTERVAL)
            
        except KeyboardInterrupt:
            print()
            print("=" * 60)
            print("⏹️  同步服务已停止")
            print("=" * 60)
            break
        except Exception as e:
            print(f"❌ 同步出错: {e}")
            print(f"   等待 {SYNC_INTERVAL} 秒后重试...")
            await asyncio.sleep(SYNC_INTERVAL)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动同步记忆数据到飞书多维表格")
    parser.add_argument(
        "--interval",
        type=int,
        help=f"同步间隔（秒），默认 {SYNC_INTERVAL}",
        default=SYNC_INTERVAL
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只同步一次，不循环"
    )
    
    args = parser.parse_args()
    
    if args.once:
        # 只同步一次
        await sync_all_memories(dry_run=False)
    else:
        # 循环同步
        global SYNC_INTERVAL
        SYNC_INTERVAL = args.interval
        await sync_loop()


if __name__ == "__main__":
    asyncio.run(main())
