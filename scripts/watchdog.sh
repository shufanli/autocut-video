#!/bin/bash
# watchdog.sh — 监控工作仓库的 claude 进程，停了就重启
#
# 用法：
#   ./scripts/watchdog.sh /path/to/working-repo
#
# 停止：
#   touch /path/to/working-repo/STOP

REPO_DIR="${1:-.}"
SKILLS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHECK_INTERVAL=30  # 每 30 秒检查一次

cd "$REPO_DIR" || exit 1
REPO_DIR="$(pwd)"

echo "Watchdog 启动，监控: $REPO_DIR"
echo "每 ${CHECK_INTERVAL} 秒检查一次"
echo "停止方式: touch $REPO_DIR/STOP"

while true; do
    # 检查停止信号
    if [ -f "$REPO_DIR/STOP" ]; then
        echo "$(date '+%H:%M:%S'): 发现 STOP，退出 watchdog"
        exit 0
    fi

    # 检查是否有 claude 进程在这个目录下工作
    if pgrep -f "claude.*$REPO_DIR" > /dev/null 2>&1 || pgrep -f "run-forever.*$REPO_DIR" > /dev/null 2>&1; then
        # 还在跑，不用管
        :
    else
        echo "$(date '+%H:%M:%S'): 检测到 agent 停止，重启..."
        nohup "$SKILLS_DIR/scripts/run-forever.sh" "$REPO_DIR" >> "$REPO_DIR/watchdog.log" 2>&1 &
        echo "$(date '+%H:%M:%S'): 已重启，PID: $!"
    fi

    sleep "$CHECK_INTERVAL"
done
