"""同步记忆数据到飞书多维表格"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import DB_PATH, search_memories, get_memory
import aiosqlite


async def get_all_memories(limit: Optional[int] = None) -> List[Dict]:
    """获取所有记忆"""
    # 使用 search_memories 获取所有记录
    # 传入空查询字符串获取所有记录
    results = await search_memories(
        query="",
        limit=limit or 1000
    )
    return results


async def get_synced_record_ids(client: FeishuClient) -> set:
    """获取已同步的记录 ID"""
    synced_ids = set()
    
    try:
        # 获取所有记录
        page_token = None
        while True:
            result = await client.list_records(page_token=page_token)
            records = result.get("items", [])
            
            for record in records:
                fields = record.get("fields", {})
                memory_id = fields.get("记忆ID")
                if memory_id:
                    synced_ids.add(memory_id)
            
            # 检查是否有下一页
            page_token = result.get("page_token")
            if not page_token:
                break
    except Exception as e:
        print(f"⚠️ 获取已同步记录失败: {e}")
        print("   将同步所有记录")
    
    return synced_ids


async def sync_memory_to_feishu(
    client: FeishuClient,
    memory: Dict,
    dry_run: bool = False
) -> bool:
    """同步单条记忆到飞书"""
    try:
        fields = convert_memory_to_feishu_fields(memory)
        
        if dry_run:
            print(f"  [DRY RUN] 将同步: {memory.get('title', 'N/A')}")
            print(f"    字段: {json.dumps(fields, ensure_ascii=False, indent=2)}")
            return True
        
        # 检查是否已存在（通过记忆ID查找）
        memory_id = memory.get("id")
        if memory_id:
            # 先尝试查找现有记录
            # 注意：飞书 API 需要通过记录ID更新，这里简化处理，直接创建
            # 实际应用中可以通过记忆ID字段查询现有记录
            pass
        
        # 创建记录
        record = await client.create_record(fields)
        print(f"  ✅ 已同步: {memory.get('title', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"  ❌ 同步失败: {memory.get('title', 'N/A')}")
        print(f"     错误: {e}")
        return False


async def auto_sync_memory_to_feishu(memory: Dict, silent: bool = True) -> bool:
    """自动同步单条记忆到飞书（静默模式）
    
    用于在保存记忆时自动同步，如果失败不会影响保存操作。
    
    Args:
        memory: 记忆数据字典
        silent: 是否静默模式（不打印错误信息），默认 True
    
    Returns:
        bool: 是否同步成功
    """
    try:
        # 尝试初始化飞书客户端
        client = FeishuClient()
    except Exception as e:
        # 如果配置不存在或初始化失败，静默返回
        if not silent:
            print(f"⚠️ 飞书同步跳过（配置未设置）: {e}")
        return False
    
    try:
        memory_id = memory.get("id")
        if not memory_id:
            return False
        
        # 检查是否已同步（通过查询飞书记录）
        synced_ids = await get_synced_record_ids(client)
        
        # 转换字段格式
        fields = convert_memory_to_feishu_fields(memory)
        
        if memory_id in synced_ids:
            # 如果已同步，尝试更新（需要先找到记录ID）
            # 这里简化处理：由于飞书API需要通过记录ID更新，而查找记录ID需要遍历
            # 为了性能考虑，已同步的记录暂时不更新，只在新增时同步
            # 如果需要更新，可以调用全量同步工具
            if not silent:
                print(f"  ℹ️  记忆已同步到飞书: {memory.get('title', 'N/A')}")
            return True
        else:
            # 创建新记录
            await client.create_record(fields)
            if not silent:
                print(f"  ✅ 已自动同步到飞书: {memory.get('title', 'N/A')}")
            return True
            
    except Exception as e:
        # 同步失败不影响保存操作，静默处理
        if not silent:
            print(f"  ⚠️  飞书同步失败（不影响保存）: {e}")
        return False


async def sync_all_memories(
    dry_run: bool = False,
    limit: Optional[int] = None
):
    """同步所有记忆到飞书"""
    print("=" * 60)
    print("🚀 开始同步记忆数据到飞书多维表格")
    print("=" * 60)
    print()
    
    # 初始化客户端
    try:
        client = FeishuClient()
        print(f"✅ 飞书客户端初始化成功")
        print(f"   App Token: {client.app_token[:20]}...")
        print(f"   Table ID: {client.table_id}")
        print()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 获取所有记忆
    print("📚 获取本地记忆数据...")
    memories = await get_all_memories(limit=limit)
    print(f"   找到 {len(memories)} 条记忆")
    print()
    
    if not memories:
        print("⚠️ 没有找到需要同步的记忆")
        return
    
    # 获取已同步的记录
    if not dry_run:
        print("🔍 检查已同步记录...")
        synced_ids = await get_synced_record_ids(client)
        print(f"   已同步 {len(synced_ids)} 条记录")
        print()
        
        # 过滤出需要同步的记录
        memories_to_sync = [
            m for m in memories
            if m.get("id") not in synced_ids
        ]
        print(f"📝 需要同步 {len(memories_to_sync)} 条新记录")
    else:
        memories_to_sync = memories
        print(f"📝 [DRY RUN] 将同步 {len(memories_to_sync)} 条记录")
    
    print()
    
    # 同步记录
    success_count = 0
    fail_count = 0
    
    for i, memory in enumerate(memories_to_sync, 1):
        print(f"[{i}/{len(memories_to_sync)}] {memory.get('title', 'N/A')}")
        success = await sync_memory_to_feishu(client, memory, dry_run=dry_run)
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        # 避免请求过快
        if not dry_run and i < len(memories_to_sync):
            await asyncio.sleep(0.2)  # 200ms 延迟
    
    print()
    print("=" * 60)
    print("📊 同步完成")
    print("=" * 60)
    print(f"✅ 成功: {success_count} 条")
    if fail_count > 0:
        print(f"❌ 失败: {fail_count} 条")
    print()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="同步记忆数据到飞书多维表格")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，不实际同步"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制同步数量（用于测试）"
    )
    
    args = parser.parse_args()
    
    await sync_all_memories(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    import json
    asyncio.run(main())
