# 📚 Jira Ticket Responder Skills

## 🔄 update-full-data

**一键更新全量工单数据并生成 HTML 报告**

### 功能
- 刷新所有 Jira 工单的最新数据
- 自动过滤已关闭/已完成工单（已关闭、RDMS 已关闭、已完成、已取消、草稿）
- 生成支持夜间模式和多维度过滤的 HTML 报告
- 只保留活跃工单（WORK IN PROGRESS、已挂起、技服验证、升级待处理）

### 使用方法
```bash
cd /home/syrme/jira-ticket-responder
python3 scripts/update_full_data.py
```

### 输出
- **数据文件**: `data/reports/YYYYMMDD_HHMMSS_all_suggestions_filtered.json`
- **HTML 报告**: `data/reports/jira_report_jiraass_YYYYMMDD_HHMMSS.html`
- **访问地址**: `http://192.168.1.134:8888/jira-report/jira-report-final.html`

### 过滤规则
自动过滤以下状态的工单：
- ❌ 已关闭
- ❌ RDMS 已关闭
- ❌ 已完成
- ❌ 已取消
- ❌ 草稿

保留以下状态的工单：
- ✅ WORK IN PROGRESS
- ✅ 已挂起
- ✅ 技服验证
- ✅ 升级待处理

### HTML 报告功能
- 🌙 夜间模式/白天模式切换（localStorage 持久化）
- 🔍 三维度过滤（组织/优先级/停滞天数）
- 📊 数据可视化图表
- 🔎 搜索和排序功能

### 详细文档
查看完整文档：`/home/syrme/jira-ticket-responder/skills/update-full-data.md`
