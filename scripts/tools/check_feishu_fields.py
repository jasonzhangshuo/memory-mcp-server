#!/usr/bin/env python3
"""检查飞书多维表格字段结构"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def check_fields():
    """检查字段结构"""
    print("=" * 60)
    print("📋 检查飞书多维表格字段结构")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 获取字段列表
        print("📊 当前字段列表:")
        fields = await client.get_table_fields()
        
        if not fields:
            print("   ⚠️  没有找到字段，需要创建字段")
        else:
            print(f"   ✅ 找到 {len(fields)} 个字段:")
            print()
            for i, field in enumerate(fields, 1):
                field_name = field.get('field_name', 'N/A')
                field_type = field.get('type', 'N/A')
                field_id = field.get('field_id', 'N/A')
                print(f"   {i}. {field_name}")
                print(f"      类型: {field_type}")
                print(f"      ID: {field_id}")
                print()
        
        # 检查必需字段
        print("=" * 60)
        print("📝 需要的字段列表")
        print("=" * 60)
        print()
        
        required_fields = {
            "记忆ID": "文本",
            "标题": "文本",
            "内容": "多行文本",
            "分类": "单选",
            "标签": "多选",
            "项目": "文本",
            "重要性": "数字",
            "创建时间": "日期时间",
            "更新时间": "日期时间",
            "是否归档": "复选框",
            "来源类型": "单选"
        }
        
        existing_field_names = {f.get('field_name') for f in fields}
        
        print("必需字段:")
        for field_name, field_type in required_fields.items():
            if field_name in existing_field_names:
                print(f"   ✅ {field_name} ({field_type})")
            else:
                print(f"   ❌ {field_name} ({field_type}) - 需要创建")
        
        print()
        print("=" * 60)
        
        if len(existing_field_names) < len(required_fields):
            print("⚠️  缺少必需字段，需要在飞书多维表格中创建")
            print()
            print("操作步骤:")
            print("1. 打开飞书多维表格")
            print("2. 点击右上角'添加字段'")
            print("3. 按照上面的列表创建字段")
            print("4. 字段名称必须完全匹配（区分大小写）")
        else:
            print("✅ 所有必需字段都已创建")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_fields())
