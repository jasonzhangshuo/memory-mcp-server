"""Memory update tool implementation."""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import aiosqlite

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import get_memory, DB_PATH, ENTRIES_DIR
from models import MemoryUpdateInput
from sync.sync_to_feishu import auto_sync_memory_to_feishu


async def memory_update(params: MemoryUpdateInput) -> str:
    """更新记忆。
    
    更新现有记忆的标题、内容或归档状态。
    只更新提供的字段，其他字段保持不变。
    """
    try:
        # 先获取现有记忆
        entry = await get_memory(params.id)
        if not entry:
            return json.dumps({
                "status": "error",
                "message": f"未找到ID为 {params.id} 的记忆",
                "suggestion": "请检查记忆ID是否正确"
            }, ensure_ascii=False, indent=2)
        
        # 更新字段
        updated = False
        if params.title is not None:
            entry['title'] = params.title
            updated = True
        if params.content is not None:
            entry['content'] = params.content
            updated = True
        if params.archived is not None:
            entry['archived'] = params.archived
            updated = True
        
        if not updated:
            return json.dumps({
                "status": "success",
                "message": "没有需要更新的字段",
                "entry": entry
            }, ensure_ascii=False, indent=2)
        
        # 更新时间戳
        entry['updated_at'] = datetime.now().isoformat()
        
        # 保存到 JSON 文件
        entry_path = None
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT entry_path FROM memories WHERE id = ?",
                (params.id,)
            )
            row = await cursor.fetchone()
            if row:
                entry_path = row["entry_path"]
        
        if entry_path and os.path.exists(entry_path):
            with open(entry_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "找不到记忆文件",
                "suggestion": "请检查数据库状态"
            }, ensure_ascii=False, indent=2)
        
        # 更新数据库
        async with aiosqlite.connect(DB_PATH) as db:
            update_fields = []
            update_values = []
            
            if params.title is not None:
                update_fields.append("title = ?")
                update_values.append(params.title)
            if params.content is not None:
                update_fields.append("content = ?")
                update_values.append(params.content)
            if params.archived is not None:
                update_fields.append("archived = ?")
                update_values.append(1 if params.archived else 0)
            
            update_fields.append("updated_at = ?")
            update_values.append(entry['updated_at'])
            update_values.append(params.id)
            
            sql = f"""
                UPDATE memories 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            await db.execute(sql, update_values)
            
            # 如果更新了标题或内容，更新 FTS5
            if params.title is not None or params.content is not None:
                # 删除旧的 FTS5 记录
                await db.execute(
                    "DELETE FROM memories_fts WHERE id = ?",
                    (params.id,)
                )
                # 插入新的 FTS5 记录
                await db.execute("""
                    INSERT INTO memories_fts (id, title, content, category, project)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    params.id,
                    entry['title'],
                    entry['content'],
                    entry['category'],
                    entry.get('project')
                ))
            
            await db.commit()
        
        # 自动同步到飞书（静默模式，失败不影响更新）
        await auto_sync_memory_to_feishu(entry, silent=True)
        
        return json.dumps({
            "status": "success",
            "message": "已更新",
            "entry": entry
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"更新失败: {str(e)}",
            "suggestion": "请检查输入参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
