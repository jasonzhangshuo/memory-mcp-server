"""更新飞书文档内容"""

import json
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuUpdateDocumentInput


async def feishu_update_document(params: FeishuUpdateDocumentInput) -> str:
    """更新飞书文档内容。
    
    更新已有飞书文档的内容。
    支持 Markdown 格式内容。
    
    Args:
        params: 参数对象
            - file_token: 文档 token
            - content: 新的文档内容（Markdown 格式）
    
    Returns:
        JSON格式的更新结果
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 更新文档内容
        # 注意：file_token 在 docx API 中就是 document_id
        success = await client.update_document_content(
            document_id=params.file_token,
            content=params.content
        )
        
        if success:
            return json.dumps({
                "status": "success",
                "message": "文档已更新",
                "file_token": params.file_token
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "文档内容更新失败",
                "suggestion": "可能需要先将 Markdown 转换为飞书文档格式，或检查文档权限"
            }, ensure_ascii=False, indent=2)
        
    except FeishuAPIError as e:
        # 使用 FeishuAPIError 提供的详细错误信息
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. file_token 是否正确 2. 文档权限（drive:drive）是否已开通"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        # 其他未预期的错误
        return json.dumps({
            "status": "error",
            "message": f"更新文档失败: {str(e)}",
            "suggestion": "请检查：1. file_token 是否正确 2. 文档权限（drive:drive）是否已开通 3. 网络连接是否正常"
        }, ensure_ascii=False, indent=2)
