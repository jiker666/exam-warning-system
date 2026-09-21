#!/usr/bin/env bash
# 说明：本脚本按照全局 ~/AGENTS.md 中的调用模板编写，选用【办公网】地址。
# 与考试预警系统业务无关，仅作为独立的 API 调用工具脚本保留，可随时删除。
# 用法: export WQ_API_KEY=<你的密钥> && ./scripts/wanqing_api_demo.sh
set -euo pipefail
: "${WQ_API_KEY:?请先执行: export WQ_API_KEY=<你的密钥>}"

curl 'https://wanqing-api.corp.kuaishou.com/api/agent/v1/apps/chat/completions' \
  -H "Authorization: Bearer $WQ_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "app-lf826k-1764053098452776117",
    "messages": [
        {
            "role": "user",
            "content": "常见的十字花科植物有哪些？"
        }
    ]
  }'
