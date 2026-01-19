"""Memory get tool implementation."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import get_memory
from models import MemoryGetInput


async def memory_get(params: MemoryGetInput) -> str:
    """获取记忆详情。
    
    根据记忆ID获取完整的记忆条目信息。
    返回记忆的完整内容，包括标题、内容、类别、时间戳等。
    """
    try:
        entry = await get_memory(params.id)
        
        if not entry:
            return json.dumps({
                "status": "error",
                "message": f"未找到ID为 {params.id} 的记忆",
                "suggestion": "请检查记忆ID是否正确"
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success",
            "entry": entry
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"获取记忆失败: {str(e)}",
            "suggestion": "请检查记忆ID是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
