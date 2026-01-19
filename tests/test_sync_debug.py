#!/usr/bin/env python3
"""调试同步问题 - 显示详细的请求和响应"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import search_memories


async def debug_sync():
    """调试同步"""
    print("=" * 60)
    print("🔍 调试同步问题")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 获取一条记忆
        memories = await search_memories(query="", limit=1)
        if not memories:
            print("❌ 没有找到记忆数据")
            return
        
        memory = memories[0]
        print(f"📝 记忆: {memory.get('title', 'N/A')}")
        print()
        
        # 转换字段
        fields = convert_memory_to_feishu_fields(memory)
        print("📊 转换后的字段:")
        print(json.dumps(fields, ensure_ascii=False, indent=2))
        print()
        
        # 检查权限
        print("🔐 检查权限...")
        print("   当前使用的是应用身份权限")
        print("   需要确保已申请: bitable:app:readwrite 或 bitable:app")
        print()
        
        # 尝试创建记录
        print("📤 尝试创建记录...")
        try:
            record = await client.create_record(fields)
            print("   ✅ 成功！")
            print(f"   记录ID: {record.get('record_id')}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            print()
            print("可能的原因:")
            print("1. 需要申请写入权限: bitable:app:readwrite")
            print("2. 字段类型不匹配")
            print("3. 字段值为空或格式不正确")
            print()
            print("建议:")
            print("1. 检查飞书开放平台权限管理")
            print("2. 确保已申请'应用身份'的写入权限")
            print("3. 检查字段类型是否正确")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_sync())
