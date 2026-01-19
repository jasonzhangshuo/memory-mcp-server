#!/usr/bin/env python3
"""删除日常安排记录（周二禅修课、周三瑜伽课）"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import aiosqlite

DB_PATH = os.path.join(project_root, "memory.db")
ENTRIES_DIR = os.path.join(project_root, "entries")


async def clean_daily_schedule():
    """删除日常安排记录"""
    print("=" * 60)
    print("🧹 删除日常安排记录")
    print("=" * 60)
    print()
    
    # 要删除的记录ID列表
    records_to_delete = [
        "ca247187-1d30-4b26-a614-dc2d8ba228a0",  # 周二禅修课
        "27f3af3b-1ff3-490a-b041-ef179df58161",  # 周三瑜伽课
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
    asyncio.run(clean_daily_schedule())
