#!/usr/bin/env python3
"""Personal Memory MCP Server.

This server provides tools for managing personal memories, goals, commitments, and insights.
"""

from fastmcp import FastMCP
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
# This ensures environment variables are available when MCP Server starts
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    # Also set working directory to project root for relative path resolution
    os.chdir(project_root)

from models import (
    MemorySearchInput,
    MemoryAddInput,
    MemoryGetInput,
    MemoryUpdateInput,
    MemoryCompressConversationInput,
    MemoryGetProjectContextInput,
    MemoryListProjectsInput,
    MemoryStatsInput,
    MemoryListTagsInput,
    MemorySummarizeInput,
    MemorySuggestCategoryInput,
    MemoryCheckConflictsInput,
    MemoryCheckDuplicatesInput,
    MemoryCheckOutdatedInput,
    MemorySyncToFeishuInput,
    FeishuListTablesInput,
    FeishuReadTableInput,
    FeishuCreateDocumentInput,
    FeishuUpdateDocumentInput,
    FeishuGetDocumentInput,
    FeishuListDocumentsInput,
    FeishuListWikiNodesInput,
    FeishuSendMessageInput,
    FeishuListChatsInput,
    FeishuOAuthAuthorizeInput,
    FeishuOAuthExchangeTokenInput,
)
from tools.memory_search import memory_search
from tools.memory_add import memory_add
from tools.memory_get import memory_get
from tools.memory_update import memory_update
from tools.memory_compress_conversation import memory_compress_conversation
from tools.memory_get_project_context import memory_get_project_context
from tools.memory_list_projects import memory_list_projects
from tools.memory_stats import memory_stats
from tools.memory_list_tags import memory_list_tags
from tools.memory_summarize import memory_summarize
from tools.memory_suggest_category import memory_suggest_category
from tools.memory_check_conflicts import memory_check_conflicts
from tools.memory_check_duplicates import memory_check_duplicates
from tools.memory_check_outdated import memory_check_outdated
from tools.memory_sync_to_feishu import memory_sync_to_feishu
from tools.feishu_list_tables import feishu_list_tables
from tools.feishu_read_table import feishu_read_table
from tools.feishu_create_document import feishu_create_document
from tools.feishu_update_document import feishu_update_document
from tools.feishu_send_message import feishu_send_message
from tools.feishu_list_chats import feishu_list_chats
from tools.feishu_get_document import feishu_get_document
from tools.feishu_list_documents import feishu_list_documents
from tools.feishu_list_wiki_nodes import feishu_list_wiki_nodes
from tools.feishu_oauth_authorize import feishu_oauth_authorize
from tools.feishu_oauth_exchange_token import feishu_oauth_exchange_token
from storage.db import init_db

# Initialize MCP server
mcp = FastMCP("personal_memory")

# Initialize database - will be called before server starts
_db_initialized = False

async def ensure_db_initialized():
    """Ensure database is initialized."""
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True


# Register tools
@mcp.tool(
    name="memory_search",
    annotations={
        "title": "搜索历史记忆",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def search_tool(
    query: str,
    category: str = None,
    project: str = None,
    tags: list = None,
    limit: int = 5
) -> str:
    """搜索历史记忆。
    
    根据关键词、类别、项目和标签搜索记忆条目。
    支持全文搜索，返回匹配的记忆列表。
    
    Args:
        query: 搜索关键词
        category: 限定类别（goal/plan/commitment/insight/pattern/progress/decision/knowledge/reference/digest）
        project: 限定项目名称
        tags: 限定标签列表（AND逻辑，所有标签都必须匹配）
        limit: 返回数量，默认5，最大50
    """
    await ensure_db_initialized()
    # 创建参数对象
    params = MemorySearchInput(
        query=query,
        category=category,
        project=project,
        tags=tags,
        limit=limit
    )
    return await memory_search(params)


@mcp.tool(
    name="memory_add",
    annotations={
        "title": "添加新记忆",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def add_tool(
    category: str,
    title: str,
    content: str,
    project: str = None,
    importance: int = 3,
    tags: list = None
) -> str:
    """添加新记忆。
    
    创建一个新的记忆条目，保存到数据库和JSON文件。
    自动生成ID和时间戳。
    
    Args:
        category: 类别（包括新增：knowledge/reference/digest）
        title: 标题（简短）
        content: 内容
        project: 所属项目（可选）
        importance: 重要性1-5，默认3
        tags: 标签列表（可选）
    """
    await ensure_db_initialized()
    params = MemoryAddInput(
        category=category,
        title=title,
        content=content,
        project=project,
        importance=importance,
        tags=tags or []
    )
    return await memory_add(params)


@mcp.tool(
    name="memory_get",
    annotations={
        "title": "获取记忆详情",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_tool(id: str) -> str:
    """获取记忆详情。
    
    根据记忆ID获取完整的记忆条目信息。
    返回记忆的完整内容，包括标题、内容、类别、时间戳等。
    
    Args:
        id: 记忆ID
    """
    await ensure_db_initialized()
    params = MemoryGetInput(id=id)
    return await memory_get(params)


@mcp.tool(
    name="memory_update",
    annotations={
        "title": "更新记忆",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def update_tool(
    id: str,
    title: str = None,
    content: str = None,
    archived: bool = None
) -> str:
    """更新记忆。
    
    更新现有记忆的标题、内容或归档状态。
    只更新提供的字段，其他字段保持不变。
    
    Args:
        id: 记忆ID
        title: 标题（可选）
        content: 内容（可选）
        archived: 是否归档（可选）
    """
    await ensure_db_initialized()
    params = MemoryUpdateInput(
        id=id,
        title=title,
        content=content,
        archived=archived
    )
    return await memory_update(params)


@mcp.tool(
    name="memory_compress_conversation",
    annotations={
        "title": "压缩保存对话",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def compress_tool(
    summary: str,
    key_decisions: list = None,
    key_insights: list = None,
    action_items: list = None,
    project: str = None
) -> str:
    """压缩保存对话。
    
    将对话内容压缩为摘要，并提取关键决定、洞察和行动项。
    保存为 conversation 类别的记忆条目。
    
    Phase 2 策略：在冷启动阶段（前2周），偏向多记录，确保不遗漏重要信息。
    尽量提取所有关键决定、洞察和行动项，宁可多记录也不要遗漏。
    
    Args:
        summary: 对话摘要
        key_decisions: 关键决定（可选）
        key_insights: 关键洞察（可选）
        action_items: 行动项（可选）
        project: 所属项目（可选）
    """
    await ensure_db_initialized()
    params = MemoryCompressConversationInput(
        summary=summary,
        key_decisions=key_decisions,
        key_insights=key_insights,
        action_items=action_items,
        project=project
    )
    return await memory_compress_conversation(params)


@mcp.tool(
    name="memory_get_project_context",
    annotations={
        "title": "加载项目上下文",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_project_context_tool(
    project: str,
    include_baseline: bool = True,
    recent_limit: int = 5
) -> str:
    """加载项目上下文。
    
    获取项目相关的记忆和基准文档。
    返回项目的基准文档和最近的相关记忆。
    
    Args:
        project: 项目名称
        include_baseline: 是否包含基准文档，默认true
        recent_limit: 最近记录数量，默认5
    """
    await ensure_db_initialized()
    params = MemoryGetProjectContextInput(
        project=project,
        include_baseline=include_baseline,
        recent_limit=recent_limit
    )
    return await memory_get_project_context(params)


@mcp.tool(
    name="memory_list_projects",
    annotations={
        "title": "列出项目",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_projects_tool(status: str = None) -> str:
    """列出项目。
    
    列出所有项目，支持按状态过滤。
    返回项目列表，包括名称、描述、状态等信息。
    
    Args:
        status: 状态过滤（active/paused/completed/archived），可选
    """
    await ensure_db_initialized()
    params = MemoryListProjectsInput(status=status)
    return await memory_list_projects(params)


@mcp.tool(
    name="memory_stats",
    annotations={
        "title": "获取统计信息",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def stats_tool(project: str = None) -> str:
    """获取统计信息。
    
    获取记忆系统的统计信息，包括总数、分类统计等。
    支持按项目维度统计。
    
    Args:
        project: 项目名称（可选，用于项目维度统计）
    """
    await ensure_db_initialized()
    params = MemoryStatsInput(project=project)
    return await memory_stats(params)


@mcp.tool(
    name="memory_list_tags",
    annotations={
        "title": "列出所有标签",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_tags_tool(project: str = None) -> str:
    """列出所有标签及其使用次数。
    
    根据项目过滤标签列表，返回每个标签的名称和使用次数。
    用于了解知识库的标签体系。
    
    Args:
        project: 项目名称（可选，不指定则列出所有标签）
    """
    await ensure_db_initialized()
    params = MemoryListTagsInput(project=project)
    return await memory_list_tags(params)


@mcp.tool(
    name="memory_suggest_category",
    annotations={
        "title": "智能建议分类",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def suggest_category_tool(title: str, content: str) -> str:
    """智能建议分类（insight vs knowledge）。
    
    分析内容特征，自动判断应该归类为个人记忆（insight）还是知识库（knowledge）。
    使用关键词检测和内容特征分析。
    
    Args:
        title: 标题
        content: 内容
    
    Returns:
        JSON格式的建议结果，包括建议分类、置信度、原因等
    """
    await ensure_db_initialized()
    params = MemorySuggestCategoryInput(title=title, content=content)
    return await memory_suggest_category(params)


@mcp.tool(
    name="memory_summarize",
    annotations={
        "title": "生成阶段性总结",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def summarize_tool(
    start_date: str = None,
    end_date: str = None,
    project: str = None,
    tags: list = None,
    save_as_digest: bool = False
) -> str:
    """生成阶段性总结。
    
    按日期范围/项目/标签检索记忆，统计高频主题和标签，提取关键洞察，
    生成结构化总结文本。可选保存为digest类别条目。
    
    Args:
        start_date: 开始日期 YYYY-MM-DD（可选）
        end_date: 结束日期 YYYY-MM-DD（可选）
        project: 限定项目（可选）
        tags: 限定标签列表（可选）
        save_as_digest: 是否保存为digest条目，默认False
    """
    await ensure_db_initialized()
    params = MemorySummarizeInput(
        start_date=start_date,
        end_date=end_date,
        project=project,
        tags=tags,
        save_as_digest=save_as_digest
    )
    return await memory_summarize(params)


@mcp.tool(
    name="memory_check_conflicts",
    annotations={
        "title": "检测冲突内容",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def check_conflicts_tool(
    new_entry_id: str = None,
    category: str = None,
    project: str = None,
    check_type: list = None
) -> str:
    """检测冲突内容。
    
    检测内容矛盾、过时和重复内容。
    如果提供了 new_entry_id，检测新内容与现有内容的冲突。
    否则，全面扫描指定范围。
    
    Args:
        new_entry_id: 新条目ID（写入时检测，可选）
        category: 限定类别（可选）
        project: 限定项目（可选）
        check_type: 检测类型列表（contradict/outdated/duplicate），默认全部
    """
    await ensure_db_initialized()
    params = MemoryCheckConflictsInput(
        new_entry_id=new_entry_id,
        category=category,
        project=project,
        check_type=check_type or ["contradict", "outdated", "duplicate"]
    )
    return await memory_check_conflicts(params)


@mcp.tool(
    name="memory_check_duplicates",
    annotations={
        "title": "检测重复内容",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def check_duplicates_tool(
    category: str = None,
    project: str = None,
    similarity_threshold: float = 0.8
) -> str:
    """检测重复内容。
    
    使用文本相似度算法找出重复条目。
    
    Args:
        category: 限定类别（可选）
        project: 限定项目（可选）
        similarity_threshold: 相似度阈值（0-1），默认0.8
    """
    await ensure_db_initialized()
    params = MemoryCheckDuplicatesInput(
        category=category,
        project=project,
        similarity_threshold=similarity_threshold
    )
    return await memory_check_duplicates(params)


@mcp.tool(
    name="memory_check_outdated",
    annotations={
        "title": "检测老旧内容",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def check_outdated_tool(
    category: str = None,
    project: str = None,
    auto_fix: bool = False
) -> str:
    """检测老旧内容。
    
    检测目标（goal）是否已过期、计划（plan）是否已过期、
    知识库条目是否长期未访问。
    
    Args:
        category: 限定类别（可选）
        project: 限定项目（可选）
        auto_fix: 是否自动修复（归档低重要性条目），默认False
    """
    await ensure_db_initialized()
    params = MemoryCheckOutdatedInput(
        category=category,
        project=project,
        auto_fix=auto_fix
    )
    return await memory_check_outdated(params)


@mcp.tool(
    name="memory_sync_to_feishu",
    annotations={
        "title": "同步到飞书多维表格",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def sync_to_feishu_tool(
    dry_run: bool = False,
    limit: int = None
) -> str:
    """同步记忆数据到飞书多维表格。
    
    将本地记忆数据同步到飞书多维表格，实现可视化查看和数据备份。
    支持增量同步，自动跳过已同步的记录。
    
    使用场景：
    - 用户说"同步到飞书"、"把记忆同步到飞书"
    - 用户说"更新飞书数据"
    - 用户询问"飞书数据是最新的吗"时，可以主动同步
    
    Args:
        dry_run: 是否试运行（不实际同步），默认 False
        limit: 限制同步数量（用于测试），默认 None（同步所有）
    """
    await ensure_db_initialized()
    params = MemorySyncToFeishuInput(dry_run=dry_run, limit=limit)
    return await memory_sync_to_feishu(params)


@mcp.tool(
    name="feishu_list_tables",
    annotations={
        "title": "列出飞书多维表格中的所有数据表",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_tables_tool(app_token: str) -> str:
    """列出飞书多维表格中的所有数据表。
    
    获取指定多维表格中的所有数据表列表，包括表格名称和ID。
    用于查看一个多维表格中有哪些数据表。
    
    使用场景：
    - 用户说"看看这个飞书表格有哪些表"、"列出所有表格"
    - 用户提供飞书表格链接，需要查看表格结构
    
    Args:
        app_token: 多维表格的 App Token（从URL的 /base/ 后面提取）
    """
    params = FeishuListTablesInput(app_token=app_token)
    return await feishu_list_tables(params)


@mcp.tool(
    name="feishu_read_table",
    annotations={
        "title": "读取飞书多维表格中的数据",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def read_table_tool(
    app_token: str,
    table_id: str,
    limit: int = 10,
    show_fields: bool = True
) -> str:
    """读取飞书多维表格中的数据。
    
    读取指定表格的字段列表和记录数据。
    支持分页读取，可以指定返回记录数量。
    
    使用场景：
    - 用户说"读取我的小红书笔记"、"看看采集库的数据"
    - 用户提供表格链接，需要查看数据内容
    - 需要从飞书表格导入数据到记忆系统
    
    Args:
        app_token: 多维表格的 App Token
        table_id: 数据表的 Table ID
        limit: 返回记录数量，默认10，最大100
        show_fields: 是否显示字段列表，默认true
    """
    params = FeishuReadTableInput(
        app_token=app_token,
        table_id=table_id,
        limit=limit,
        show_fields=show_fields
    )
    return await feishu_read_table(params)


@mcp.tool(
    name="feishu_create_document",
    annotations={
        "title": "创建飞书文档",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def create_document_tool(
    title: str,
    content: str,
    folder_token: str = None
) -> str:
    """创建飞书文档并写入内容。
    
    创建新的飞书文档，并写入指定内容。
    支持 Markdown 格式内容。
    
    使用场景：
    - 用户说"创建一份报告文档"、"生成文档"、"保存为文档"
    - 用户说"把这周的记忆总结成文档"
    - 需要将对话内容或数据保存为文档
    
    Args:
        title: 文档标题
        content: 文档内容（Markdown 格式）
        folder_token: 文件夹 token（可选，不指定则创建在根目录）
    """
    params = FeishuCreateDocumentInput(
        title=title,
        content=content,
        folder_token=folder_token
    )
    return await feishu_create_document(params)


@mcp.tool(
    name="feishu_update_document",
    annotations={
        "title": "更新飞书文档内容",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def update_document_tool(
    file_token: str,
    content: str
) -> str:
    """更新飞书文档内容。
    
    更新已有飞书文档的内容。
    支持 Markdown 格式内容。
    
    使用场景：
    - 用户说"更新我的周报"、"修改文档"、"编辑文档"
    - 需要更新已有文档的内容
    
    Args:
        file_token: 文档 token
        content: 新的文档内容（Markdown 格式）
    """
    params = FeishuUpdateDocumentInput(
        file_token=file_token,
        content=content
    )
    return await feishu_update_document(params)


@mcp.tool(
    name="feishu_send_message",
    annotations={
        "title": "发送飞书 IM 消息",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def send_message_tool(
    receive_id_type: str,
    receive_id: str,
    content: str,
    msg_type: str = "text",
    use_user_token: bool = False
) -> str:
    """发送飞书 IM 消息。

    使用场景：
    - 推送每日提醒、事项、复盘提示
    - 机器人定时消息推送

    Args:
        receive_id_type: 接收者类型（chat_id/open_id/user_id/email）
        receive_id: 对应接收者 ID
        content: 消息内容（text 传纯文本；其他类型传 JSON 字符串）
        msg_type: 消息类型，默认 text
        use_user_token: 是否使用用户身份 token（默认 False）
    """
    params = FeishuSendMessageInput(
        receive_id_type=receive_id_type,
        receive_id=receive_id,
        msg_type=msg_type,
        content=content,
        use_user_token=use_user_token
    )
    return await feishu_send_message(params)


@mcp.tool(
    name="feishu_list_chats",
    annotations={
        "title": "列出飞书群聊列表",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_chats_tool(
    page_size: int = 50,
    page_token: str = None,
    use_user_token: bool = False
) -> str:
    """列出当前应用可见的群聊列表。

    Args:
        page_size: 每页数量，默认50
        page_token: 分页 token（可选）
        use_user_token: 是否使用用户身份 token（默认 False）
    """
    params = FeishuListChatsInput(
        page_size=page_size,
        page_token=page_token,
        use_user_token=use_user_token
    )
    return await feishu_list_chats(params)


@mcp.tool(
    name="feishu_get_document",
    annotations={
        "title": "读取飞书文档信息",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_document_tool(file_token: str) -> str:
    """读取飞书文档信息和内容。
    
    获取飞书文档的基本信息和内容。
    
    使用场景：
    - 用户说"读取文档内容"、"查看文档"
    - 需要获取文档信息以便更新
    
    Args:
        file_token: 文档 token
    """
    params = FeishuGetDocumentInput(file_token=file_token)
    return await feishu_get_document(params)


@mcp.tool(
    name="feishu_list_documents",
    annotations={
        "title": "列出飞书文档列表",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_documents_tool(
    folder_token: str = None,
    page_size: int = 50,
    use_user_token: bool = False
) -> str:
    """列出飞书文档列表。
    
    获取指定文件夹中的文档列表，包括文档名称、类型、创建时间等信息。
    
    使用场景：
    - 用户说"列出我的文档"、"查看文档列表"、"有哪些文档"
    - 需要查看指定文件夹中的文档
    
    Args:
        folder_token: 文件夹 token（可选，不指定则列出根目录）
        page_size: 每页数量，默认50，最大100
        use_user_token: 是否使用用户身份 token（默认 False，使用应用身份 token）
    """
    params = FeishuListDocumentsInput(
        folder_token=folder_token,
        page_size=page_size,
        use_user_token=use_user_token
    )
    return await feishu_list_documents(params)


@mcp.tool(
    name="feishu_list_wiki_nodes",
    annotations={
        "title": "列出飞书知识库中的文档列表",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_wiki_nodes_tool(
    space_id: str,
    page_size: int = 50
) -> str:
    """列出飞书知识库中的文档列表。
    
    获取指定知识库空间中的所有节点（文档）列表。
    
    使用场景：
    - 用户说"列出我的知识库文档"、"查看知识库内容"、"有哪些文档"
    - 需要查看指定知识库中的文档
    
    Args:
        space_id: 知识库空间 ID（从知识库 URL 中获取，如 https://my.feishu.cn/wiki/{space_id}）
        page_size: 每页数量，默认50，最大100
    """
    params = FeishuListWikiNodesInput(
        space_id=space_id,
        page_size=page_size
    )
    return await feishu_list_wiki_nodes(params)


@mcp.tool(
    name="feishu_oauth_authorize",
    annotations={
        "title": "生成飞书 OAuth 授权链接",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def oauth_authorize_tool(
    redirect_uri: str,
    state: str = None
) -> str:
    """生成飞书 OAuth 授权链接。
    
    用户需要：
    1. 访问返回的授权链接
    2. 完成授权后，从回调 URL 中获取 code 参数
    3. 使用 feishu_oauth_exchange_token 工具将 code 换取 user_access_token
    
    使用场景：
    - 用户说"授权访问我的文档"、"获取用户权限"、"OAuth 授权"
    - 需要获取用户身份 token 以访问用户的文档库
    
    Args:
        redirect_uri: 授权后的回调地址（需要在飞书开放平台配置）
        state: 可选的状态参数，用于防止 CSRF 攻击
    """
    params = FeishuOAuthAuthorizeInput(
        redirect_uri=redirect_uri,
        state=state
    )
    return await feishu_oauth_authorize(params)


@mcp.tool(
    name="feishu_oauth_exchange_token",
    annotations={
        "title": "使用 OAuth 授权码换取 user_access_token",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def oauth_exchange_token_tool(code: str) -> str:
    """使用 OAuth 授权码换取 user_access_token。
    
    使用场景：
    - 用户说"换取 token"、"完成授权"、"获取用户 token"
    - 在完成 OAuth 授权后，使用授权码换取访问令牌
    
    Args:
        code: OAuth 授权码（从授权回调 URL 中获取）
    """
    params = FeishuOAuthExchangeTokenInput(code=code)
    return await feishu_oauth_exchange_token(params)


if __name__ == "__main__":
    mcp.run()
