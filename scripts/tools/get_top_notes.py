#!/usr/bin/env python3
"""获取Jason.半山问道点赞最高的3条笔记"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def get_top_notes():
    app_token = 'PDcyb3J5GaPzAtsqVmdcEt5xnEc'
    table_id = 'tblVe01tmcfBwPeO'  # 小红书博主笔记
    
    client = FeishuClient()
    original_app_token = client.app_token
    original_table_id = client.table_id
    
    client.app_token = app_token
    client.table_id = table_id
    
    # 获取所有记录
    all_records = []
    page_token = None
    while True:
        result = await client.list_records(table_id=table_id, page_token=page_token, page_size=100)
        records = result.get('items', [])
        all_records.extend(records)
        page_token = result.get('page_token')
        if not page_token:
            break
    
    # 筛选和排序
    jason_notes = []
    for record in all_records:
        fields = record.get('fields', {})
        blogger = fields.get('博主', '')
        
        # 处理点赞数（可能是数字或字符串）
        likes_raw = fields.get('点赞数', 0)
        if isinstance(likes_raw, str):
            try:
                likes = int(likes_raw)
            except:
                likes = 0
        elif isinstance(likes_raw, (int, float)):
            likes = int(likes_raw)
        else:
            likes = 0
        
        if blogger == 'Jason.半山问道':
            jason_notes.append({
                'title': fields.get('标题', 'N/A'),
                'likes': likes,
                'link': fields.get('笔记链接', {}).get('link', 'N/A') if isinstance(fields.get('笔记链接'), dict) else fields.get('笔记链接', 'N/A'),
                'cover_link': fields.get('封面链接', 'N/A'),
                'record_id': record.get('record_id', 'N/A')
            })
    
    # 按点赞数排序
    jason_notes.sort(key=lambda x: x['likes'], reverse=True)
    
    # 返回前3条
    top3 = jason_notes[:3]
    
    print(json.dumps({
        'status': 'success',
        'total_notes': len(jason_notes),
        'top_3': top3
    }, ensure_ascii=False, indent=2))
    
    client.app_token = original_app_token
    client.table_id = original_table_id


if __name__ == "__main__":
    asyncio.run(get_top_notes())
