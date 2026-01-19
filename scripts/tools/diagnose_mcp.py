#!/usr/bin/env python3
"""MCP Server 诊断脚本

全面测试 MCP Server 的启动、工具注册和执行流程。
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success, message):
    """打印测试结果"""
    symbol = "✓" if success else "✗"
    print(f"{symbol} {message}")

async def test_imports():
    """测试所有必要的导入"""
    print_section("1. 测试导入")
    
    results = []
    
    try:
        from fastmcp import FastMCP
        print_result(True, "FastMCP 导入成功")
        results.append(True)
    except Exception as e:
        print_result(False, f"FastMCP 导入失败: {e}")
        results.append(False)
    
    try:
        from models import MemorySyncToFeishuInput
        print_result(True, "MemorySyncToFeishuInput 导入成功")
        results.append(True)
    except Exception as e:
        print_result(False, f"MemorySyncToFeishuInput 导入失败: {e}")
        results.append(False)
    
    try:
        from tools.memory_sync_to_feishu import memory_sync_to_feishu
        print_result(True, "memory_sync_to_feishu 导入成功")
        results.append(True)
    except Exception as e:
        print_result(False, f"memory_sync_to_feishu 导入失败: {e}")
        results.append(False)
    
    try:
        from sync.feishu_client import FeishuClient, convert_memory_to_feishu_fields
        print_result(True, "FeishuClient 导入成功")
        results.append(True)
    except Exception as e:
        print_result(False, f"FeishuClient 导入失败: {e}")
        results.append(False)
    
    try:
        from storage.db import search_memories, init_db
        print_result(True, "storage.db 导入成功")
        results.append(True)
    except Exception as e:
        print_result(False, f"storage.db 导入失败: {e}")
        results.append(False)
    
    return all(results)

def test_environment():
    """测试环境变量"""
    print_section("2. 测试环境变量")
    
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    
    if not env_path.exists():
        print_result(False, f".env 文件不存在: {env_path}")
        return False
    
    print_result(True, f".env 文件存在: {env_path}")
    
    # 加载环境变量
    load_dotenv(env_path)
    
    required_vars = [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_APP_TOKEN",
        "FEISHU_TABLE_ID"
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 只显示前几个字符，隐藏敏感信息
            masked = value[:4] + "..." if len(value) > 4 else "***"
            print_result(True, f"{var} = {masked}")
        else:
            print_result(False, f"{var} 未设置")
            all_present = False
    
    return all_present

async def test_mcp_server():
    """测试 MCP Server 初始化"""
    print_section("3. 测试 MCP Server 初始化")
    
    try:
        from main import mcp
        print_result(True, "MCP Server 对象创建成功")
        
        # 检查 MCP 对象类型
        from fastmcp import FastMCP
        if isinstance(mcp, FastMCP):
            print_result(True, "MCP 对象类型正确 (FastMCP)")
        else:
            print_result(False, f"MCP 对象类型不正确: {type(mcp)}")
            return False
        
        return True
    except Exception as e:
        print_result(False, f"MCP Server 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_registration():
    """测试工具注册"""
    print_section("4. 测试工具注册")
    
    try:
        from main import mcp
        
        # 尝试获取工具列表（如果 FastMCP 支持）
        # 注意：FastMCP 可能没有直接的 get_tools 方法
        # 我们通过检查装饰器注册的函数来验证
        
        # 检查 sync_to_feishu_tool 是否存在
        if hasattr(mcp, 'sync_to_feishu_tool'):
            print_result(True, "sync_to_feishu_tool 函数存在")
        else:
            # 工具函数可能不在 mcp 对象上，而是在模块作用域
            import main
            if hasattr(main, 'sync_to_feishu_tool'):
                print_result(True, "sync_to_feishu_tool 函数在模块中")
            else:
                print_result(False, "sync_to_feishu_tool 函数未找到")
                return False
        
        # 检查所有工具函数
        # FastMCP 装饰器会将函数包装成 FunctionTool 对象，这是正常的
        import inspect
        from fastmcp.tools.tool import FunctionTool
        import main as main_module
        
        tool_functions = [
            'search_tool',
            'add_tool',
            'get_tool',
            'update_tool',
            'compress_tool',
            'get_project_context_tool',
            'list_projects_tool',
            'stats_tool',
            'sync_to_feishu_tool'
        ]
        
        found_tools = []
        for tool_name in tool_functions:
            if hasattr(main_module, tool_name):
                func = getattr(main_module, tool_name)
                # FastMCP 装饰器会将函数包装成 FunctionTool
                if isinstance(func, FunctionTool):
                    found_tools.append(tool_name)
                    print_result(True, f"{tool_name} 已注册（FunctionTool）")
                elif inspect.iscoroutinefunction(func):
                    found_tools.append(tool_name)
                    print_result(True, f"{tool_name} 已注册（异步函数）")
                else:
                    print_result(False, f"{tool_name} 类型不正确: {type(func)}")
            else:
                print_result(False, f"{tool_name} 未找到")
        
        print(f"\n总计找到 {len(found_tools)}/{len(tool_functions)} 个工具")
        
        return len(found_tools) == len(tool_functions)
        
    except Exception as e:
        print_result(False, f"工具注册检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_execution():
    """测试工具执行"""
    print_section("5. 测试工具执行")
    
    try:
        from models import MemorySyncToFeishuInput
        from tools.memory_sync_to_feishu import memory_sync_to_feishu
        
        # 测试 dry_run 模式
        print("\n测试 dry_run 模式...")
        params = MemorySyncToFeishuInput(dry_run=True, limit=1)
        
        try:
            result = await memory_sync_to_feishu(params)
            print_result(True, "工具执行成功（dry_run）")
            print(f"\n执行结果预览（前200字符）:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        except Exception as e:
            print_result(False, f"工具执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print_result(False, f"工具执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database():
    """测试数据库连接"""
    print_section("6. 测试数据库连接")
    
    try:
        from storage.db import init_db, search_memories
        
        # 初始化数据库
        await init_db()
        print_result(True, "数据库初始化成功")
        
        # 测试搜索（空查询应该返回所有记录）
        results = await search_memories(query="", limit=5)
        print_result(True, f"数据库查询成功，找到 {len(results)} 条记录")
        
        return True
    except Exception as e:
        print_result(False, f"数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_config():
    """测试 MCP 配置文件"""
    print_section("7. 测试 MCP 配置文件")
    
    mcp_config_path = Path.home() / ".cursor" / "mcp.json"
    
    if not mcp_config_path.exists():
        print_result(False, f"MCP 配置文件不存在: {mcp_config_path}")
        return False
    
    print_result(True, f"MCP 配置文件存在: {mcp_config_path}")
    
    try:
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print_result(False, "配置文件中缺少 mcpServers 键")
            return False
        
        if "personal_memory" not in config["mcpServers"]:
            print_result(False, "配置文件中缺少 personal_memory 服务器配置")
            return False
        
        server_config = config["mcpServers"]["personal_memory"]
        print_result(True, "personal_memory 服务器配置存在")
        
        # 检查必要的配置项
        required_keys = ["command", "args", "cwd"]
        for key in required_keys:
            if key in server_config:
                value = server_config[key]
                if key == "args" and isinstance(value, list):
                    print_result(True, f"{key}: {value[0] if value else 'empty'}")
                else:
                    print_result(True, f"{key}: {value}")
            else:
                print_result(False, f"缺少配置项: {key}")
                return False
        
        # 检查路径是否存在
        python_path = Path(server_config["command"])
        if python_path.exists():
            print_result(True, f"Python 路径存在: {python_path}")
        else:
            print_result(False, f"Python 路径不存在: {python_path}")
            return False
        
        main_py_path = Path(server_config["cwd"]) / server_config["args"][0] if server_config["args"] else None
        if main_py_path and main_py_path.exists():
            print_result(True, f"main.py 路径存在: {main_py_path}")
        else:
            print_result(False, f"main.py 路径不存在: {main_py_path}")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print_result(False, f"配置文件 JSON 格式错误: {e}")
        return False
    except Exception as e:
        print_result(False, f"配置文件检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  MCP Server 诊断工具")
    print("=" * 60)
    
    results = {}
    
    # 1. 测试导入
    results["imports"] = await test_imports()
    
    # 2. 测试环境变量
    results["environment"] = test_environment()
    
    # 3. 测试数据库
    results["database"] = await test_database()
    
    # 4. 测试 MCP Server
    results["mcp_server"] = await test_mcp_server()
    
    # 5. 测试工具注册
    results["tool_registration"] = await test_tool_registration()
    
    # 6. 测试工具执行
    results["tool_execution"] = await test_tool_execution()
    
    # 7. 测试 MCP 配置
    results["mcp_config"] = test_mcp_config()
    
    # 总结
    print_section("诊断总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"总计: {total} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {total - passed} 项")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {test_name}")
    
    if all(results.values()):
        print("\n✅ 所有测试通过！MCP Server 应该可以正常工作。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
