#!/usr/bin/env python3
"""检查飞书多维表格中的记录"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def check_records():
    """检查记录"""
    print("=" * 60)
    print("📊 检查飞书多维表格中的记录")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 获取所有记录
        print("📖 获取所有记录...")
        all_records = []
        page_token = None
        
        while True:
            result = await client.list_records(page_token=page_token, page_size=100)
            records = result.get("items", [])
            all_records.extend(records)
            
            page_token = result.get("page_token")
            if not page_token:
                break
        
        print(f"   ✅ 找到 {len(all_records)} 条记录")
        print()
        
        # 显示前10条记录
        print("📝 前10条记录:")
        for i, record in enumerate(all_records[:10], 1):
            fields = record.get("fields", {})
            title = fields.get("标题", "N/A")
            memory_id = fields.get("记忆ID", "N/A")
            created_time = fields.get("创建时间", "N/A")
            print(f"   {i}. {title}")
            print(f"      记忆ID: {memory_id[:20]}...")
            print(f"      创建时间: {created_time}")
            print()
        
        # 检查是否有空记录
        empty_count = sum(1 for r in all_records if not r.get("fields", {}).get("标题"))
        if empty_count > 0:
            print(f"⚠️  发现 {empty_count} 条空记录（可能是在前面的行）")
        
        print("=" * 60)
        print("💡 提示:")
        print("   如果数据不是从第一行开始，可能是:")
        print("   1. 视图排序设置（按创建时间倒序）")
        print("   2. 视图筛选条件")
        print("   3. 前面有手动添加的空记录")
        print()
        print("   解决方法:")
        print("   1. 在飞书多维表格中调整视图排序")
        print("   2. 清除筛选条件")
        print("   3. 删除前面的空行")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_records())
