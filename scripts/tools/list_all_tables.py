#!/usr/bin/env python3
"""列出飞书多维表格中的所有数据表"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def list_all_tables():
    """列出所有表格"""
    print("=" * 60)
    print("📋 列出飞书多维表格中的所有数据表")
    print("=" * 60)
    print()
    
    # 从URL提取的信息
    xiaohongshu_app_token = "PDcyb3J5GaPzAtsqVmdcEt5xnEc"
    
    try:
        # 使用现有的应用配置
        client = FeishuClient()
        
        # 临时使用新的表格配置
        original_app_token = client.app_token
        
        client.app_token = xiaohongshu_app_token
        
        print(f"📋 多维表格信息:")
        print(f"   App Token: {xiaohongshu_app_token}")
        print()
        
        # 获取所有表格
        print("📊 获取所有数据表...")
        tables = await client.list_tables()
        
        print(f"   ✅ 找到 {len(tables)} 个数据表:")
        print()
        
        for i, table in enumerate(tables, 1):
            table_name = table.get('name', 'N/A')
            table_id = table.get('table_id', 'N/A')
            revision = table.get('revision', 'N/A')
            
            print(f"   【表格 {i}】")
            print(f"      名称: {table_name}")
            print(f"      Table ID: {table_id}")
            print(f"      版本: {revision}")
            print()
        
        # 恢复原始配置
        client.app_token = original_app_token
        
        print("=" * 60)
        print("✅ 完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(list_all_tables())
