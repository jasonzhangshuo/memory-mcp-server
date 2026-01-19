#!/usr/bin/env python3
"""测试同步一条记忆数据到飞书"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import search_memories


async def test_sync_one():
    """测试同步一条数据"""
    print("=" * 60)
    print("🧪 测试同步一条记忆数据到飞书")
    print("=" * 60)
    print()
    
    try:
        # 初始化客户端
        client = FeishuClient()
        print("✅ 飞书客户端初始化成功")
        print()
        
        # 获取一条记忆
        print("📚 获取本地记忆数据...")
        memories = await search_memories(query="", limit=1)
        
        if not memories:
            print("❌ 没有找到记忆数据")
            return
        
        memory = memories[0]
        print(f"   找到记忆: {memory.get('title', 'N/A')}")
        print()
        
        # 转换为飞书字段格式
        print("🔄 转换数据格式...")
        fields = convert_memory_to_feishu_fields(memory)
        print(f"   字段数量: {len(fields)}")
        print("   字段列表:")
        for key, value in fields.items():
            # 截断长内容
            if isinstance(value, str) and len(value) > 50:
                display_value = value[:50] + "..."
            else:
                display_value = value
            print(f"      - {key}: {display_value}")
        print()
        
        # 同步到飞书
        print("📤 同步到飞书多维表格...")
        record = await client.create_record(fields)
        print(f"   ✅ 同步成功！")
        print(f"   记录ID: {record.get('record_id', 'N/A')}")
        print()
        
        print("=" * 60)
        print("✅ 测试成功！")
        print("=" * 60)
        print()
        print("💡 提示:")
        print("   1. 请在飞书多维表格中查看新创建的记录")
        print("   2. 确认数据格式是否正确")
        print("   3. 如果一切正常，可以运行完整同步：")
        print("      python sync/sync_to_feishu.py")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sync_one())
