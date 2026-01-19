"""Memory check outdated tool implementation.

检测老旧内容：目标过期、计划过期、长期未访问的知识库条目。
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import search_memories
from models import MemoryCheckOutdatedInput


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        # 处理 ISO 格式日期
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt
        else:
            return datetime.fromisoformat(date_str)
    except:
        return None


async def memory_check_outdated(params: MemoryCheckOutdatedInput) -> str:
    """检测老旧内容。
    
    检测目标（goal）是否已过期、计划（plan）是否已过期、
    知识库条目是否长期未访问。
    
    Args:
        params: 参数对象
            - category: 限定类别（可选）
            - project: 限定项目（可选）
            - auto_fix: 是否自动修复（归档低重要性条目），默认False
    
    Returns:
        JSON格式的老旧内容报告
    """
    try:
        # 检索相关条目
        entries = await search_memories(
            query="",
            category=params.category,
            project=params.project,
            tags=None,
            limit=1000
        )
        
        now = datetime.now()
        outdated = []
        auto_archived = []
        
        for entry in entries:
            category = entry.get('category', '')
            created_at = entry.get('created_at', '')
            updated_at = entry.get('updated_at', created_at)
            importance = entry.get('importance', 3)
            archived = entry.get('archived', False)
            
            if archived:
                continue
            
            created_date = parse_date(created_at)
            updated_date = parse_date(updated_at)
            
            if not created_date:
                continue
            
            # 计算年龄（月）
            months_old = (now - created_date).days / 30
            months_since_update = (now - updated_date).days / 30 if updated_date else months_old
            
            # 检测目标（goal）是否已过期
            if category == 'goal':
                # 检查目标中是否包含时间信息
                title = entry.get('title', '')
                content = entry.get('content', '')
                full_text = f"{title} {content}"
                
                # 简单检测：如果包含年龄或年份信息
                age_mentioned = any(keyword in full_text 
                                 for keyword in ['50岁', '50', '2026', '2027', '2028', '2029', '2030'])
                
                if age_mentioned and months_old > 6:
                    outdated.append({
                        "type": "outdated_goal",
                        "severity": "high",
                        "entry": {
                            "id": entry.get('id'),
                            "title": title,
                            "category": category,
                            "created_at": created_at,
                            "months_old": round(months_old, 1)
                        },
                        "suggestion": f"目标 '{title}' 已创建 {round(months_old, 1)} 个月，是否需要更新状态？"
                    })
            
            # 检测计划（plan）是否已过期
            elif category == 'plan':
                if months_old > 3:  # 计划3个月未更新视为可能过期
                    outdated.append({
                        "type": "outdated_plan",
                        "severity": "medium",
                        "entry": {
                            "id": entry.get('id'),
                            "title": entry.get('title', ''),
                            "category": category,
                            "created_at": created_at,
                            "months_old": round(months_old, 1)
                        },
                        "suggestion": f"计划 '{entry.get('title', '')}' 已创建 {round(months_old, 1)} 个月，是否已完成或需要更新？"
                    })
            
            # 检测知识库条目是否长期未访问
            elif category in ['knowledge', 'reference']:
                if months_since_update > 6 and importance <= 2:
                    if params.auto_fix:
                        # 自动归档
                        from tools.memory_update import memory_update
                        from models import MemoryUpdateInput
                        update_params = MemoryUpdateInput(
                            id=entry.get('id'),
                            archived=True
                        )
                        await memory_update(update_params)
                        auto_archived.append({
                            "id": entry.get('id'),
                            "title": entry.get('title', '')
                        })
                    else:
                        outdated.append({
                            "type": "outdated_knowledge",
                            "severity": "low",
                            "entry": {
                                "id": entry.get('id'),
                                "title": entry.get('title', ''),
                                "category": category,
                                "updated_at": updated_at,
                                "months_since_update": round(months_since_update, 1),
                                "importance": importance
                            },
                            "suggestion": f"知识库条目 '{entry.get('title', '')}' 已 {round(months_since_update, 1)} 个月未更新且重要性较低，建议归档"
                        })
        
        result = {
            "status": "success",
            "count": len(outdated),
            "outdated": outdated
        }
        
        if params.auto_fix and auto_archived:
            result["auto_archived"] = auto_archived
            result["auto_archived_count"] = len(auto_archived)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"老旧内容检测失败: {str(e)}",
            "suggestion": "请检查参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
