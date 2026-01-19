#!/usr/bin/env python3
"""测试飞书同步 MCP 工具"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models import MemorySyncToFeishuInput
from tools.memory_sync_to_feishu import memory_sync_to_feishu


async def test_sync_tool():
    """测试同步工具（试运行）"""
    print("=" * 60)
    print("🧪 测试飞书同步 MCP 工具（试运行）")
    print("=" * 60)
    print()
    
    # 创建参数
    params = MemorySyncToFeishuInput(
        dry_run=True,  # 试运行，不实际同步
        limit=5  # 只测试5条
    )
    
    # 调用工具
    result = await memory_sync_to_feishu(params)
    
    print(result)
    print()
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sync_tool())
