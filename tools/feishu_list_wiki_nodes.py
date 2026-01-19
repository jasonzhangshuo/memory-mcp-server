"""列出飞书知识库（Wiki）中的文档列表"""

import json
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuListWikiNodesInput


async def feishu_list_wiki_nodes(params: FeishuListWikiNodesInput) -> str:
    """列出飞书知识库中的文档列表。
    
    获取指定知识库空间中的所有节点（文档）列表。
    
    Args:
        params: 参数对象
            - space_id: 知识库空间 ID（从知识库 URL 中获取，如 https://my.feishu.cn/wiki/{space_id}）
            - page_size: 每页数量，默认50，最大100
    
    Returns:
        JSON格式的节点列表，包括文档名称、类型、token等信息
    """
    try:
        # 创建客户端
        client = FeishuClient()
        
        # 获取知识库节点列表
        result = await client.list_wiki_nodes(
            space_id=params.space_id,
            page_size=params.page_size
        )
        
        nodes = result.get("items", [])
        page_token = result.get("page_token")
        
        # 格式化结果
        documents = []
        for node in nodes:
            obj_type = node.get("obj_type", "N/A")
            obj_token = node.get("obj_token", "N/A")
            node_token = node.get("node_token", "N/A")
            title = node.get("title", "N/A")
            
            # 根据类型构建 URL
            url = None
            if obj_type == "doc":
                url = f"https://my.feishu.cn/docs/{obj_token}"
            elif obj_type == "docx":
                url = f"https://my.feishu.cn/docx/{obj_token}"
            elif obj_type == "sheet":
                url = f"https://my.feishu.cn/sheets/{obj_token}"
            elif obj_type == "bitable":
                url = f"https://my.feishu.cn/base/{obj_token}"
            
            documents.append({
                "node_token": node_token,
                "obj_token": obj_token,
                "obj_type": obj_type,
                "title": title,
                "url": url
            })
        
        return json.dumps({
            "status": "success",
            "space_id": params.space_id,
            "node_count": len(documents),
            "nodes": documents,
            "page_token": page_token,
            "has_more": bool(page_token)
        }, ensure_ascii=False, indent=2)
        
    except FeishuAPIError as e:
        # 使用 FeishuAPIError 提供的详细错误信息
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. 知识库权限（wiki:wiki.readonly）是否已开通 2. space_id 是否正确"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        # 其他未预期的错误
        return json.dumps({
            "status": "error",
            "message": f"读取知识库文档列表失败: {str(e)}",
            "suggestion": "请检查：1. 知识库权限（wiki:wiki.readonly）是否已开通 2. space_id 是否正确 3. 网络连接是否正常"
        }, ensure_ascii=False, indent=2)
