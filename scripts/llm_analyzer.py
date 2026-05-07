#!/usr/bin/env python3
"""
LLM 工单分析器 - 使用 Qwen AI 生成个性化回复建议

用法:
    python3 scripts/llm_analyzer.py          # 全量分析
    python3 scripts/llm_analyzer.py --test   # 测试模式（仅 3 个工单）
"""

import json
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# LLM API 配置
LLM_CONFIG = {
    "base_url": "http://192.168.80.121:32788/v1/chat/completions",
    "model": "qwen35-397b-a17b",
    "api_key": "sSMCVe7TBAJPx0d0Ff4cB3569f7a41B7980bFd02888fA7A8",  # 从 AGENTS.md 获取
    "temperature": 0.7,
    "max_tokens": 3000,  # 增加 token 限制，确保完整输出
    "max_retries": 3  # 输出不完整时重试次数
}

# 需要排除的状态
EXCLUDED_STATUS = [
    'closed', 'done', 'resolved', 
    '已关闭', '已完成', '草稿',
    'rdms 已关闭', 'rdms closed'
]


def load_issue_data(issue_key: str) -> Optional[Dict]:
    """从本地缓存加载工单完整数据"""
    raw_issues_dir = Path('data/raw_issues')
    
    for project_dir in raw_issues_dir.iterdir():
        if not project_dir.is_dir():
            continue
        issue_file = project_dir / f"{issue_key}.json"
        if issue_file.exists():
            with open(issue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    print(f"  ❌ 未找到 {issue_key}")
    return None


def extract_comments_text(issue_data: Dict, max_comments: int = 20) -> str:
    """提取评论文本（按时间顺序）"""
    fields = issue_data.get('fields', {})
    comments = fields.get('comment', {}).get('comments', [])
    
    def extract_text(adf):
        if isinstance(adf, str):
            return adf
        if isinstance(adf, dict):
            if adf.get('type') == 'text':
                return adf.get('text', '')
            content = adf.get('content', [])
            return ' '.join([extract_text(c) for c in content])
        if isinstance(adf, list):
            return ' '.join([extract_text(i) for i in adf])
        return ''
    
    # 限制评论数量，避免 token 过多
    recent_comments = comments[-max_comments:] if len(comments) > max_comments else comments
    
    comments_text = []
    for i, c in enumerate(recent_comments, 1):
        author = c.get('author', {}).get('displayName', 'Unknown')
        created = c.get('created', '')[:10]
        body = extract_text(c.get('body', ''))
        comments_text.append(f"{i}. {author} @ {created}\n   {body[:300]}")
    
    return '\n\n'.join(comments_text)


def should_exclude(issue_data: Dict) -> bool:
    """判断是否应该排除该工单"""
    fields = issue_data.get('fields', {})
    status = fields.get('status', {}).get('name', '').lower()
    
    # 明确排除的状态
    if any(excluded in status for excluded in EXCLUDED_STATUS):
        return True
    
    # 计算停滞天数
    comments = fields.get('comment', {}).get('comments', [])
    if comments:
        last_comment_date = comments[-1].get('created', '')
        if last_comment_date:
            try:
                last_dt = datetime.fromisoformat(last_comment_date.replace('Z', '+00:00'))
                now = datetime.now(last_dt.tzinfo)
                stagnation_days = (now - last_dt).days
                
                # 停滞>90 天 且 无团队回复
                if stagnation_days > 90:
                    # 简单判断：最后一条不是团队的就是客户的
                    last_author = comments[-1].get('author', {}).get('displayName', '')
                    team_names = ['MarcoQi', 'Tony', 'Nora', 'Frank', 'Adam', 'Sean', 'Lucas', 'Amos', 'GRID', 'Automation']
                    if not any(name in last_author for name in team_names):
                        return True
            except:
                pass
    
    return False


def build_prompt(issue_data: Dict) -> str:
    """构建 LLM Prompt（优化版：历史范式 + 最后 3-5 轮对话）"""
    fields = issue_data.get('fields', {})
    key = issue_data.get('key', 'Unknown')
    status = fields.get('status', {}).get('name', 'Unknown')
    assignee = fields.get('assignee', {})
    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
    
    # 计算停滞天数
    comments = fields.get('comment', {}).get('comments', [])
    stagnation_days = 0
    if comments:
        last_comment_date = comments[-1].get('created', '')
        if last_comment_date:
            try:
                last_dt = datetime.fromisoformat(last_comment_date.replace('Z', '+00:00'))
                now = datetime.now(last_dt.tzinfo)
                stagnation_days = (now - last_dt).days
            except:
                pass
    
    # 提取最后 3-5 轮人类评论（去除系统自动评论）
    human_comments = [
        c for c in comments 
        if 'Automation' not in c.get('author', {}).get('displayName', '')
        and 'Jira' not in c.get('author', {}).get('displayName', '')
    ]
    recent_comments = human_comments[-5:]  # 最后 5 条
    
    # 内部函数：提取 ADF 文本
    def extract_text(adf):
        if isinstance(adf, str):
            return adf
        if isinstance(adf, dict):
            if adf.get('type') == 'text':
                return adf.get('text', '')
            content = adf.get('content', [])
            return ' '.join([extract_text(c) for c in content])
        if isinstance(adf, list):
            return ' '.join([extract_text(i) for i in adf])
        return ''
    
    def format_comment(c):
        author = c.get('author', {}).get('displayName', 'Unknown')
        date = c.get('created', '')[5:10]  # MM-DD 格式
        body = extract_text(c.get('body', ''))[:200]  # 每条最多 200 字
        return f"[{date}] {author}: {body}"
    
    comments_text = '\n'.join([format_comment(c) for c in recent_comments])
    
    # 历史成功范式（从已发表的评论中提取）
    historical_patterns = f"""## 历史成功范式（参考学习）

### 范式 1：有承诺但超期
> @{assignee_name} 此工单已停滞 [N] 天，你于 [日期] 承诺'[承诺内容]'，请确认最新进展。

### 范式 2：长期停滞无承诺（>21 天）
> @{assignee_name} 此工单已停滞 [N] 天（长期），客户最后待处理，是否需要跟进或关闭？

### 范式 3：有回复但未确认
> @{assignee_name} 此工单已停滞 [N] 天，虽然有团队回复但客户尚未确认，请确认是否需要进一步跟进。

### 范式 4：短期停滞请求更新（<14 天）
> @{assignee_name} 请更新此工单的最新进展，已经停滞 [N] 天。
"""
    
    prompt = f"""## 角色
你是 Jira 工单助手，负责生成内部评论建议。

## 工单信息
- 工单号：{key}
- 负责人：{assignee_name}
- 停滞天数：{stagnation_days}天
- 当前日期：2026-05-06

## 最近评论（最后 3-5 轮对话，去除系统自动评论）
---
{comments_text}
---

{historical_patterns}
## 任务
1. 阅读最近评论，理解上下文
2. 判断场景类型：
   - 有明确承诺且超期 → 参考范式 1
   - 长期停滞（>21 天）无承诺 → 参考范式 2
   - 有团队回复但客户未确认 → 参考范式 3
   - 短期停滞（<14 天） → 参考范式 4
3. 生成@{assignee_name}开头的内部评论
4. 50-100 字，专业友好，非指责语气

## 生成评论:
"""
    
    return prompt


def is_complete_suggestion(suggestion: str) -> bool:
    """检查建议是否完整"""
    if not suggestion:
        return False
    
    # 长度检查（至少 40 字符）
    if len(suggestion) < 40:
        return False
    
    # 结尾标点检查（应该有句号/问号）
    if not any(suggestion.endswith(p) for p in ['。', '？', '!', '.', '?', '谢谢']):
        return False
    
    # 检查是否有截断痕迹（如"将"后面没有内容）
    if suggestion.endswith(('将', '会', '要', '请', '的', '了')):
        return False
    
    return True

def extract_suggestion_from_reasoning(reasoning: str) -> Optional[str]:
    """从 reasoning 字段提取建议"""
    if not reasoning:
        return None
    
    import re
    
    # 策略 1：查找*Draft*标记后的@句子（支持 *Draft 1:* *Draft 1 (Mental):* 等格式）
    draft_matches = re.findall(r'\*Draft[^*]*\*[:\s]*\n(\s*@+[^\n]+)', reasoning, re.IGNORECASE)
    if draft_matches:
        suggestion = draft_matches[-1].strip()
        if is_complete_suggestion(suggestion):
            return suggestion
    
    # 策略 2：查找所有@开头且长度 40-250 的行（允许前导空格）
    lines = reasoning.split('\n')
    candidates = []
    
    for line in lines:
        stripped = line.strip()
        # 简单匹配：@开头，长度合适
        if stripped.startswith('@') and 40 <= len(stripped) <= 250:
            # 排除包含"Output Format"等分析性内容
            if not any(kw in stripped for kw in ['Output', 'Format', 'Task', 'Ticket ID', 'Status:', 'Assignee:', 'Start with', 'Salutation']):
                # 额外排除：不包含中文的（纯英文分析）
                if re.search(r'[\u4e00-\u9fa5]', stripped):
                    if is_complete_suggestion(stripped):
                        candidates.append((len(stripped), stripped))
    
    if candidates:
        # 选择长度最接近 100 的（通常是最佳长度）
        candidates.sort(key=lambda x: abs(len(x[1]) - 100))
        return candidates[0][1].strip()
    
    return None


def call_llm(prompt: str) -> Optional[str]:
    """调用 LLM API（带重试机制）"""
    for attempt in range(LLM_CONFIG.get('max_retries', 3)):
        try:
            headers = {
                'Authorization': f'Bearer {LLM_CONFIG["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                LLM_CONFIG['base_url'],
                headers=headers,
                json={
                    'model': LLM_CONFIG['model'],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': LLM_CONFIG['temperature'],
                    'max_tokens': LLM_CONFIG['max_tokens']
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']
                
                # Qwen35 返回 reasoning 而不是 content
                reasoning = message.get('reasoning', '')
                content = message.get('content', '')
                
                # 优先从 reasoning 提取
                if reasoning:
                    suggestion = extract_suggestion_from_reasoning(reasoning)
                    if suggestion and is_complete_suggestion(suggestion):
                        return suggestion
                    elif suggestion:
                        print(f"  ⚠️ 输出不完整（尝试 {attempt+1}/{LLM_CONFIG['max_retries']}）")
                
                # 回退到 content
                if content:
                    cleaned = content.strip()
                    if is_complete_suggestion(cleaned):
                        return cleaned
                    else:
                        print(f"  ⚠️ content 不完整（尝试 {attempt+1}/{LLM_CONFIG['max_retries']}）")
                
                print(f"  ⚠️ 未提取到完整建议，重试...")
            else:
                print(f"  ❌ API 错误：{response.status_code}")
                return None
        
        except Exception as e:
            print(f"  ❌ 调用失败：{e}")
        
        # 重试前等待
        if attempt < LLM_CONFIG['max_retries'] - 1:
            import time
            time.sleep(2)
    
    print(f"  ❌ 重试{LLM_CONFIG['max_retries']}次后仍失败")
    return None


def analyze_issue(issue_key: str, test_mode: bool = False) -> Optional[Dict]:
    """分析单个工单"""
    print(f"\n🔍 分析 {issue_key}...")
    
    # 加载工单数据
    issue_data = load_issue_data(issue_key)
    if not issue_data:
        return None
    
    # 检查是否应该排除
    if should_exclude(issue_data):
        print(f"  ⏭️  已排除（非活跃工单）")
        return None
    
    # 构建 Prompt
    prompt = build_prompt(issue_data)
    
    if test_mode:
        print(f"\n📝 Prompt 预览:")
        print("="*80)
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        print("="*80)
        return {'prompt': prompt, 'skipped': False}
    
    # 调用 LLM
    print(f"  🤖 调用 LLM...")
    suggestion = call_llm(prompt)
    
    if suggestion:
        print(f"  ✅ 建议生成成功")
        print(f"     {suggestion[:100]}...")
        
        return {
            'issue_key': issue_key,
            'suggestion': suggestion,
            'prompt': prompt,
            'timestamp': datetime.now().isoformat()
        }
    else:
        print(f"  ❌ 建议生成失败")
        return None


def load_all_issues() -> List[str]:
    """加载所有工单号"""
    raw_issues_dir = Path('data/raw_issues')
    issue_keys = []
    
    for project_dir in raw_issues_dir.iterdir():
        if not project_dir.is_dir():
            continue
        for issue_file in project_dir.glob('*.json'):
            issue_key = issue_file.stem
            issue_keys.append(issue_key)
    
    return sorted(issue_keys)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM 工单分析器')
    parser.add_argument('--test', action='store_true', help='测试模式（仅 3 个工单）')
    parser.add_argument('--issue', type=str, help='指定工单号')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🤖 Jira Ticket Responder - LLM 分析器")
    print("="*80)
    print()
    
    # 测试模式：只分析 3 个工单
    if args.test:
        print("📍 测试模式：分析前 3 个工单")
        issue_keys = load_all_issues()[:3]
    elif args.issue:
        print(f"📍 指定工单：{args.issue}")
        issue_keys = [args.issue]
    else:
        print("📍 全量模式：分析所有活跃工单")
        issue_keys = load_all_issues()
    
    print(f"📄 总工单数：{len(issue_keys)}")
    print()
    
    # 分析工单
    results = []
    skipped = 0
    failed = 0
    
    for issue_key in issue_keys:
        result = analyze_issue(issue_key, test_mode=args.test)
        
        if result:
            if result.get('skipped'):
                skipped += 1
            else:
                results.append(result)
        else:
            failed += 1
    
    # 输出统计
    print()
    print("="*80)
    print("📊 分析统计")
    print("="*80)
    print(f"总工单数：{len(issue_keys)}")
    print(f"成功：{len(results)}")
    print(f"跳过：{skipped}")
    print(f"失败：{failed}")
    print()
    
    # 保存结果
    if results:
        output_dir = Path('data/reports')
        output_dir.mkdir(exist_ok=True)
        
        # 保存 JSON
        output_file = output_dir / f'llm_analysis_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': len(issue_keys),
                'analyzed': len(results),
                'suggestions': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 结果已保存：{output_file}")
        
        # 测试模式下显示所有建议
        if args.test:
            print()
            print("="*80)
            print("💡 生成的建议")
            print("="*80)
            for r in results:
                print(f"\n{r['issue_key']}:")
                print(r['suggestion'])
    else:
        print("⚠️  没有生成任何建议")


if __name__ == '__main__':
    main()
