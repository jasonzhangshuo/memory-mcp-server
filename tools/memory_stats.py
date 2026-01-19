"""Memory stats tool implementation."""

import json
import sys
import aiosqlite
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import DB_PATH
from models import MemoryStatsInput


async def memory_stats(params: MemoryStatsInput) -> str:
    """获取统计信息。
    
    获取记忆系统的统计信息，包括总数、分类统计等。
    支持按项目维度统计。
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            stats = {
                "total": 0,
                "by_category": {},
                "by_project": {},
                "archived": 0,
                "active": 0
            }
            
            # 总数量
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM memories WHERE archived = 0"
            )
            row = await cursor.fetchone()
            stats["total"] = row["count"] if row else 0
            
            # 归档数量
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM memories WHERE archived = 1"
            )
            row = await cursor.fetchone()
            stats["archived"] = row["count"] if row else 0
            stats["active"] = stats["total"]
            
            # 按类别统计
            cursor = await db.execute("""
                SELECT category, COUNT(*) as count 
                FROM memories 
                WHERE archived = 0
                GROUP BY category
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()
            for row in rows:
                stats["by_category"][row["category"]] = row["count"]
            
            # 按项目统计（如果指定了项目）
            if params.project:
                cursor = await db.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM memories 
                    WHERE project = ? AND archived = 0
                    GROUP BY category
                    ORDER BY count DESC
                """, (params.project,))
                rows = await cursor.fetchall()
                stats["by_project"][params.project] = {}
                for row in rows:
                    stats["by_project"][params.project][row["category"]] = row["count"]
            else:
                # 所有项目的统计
                cursor = await db.execute("""
                    SELECT project, COUNT(*) as count 
                    FROM memories 
                    WHERE project IS NOT NULL AND archived = 0
                    GROUP BY project
                    ORDER BY count DESC
                """)
                rows = await cursor.fetchall()
                for row in rows:
                    if row["project"]:
                        stats["by_project"][row["project"]] = row["count"]
            
            return json.dumps({
                "status": "success",
                "stats": stats
            }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"获取统计信息失败: {str(e)}",
            "suggestion": "请稍后重试"
        }, ensure_ascii=False, indent=2)
