"""同步记忆数据到飞书多维表格的 MCP 工具"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
from storage.db import search_memories
from models import MemorySyncToFeishuInput


async def get_synced_records(client: FeishuClient) -> Tuple[set, Dict[str, str]]:
    """获取已同步的记录信息
    
    Returns:
        (synced_memory_ids, memory_id_to_record_id): 
        - synced_memory_ids: 已同步的记忆ID集合
        - memory_id_to_record_id: 记忆ID到飞书记录ID的映射
    """
    synced_ids = set()
    memory_id_to_record_id = {}
    
    try:
        # 获取所有记录
        page_token = None
        while True:
            result = await client.list_records(page_token=page_token)
            records = result.get("items", [])
            
            for record in records:
                record_id = record.get("record_id")
                fields = record.get("fields", {})
                memory_id = fields.get("记忆ID")
                if memory_id:
                    synced_ids.add(memory_id)
                    memory_id_to_record_id[memory_id] = record_id
            
            # 检查是否有下一页
            page_token = result.get("page_token")
            if not page_token:
                break
    except Exception as e:
        # 如果获取失败，返回空集合，将同步所有记录
        pass
    
    return synced_ids, memory_id_to_record_id


async def memory_sync_to_feishu(params: MemorySyncToFeishuInput) -> str:
    """同步记忆数据到飞书多维表格。
    
    将本地记忆数据同步到飞书多维表格，实现可视化查看和数据备份。
    支持增量同步，自动跳过已同步的记录。
    
    Args:
        params: 同步参数
            - dry_run: 是否试运行（不实际同步），默认 False
            - limit: 限制同步数量（用于测试），默认 None（同步所有）
    
    Returns:
        同步结果摘要，包括成功和失败的数量
    """
    dry_run = params.dry_run or False
    limit = params.limit
    
    try:
        # 初始化客户端
        client = FeishuClient()
    except Exception as e:
        return f"❌ 初始化飞书客户端失败: {str(e)}\n请检查 .env 文件中的配置（FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID）"
    
    # 获取所有记忆
    memories = await search_memories(
        query="",
        limit=limit or 1000
    )
    
    if not memories:
        return "⚠️ 没有找到需要同步的记忆"
    
    # 获取本地记忆ID集合
    local_memory_ids = {m.get("id") for m in memories if m.get("id")}
    
    # 获取已同步的记录
    synced_ids = set()
    memory_id_to_record_id = {}
    if not dry_run:
        synced_ids, memory_id_to_record_id = await get_synced_records(client)
    
    # 找出需要删除的记录（飞书中有但本地没有的）
    records_to_delete = []
    if not dry_run:
        for memory_id, record_id in memory_id_to_record_id.items():
            if memory_id not in local_memory_ids:
                records_to_delete.append((memory_id, record_id))
    
    # 删除飞书中多余的记录
    deleted_count = 0
    delete_fail_count = 0
    if records_to_delete:
        for memory_id, record_id in records_to_delete:
            try:
                if not dry_run:
                    await client.delete_record(record_id)
                    # 从 synced_ids 中移除被删除的记录ID
                    synced_ids.discard(memory_id)
                    deleted_count += 1
                    await asyncio.sleep(0.2)  # 避免请求过快
                else:
                    deleted_count += 1
            except Exception as e:
                delete_fail_count += 1
    
    # 过滤出需要同步的记录（本地有但飞书中没有的）
    if not dry_run:
        memories_to_sync = [
            m for m in memories
            if m.get("id") not in synced_ids
        ]
    else:
        memories_to_sync = memories
    
    # 同步记录
    success_count = 0
    fail_count = 0
    fail_details = []
    
    for i, memory in enumerate(memories_to_sync, 1):
        try:
            fields = convert_memory_to_feishu_fields(memory)
            
            if not dry_run:
                # 创建记录
                await client.create_record(fields)
                success_count += 1
                
                # 避免请求过快
                if i < len(memories_to_sync):
                    await asyncio.sleep(0.2)  # 200ms 延迟
            else:
                success_count += 1
                
        except Exception as e:
            fail_count += 1
            title = memory.get("title", "N/A")
            fail_details.append(f"  - {title}: {str(e)}")
    
    # 构建结果摘要
    result = []
    result.append("=" * 60)
    result.append("📊 同步完成")
    result.append("=" * 60)
    
    if records_to_delete:
        result.append(f"🗑️  删除: {deleted_count} 条（飞书中多余的记录）")
        if delete_fail_count > 0:
            result.append(f"   ❌ 删除失败: {delete_fail_count} 条")
    elif not dry_run:
        result.append(f"🗑️  删除: 0 条（飞书中没有多余的记录）")
    
    if memories_to_sync:
        result.append(f"✅ 新增: {success_count} 条")
        if fail_count > 0:
            result.append(f"❌ 失败: {fail_count} 条")
            if fail_details:
                result.append("\n失败详情:")
                result.extend(fail_details[:5])  # 只显示前5个失败详情
                if len(fail_details) > 5:
                    result.append(f"  ... 还有 {len(fail_details) - 5} 条失败记录")
    else:
        result.append(f"✅ 新增: 0 条（所有记忆已同步）")
    
    result.append(f"\n总计: {len(memories)} 条本地记忆")
    if not dry_run:
        initial_synced_count = len(synced_ids) + len(records_to_delete) if records_to_delete else len(synced_ids)
        result.append(f"飞书记录: {initial_synced_count} 条（同步前）")
        if records_to_delete:
            result.append(f"本次删除: {len(records_to_delete)} 条")
        result.append(f"本次新增: {len(memories_to_sync)} 条")
        result.append(f"飞书记录: {len(synced_ids)} 条（同步后）")
    
    if dry_run:
        result.append("\n⚠️ 这是试运行，未实际同步数据")
    
    return "\n".join(result)
