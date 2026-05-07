"""Jira API 配置示例

复制此文件为 config.local.py 并填入你的 API token
"""

JIRA_CONFIG = {
    "domain": "your-domain.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "YOUR_API_TOKEN_HERE",  # 从 https://id.atlassian.com/api-token 获取
}

# 监控的项目
MONITORED_PROJECTS = ["PROJECT1", "PROJECT2", "PROJECT3"]

# 本地 Qwen API 配置（可选）
QWEN_API = {
    "base_url": "http://localhost:11434/v1",
    "model": "qwen35-397b-a17b",
}
