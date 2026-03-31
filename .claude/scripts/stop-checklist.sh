#!/bin/bash
# Stop Hook: 行为意识自查清单（模板）
# 每次 Claude Code 停止时自动执行，提醒 Lead Agent 自检
#
# 使用方式：
#   1. 复制到工作仓库的 .claude/scripts/stop-checklist.sh
#   2. 在 .claude/settings.json 中配置 hooks（见下方模板）
#   3. 根据项目需要自定义检查项
#
# 配置 .claude/settings.json:
# {
#   "hooks": {
#     "Stop": [{
#       "hooks": [{
#         "type": "command",
#         "command": "bash .claude/scripts/stop-checklist.sh",
#         "timeout": 30,
#         "statusMessage": "行为意识自查..."
#       }]
#     }]
#   }
# }

# === 可自定义区域 ===
# 在这里添加项目特定的自动化检查（curl 线上服务、检查文件等）
# 示例：
#   DOMAIN="your-domain.com"
#   HTTP_CODE=$(curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/health")

# === 自查清单输出 ===
cat <<'CHECKLIST'
{
  "systemMessage": "=== 行为意识自查（Stop Hook）===\n\n请在退出前逐条确认：\n\n1️⃣ 语言：本次回复是否默认中文、专业术语保留英文？\n\n2️⃣ Skill 优先：遇到不会的事时，是否先搜了 ~/.claude/skills/、WebSearch、GitHub 的现有 skill，而不是从头实现？\n\n3️⃣ 不要闷头干：是否有某个方向尝试超过 3 次仍失败却没停下来换思路或通知用户？\n\n4️⃣ 执行后回顾沉淀：本次执行中是否遇到失败、报错、走弯路？如有，是否已提炼为意识条目或更新到 skills 中？\n\n5️⃣ 用户反馈即时沉淀：本次对话中用户是否有吐槽、指导、要求？如有，是否已固化为意识条目或 skills？\n\n6️⃣ NEXT_STEP.md：是否已更新当前进度和下一步任务？\n\n⚠️ 如有未做到的项，请在退出前补救。"
}
CHECKLIST
