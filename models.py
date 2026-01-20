"""Pydantic data models for personal memory system."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class MemoryCategory(str, Enum):
    """Memory entry categories."""
    IDENTITY = "identity"
    GOAL = "goal"
    PLAN = "plan"
    COMMITMENT = "commitment"
    INSIGHT = "insight"
    PRINCIPLE = "principle"
    PATTERN = "pattern"
    PROGRESS = "progress"
    DECISION = "decision"
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    REFERENCE = "reference"
    DIGEST = "digest"


class SourceType(str, Enum):
    """Source types for memory entries."""
    CLAUDE_AI = "claude_ai"
    CURSOR = "cursor"
    MANUAL = "manual"


class ProjectStatus(str, Enum):
    """Project status values."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Source(BaseModel):
    """Source information for memory entries."""
    type: SourceType
    timestamp: str


class MemoryEntry(BaseModel):
    """Memory entry data model."""
    id: str
    created_at: str
    updated_at: str
    
    category: MemoryCategory
    tags: List[str] = Field(default_factory=list)
    
    title: str  # Short title, will be indexed
    content: str  # Full content
    
    project: Optional[str] = None
    importance: int = Field(ge=1, le=5, default=3)
    archived: bool = False
    
    source: Source


class Project(BaseModel):
    """Project data model."""
    id: str
    name: str
    description: str
    baseline_doc: Optional[str] = None
    status: ProjectStatus


# Tool input models
class MemorySearchInput(BaseModel):
    """Input model for memory_search tool."""
    query: str = Field(..., description="搜索关键词")
    category: Optional[str] = Field(None, description="限定类别：goal/plan/commitment/insight/pattern/progress/decision/knowledge/reference/digest")
    project: Optional[str] = Field(None, description="限定项目")
    tags: Optional[List[str]] = Field(None, description="限定标签（AND逻辑，所有标签都必须匹配）")
    limit: Optional[int] = Field(5, description="返回数量，默认5", ge=1, le=50)


class MemoryGetInput(BaseModel):
    """Input model for memory_get tool."""
    id: str = Field(..., description="记忆ID")


class MemoryGetProjectContextInput(BaseModel):
    """Input model for memory_get_project_context tool."""
    project: str = Field(..., description="项目名称")
    include_baseline: Optional[bool] = Field(True, description="是否包含基准文档，默认true")
    recent_limit: Optional[int] = Field(5, description="最近记录数量，默认5")


class MemoryAddInput(BaseModel):
    """Input model for memory_add tool."""
    category: str = Field(..., description="类别（可使用 'auto' 自动判定）")
    title: str = Field(..., description="标题（简短）")
    content: str = Field(..., description="内容")
    project: Optional[str] = Field(None, description="所属项目")
    importance: Optional[int] = Field(3, description="重要性1-5", ge=1, le=5)
    tags: Optional[List[str]] = Field(None, description="标签列表")


class MemoryUpdateInput(BaseModel):
    """Input model for memory_update tool."""
    id: str = Field(..., description="记忆ID")
    title: Optional[str] = Field(None, description="标题")
    content: Optional[str] = Field(None, description="内容")
    archived: Optional[bool] = Field(None, description="是否归档")


class MemoryCompressConversationInput(BaseModel):
    """Input model for memory_compress_conversation tool."""
    summary: str = Field(..., description="对话摘要")
    key_decisions: Optional[List[str]] = Field(None, description="关键决定")
    key_insights: Optional[List[str]] = Field(None, description="关键洞察")
    action_items: Optional[List[str]] = Field(None, description="行动项")
    project: Optional[str] = Field(None, description="所属项目")


class MemoryListProjectsInput(BaseModel):
    """Input model for memory_list_projects tool."""
    status: Optional[str] = Field(None, description="状态过滤：active/paused/completed/archived")


class MemoryStatsInput(BaseModel):
    """Input model for memory_stats tool."""
    project: Optional[str] = Field(None, description="项目名称（可选，用于项目维度统计）")


class MemoryListTagsInput(BaseModel):
    """Input model for memory_list_tags tool."""
    project: Optional[str] = Field(None, description="限定项目（可选，不指定则列出所有标签）")


class MemorySuggestCategoryInput(BaseModel):
    """Input model for memory_suggest_category tool."""
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")


class MemorySummarizeInput(BaseModel):
    """Input model for memory_summarize tool."""
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD（可选）")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD（可选）")
    project: Optional[str] = Field(None, description="限定项目（可选）")
    tags: Optional[List[str]] = Field(None, description="限定标签（可选）")
    save_as_digest: Optional[bool] = Field(False, description="是否保存为digest条目，默认False")


class MemoryCheckConflictsInput(BaseModel):
    """Input model for memory_check_conflicts tool."""
    new_entry_id: Optional[str] = Field(None, description="新条目ID（写入时检测，可选）")
    category: Optional[str] = Field(None, description="限定类别（可选）")
    project: Optional[str] = Field(None, description="限定项目（可选）")
    check_type: Optional[List[str]] = Field(["contradict", "outdated", "duplicate"], description="检测类型：contradict/outdated/duplicate")


class MemoryCheckDuplicatesInput(BaseModel):
    """Input model for memory_check_duplicates tool."""
    category: Optional[str] = Field(None, description="限定类别（可选）")
    project: Optional[str] = Field(None, description="限定项目（可选）")
    similarity_threshold: Optional[float] = Field(0.8, description="相似度阈值 0-1，默认0.8")


class MemoryCheckOutdatedInput(BaseModel):
    """Input model for memory_check_outdated tool."""
    category: Optional[str] = Field(None, description="限定类别（可选）")
    project: Optional[str] = Field(None, description="限定项目（可选）")
    auto_fix: Optional[bool] = Field(False, description="是否自动修复（归档低重要性条目），默认False")


class MemorySyncToFeishuInput(BaseModel):
    """Input model for memory_sync_to_feishu tool."""
    dry_run: Optional[bool] = Field(False, description="是否试运行（不实际同步），默认 False")
    limit: Optional[int] = Field(None, description="限制同步数量（用于测试），默认 None（同步所有）")


class FeishuListTablesInput(BaseModel):
    """Input model for feishu_list_tables tool."""
    app_token: str = Field(..., description="多维表格的 App Token（从URL的 /base/ 后面提取）")


class FeishuReadTableInput(BaseModel):
    """Input model for feishu_read_table tool."""
    app_token: str = Field(..., description="多维表格的 App Token")
    table_id: str = Field(..., description="数据表的 Table ID")
    limit: Optional[int] = Field(10, description="返回记录数量，默认10，最大100", ge=1, le=100)
    show_fields: Optional[bool] = Field(True, description="是否显示字段列表，默认true")


class FeishuCreateDocumentInput(BaseModel):
    """Input model for feishu_create_document tool."""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容（Markdown 格式）")
    folder_token: Optional[str] = Field(None, description="文件夹 token（可选，不指定则创建在根目录）")


class FeishuUpdateDocumentInput(BaseModel):
    """Input model for feishu_update_document tool."""
    file_token: str = Field(..., description="文档 token")
    content: str = Field(..., description="新的文档内容（Markdown 格式）")


class FeishuGetDocumentInput(BaseModel):
    """Input model for feishu_get_document tool."""
    file_token: str = Field(..., description="文档 token")


class FeishuListDocumentsInput(BaseModel):
    """Input model for feishu_list_documents tool."""
    folder_token: Optional[str] = Field(None, description="文件夹 token（可选，不指定则列出根目录）")
    page_size: int = Field(50, description="每页数量，默认50，最大100")
    use_user_token: Optional[bool] = Field(False, description="是否使用用户身份 token（默认 False，使用应用身份 token）")


class FeishuListWikiNodesInput(BaseModel):
    """Input model for feishu_list_wiki_nodes tool."""
    space_id: str = Field(..., description="知识库空间 ID（从知识库 URL 中获取，如 https://my.feishu.cn/wiki/{space_id}）")
    page_size: int = Field(50, description="每页数量，默认50，最大100")


class FeishuSendMessageInput(BaseModel):
    """Input model for feishu_send_message tool."""
    receive_id_type: str = Field(
        ...,
        description="接收者类型：chat_id/open_id/user_id/email",
    )
    receive_id: str = Field(..., description="接收者 ID（与 receive_id_type 对应）")
    msg_type: str = Field("text", description="消息类型，默认 text")
    content: str = Field(..., description="消息内容（text 类型传纯文本；其他类型传 JSON 字符串）")
    use_user_token: Optional[bool] = Field(False, description="是否使用用户身份 token（默认 False）")


class FeishuListChatsInput(BaseModel):
    """Input model for feishu_list_chats tool."""
    page_size: int = Field(50, description="每页数量，默认50，最大100")
    page_token: Optional[str] = Field(None, description="分页 token（可选）")
    use_user_token: Optional[bool] = Field(False, description="是否使用用户身份 token（默认 False）")


class FeishuRealtimeFetchInput(BaseModel):
    """Input model for feishu_realtime_fetch tool."""
    limit: Optional[int] = Field(5, description="返回数量，默认5，最大100", ge=1, le=100)


class FeishuOAuthAuthorizeInput(BaseModel):
    """Input model for feishu_oauth_authorize tool."""
    redirect_uri: str = Field(..., description="授权后的回调地址（需要在飞书开放平台配置）")
    state: Optional[str] = Field(None, description="可选的状态参数，用于防止 CSRF 攻击")


class FeishuOAuthExchangeTokenInput(BaseModel):
    """Input model for feishu_oauth_exchange_token tool."""
    code: str = Field(..., description="OAuth 授权码（从授权回调 URL 中获取）")
