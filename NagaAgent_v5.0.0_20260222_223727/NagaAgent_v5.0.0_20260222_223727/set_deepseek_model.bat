@echo off
set OPENCLAW_DEFAULT_MODEL=deepseek-chat
set OPENCLAW_DEFAULT_PROVIDER=deepseek
cd /d "D:\AI_MIYA_Facyory\MIYA_try\openclaw"
node scripts/run-node.mjs "gateway" "--port" "18789" "--verbose"
pause