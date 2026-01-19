#!/usr/bin/env python3
"""删除本地数据库中的测试记忆"""

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


async def delete_test_memories():
    """删除测试记忆"""
    print("=" * 60)
    print("🗑️  删除本地数据库中的测试记忆")
    print("=" * 60)
    print()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 查找所有测试记忆
        # 1. category 为 "test" 的
        # 2. 标题包含"测试"的
        # 3. 项目为"测试项目"的
        cursor = await db.execute("""
            SELECT id, title, category, project, entry_path
            FROM memories
            WHERE category = 'test' 
               OR title LIKE '%测试%'
               OR project = '测试项目'
        """)
        
        test_memories = await cursor.fetchall()
        
        if not test_memories:
            print("✅ 没有发现测试记忆")
            return
        
        print(f"⚠️  发现 {len(test_memories)} 条测试记忆:")
        print()
        for i, memory in enumerate(test_memories, 1):
            print(f"   {i}. {memory['title']}")
            print(f"      分类: {memory['category']}, 项目: {memory['project'] or 'N/A'}")
        
        print()
        print("=" * 60)
        print("⚠️  警告：将删除以上测试记忆")
        print("=" * 60)
        print()
        
        # 检查命令行参数
        if "--yes" in sys.argv or "-y" in sys.argv:
            confirm = "yes"
            print("✅ 使用 --yes 参数，自动确认删除")
        else:
            try:
                confirm = input(f"确认删除 {len(test_memories)} 条测试记忆？(yes/no): ").strip().lower()
            except EOFError:
                print("❌ 非交互式环境，请使用 --yes 参数自动确认")
                print("   运行: python delete_local_test_memories.py --yes")
                return
        
        if confirm != "yes":
            print("❌ 已取消")
            return
        
        # 删除测试记忆
        print()
        print("🗑️  开始删除...")
        deleted_count = 0
        failed_count = 0
        
        for memory in test_memories:
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
        print("📊 删除完成")
        print("=" * 60)
        print(f"✅ 成功删除: {deleted_count} 条")
        if failed_count > 0:
            print(f"❌ 删除失败: {failed_count} 条")


if __name__ == "__main__":
    asyncio.run(delete_test_memories())
