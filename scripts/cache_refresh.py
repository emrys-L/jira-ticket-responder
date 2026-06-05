#!/usr/bin/env python3
"""
缓存刷新模块
功能：从 Jira API 获取最新工单数据，更新本地缓存
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 导入配置
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import JIRA_CONFIG, BASE_URL, HEADERS


def fetch_issue_details(issue_key: str) -> Optional[Dict]:
    """从 Jira API 获取工单详情"""
    url = f"{BASE_URL}/issue/{issue_key}"
    params = {
        "expand": "changelog",
        "fields": "*all"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, auth=(JIRA_CONFIG["email"], JIRA_CONFIG["api_token"]), timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ❌ 获取 {issue_key} 失败：{e}")
        return None


def save_to_cache(issue_key: str, issue_data: Dict):
    """保存工单数据到缓存"""
    # 确定项目目录
    for project in ['EEESC', 'ESESC', 'ETESC']:
        if issue_key.startswith(project):
            cache_dir = Path(f'data/raw_issues/{project}')
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_file = cache_dir / f"{issue_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(issue_data, f, ensure_ascii=False, indent=2)
            
            # 提取基本信息
            fields = issue_data.get('fields', {})
            status = fields.get('status', {}).get('name', 'Unknown')
            updated = issue_data.get('fields', {}).get('updated', '')[:10]
            comments = fields.get('comment', {}).get('comments', [])
            
            print(f"  ✅ {issue_key}: 已更新 (状态：{status}, 更新：{updated}, 评论：{len(comments)}条)")
            return
    
    print(f"  ⚠️  {issue_key}: 未知项目，跳过")


def refresh_cache(issue_keys: List[str], force: bool = False) -> Dict[str, bool]:
    """
    批量刷新缓存
    
    Args:
        issue_keys: 工单号列表
        force: 是否强制刷新（否则只刷新超过 7 天未更新的）
    
    Returns:
        {issue_key: success}
    """
    results = {}
    
    for i, issue_key in enumerate(issue_keys, 1):
        print(f"[{i}/{len(issue_keys)}] 刷新 {issue_key}...", end=" ")
        
        # 检查是否需要刷新
        cache_file = None
        for project in ['EEESC', 'ESESC', 'ETESC']:
            if issue_key.startswith(project):
                cache_file = Path(f'data/raw_issues/{project}/{issue_key}.json')
                break
        
        if not force and cache_file and cache_file.exists():
            # 检查缓存年龄
            cache_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_days = (datetime.now() - cache_mtime).days
            
            if age_days < 7:
                # 缓存小于 7 天，跳过
                print(f"⏭️  跳过（缓存{age_days}天）")
                results[issue_key] = True
                continue
        
        # 从 Jira API 获取最新数据
        issue_data = fetch_issue_details(issue_key)
        
        if issue_data:
            save_to_cache(issue_key, issue_data)
            results[issue_key] = True
        else:
            results[issue_key] = False
    
    return results


def main():
    """命令行工具：刷新缓存"""
    import argparse
    
    parser = argparse.ArgumentParser(description='刷新工单缓存')
    parser.add_argument('--all', action='store_true', help='刷新所有工单')
    parser.add_argument('--issue', type=str, help='刷新指定工单')
    parser.add_argument('--force', action='store_true', help='强制刷新（忽略缓存年龄）')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🔄 Jira 缓存刷新工具")
    print("="*80)
    print()
    
    # 加载工单列表
    if args.issue:
        issue_keys = [args.issue]
    else:
        # 加载所有工单
        issue_keys = []
        for project in ['EEESC', 'ESESC', 'ETESC']:
            project_dir = Path(f'data/raw_issues/{project}')
            if project_dir.exists():
                for f in project_dir.glob('*.json'):
                    issue_keys.append(f.stem)
        
        if not args.all:
            # 默认只刷新超过 7 天的
            print(f"ℹ️  提示：默认只刷新超过 7 天未更新的缓存")
            print(f"   使用 --all 强制刷新所有，或使用 --issue 指定工单")
            print()
    
    print(f"📋 待刷新工单数：{len(issue_keys)}")
    print()
    
    # 刷新缓存
    results = refresh_cache(issue_keys, force=args.force)
    
    # 统计
    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    print()
    print("="*80)
    print(f"📊 刷新完成")
    print("="*80)
    print(f"   成功：{success} 个")
    print(f"   失败：{failed} 个")
    print()


if __name__ == '__main__':
    main()
