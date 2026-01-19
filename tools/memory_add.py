"""Memory add tool implementation."""

import json
import uuid
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import add_memory
from models import MemoryAddInput, MemorySuggestCategoryInput, MemoryCheckConflictsInput
from tools.memory_suggest_category import memory_suggest_category
from tools.memory_check_conflicts import memory_check_conflicts
from sync.sync_to_feishu import auto_sync_memory_to_feishu


async def memory_add(params: MemoryAddInput) -> str:
    """添加新记忆。
    
    创建一个新的记忆条目，保存到数据库和JSON文件。
    自动生成ID和时间戳。
    保存成功后自动同步到飞书多维表格。
    
    如果 category 为 "auto"，会自动调用智能分类判定。
    """
    try:
        memory_id = str(uuid.uuid4())
        
        # 智能分类判定：如果 category 为 "auto"，自动判定
        final_category = params.category
        category_suggestion = None
        
        if params.category == "auto" or not params.category:
            # 调用智能分类建议
            suggest_params = MemorySuggestCategoryInput(
                title=params.title,
                content=params.content
            )
            suggest_result_str = await memory_suggest_category(suggest_params)
            suggest_result = json.loads(suggest_result_str)
            
            if suggest_result.get("status") == "success":
                suggestion = suggest_result.get("suggestion", {})
                final_category = suggestion.get("suggested_category", "insight")
                category_suggestion = suggestion
        
        entry = await add_memory(
            memory_id=memory_id,
            category=final_category,
            title=params.title,
            content=params.content,
            project=params.project,
            importance=params.importance or 3,
            source_type="claude_ai",
            tags=params.tags or []
        )
        
        # 自动同步到飞书（静默模式，失败不影响保存）
        await auto_sync_memory_to_feishu(entry, silent=True)
        
        result = {
            "status": "success",
            "message": "已记录",
            "id": memory_id,
            "entry": entry
        }
        
        # 如果使用了智能判定，返回判定信息
        if category_suggestion:
            result["category_suggestion"] = category_suggestion
            result["auto_classified"] = True
        
        # 自动检测冲突（静默模式，失败不影响保存）
        try:
            conflict_params = MemoryCheckConflictsInput(
                new_entry_id=memory_id,
                category=final_category,
                project=params.project,
                check_type=["contradict", "duplicate"]
            )
            conflict_result_str = await memory_check_conflicts(conflict_params)
            conflict_result = json.loads(conflict_result_str)
            
            if conflict_result.get("status") == "success" and conflict_result.get("count", 0) > 0:
                result["conflicts_detected"] = True
                result["conflicts"] = conflict_result.get("conflicts", [])
                result["message"] = "已记录（检测到冲突，请查看 conflicts 字段）"
        except Exception:
            # 冲突检测失败不影响保存
            pass
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"保存失败: {str(e)}",
            "suggestion": "请检查输入参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)
