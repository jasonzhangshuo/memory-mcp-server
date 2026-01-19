#!/usr/bin/env python3
"""测试读取权限"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def test_read():
    """测试读取权限"""
    print("=" * 60)
    print("🔍 测试读取权限")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 测试列出记录（读取操作）
        print("📖 尝试读取记录...")
        result = await client.list_records(page_size=1)
        records = result.get("items", [])
        print(f"   ✅ 读取成功！找到 {len(records)} 条记录")
        
        if records:
            print(f"   第一条记录:")
            record = records[0]
            print(f"     记录ID: {record.get('record_id')}")
            print(f"     字段: {list(record.get('fields', {}).keys())}")
        
        print()
        print("=" * 60)
        print("✅ 读取权限正常")
        print("=" * 60)
        print()
        print("💡 如果能读取但不能写入，说明:")
        print("   1. 读取权限已生效")
        print("   2. 写入权限可能还未生效或需要额外配置")
        print("   3. 建议检查应用是否需要发布")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 读取测试失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        if "403" in str(e):
            print("⚠️  读取权限也没有生效")
            print("   建议检查权限申请状态")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_read())
