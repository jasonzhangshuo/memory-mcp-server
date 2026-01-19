"""读取飞书文档信息和内容"""

import json
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuGetDocumentInput


async def feishu_get_document(params: FeishuGetDocumentInput) -> str:
    """读取飞书文档信息和内容。
    
    获取飞书文档的基本信息和内容。
    
    Args:
        params: 参数对象
            - file_token: 文档 token
    
    Returns:
        JSON格式的文档信息，包括标题、URL、内容等
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 获取文档信息
        result = await client.get_document(params.file_token)
        
        file_info = result.get("file", {})
        file_token = file_info.get("token", params.file_token)
        file_name = file_info.get("name", "N/A")
        
        # 构建文档 URL
        # 注意：docx API 创建的文档，URL 格式是 https://my.feishu.cn/docx/{document_id}
        url = f"https://my.feishu.cn/docx/{file_token}" if file_token else None
        
        # 注意：飞书文档内容可能需要通过其他 API 获取
        # 这里先返回基本信息
        return json.dumps({
            "status": "success",
            "file_token": file_token,
            "title": file_name,
            "url": url,
            "note": "文档内容需要通过飞书文档内容 API 获取，当前返回基本信息"
        }, ensure_ascii=False, indent=2)
        
    except FeishuAPIError as e:
        # 使用 FeishuAPIError 提供的详细错误信息
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. file_token 是否正确 2. 文档权限（docx:document）是否已开通 3. 文档是否真的创建成功"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        # 其他未预期的错误
        return json.dumps({
            "status": "error",
            "message": f"读取文档失败: {str(e)}",
            "suggestion": "请检查：1. file_token 是否正确 2. 文档权限（drive:drive）是否已开通 3. 网络连接是否正常"
        }, ensure_ascii=False, indent=2)
