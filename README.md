# Jira Ticket Responder v1.1.0

🤖 基于 LLM 的 Jira 工单自动回复建议生成工具（支持 HTML 报告 + 智能过滤）

## ✨ 核心功能

- ✅ **LLM 深度分析** - 本地 Qwen35 模型，理解上下文和承诺
- ✅ **智能场景识别** - 自动判断停滞/承诺超期/需跟进等场景
- ✅ **批量分析工具** - 支持小批量测试和全量分析
- ✅ **Excel 导出** - 精美样式，Y/N 确认列，超链接直达工单
- ✅ **HTML 报告** - jiraAss 风格，支持夜间模式、多维度过滤
- ✅ **内部评论发表** - 一键发表内部说明（客户不可见）
- ✅ **完整性验证** - 自动重试，确保建议完整
- ✅ **智能过滤** - 自动过滤已关闭/已完成工单，只保留活跃工单

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install openpyxl requests
```

### 2. 配置

```bash
cp config.example.py config.local.py
# 编辑 config.local.py，填入 Jira API token
```

### 3. 更新全量数据（推荐）

```bash
# 使用 skill 自动更新（新增）
python3 scripts/update_full_data.py

# 或手动执行
python3 scripts/cache_refresh.py --all
python3 scripts/llm_analyzer.py
```

### 4. 生成报告

```bash
# Excel 报告
python3 scripts/generate_excel_optimized.py

# HTML 报告（jiraAss 风格，支持夜间模式/过滤）
python3 scripts/generate_html_report_jiraass.py
```

### 5. 审查并发表

1. 打开 Excel/HTML 报告，审查建议
2. 使用发表脚本批量发表（或手动在 Jira 中发表）

## 📊 使用案例

### 案例 1：小批量测试

```bash
python3 scripts/batch_analyze_10.py
# 输出：data/reports/YYYYMMDD_HHMMSS_batch10_suggestions.xlsx
```

### 案例 2：全量分析

```bash
python3 scripts/llm_analyzer.py
# 输出：data/reports/YYYYMMDD_HHMMSS_all_suggestions.json
python3 scripts/generate_excel_optimized.py
# 输出：data/reports/YYYYMMDD_HHMMSS_LLM 工单回复建议_优化版.xlsx
```

## 🎯 场景分类

| 场景 | 描述 | 示例 |
|------|------|------|
| **承诺超期** | 有明确承诺且已到期 | "@Frank 你于 04-02 承诺'5 月初发布'，请确认进展" |
| **长期停滞** | >21 天无承诺无回复 | "@Adam H. 此工单已停滞 42 天，是否需要跟进或关闭？" |
| **需确认** | 有回复但客户未确认 | "@Tony 请确认是否需要进一步跟进客户" |
| **短期停滞** | <14 天请求更新 | "@Adam H. 请更新此工单的最新进展" |

## 📁 项目结构

```
jira-ticket-responder/
├── scripts/                    # 核心工具
│   ├── llm_analyzer.py         # LLM 分析器
│   ├── batch_analyze_10.py     # 批量分析（10 个）
│   ├── cache_refresh.py        # 缓存刷新工具
│   ├── update_full_data.py     # 全量数据更新（v1.1 新增）
│   ├── generate_excel.py       # Excel 导出（基础）
│   ├── generate_excel_optimized.py  # Excel 导出（优化）
│   └── generate_html_report_jiraass.py  # HTML 报告（jiraAss 风格）
├── data/
│   ├── raw_issues/             # 工单原始数据（缓存）
│   └── reports/                # 生成的报告
├── config.example.py           # 配置示例
├── README.md
└── .gitignore
```

## 🔧 配置说明

### Jira API 配置

```python
JIRA_CONFIG = {
    "domain": "streamaxamerica.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "YOUR_API_TOKEN",
}
```

### LLM API 配置

```python
LLM_CONFIG = {
    "base_url": "http://192.168.80.121:32788/v1/chat/completions",
    "model": "qwen35-397b-a17b",
    "api_key": "YOUR_API_KEY",
    "max_tokens": 3000,
    "max_retries": 3,
}
```

## ✅ 实战验证（v1.0.0 统计）

### 发表统计

**统计时间**: 2026-05-07  
**总计**: **10 条内部评论** 已发表并通过审核

| 批次 | 工单号 | 负责人（化名） | 停滞天数 | 评论类型 | 状态 |
|------|--------|---------------|---------|---------|------|
| **批次 1** | EEESC-297 | Frank | 34 天 | 承诺超期提醒 | ✅ 已发表 |
| | EEESC-325 | Adam H. | 9 天 | 需确认解决 | ✅ 已发表 |
| | EEESC-409 | Tony | 29 天 | 承诺超期提醒 | ✅ 已发表 |
| **批次 2** | EEESC-340 | Tony | 14 天 | 长期停滞询问 | ✅ 已发表 |
| | EEESC-365 | Adam H. | 30 天 | 询问是否关闭 | ✅ 已发表 |
| | EEESC-370 | Adam H. | 21 天 | 加入黑名单 | ✅ 已发表 |
| | EEESC-376 | Adam H. | 8 天 | 请求更新进展 | ✅ 已发表 |
| | EEESC-379 | Adam H. | 40 天 | 承诺超期提醒 | ✅ 已发表 |
| | EEESC-415 | Frank | 16 天 | 承诺超期提醒 | ✅ 已发表 |
| | EEESC-453 | Nora D. | 15 天 | 承诺超期提醒 | ✅ 已发表 |

### 发表结果分析

**场景分布**:
- 承诺超期：6 条（60%）
- 长期停滞：2 条（20%）
- 需确认/更新：2 条（20%）

**负责人分布**:
- Adam H.: 5 条（50%）
- Frank: 3 条（30%）
- Tony: 2 条（20%）
- Nora D.: 1 条（10%）

**验证指标**:
- ✅ 所有评论均为内部说明（`jsdPublic: false`）
- ✅ 客户不可见，仅团队内部可见
- ✅ 无截断、无 artifacts
- ✅ 100% 通过人工审核

### 发表示例

**EEESC-297**（承诺超期）:
> @Frank 此工单已停滞 34 天，你于 04-02 承诺'5 月初发布新固件'。目前时间已到，请确认固件是否已按计划发布？若有进展请及时更新工单，以便我们跟进客户反馈，谢谢。

**EEESC-325**（需确认解决）:
> @Adam H. 此工单已停滞 9 天，虽然有团队回复但客户尚未确认解决方案是否有效。请确认是否需要进一步跟进客户，或根据无响应策略关闭工单。

**EEESC-409**（承诺超期）:
> @Tony 此工单已停滞 29 天，注意到你于 04-07 提到会将修复纳入下次固件升级。请问目前固件发布进展如何？是否需跟进客户验证结果？请确认最新状态以便推进或关闭，谢谢。

## 📝 版本历史

### v1.1.0 (2026-06-05) - 新增

**核心功能**:
- ✨ **HTML 报告生成**（jiraAss 风格）
  - 🌙 夜间模式/白天模式切换
  - 🔍 三维度过滤（组织/优先级/停滞天数）
  - 💾 localStorage 持久化
  - 📊 数据可视化图表
- ✨ **智能过滤系统**
  - 自动过滤已关闭/已完成/RDMS 已关闭工单
  - 只保留活跃工单（WORK IN PROGRESS/已挂起/技服验证/升级待处理）
- ✨ **全量数据更新流程**
  - 一键刷新所有工单缓存
  - 自动重新分析并生成报告

**实战验证**:
- ✅ 处理 193 个工单，过滤后保留 46 个活跃工单
- ✅ 成功过滤 147 个已关闭工单（包括 35 个 RDMS 已关闭）
- ✅ HTML 报告支持完整的夜间模式和过滤功能

### v1.0.0 (2026-05-07)

**核心功能**:
- ✨ LLM 分析器（完整性验证 + 重试机制）
- ✨ Excel 导出工具（基础版 + 优化版）
- ✨ 批量分析工具（小批量测试）
- ✨ 内部评论发表（支持@提及）

**实战验证**:
- ✅ 分析 10 个工单，生成建议
- ✅ 成功发表 10 条内部评论
- ✅ 所有评论均为内部说明（jsdPublic: false）
- ✅ 100% 通过人工审核

**技术特性**:
- max_tokens: 3000（确保完整输出）
- max_retries: 3（自动重试）
- 完整性验证：长度 + 结尾标点 + 截断检测

## 🚧 Roadmap

- [ ] v1.1: 批量发表内部评论（自动读取 Excel Y/N 列）
- [ ] v1.2: 支持自定义场景分类规则
- [ ] v2.0: 支持多项目配置（EEESC/ESESC/ETESC）

## ⚠️ 注意事项

1. **API Token**: 从 https://id.atlassian.com/api-token 获取
2. **数据缓存**: 工单数据缓存在 `data/raw_issues/` 目录
3. **内部评论**: 所有评论默认为内部说明（客户不可见）
4. **LLM 输出**: 建议人工审查后再发表

## 📄 License

MIT
