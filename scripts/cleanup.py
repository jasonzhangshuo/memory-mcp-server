#!/usr/bin/env python3
"""清理脚本：清理无用的 JSON 文件和过期的 FTS5 索引数据

使用方法:
    python scripts/cleanup.py [--dry-run]

参数:
    --dry-run: 试运行模式，只显示要删除的内容，不实际删除
"""

import os
import sys
import asyncio
import aiosqlite
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import DB_PATH

ENTRIES_DIR = os.path.join(project_root, "entries")


async def cleanup_orphaned_json_files(dry_run: bool = False) -> dict:
    """清理无用的 JSON 文件（数据库中没有引用的）"""
    
    # 获取数据库中所有有效的记忆 ID
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM memories")
        rows = await cursor.fetchall()
        valid_ids = {row[0] for row in rows}
    
    print(f"💾 数据库中有效记忆: {len(valid_ids)} 条")
    
    # 扫描 entries 目录下的所有 JSON 文件
    total_files = 0
    orphaned_files = []
    kept_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(ENTRIES_DIR):
        for file in files:
            if file.endswith('.json'):
                total_files += 1
                file_id = file.replace('.json', '')
                file_path = os.path.join(root, file)
                
                if file_id not in valid_ids:
                    # 无用文件
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    orphaned_files.append((file_path, file_size))
                else:
                    kept_files += 1
    
    print(f"\n📁 扫描结果:")
    print(f"   总文件数: {total_files}")
    print(f"   保留: {kept_files} 个")
    print(f"   无用: {len(orphaned_files)} 个 ({total_size / 1024:.1f} KB)")
    
    # 删除无用文件
    deleted_count = 0
    if orphaned_files:
        if dry_run:
            print(f"\n⚠️  试运行模式，不实际删除")
            if len(orphaned_files) <= 10:
                print(f"\n无用文件列表:")
                for path, size in orphaned_files:
                    print(f"  - {path} ({size} bytes)")
            else:
                print(f"\n前10个无用文件:")
                for path, size in orphaned_files[:10]:
                    print(f"  - {path} ({size} bytes)")
                print(f"  ... 还有 {len(orphaned_files) - 10} 个文件")
        else:
            print(f"\n🗑️  开始删除无用文件...")
            for file_path, _ in orphaned_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    if deleted_count % 100 == 0:
                        print(f"   已删除 {deleted_count}/{len(orphaned_files)}...")
                except Exception as e:
                    print(f"   删除失败: {file_path} - {e}")
            
            print(f"✅ 删除完成: {deleted_count} 个文件")
    
    return {
        "total_files": total_files,
        "kept_files": kept_files,
        "orphaned_files": len(orphaned_files),
        "deleted_files": deleted_count,
        "freed_space_kb": total_size / 1024
    }


async def cleanup_fts5_index(dry_run: bool = False) -> dict:
    """清理 FTS5 索引中的过期数据（主表中已删除的记录）"""
    
    async with aiosqlite.connect(DB_PATH) as db:
        # 获取主表中的所有 ID
        cursor = await db.execute("SELECT id FROM memories")
        rows = await cursor.fetchall()
        valid_ids = {row[0] for row in rows}
        
        # 获取 FTS5 表中的所有 ID
        cursor = await db.execute("SELECT id FROM memories_fts")
        rows = await cursor.fetchall()
        fts_ids = {row[0] for row in rows}
        
        # 找出 FTS5 中的过期记录
        orphaned_ids = fts_ids - valid_ids
        
        print(f"\n🔍 FTS5 索引检查:")
        print(f"   主表记录: {len(valid_ids)} 条")
        print(f"   FTS5 记录: {len(fts_ids)} 条")
        print(f"   过期记录: {len(orphaned_ids)} 条")
        
        deleted_count = 0
        if orphaned_ids:
            if dry_run:
                print(f"\n⚠️  试运行模式，不实际删除")
                if len(orphaned_ids) <= 10:
                    print(f"\n过期记录 ID:")
                    for id in list(orphaned_ids)[:10]:
                        print(f"  - {id}")
                else:
                    print(f"\n前10个过期记录 ID:")
                    for id in list(orphaned_ids)[:10]:
                        print(f"  - {id}")
                    print(f"  ... 还有 {len(orphaned_ids) - 10} 条")
            else:
                print(f"\n🗑️  开始清理 FTS5 过期记录...")
                # 删除 FTS5 中的过期记录
                for id in orphaned_ids:
                    try:
                        await db.execute("DELETE FROM memories_fts WHERE id = ?", (id,))
                        deleted_count += 1
                        if deleted_count % 100 == 0:
                            print(f"   已删除 {deleted_count}/{len(orphaned_ids)}...")
                    except Exception as e:
                        print(f"   删除失败: {id} - {e}")
                
                await db.commit()
                print(f"✅ 清理完成: {deleted_count} 条记录")
        elif len(fts_ids) == len(valid_ids):
            print(f"✅ FTS5 索引状态正常，无需清理")
        
        return {
            "main_table_records": len(valid_ids),
            "fts_records": len(fts_ids),
            "orphaned_records": len(orphaned_ids),
            "deleted_records": deleted_count
        }


async def cleanup_empty_directories(dry_run: bool = False) -> dict:
    """清理空目录"""
    
    deleted_dirs = []
    
    # 从最深层开始遍历，确保子目录先被删除
    for root, dirs, files in os.walk(ENTRIES_DIR, topdown=False):
        if root == ENTRIES_DIR:
            continue
        
        # 检查目录是否为空（忽略 .DS_Store）
        contents = os.listdir(root)
        real_contents = [f for f in contents if f != '.DS_Store']
        
        if not real_contents:
            deleted_dirs.append(root)
            if not dry_run:
                try:
                    # 删除 .DS_Store（如果存在）
                    for f in contents:
                        os.remove(os.path.join(root, f))
                    os.rmdir(root)
                except Exception as e:
                    print(f"   删除目录失败: {root} - {e}")
    
    if deleted_dirs:
        print(f"\n📂 空目录清理:")
        if dry_run:
            print(f"   找到 {len(deleted_dirs)} 个空目录（试运行模式）")
            if len(deleted_dirs) <= 10:
                for d in deleted_dirs:
                    print(f"   - {d}")
            else:
                for d in deleted_dirs[:10]:
                    print(f"   - {d}")
                print(f"   ... 还有 {len(deleted_dirs) - 10} 个目录")
        else:
            print(f"   已删除 {len(deleted_dirs)} 个空目录")
    else:
        print(f"\n📂 没有空目录需要清理")
    
    return {
        "empty_directories": len(deleted_dirs),
        "deleted_directories": 0 if dry_run else len(deleted_dirs)
    }


async def main():
    parser = argparse.ArgumentParser(description='清理无用的记忆文件和索引数据')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式，不实际删除')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧹 个人记忆系统清理工具")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️  运行模式: 试运行（不会实际删除任何内容）\n")
    else:
        print("\n⚠️  运行模式: 实际清理（将删除无用文件）\n")
    
    # 1. 清理无用的 JSON 文件
    print("\n" + "=" * 60)
    print("1️⃣  清理无用的 JSON 文件")
    print("=" * 60)
    json_result = await cleanup_orphaned_json_files(dry_run=args.dry_run)
    
    # 2. 清理 FTS5 索引
    print("\n" + "=" * 60)
    print("2️⃣  清理 FTS5 索引过期数据")
    print("=" * 60)
    fts_result = await cleanup_fts5_index(dry_run=args.dry_run)
    
    # 3. 清理空目录
    print("\n" + "=" * 60)
    print("3️⃣  清理空目录")
    print("=" * 60)
    dir_result = await cleanup_empty_directories(dry_run=args.dry_run)
    
    # 汇总报告
    print("\n" + "=" * 60)
    print("📊 清理汇总")
    print("=" * 60)
    
    if args.dry_run:
        print(f"\n将要清理:")
        print(f"  - JSON 文件: {json_result['orphaned_files']} 个 ({json_result['freed_space_kb']:.1f} KB)")
        print(f"  - FTS5 记录: {fts_result['orphaned_records']} 条")
        print(f"  - 空目录: {dir_result['empty_directories']} 个")
        print(f"\n提示: 运行 'python scripts/cleanup.py' 执行实际清理")
    else:
        print(f"\n已清理:")
        print(f"  - JSON 文件: {json_result['deleted_files']} 个 ({json_result['freed_space_kb']:.1f} KB)")
        print(f"  - FTS5 记录: {fts_result['deleted_records']} 条")
        print(f"  - 空目录: {dir_result['deleted_directories']} 个")
        print(f"\n✅ 清理完成！")


if __name__ == "__main__":
    asyncio.run(main())
