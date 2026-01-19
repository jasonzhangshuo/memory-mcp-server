"""Memory list tags tool implementation."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import list_tags
from models import MemoryListTagsInput


async def memory_list_tags(params: MemoryListTagsInput) -> str:
    """列出所有标签及其使用次数。
    
    根据项目过滤标签列表，返回每个标签的名称和使用次数。
    
    Args:
        params: 参数对象
            - project: 限定项目（可选，不指定则列出所有标签）
    
    Returns:
        JSON格式的标签列表，包括标签名称和使用次数
    """
    try:
        tags = await list_tags(project=params.project)
        
        return json.dumps({
            "status": "success",
            "count": len(tags),
            "tags": tags
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"获取标签列表失败: {str(e)}",
            "suggestion": "请检查参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
