"""Memory list projects tool implementation."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.projects import list_projects
from models import MemoryListProjectsInput


async def memory_list_projects(params: MemoryListProjectsInput) -> str:
    """列出项目。
    
    列出所有项目，支持按状态过滤。
    返回项目列表，包括名称、描述、状态等信息。
    """
    try:
        projects = await list_projects(status=params.status)
        
        return json.dumps({
            "status": "success",
            "count": len(projects),
            "projects": projects
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"列出项目失败: {str(e)}",
            "suggestion": "请稍后重试"
        }, ensure_ascii=False, indent=2)
