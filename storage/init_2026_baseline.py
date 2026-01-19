"""Initialize 2026-baseline project and associate seed data."""

import asyncio
import uuid
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, DB_PATH
from storage.projects import create_project, get_project_by_name
import aiosqlite


async def init_2026_baseline_project():
    """Initialize 2026-baseline project."""
    print("=" * 70)
    print("初始化 2026-baseline 项目")
    print("=" * 70)
    
    await init_db()
    
    # Check if project already exists
    existing_project = await get_project_by_name("2026-baseline")
    if existing_project:
        print("⚠️  项目 '2026-baseline' 已存在，跳过创建")
        project_id = existing_project["id"]
    else:
        # Read baseline document
        baseline_path = os.path.join(project_root, "projects", "2026-baseline_baseline.md")
        baseline_doc = ""
        if os.path.exists(baseline_path):
            with open(baseline_path, "r", encoding="utf-8") as f:
                baseline_doc = f.read()
        else:
            print(f"⚠️  警告: 基准文档不存在: {baseline_path}")
        
        # Create project
        project_id = str(uuid.uuid4())
        project_data = await create_project(
            project_id=project_id,
            name="2026-baseline",
            description="2026年个人基准线项目，包含身份、目标、模式、承诺和原则等核心信息",
            baseline_doc=baseline_doc,
            status="active"
        )
        print(f"✅ 项目创建成功: {project_data['name']}")
        print(f"   项目ID: {project_id}")
    
    # Associate existing seed data to the project
    print("\n关联种子数据到项目...")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Get seed data titles from seed.py
        seed_titles = [
            "基本身份信息",
            "核心目标：50岁退休",
            "行为模式：研究替代到达",
            "三个锚点",
            "止损规则"
        ]
        
        # Find memories matching seed data titles
        placeholders = ",".join(["?"] * len(seed_titles))
        cursor = await db.execute(f"""
            SELECT id, category, title FROM memories
            WHERE title IN ({placeholders})
            AND (project IS NULL OR project = '')
        """, seed_titles)
        rows = await cursor.fetchall()
        
        if rows:
            updated = 0
            for row in rows:
                await db.execute(
                    "UPDATE memories SET project = ? WHERE id = ?",
                    ("2026-baseline", row["id"])
                )
                updated += 1
                print(f"  ✓ 关联: {row['title']} ({row['category']})")
            
            await db.commit()
            print(f"\n✅ 成功关联 {updated} 条种子数据到 '2026-baseline' 项目")
        else:
            print("⚠️  未找到需要关联的种子数据（可能已关联）")
    
    print("\n" + "=" * 70)
    print("2026-baseline 项目初始化完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(init_2026_baseline_project())
