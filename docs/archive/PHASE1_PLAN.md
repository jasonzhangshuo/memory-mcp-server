# Phase 1 开发计划

## 目标

实现完整的 MCP Server，包括所有核心工具和项目支持功能。

## 开发任务

### 1. 实现核心工具

#### 1.1 memory_get - 获取记忆详情
- [ ] 创建 `tools/memory_get.py`
- [ ] 实现根据 ID 获取完整记忆内容
- [ ] 在 main.py 中注册工具

#### 1.2 memory_update - 更新记忆
- [ ] 创建 `tools/memory_update.py`
- [ ] 实现更新记忆的标题、内容、归档状态
- [ ] 更新数据库和 JSON 文件
- [ ] 在 main.py 中注册工具

#### 1.3 memory_compress_conversation - 压缩保存对话
- [ ] 创建 `tools/memory_compress_conversation.py`
- [ ] 实现对话摘要保存
- [ ] 支持关键决定、洞察、行动项
- [ ] 在 main.py 中注册工具

### 2. 实现项目支持

#### 2.1 项目数据模型
- [ ] 在 models.py 中添加 Project 相关模型
- [ ] 在 storage/db.py 中实现项目表

#### 2.2 memory_get_project_context - 项目上下文
- [ ] 创建 `tools/memory_get_project_context.py`
- [ ] 实现加载项目相关记忆
- [ ] 支持基准文档加载
- [ ] 在 main.py 中注册工具

#### 2.3 memory_list_projects - 列出项目
- [ ] 创建 `tools/memory_list_projects.py`
- [ ] 实现项目列表查询
- [ ] 支持状态过滤
- [ ] 在 main.py 中注册工具

#### 2.4 memory_stats - 统计信息
- [ ] 创建 `tools/memory_stats.py`
- [ ] 实现记忆统计（总数、分类统计等）
- [ ] 支持项目维度统计
- [ ] 在 main.py 中注册工具

### 3. 优化存储层

#### 3.1 优化 FTS5 全文搜索
- [ ] 修复 FTS5 搜索功能（替代 LIKE）
- [ ] 实现正确的 FTS5 表结构
- [ ] 测试搜索性能

#### 3.2 项目表实现
- [ ] 创建 projects 表
- [ ] 实现项目 CRUD 操作
- [ ] 关联记忆和项目

### 4. 项目初始化

#### 4.1 2026-baseline 种子数据
- [ ] 创建项目数据
- [ ] 创建基准文档
- [ ] 初始化项目相关记忆

### 5. 更新文档

#### 5.1 更新 SKILL.md
- [ ] 添加新工具的使用说明
- [ ] 更新触发规则

#### 5.2 更新 README
- [ ] 更新功能列表
- [ ] 添加新工具说明

## 验收标准

- 所有核心工具正常工作
- 项目支持功能正常
- 检索延迟 <500ms
- 所有工具测试通过

## 时间估算

- Day 1-2: 实现核心工具（memory_get, memory_update, compress_conversation）
- Day 3-4: 实现项目支持功能
- Day 5: 优化 FTS5 搜索
- Day 6: 测试和优化
