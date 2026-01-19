"""Memory search tool implementation."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import search_memories
from models import MemorySearchInput


async def memory_search(params: MemorySearchInput) -> str:
    """搜索历史记忆。
    
    根据关键词、类别和项目搜索记忆条目。
    返回匹配的记忆列表，按重要性和创建时间排序。
    """
    try:
        results = await search_memories(
            query=params.query,
            category=params.category,
            project=params.project,
            tags=params.tags,
            limit=params.limit or 5
        )
        
        if not results:
            return json.dumps({
                "status": "success",
                "count": 0,
                "message": "没有找到相关记录",
                "results": []
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success",
            "count": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "suggestion": "请检查查询参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
