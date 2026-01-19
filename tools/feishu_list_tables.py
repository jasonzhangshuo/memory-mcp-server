"""列出飞书多维表格中的所有数据表"""

import json
from typing import Optional
from sync.feishu_client import FeishuClient
from models import BaseModel, Field


class FeishuListTablesInput(BaseModel):
    """Input model for feishu_list_tables tool."""
    app_token: str = Field(..., description="多维表格的 App Token（从URL的 /base/ 后面提取）")


async def feishu_list_tables(params: FeishuListTablesInput) -> str:
    """列出飞书多维表格中的所有数据表。
    
    获取指定多维表格中的所有数据表列表，包括表格名称和ID。
    
    Args:
        params: 参数对象
            - app_token: 多维表格的 App Token
    
    Returns:
        JSON格式的表格列表，包括名称、ID等信息
    """
    try:
        # 创建客户端（使用环境变量中的 APP_ID 和 APP_SECRET）
        client = FeishuClient()
        
        # 临时使用新的表格配置
        original_app_token = client.app_token
        client.app_token = params.app_token
        
        # 获取所有表格
        tables = await client.list_tables()
        
        # 恢复原始配置
        client.app_token = original_app_token
        
        # 格式化结果
        result = {
            "status": "success",
            "app_token": params.app_token,
            "table_count": len(tables),
            "tables": []
        }
        
        for table in tables:
            result["tables"].append({
                "name": table.get("name", "N/A"),
                "table_id": table.get("table_id", "N/A"),
                "revision": table.get("revision", "N/A")
            })
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "suggestion": "请检查：1. 应用是否已添加为该表格的协作者 2. 应用权限是否已开通"
        }, ensure_ascii=False, indent=2)
