#!/usr/bin/env python3
"""查看记忆数据的脚本"""

import asyncio
import json
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import DB_PATH, ENTRIES_DIR
import aiosqlite


async def view_all_memories():
    """查看所有记忆"""
    print("=" * 60)
    print("📚 个人记忆系统 - 数据查看")
    print("=" * 60)
    print()
    
    # 统计信息
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 总数
        cursor = await db.execute("SELECT COUNT(*) as count FROM memories")
        total = (await cursor.fetchone())["count"]
        
        # 按分类统计
        cursor = await db.execute("""
            SELECT category, COUNT(*) as count 
            FROM memories 
            GROUP BY category 
            ORDER BY count DESC
        """)
        categories = await cursor.fetchall()
        
        # 按项目统计
        cursor = await db.execute("""
            SELECT project, COUNT(*) as count 
            FROM memories 
            WHERE project IS NOT NULL
            GROUP BY project 
            ORDER BY count DESC
        """)
        projects = await cursor.fetchall()
        
        print(f"📊 统计信息")
        print(f"   总记忆数: {total}")
        print()
        
        print(f"📁 按分类统计:")
        for row in categories:
            print(f"   {row['category']}: {row['count']} 条")
        print()
        
        if projects:
            print(f"📂 按项目统计:")
            for row in projects:
                print(f"   {row['project']}: {row['count']} 条")
            print()
    
    # 列出最近的记忆
    print("=" * 60)
    print("📝 最近的记忆条目（最近 10 条）")
    print("=" * 60)
    print()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, title, category, created_at, project, importance
            FROM memories
            ORDER BY created_at DESC
            LIMIT 10
        """)
        rows = await cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            print(f"{i}. [{row['category']}] {row['title']}")
            print(f"   ID: {row['id']}")
            print(f"   时间: {row['created_at']}")
            if row['project']:
                print(f"   项目: {row['project']}")
            print(f"   重要性: {'⭐' * row['importance']}")
            print()
    
    # 文件位置信息
    print("=" * 60)
    print("📂 文件存储位置")
    print("=" * 60)
    print()
    print(f"数据库文件: {DB_PATH}")
    print(f"  大小: {os.path.getsize(DB_PATH) / 1024:.1f} KB")
    print()
    print(f"JSON 文件目录: {ENTRIES_DIR}")
    json_count = len(list(Path(ENTRIES_DIR).rglob("*.json")))
    print(f"  JSON 文件数: {json_count}")
    print()
    
    # 列出目录结构
    print("目录结构:")
    for year_dir in sorted(Path(ENTRIES_DIR).iterdir()):
        if year_dir.is_dir():
            print(f"  {year_dir.name}/")
            for month_dir in sorted(year_dir.iterdir()):
                if month_dir.is_dir():
                    json_files = list(month_dir.glob("*.json"))
                    print(f"    {month_dir.name}/ ({len(json_files)} 个文件)")


async def view_memory_detail(memory_id: str = None):
    """查看单个记忆的详细信息"""
    if not memory_id:
        print("请提供记忆 ID")
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM memories WHERE id = ?
        """, (memory_id,))
        row = await cursor.fetchone()
        
        if not row:
            print(f"❌ 未找到 ID 为 {memory_id} 的记忆")
            return
        
        print("=" * 60)
        print("📝 记忆详情")
        print("=" * 60)
        print()
        print(f"标题: {row['title']}")
        print(f"分类: {row['category']}")
        print(f"项目: {row['project'] or '无'}")
        print(f"重要性: {'⭐' * row['importance']}")
        print(f"创建时间: {row['created_at']}")
        print(f"更新时间: {row['updated_at']}")
        print(f"标签: {json.loads(row['tags'] or '[]')}")
        print()
        print("内容:")
        print("-" * 60)
        print(row['content'])
        print("-" * 60)
        print()
        print(f"文件路径: {row['entry_path']}")
        
        # 读取 JSON 文件
        if os.path.exists(row['entry_path']):
            with open(row['entry_path'], 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print()
            print("完整 JSON 数据:")
            print(json.dumps(json_data, ensure_ascii=False, indent=2))


async def search_memories(query: str):
    """搜索记忆"""
    print("=" * 60)
    print(f"🔍 搜索: {query}")
    print("=" * 60)
    print()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, title, category, created_at, project
            FROM memories
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (f"%{query}%", f"%{query}%"))
        rows = await cursor.fetchall()
        
        if not rows:
            print("❌ 未找到相关记忆")
            return
        
        print(f"找到 {len(rows)} 条相关记忆:")
        print()
        for i, row in enumerate(rows, 1):
            print(f"{i}. [{row['category']}] {row['title']}")
            print(f"   ID: {row['id']}")
            print(f"   时间: {row['created_at']}")
            if row['project']:
                print(f"   项目: {row['project']}")
            print()


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "detail" and len(sys.argv) > 2:
            await view_memory_detail(sys.argv[2])
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            await search_memories(sys.argv[2])
        else:
            print("用法:")
            print("  python view_memories.py              # 查看所有记忆")
            print("  python view_memories.py detail <ID>  # 查看单个记忆详情")
            print("  python view_memories.py search <关键词>  # 搜索记忆")
    else:
        await view_all_memories()


if __name__ == "__main__":
    asyncio.run(main())
