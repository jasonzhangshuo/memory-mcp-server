"""Memory get project context tool implementation."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.projects import get_project_by_name, get_project_memories, get_project_baseline
from models import MemoryGetProjectContextInput


async def memory_get_project_context(params: MemoryGetProjectContextInput) -> str:
    """加载项目上下文。
    
    获取项目相关的记忆和基准文档。
    返回项目的基准文档和最近的相关记忆。
    """
    try:
        # 获取项目信息
        project = await get_project_by_name(params.project)
        if not project:
            return json.dumps({
                "status": "error",
                "message": f"未找到项目: {params.project}",
                "suggestion": "请检查项目名称是否正确，或先创建项目"
            }, ensure_ascii=False, indent=2)
        
        result = {
            "status": "success",
            "project": {
                "id": project["id"],
                "name": project["name"],
                "description": project.get("description", ""),
                "status": project.get("status", "active")
            },
            "baseline": None,
            "recent_memories": []
        }
        
        # 获取基准文档
        if params.include_baseline:
            baseline = await get_project_baseline(params.project)
            if baseline:
                result["baseline"] = baseline
        
        # 获取最近记忆
        memories = await get_project_memories(
            params.project,
            limit=params.recent_limit or 5
        )
        result["recent_memories"] = memories
        result["memory_count"] = len(memories)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"加载项目上下文失败: {str(e)}",
            "suggestion": "请检查项目名称是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
