#!/usr/bin/env python3
"""测试同步 - 强制刷新token"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import search_memories


async def test_sync_with_refresh():
    """测试同步 - 强制刷新token"""
    print("=" * 60)
    print("🧪 测试同步 - 强制刷新Token")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 强制刷新token（清除旧的token缓存）
        print("🔄 强制刷新访问令牌...")
        client.access_token = None
        client.token_expires_at = None
        token = await client.get_access_token(force_refresh=True)
        print(f"   ✅ 新Token获取成功: {token[:30]}...")
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
        
        # 转换字段
        fields = convert_memory_to_feishu_fields(memory)
        print(f"   字段数量: {len(fields)}")
        print()
        
        # 尝试创建记录
        print("📤 同步到飞书多维表格...")
        record = await client.create_record(fields)
        print(f"   ✅ 同步成功！")
        print(f"   记录ID: {record.get('record_id', 'N/A')}")
        print()
        
        print("=" * 60)
        print("✅ 测试成功！")
        print("=" * 60)
        print()
        print("💡 请在飞书多维表格中查看新创建的记录")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        
        if "403" in str(e) or "Forbidden" in str(e):
            print("⚠️  仍然是403错误，可能的原因:")
            print("   1. 权限虽然勾选了，但还没有生效（需要等待几分钟）")
            print("   2. 需要重新发布应用")
            print("   3. 权限申请后需要管理员审核（如果不是免审权限）")
            print()
            print("建议:")
            print("   1. 等待2-3分钟后重试")
            print("   2. 检查飞书开放平台的应用状态")
            print("   3. 确认权限页面显示'已开通'状态")
        
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sync_with_refresh())
