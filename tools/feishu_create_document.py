"""创建飞书文档"""

import json
import os
from typing import Optional
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuCreateDocumentInput


async def feishu_create_document(params: FeishuCreateDocumentInput) -> str:
    """创建飞书文档并写入内容。
    
    创建新的飞书文档，并写入指定内容。
    支持 Markdown 格式内容。
    
    Args:
        params: 参数对象
            - title: 文档标题
            - content: 文档内容（Markdown 格式）
            - folder_token: 文件夹 token（可选）
    
    Returns:
        JSON格式的文档信息，包括 file_token 和 url
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 创建文档
        # 注意：如果需要访问用户云盘文件夹，需要使用用户身份 token
        # 默认使用应用身份，如果有文件夹 token（传入或环境变量）则使用用户身份

        # 检查是否使用了文件夹（传入参数或环境变量默认值）
        default_folder = os.getenv("FEISHU_DEFAULT_FOLDER_TOKEN")
        actual_folder = params.folder_token or default_folder
        
        # 如果指定了文件夹，使用用户身份 token（因为用户文件夹需要用户权限）
        # 否则使用应用身份 token
        use_user = bool(actual_folder)
        
        # 确定要使用的 folder_token（优先使用传入的，否则使用默认的）
        target_folder = params.folder_token or default_folder
        
        print(f"📁 文件夹 token: {target_folder if target_folder else '未指定（将创建在默认位置）'}")
        print(f"🔑 使用{'用户身份' if use_user else '应用身份'} token")

        result = await client.create_document(
            title=params.title,
            content=params.content,
            folder_token=target_folder,
            use_user_token=use_user
        )
        
        file_token = result.get("file", {}).get("token")
        file_name = result.get("file", {}).get("name", params.title)
        
        # 构建文档 URL（飞书文档的 URL 格式）
        # 注意：docx API 创建的文档，URL 格式是 https://my.feishu.cn/docx/{document_id}
        url = f"https://my.feishu.cn/docx/{file_token}" if file_token else None
        
        return json.dumps({
            "status": "success",
            "message": "文档已创建",
            "file_token": file_token,
            "title": file_name,
            "url": url
        }, ensure_ascii=False, indent=2)
        
    except FeishuAPIError as e:
        # 使用 FeishuAPIError 提供的详细错误信息
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. 文档权限（drive:drive）是否已开通 2. 文件夹 token 是否正确（如果指定了）"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        # 其他未预期的错误
        return json.dumps({
            "status": "error",
            "message": f"创建文档失败: {str(e)}",
            "suggestion": "请检查：1. 文档权限（drive:drive）是否已开通 2. 文件夹 token 是否正确（如果指定了）3. 网络连接是否正常"
        }, ensure_ascii=False, indent=2)
