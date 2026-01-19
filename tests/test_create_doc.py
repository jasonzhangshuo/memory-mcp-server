#!/usr/bin/env python3
"""测试创建飞书文档"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def test_create_document():
    """测试创建文档"""
    try:
        print("=" * 60)
        print("🧪 测试创建飞书文档")
        print("=" * 60)
        print()
        
        # 初始化客户端
        print("📋 初始化飞书客户端...")
        client = FeishuClient()
        print(f"   App ID: {client.app_id}")
        print()
        
        # 创建文档
        print("📝 创建文档...")
        print("   标题: 我要睡觉")
        print("   内容: 马上睡")
        print()
        
        result = await client.create_document(
            title="我要睡觉",
            content="马上睡"
        )
        
        print("✅ 文档创建成功！")
        print()
        print("📄 文档信息:")
        print(f"   Document ID: {result.get('file', {}).get('token')}")
        print(f"   标题: {result.get('file', {}).get('name')}")
        print()
        
        return result
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 创建文档失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_create_document())
