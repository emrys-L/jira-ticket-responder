#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jira Ticket Responder - HTML Report Generator (jiraAss 风格)

功能：
- 复用 jiraAss 的 CSS 变量系统（支持夜间模式）
- 过滤面板（组织/优先级/停滞天数）
- 主题切换按钮（🌙 ↔ ☀️）
- localStorage 持久化
- 数据属性过滤逻辑
- 适配 jira-ticket-responder 的数据结构
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# 配置
PROJECT_ROOT = Path('/home/syrme/jira-ticket-responder')
DATA_DIR = PROJECT_ROOT / 'data' / 'reports'
OUTPUT_DIR = DATA_DIR


def find_latest_json_data():
    """查找最新的 JSON 数据文件"""
    json_files = list(DATA_DIR.glob('*_all_suggestions*.json'))
    if not json_files:
        json_files = list(DATA_DIR.glob('*.json'))
    
    if not json_files:
        raise FileNotFoundError("在 data/reports 目录中未找到 JSON 数据文件")
    
    latest = max(json_files, key=lambda p: p.stat().st_mtime)
    return latest


def load_json_data(json_path):
    """加载 JSON 数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _get_urgency_color(urgency: str) -> str:
    """获取紧急程度对应的颜色"""
    colors = {
        "高": "#dc3545",
        "中": "#ffc107",
        "低": "#28a745",
    }
    return colors.get(urgency, "#6c757d")


def _format_comment_date(date_str: str) -> str:
    """格式化评论时间"""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_str


def _get_issue_url(issue_key: str) -> str:
    """生成 Jira 工单 URL"""
    project_key = issue_key.split("-")[0]
    return f"https://streamaxamerica.atlassian.net/jira/servicedesk/projects/{project_key}/issues/{issue_key}"


def generate_html_report(data: Dict[str, Any], report_date: str) -> str:
    """
    生成 HTML 报告（jiraAss 风格）
    
    Args:
        data: JSON 数据（包含 suggestions 和 metadata）
        report_date: 报告日期（YYYY-MM-DD）
    
    Returns:
        HTML 内容
    """
    suggestions = data.get('suggestions', [])
    metadata = data.get('metadata', {})
    
    # 计算状态分布
    status_dist = defaultdict(int)
    for s in suggestions:
        status = s.get('status', 'Unknown')
        status_dist[status] += 1
    
    # 收集所有组织
    all_orgs = set()
    for s in suggestions:
        org = s.get('organization', '未知组织')
        if org:
            all_orgs.add(org)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Ticket Responder 报告 - {report_date}</title>
    <style>
        :root {{
            --bg-primary: #f5f5f5;
            --bg-card: #ffffff;
            --bg-secondary: #f8f9fa;
            --text-primary: #333333;
            --text-secondary: #555555;
            --text-muted: #6c757d;
            --border-color: #e0e0e0;
            --border-light: #dee2e6;
            --shadow: 0 2px 4px rgba(0,0,0,0.1);
            --accent-blue: #007bff;
            --accent-purple: #667eea;
            --accent-pink: #f093fb;
            --accent-cyan: #4facfe;
        }}
        
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-primary: #1a1a2e;
                --bg-card: #16213e;
                --bg-secondary: #0f3460;
                --text-primary: #eaeaea;
                --text-secondary: #b8b8b8;
                --text-muted: #888888;
                --border-color: #2d3748;
                --border-light: #4a5568;
                --shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s, color 0.3s;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: var(--bg-card);
            padding: 30px;
            border-radius: 8px;
            box-shadow: var(--shadow);
            transition: background-color 0.3s, box-shadow 0.3s;
        }}
        h1 {{
            color: var(--text-primary);
            border-bottom: 3px solid var(--accent-blue);
            padding-bottom: 10px;
        }}
        h2 {{
            color: var(--text-secondary);
            margin-top: 30px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            flex: 1;
            min-width: 150px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0;
            font-size: 2em;
        }}
        .stat-card p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .filter-panel {{
            background: var(--bg-card);
            padding: 20px;
            margin: 30px 0;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .filter-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .filter-header h2 {{
            margin: 0;
            color: var(--text-primary);
            font-size: 1.2em;
        }}
        .filter-controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .filter-group label {{
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
        }}
        .filter-group select {{
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            background: var(--bg-card);
            color: var(--text-primary);
            min-width: 150px;
            cursor: pointer;
        }}
        .filter-group select:hover {{
            border-color: var(--accent-blue);
        }}
        .reset-btn {{
            padding: 8px 16px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }}
        .reset-btn:hover {{
            background: #5a6268;
        }}
        .filter-stats {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--border-light);
            font-weight: 600;
            color: var(--text-primary);
        }}
        .theme-toggle {{
            padding: 8px 16px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        .theme-toggle:hover {{
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }}
        body.dark-mode {{
            --bg-primary: #121212;
            --bg-card: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-muted: #888888;
            --border-color: #444444;
            --border-light: #555555;
            --shadow: 0 2px 4px rgba(0,0,0,0.4);
            --accent-blue: #4a9eff;
            --accent-purple: #7b68ee;
            --accent-pink: #ff69b4;
            --accent-cyan: #00ced1;
        }}
        .issue-card {{
            margin: 15px 0;
            padding: 15px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            transition: all 0.2s;
        }}
        .issue-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .issue-key {{
            font-weight: bold;
            color: var(--accent-blue);
            text-decoration: none;
            font-size: 1.1em;
        }}
        .issue-key:hover {{
            text-decoration: underline;
        }}
        .issue-summary {{
            color: var(--text-primary);
            margin: 10px 0;
            font-size: 1.05em;
        }}
        .issue-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.9em;
            color: var(--text-muted);
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .urgency-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }}
        .stagnation {{
            font-size: 0.9em;
        }}
        .stagnation.warning {{
            color: #dc3545;
            font-weight: bold;
        }}
        .stagnation.normal {{
            color: #28a745;
        }}
        .suggestion-box {{
            background: var(--bg-card);
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid var(--accent-blue);
            margin: 10px 0;
            font-size: 0.95em;
            color: var(--text-secondary);
            line-height: 1.6;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Jira Ticket Responder 报告</h1>
        <p style="color: var(--text-muted);">报告日期：{report_date}</p>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{metadata.get('total_issues', len(suggestions))}</h3>
                <p>总工单数</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>{metadata.get('analyzed', 0)}</h3>
                <p>已分析</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>{metadata.get('success', 0)}</h3>
                <p>成功</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <h3>{metadata.get('skipped', 0)}</h3>
                <p>跳过</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h3>{metadata.get('failed', 0)}</h3>
                <p>失败</p>
            </div>
        </div>
        
        <!-- 动态过滤面板 -->
        <div class="filter-panel">
            <div class="filter-header">
                <h2>🔍 筛选器</h2>
                <button class="theme-toggle" onclick="toggleTheme()" title="切换黑夜/白天模式">🌙 黑夜模式</button>
            </div>
            <div class="filter-controls">
                <div class="filter-group">
                    <label>组织：</label>
                    <select id="filter-org" onchange="applyFilters()">
                        <option value="">全部组织</option>
'''
    
    # 生成组织选项
    for org in sorted(all_orgs):
        html += f'                        <option value="{org}">{org}</option>\n'
    
    html += '''                    </select>
                </div>
                
                <div class="filter-group">
                    <label>紧急程度：</label>
                    <select id="filter-urgency" onchange="applyFilters()">
                        <option value="">全部</option>
                        <option value="高">高 🔴</option>
                        <option value="中">中 🟡</option>
                        <option value="低">低 🟢</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>停滞天数：</label>
                    <select id="filter-stagnation" onchange="applyFilters()">
                        <option value="">全部</option>
                        <option value="0-7">0-7 天</option>
                        <option value="8-14">8-14 天</option>
                        <option value="15-30">15-30 天</option>
                        <option value="30+">30 天以上</option>
                    </select>
                </div>
                
                <button class="reset-btn" onclick="resetFilters()">🔄 重置</button>
            </div>
            
            <div class="filter-stats">
                已显示：<span id="show-count">0</span>/<span id="total-count">0</span> 个工单
            </div>
        </div>
'''
    
    # 生成工单卡片
    for s in suggestions:
        issue_key = s.get('issue_key', 'Unknown')
        issue_url = _get_issue_url(issue_key)
        summary = s.get('summary', 'No summary')
        assignee = s.get('assignee', '未分配')
        status = s.get('status', 'Unknown')
        stagnation_days = s.get('stagnation_days', 0)
        suggestion_text = s.get('suggestion', 'No suggestion')
        organization = s.get('organization', '未知组织')
        last_comment = s.get('last_comment', '')
        
        # 紧急程度（从 status 或 suggestion 推断）
        urgency = '中'
        if '升级' in status or 'escalat' in status.lower():
            urgency = '高'
        elif stagnation_days > 30:
            urgency = '高'
        elif stagnation_days > 14:
            urgency = '中'
        else:
            urgency = '低'
        
        urgency_color = _get_urgency_color(urgency)
        
        # 停滞天数样式
        if stagnation_days > 30:
            stagnation_class = 'warning'
        elif stagnation_days > 14:
            stagnation_class = 'normal'
        else:
            stagnation_class = 'normal'
        
        html += f'''
        <div class="issue-card" 
             data-organization="{organization}"
             data-urgency="{urgency}"
             data-stagnation="{stagnation_days}">
            <div class="issue-header">
                <div>
                    <a href="{issue_url}" target="_blank" class="issue-key">{issue_key}</a>
                    <span class="status-badge">{status}</span>
                </div>
                <span class="urgency-badge" style="background: {urgency_color};">
                    {urgency}
                </span>
            </div>
            <div class="issue-summary">{summary}</div>
            
            <div class="issue-meta">
                <span>👤 负责人：{assignee}</span>
                <span class="stagnation {stagnation_class}">📅 停滞：{stagnation_days} 天</span>
                <span>🏢 组织：{organization}</span>
            </div>
            
            <div class="suggestion-box">
                <strong>💡 建议：</strong><br>
                {suggestion_text}
            </div>
'''
        
        if last_comment:
            html += f'''
            <details style="margin-top: 10px; color: var(--text-secondary);">
                <summary style="cursor: pointer; font-weight: 600;">💬 最后评论</summary>
                <div style="margin-top: 10px; padding: 10px; background: var(--bg-secondary); border-radius: 4px; font-size: 0.9em;">
                    {last_comment}
                </div>
            </details>
'''
        
        html += '''
        </div>
'''
    
    html += f'''
        <div class="footer">
            <p>Generated by Jira Ticket Responder @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <script>
    // 应用过滤条件
    function applyFilters() {{
        const orgFilter = document.getElementById('filter-org').value;
        const urgencyFilter = document.getElementById('filter-urgency').value;
        const stagnationFilter = document.getElementById('filter-stagnation').value;
        
        let showCount = 0;
        let totalCount = 0;
        
        document.querySelectorAll('.issue-card').forEach(card => {{
            totalCount++;
            
            const org = card.dataset.organization || '';
            const urgency = card.dataset.urgency || '';
            const stagnation = parseInt(card.dataset.stagnation || '0');
            
            let matches = true;
            
            if (orgFilter && org !== orgFilter) matches = false;
            if (urgencyFilter && urgency !== urgencyFilter) matches = false;
            if (stagnationFilter) {{
                if (stagnationFilter === '0-7' && stagnation > 7) matches = false;
                if (stagnationFilter === '8-14' && (stagnation < 8 || stagnation > 14)) matches = false;
                if (stagnationFilter === '15-30' && (stagnation < 15 || stagnation > 30)) matches = false;
                if (stagnationFilter === '30+' && stagnation <= 30) matches = false;
            }}
            
            if (matches) {{
                card.style.display = 'block';
                showCount++;
            }} else {{
                card.style.display = 'none';
            }}
        }});
        
        document.getElementById('show-count').textContent = showCount;
        document.getElementById('total-count').textContent = totalCount;
    }}
    
    // 重置过滤
    function resetFilters() {{
        document.getElementById('filter-org').value = '';
        document.getElementById('filter-urgency').value = '';
        document.getElementById('filter-stagnation').value = '';
        applyFilters();
    }}
    
    // 切换黑夜/白天模式
    function toggleTheme() {{
        document.body.classList.toggle('dark-mode');
        const btn = document.querySelector('.theme-toggle');
        if (document.body.classList.contains('dark-mode')) {{
            btn.textContent = '☀️ 白天模式';
            localStorage.setItem('theme', 'dark');
        }} else {{
            btn.textContent = '🌙 黑夜模式';
            localStorage.setItem('theme', 'light');
        }}
    }}
    
    // 加载保存的主题偏好
    window.addEventListener('DOMContentLoaded', function() {{
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {{
            document.body.classList.add('dark-mode');
            document.querySelector('.theme-toggle').textContent = '☀️ 白天模式';
        }}
        
        applyFilters();
    }});
    </script>
</body>
</html>
'''
    
    return html


def generate_report(data=None):
    """生成 HTML 报告"""
    if data is None:
        json_path = find_latest_json_data()
        print(f"📊 使用数据文件：{json_path}")
        data = load_json_data(json_path)
    
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    print("💉 生成 HTML 报告...")
    html_content = generate_html_report(data, report_date)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'jira_report_jiraass_{timestamp}.html'
    output_path = OUTPUT_DIR / output_filename
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 保存报告到：{output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_size = output_path.stat().st_size
    metadata = data.get('metadata', {})
    
    print(f"✅ 报告生成成功！")
    print(f"   文件大小：{file_size:,} 字节")
    print(f"   工单总数：{metadata.get('total_issues', 'N/A')}")
    print(f"   已分析：{metadata.get('analyzed', 'N/A')}")
    print(f"   成功：{metadata.get('success', 'N/A')}")
    
    return output_path


def validate_report(output_path):
    """验证生成的 HTML 报告"""
    print("\n🔍 验证报告...")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'CSS 变量系统': '--bg-primary:' in content,
        '夜间模式支持': 'dark-mode' in content,
        '过滤面板': 'filter-org' in content,
        '主题切换': 'toggleTheme' in content,
        'localStorage': 'localStorage' in content,
        '工单卡片': 'issue-card' in content,
        '数据属性过滤': 'data-organization' in content,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def main():
    """主函数"""
    print("=" * 60)
    print("Jira Ticket Responder - HTML 报告生成器 (jiraAss 风格)")
    print("=" * 60)
    print()
    
    try:
        output_path = generate_report()
        is_valid = validate_report(output_path)
        
        print()
        print("=" * 60)
        if is_valid:
            print("🎉 报告验证通过！")
            print()
            print(f"📁 文件路径：{output_path}")
            print(f"🌐 访问方式：直接用浏览器打开文件")
            print(f"   或使用：xdg-open {output_path}")
        else:
            print("⚠️  报告验证失败，请检查输出文件")
        print("=" * 60)
        
        return 0 if is_valid else 1
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
