#!/usr/bin/env python3
"""测试同步 - 使用字段ID"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import search_memories


async def test_sync_with_field_id():
    """测试同步 - 使用字段ID"""
    print("=" * 60)
    print("🧪 测试同步 - 使用字段ID")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 获取字段列表
        print("📋 获取字段列表...")
        fields_list = await client.get_table_fields()
        field_name_to_id = {f.get("field_name"): f.get("field_id") for f in fields_list}
        print(f"   ✅ 找到 {len(field_name_to_id)} 个字段")
        print("   字段映射:")
        for name, field_id in field_name_to_id.items():
            print(f"      {name} -> {field_id}")
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
        
        # 转换字段（使用字段名称）
        fields_by_name = convert_memory_to_feishu_fields(memory)
        print(f"   字段数量: {len(fields_by_name)}")
        print()
        
        # 尝试方法1: 使用字段名称
        print("📤 方法1: 使用字段名称创建记录...")
        try:
            record = await client.create_record(fields_by_name, use_field_id=False)
            print(f"   ✅ 成功！记录ID: {record.get('record_id')}")
            print()
            print("=" * 60)
            print("✅ 测试成功！")
            print("=" * 60)
            return
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            print()
        
        # 尝试方法2: 使用字段ID
        print("📤 方法2: 使用字段ID创建记录...")
        try:
            record = await client.create_record(fields_by_name, use_field_id=True)
            print(f"   ✅ 成功！记录ID: {record.get('record_id')}")
            print()
            print("=" * 60)
            print("✅ 测试成功！")
            print("=" * 60)
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            print()
            print("=" * 60)
            print("❌ 两种方法都失败了")
            print("=" * 60)
            print()
            print("可能的原因:")
            print("1. 权限虽然已申请，但写入权限还未生效")
            print("2. 应用发布后需要等待更长时间")
            print("3. 可能需要联系飞书技术支持")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sync_with_field_id())
