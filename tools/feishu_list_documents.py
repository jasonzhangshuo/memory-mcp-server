"""列出飞书文档列表"""

import json
from typing import Optional
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuListDocumentsInput


async def feishu_list_documents(params: FeishuListDocumentsInput) -> str:
    """列出飞书文档列表。
    
    获取指定文件夹中的文档列表，包括文档名称、类型、创建时间等信息。
    
    Args:
        params: 参数对象
            - folder_token: 文件夹 token（可选，不指定则列出根目录）
            - page_size: 每页数量，默认50，最大100
    
    Returns:
        JSON格式的文档列表，包括文档名称、类型、token等信息
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 如果没有指定 folder_token，尝试获取根目录
        folder_token = params.folder_token
        if not folder_token:
            try:
                root_info = await client.get_root_folder_meta(use_user_token=params.use_user_token)
                folder_token = root_info.get("token")
                print(f"📁 使用根目录 folder_token: {folder_token}")
            except Exception as e:
                print(f"⚠️  无法获取根目录信息: {e}")
                if not params.use_user_token:
                    print("   将读取应用创建的文档（不是用户文档库）")
                    print("   💡 提示：设置 use_user_token=True 可以使用用户身份访问你的文档库")
        
        # 获取文档列表
        result = await client.list_documents(
            folder_token=folder_token,
            page_size=params.page_size,
            use_user_token=params.use_user_token
        )
        
        files = result.get("files", [])
        page_token = result.get("page_token")
        
        # 格式化结果
        documents = []
        folders = []
        for file in files:
            file_type = file.get("type", "N/A")
            if file_type == "folder":
                # 文件夹
                folders.append({
                    "token": file.get("token", "N/A"),
                    "name": file.get("name", "N/A"),
                    "type": "folder",
                    "created_time": file.get("created_time", "N/A"),
                    "modified_time": file.get("modified_time", "N/A")
                })
            else:
                # 文档
                documents.append({
                    "token": file.get("token", "N/A"),
                    "name": file.get("name", "N/A"),
                    "type": file_type,
                    "url": file.get("url") or (f"https://my.feishu.cn/docx/{file.get('token', '')}" if file_type == "docx" else None),
                    "created_time": file.get("created_time", "N/A"),
                    "modified_time": file.get("modified_time", "N/A")
                })
        
        return json.dumps({
            "status": "success",
            "folder_token": folder_token or "根目录",
            "document_count": len(documents),
            "folder_count": len(folders),
            "documents": documents,
            "folders": folders,
            "page_token": page_token,
            "has_more": bool(page_token),
            "note": "如果这些不是你的文档，可能需要指定具体的文件夹 token，或者你的文档在其他子文件夹中"
        }, ensure_ascii=False, indent=2)
        
    except FeishuAPIError as e:
        # 使用 FeishuAPIError 提供的详细错误信息
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. 文档权限（drive:drive）是否已开通 2. folder_token 是否正确（如果指定了）"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        # 其他未预期的错误
        return json.dumps({
            "status": "error",
            "message": f"读取文档列表失败: {str(e)}",
            "suggestion": "请检查：1. 文档权限（drive:drive）是否已开通 2. 网络连接是否正常"
        }, ensure_ascii=False, indent=2)
