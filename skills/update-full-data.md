# 🔄 Jira 工单全量数据更新

## 📋 功能说明

一键更新所有 Jira 工单的最新数据，自动过滤已关闭/已完成工单，生成包含完整过滤功能和夜间模式的 HTML 报告。

## 🎯 使用场景

- 每日/每周定期更新工单数据
- 生成最新的 HTML 报告（包含活跃的工单）
- 自动过滤已关闭/RDMS 已关闭/已完成工单
- 确保报告只包含需要跟进的活跃工单

## 🚀 快速开始

### 方法 1：使用更新脚本（推荐）

```bash
cd /home/syrme/jira-ticket-responder
python3 scripts/update_full_data.py
```

### 方法 2：手动执行各步骤

```bash
# 1. 刷新所有工单缓存
python3 scripts/cache_refresh.py --all

# 2. 重新分析所有工单
python3 scripts/llm_analyzer.py

# 3. 生成 HTML 报告（jiraAss 风格）
python3 scripts/generate_html_report_jiraass.py
```

## 📊 过滤规则

**自动过滤的状态**：
- ❌ 已关闭
- ❌ RDMS 已关闭
- ❌ 已完成
- ❌ 已取消
- ❌ 草稿

**保留的状态**（活跃工单）：
- ✅ WORK IN PROGRESS
- ✅ 已挂起
- ✅ 技服验证
- ✅ 升级待处理

## 📁 输出文件

### 数据文件
- `data/raw_issues/full_data.json` - 完整的工单数据（包含所有工单）
- `data/reports/YYYYMMDD_HHMMSS_all_suggestions_filtered.json` - 过滤后的建议数据

### 报告文件
- `data/reports/jira_report_jiraass_YYYYMMDD_HHMMSS.html` - HTML 报告（支持夜间模式/过滤）

## 🌐 访问报告

报告生成后会自动部署到 Nginx：

```bash
# 访问最新报告
http://192.168.1.134:8888/jira-report/jira-report-final.html

# 或手动复制
cp data/reports/jira_report_jiraass_*.html /mnt/data/workshop/web-demos/jira-report/
```

## 🔧 配置说明

### Jira API 配置

编辑 `config.py`：

```python
JIRA_CONFIG = {
    "domain": "streamaxamerica.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "YOUR_API_TOKEN",
}
```

### 过滤规则配置

编辑 `scripts/update_full_data.py` 中的 `FILTER_STATUSES` 列表：

```python
FILTER_STATUSES = [
    '已关闭',
    'RDMS 已关闭',
    '已完成',
    '已取消',
    '草稿'
]
```

## 📊 统计信息

执行完成后会显示：

```
================================================================================
📊 更新完成
================================================================================
原始工单数：193 个
过滤掉的工单：147 个
保留的工单：46 个

保留的状态分布:
   WORK IN PROGRESS: 21 个
   已挂起：12 个
   技服验证：7 个
   升级待处理：6 个

✅ HTML 报告已生成
📁 文件路径：data/reports/jira_report_jiraass_20260605_174902.html
🌐 访问地址：http://192.168.1.134:8888/jira-report/jira-report-final.html
================================================================================
```

## ⚠️ 注意事项

1. **API 限制**：大量工单刷新可能需要较长时间（193 个工单约 2-3 分钟）
2. **缓存更新**：建议定期执行（每日或每周）
3. **过滤规则**：根据实际需求调整 `FILTER_STATUSES`
4. **HTML 功能**：生成的报告支持夜间模式、多维度过滤、搜索排序等功能

## 🛠️ 故障排除

### 问题 1：410 Gone 错误

**原因**：Jira API 端点变更

**解决**：使用缓存刷新工具而不是直接 API 调用

```bash
python3 scripts/cache_refresh.py --all
```

### 问题 2：过滤不生效

**原因**：状态字符串不匹配（空格问题）

**解决**：检查实际数据中的状态名称，确保完全匹配

```python
# 从数据中获取实际的状态名称
all_statuses = set(issue['fields']['status']['name'] for issue in issues)
print(all_statuses)
```

### 问题 3：HTML 报告没有最新数据

**原因**：使用了旧的 JSON 文件

**解决**：确保使用最新生成的 `*_all_suggestions_filtered.json` 文件

```bash
# 删除旧文件
rm data/reports/*_all_suggestions*.json

# 重新生成
python3 scripts/update_full_data.py
```

## 📚 相关文档

- [HTML 报告功能说明](docs/html_report.md)
- [缓存刷新功能](docs/缓存刷新功能.md)
- [LLM 分析器使用指南](docs/llm_analyzer.md)
