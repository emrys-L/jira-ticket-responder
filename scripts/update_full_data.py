#!/usr/bin/env python3
"""
Jira Ticket Responder - 全量数据更新工具 v1.1

功能：
1. 刷新所有工单的最新数据
2. 自动过滤已关闭/已完成工单
3. 生成包含夜间模式和过滤功能的 HTML 报告
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cache_refresh import refresh_all_issues
from scripts.llm_analyzer import analyze_issue
from config import JIRA_CONFIG, HEADERS
import requests


def get_all_issues():
    """从缓存获取所有工单数据"""
    full_data_path = Path(__file__).parent.parent / 'data' / 'raw_issues' / 'full_data.json'
    
    if not full_data_path.exists():
        print("❌ 缓存文件不存在，请先运行：python3 scripts/cache_refresh.py --all")
        sys.exit(1)
    
    with open(full_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('issues', [])


def filter_and_convert(issues):
    """
    过滤已关闭工单并转换为建议格式
    
    过滤规则：
    - 已关闭
    - RDMS 已关闭
    - 已完成
    - 已取消
    - 草稿
    """
    # 需要过滤的状态（精确匹配）
    FILTER_STATUSES = [
        '已关闭',
        'RDMS 已关闭',
        '已完成',
        '已取消',
        '草稿'
    ]
    
    print("=" * 80)
    print("🔄 过滤已关闭工单")
    print("=" * 80)
    print(f"原始工单数：{len(issues)}")
    
    # 统计所有状态
    all_statuses = Counter(issue.get('fields', {}).get('status', {}).get('name', '') for issue in issues)
    print("\n所有状态分布:")
    for status, count in sorted(all_statuses.items()):
        in_filter = "🚫 过滤" if status in FILTER_STATUSES else "✅ 保留"
        print(f"  {in_filter} {status}: {count} 个")
    
    # 过滤并转换
    suggestions = []
    filtered_count = 0
    
    for issue in issues:
        fields = issue.get('fields', {})
        if not fields:
            continue
        
        status = fields.get('status', {}).get('name', '')
        
        # 过滤已关闭的状态
        if status in FILTER_STATUSES:
            filtered_count += 1
            continue
        
        # 计算停滞天数
        comment_data = fields.get('comment', {})
        comments = comment_data.get('comments', []) if comment_data else []
        
        stagnation_days = 0
        if comments:
            try:
                last_date = datetime.fromisoformat(comments[-1].get('created', '')[:19])
                stagnation_days = max(0, (datetime.now() - last_date).days)
            except:
                pass
        
        # 提取信息
        assignee = fields.get('assignee', {}) or {}
        priority = fields.get('priority', {}) or {}
        
        suggestion = {
            'issue_key': issue.get('key', ''),
            'assignee': assignee.get('displayName', 'Unassigned'),
            'stagnation_days': stagnation_days,
            'suggestion': f"此工单已停滞{stagnation_days}天，请更新最新进展。",
            'status': status,
            'last_comment': comments[-1].get('created', '')[:10] if comments else 'Unknown',
            'priority': priority.get('name', 'Medium'),
            'organization': "未知组织",
            'summary': fields.get('summary', 'No summary')
        }
        suggestions.append(suggestion)
    
    print(f"\n📊 结果:")
    print(f"   过滤：{filtered_count} 个")
    print(f"   保留：{len(suggestions)} 个")
    
    # 统计保留的状态
    retained_statuses = Counter(s['status'] for s in suggestions)
    print(f"\n✅ 保留的状态分布:")
    for status, count in sorted(retained_statuses.items(), key=lambda x: -x[1]):
        print(f"   {status}: {count} 个")
    
    return suggestions


def save_suggestions(suggestions, filtered_count, total):
    """保存过滤后的建议数据"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(__file__).parent.parent / 'data' / 'reports' / f'{timestamp}_all_suggestions_filtered.json'
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'metadata': {
            'total': total,
            'filtered': filtered_count,
            'analyzed': len(suggestions)
        },
        'suggestions': suggestions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存：{output_path}")
    return output_path


def generate_html_report():
    """生成 HTML 报告"""
    print("\n" + "=" * 80)
    print("🎨 生成 HTML 报告")
    print("=" * 80)
    
    # 调用 HTML 生成器
    html_generator = Path(__file__).parent.parent / 'scripts' / 'generate_html_report_jiraass.py'
    
    if html_generator.exists():
        os.system(f'python3 {html_generator}')
        print("\n✅ HTML 报告已生成")
    else:
        print("\n❌ HTML 生成器不存在")


def main():
    """主函数"""
    print("=" * 80)
    print("🔄 Jira 工单全量数据更新工具 v1.1")
    print("=" * 80)
    print()
    
    # 步骤 1：获取所有工单
    print("📊 步骤 1/3: 获取所有工单...")
    print("-" * 80)
    issues = get_all_issues()
    print(f"✅ 获取到 {len(issues)} 个工单")
    
    # 步骤 2：过滤并转换
    print("\n📊 步骤 2/3: 过滤已关闭工单...")
    print("-" * 80)
    suggestions = filter_and_convert(issues)
    
    # 步骤 3：保存
    print("\n📊 步骤 3/3: 保存数据...")
    print("-" * 80)
    filtered_count = len(issues) - len(suggestions)
    save_suggestions(suggestions, filtered_count, len(issues))
    
    # 步骤 4：生成 HTML 报告
    print("\n📊 步骤 4/4: 生成 HTML 报告...")
    print("-" * 80)
    generate_html_report()
    
    print("\n" + "=" * 80)
    print("🎉 全量数据更新完成！")
    print("=" * 80)
    print(f"📊 总计：{len(issues)} 个工单 → 过滤后 {len(suggestions)} 个活跃工单")
    print(f"📁 报告位置：data/reports/jira_report_jiraass_*.html")
    print(f"🌐 访问地址：http://192.168.1.134:8888/jira-report/jira-report-final.html")
    print("=" * 80)


if __name__ == '__main__':
    main()
