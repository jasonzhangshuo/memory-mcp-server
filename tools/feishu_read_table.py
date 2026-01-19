"""读取飞书多维表格中的数据"""

import json
from typing import Optional
from sync.feishu_client import FeishuClient
from models import BaseModel, Field


class FeishuReadTableInput(BaseModel):
    """Input model for feishu_read_table tool."""
    app_token: str = Field(..., description="多维表格的 App Token")
    table_id: str = Field(..., description="数据表的 Table ID")
    limit: Optional[int] = Field(10, description="返回记录数量，默认10，最大100", ge=1, le=100)
    show_fields: Optional[bool] = Field(True, description="是否显示字段列表，默认true")


async def feishu_read_table(params: FeishuReadTableInput) -> str:
    """读取飞书多维表格中的数据。
    
    读取指定表格的字段列表和记录数据。
    支持分页读取，可以指定返回记录数量。
    
    Args:
        params: 参数对象
            - app_token: 多维表格的 App Token
            - table_id: 数据表的 Table ID
            - limit: 返回记录数量，默认10
            - show_fields: 是否显示字段列表，默认true
    
    Returns:
        JSON格式的表格数据，包括字段列表和记录
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 临时使用新的表格配置
        original_app_token = client.app_token
        original_table_id = client.table_id
        
        client.app_token = params.app_token
        client.table_id = params.table_id
        
        result = {
            "status": "success",
            "app_token": params.app_token,
            "table_id": params.table_id,
            "fields": [],
            "records": []
        }
        
        # 获取字段列表
        if params.show_fields:
            fields = await client.get_table_fields(table_id=params.table_id)
            for field in fields:
                result["fields"].append({
                    "name": field.get("field_name", "N/A"),
                    "type": field.get("type", "N/A"),
                    "field_id": field.get("field_id", "N/A")
                })
        
        # 获取记录
        all_records = []
        page_token = None
        count = 0
        
        while count < params.limit:
            page_size = min(100, params.limit - count)
            page_result = await client.list_records(
                table_id=params.table_id,
                page_token=page_token,
                page_size=page_size
            )
            
            records = page_result.get("items", [])
            all_records.extend(records)
            count += len(records)
            
            page_token = page_result.get("page_token")
            if not page_token or count >= params.limit:
                break
        
        # 格式化记录
        for record in all_records[:params.limit]:
            record_data = {
                "record_id": record.get("record_id", "N/A"),
                "fields": {}
            }
            
            fields_data = record.get("fields", {})
            for field_name, field_value in fields_data.items():
                # 处理不同类型的字段值
                if isinstance(field_value, list):
                    if field_value and isinstance(field_value[0], dict):
                        # 附件字段
                        record_data["fields"][field_name] = {
                            "type": "attachment",
                            "count": len(field_value),
                            "items": [
                                {
                                    "name": item.get("name", "N/A"),
                                    "type": item.get("type", "N/A"),
                                    "token": item.get("token", "N/A")[:50] + "..." if item.get("token") else "N/A"
                                }
                                for item in field_value[:3]  # 只显示前3个
                            ]
                        }
                    else:
                        record_data["fields"][field_name] = field_value
                elif isinstance(field_value, dict):
                    # 复杂对象（如链接）
                    if "link" in field_value:
                        record_data["fields"][field_name] = field_value.get("link", "N/A")
                    else:
                        record_data["fields"][field_name] = field_value
                else:
                    # 文本字段，截断过长内容
                    value_str = str(field_value)
                    if len(value_str) > 500:
                        value_str = value_str[:500] + "..."
                    record_data["fields"][field_name] = value_str
            
            result["records"].append(record_data)
        
        result["record_count"] = len(result["records"])
        result["total_found"] = len(all_records)
        
        # 恢复原始配置
        client.app_token = original_app_token
        client.table_id = original_table_id
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "suggestion": "请检查：1. 应用是否已添加为该表格的协作者 2. app_token 和 table_id 是否正确"
        }, ensure_ascii=False, indent=2)
