#!/usr/bin/env python3
"""检查飞书同步状态"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient
from storage.db import search_memories


async def check_sync_status():
    """检查同步状态"""
    print("=" * 60)
    print("🔍 检查飞书同步状态")
    print("=" * 60)
    print()
    
    # 1. 检查本地记忆数量
    print("📚 本地记忆:")
    local_memories = await search_memories(query="", limit=1000)
    print(f"   总数: {len(local_memories)} 条")
    local_ids = {m.get("id") for m in local_memories}
    print(f"   记忆ID列表: {sorted(list(local_ids))[:10]}...")  # 只显示前10个
    print()
    
    # 2. 检查飞书表格中的记录
    print("📊 飞书表格记录:")
    try:
        client = FeishuClient()
        
        # 获取所有记录
        all_records = []
        page_token = None
        while True:
            result = await client.list_records(page_token=page_token)
            records = result.get("items", [])
            all_records.extend(records)
            
            page_token = result.get("page_token")
            if not page_token:
                break
        
        print(f"   总数: {len(all_records)} 条")
        
        # 提取记忆ID
        feishu_ids = set()
        for record in all_records:
            fields = record.get("fields", {})
            memory_id = fields.get("记忆ID")
            if memory_id:
                feishu_ids.add(memory_id)
        
        print(f"   有效记忆ID: {len(feishu_ids)} 个")
        if feishu_ids:
            print(f"   记忆ID列表: {sorted(list(feishu_ids))[:10]}...")  # 只显示前10个
        print()
        
        # 3. 对比
        print("📊 对比结果:")
        print(f"   本地记忆: {len(local_ids)} 条")
        print(f"   飞书记录: {len(feishu_ids)} 条")
        
        # 找出未同步的
        not_synced = local_ids - feishu_ids
        if not_synced:
            print(f"   ⚠️  未同步: {len(not_synced)} 条")
            print(f"   未同步的ID: {sorted(list(not_synced))[:10]}...")
        else:
            print(f"   ✅ 所有记忆已同步")
        
        # 找出飞书中有但本地没有的（可能是已删除的）
        extra_in_feishu = feishu_ids - local_ids
        if extra_in_feishu:
            print(f"   ⚠️  飞书中多余: {len(extra_in_feishu)} 条（可能是已删除的本地记忆）")
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_sync_status())
