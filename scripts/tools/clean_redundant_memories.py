#!/usr/bin/env python3
"""清理冗余记忆记录"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import aiosqlite

DB_PATH = os.path.join(project_root, "memory.db")
ENTRIES_DIR = os.path.join(project_root, "entries")


async def clean_redundant_memories():
    """清理冗余记忆"""
    print("=" * 60)
    print("🧹 清理冗余记忆记录")
    print("=" * 60)
    print()
    
    # 要删除的记录ID列表
    records_to_delete = [
        # 重复的"周二禅修课"（保留最新的，删除2条旧的）
        "690fdc5d-25c7-46a8-945e-0a68fcd595ad",  # 10:19
        "8941f1a2-558a-4eb2-af74-976de1bfed5e",  # 10:09
        
        # 内容过于简单的记录
        "dedd8a3d-de65-4665-b9bd-060bf0c958d3",  # 每天冥想10分钟
        "47abb934-4bb1-41b8-9338-87b47de59333",  # 工作生活平衡
        
        # 重复的"戒糖讨论"（与"戒糖进展"重复）
        "4c5d4a11-51f8-4b01-a1e5-ba8ac46adebd",  # 戒糖讨论
    ]
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 获取要删除的记录信息
        print("📋 准备删除的记录：")
        print()
        memories_to_delete = []
        for memory_id in records_to_delete:
            cursor = await db.execute(
                "SELECT id, title, category, entry_path FROM memories WHERE id = ?",
                (memory_id,)
            )
            row = await cursor.fetchone()
            if row:
                memories_to_delete.append(row)
                print(f"   - {row['title']} ({row['category']})")
            else:
                print(f"   ⚠️  未找到记录: {memory_id}")
        
        if not memories_to_delete:
            print("✅ 没有需要删除的记录")
            return
        
        print()
        print(f"总计: {len(memories_to_delete)} 条记录将被删除")
        print()
        
        # 执行删除
        print("🗑️  开始删除...")
        deleted_count = 0
        failed_count = 0
        
        for memory in memories_to_delete:
            memory_id = memory['id']
            entry_path = memory['entry_path']
            
            try:
                # 删除数据库记录
                await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                
                # 删除 FTS5 索引
                await db.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
                
                # 删除 JSON 文件
                if entry_path and os.path.exists(entry_path):
                    try:
                        os.remove(entry_path)
                    except Exception as e:
                        print(f"   ⚠️  无法删除文件 {entry_path}: {e}")
                
                deleted_count += 1
                print(f"   ✅ 已删除: {memory['title']}")
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ 删除失败: {memory['title']} - {e}")
        
        await db.commit()
        
        print()
        print("=" * 60)
        print("📊 清理完成")
        print("=" * 60)
        print(f"✅ 成功删除: {deleted_count} 条")
        if failed_count > 0:
            print(f"❌ 删除失败: {failed_count} 条")
        print()
        
        # 显示剩余记录数
        cursor = await db.execute("SELECT COUNT(*) as count FROM memories WHERE archived = 0")
        row = await cursor.fetchone()
        remaining = row['count'] if row else 0
        print(f"📚 剩余活跃记忆: {remaining} 条")


if __name__ == "__main__":
    asyncio.run(clean_redundant_memories())
