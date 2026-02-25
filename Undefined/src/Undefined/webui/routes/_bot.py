import asyncio
from aiohttp import web
from aiohttp.web_response import Response

from ._shared import routes, check_auth, get_bot


def _truncate(text: str, *, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


@routes.get("/api/status")
async def status_handler(request: web.Request) -> Response:
    bot = get_bot(request)
    status = bot.status()
    if not check_auth(request):
        return web.json_response(
            {"running": bool(status.get("running")), "public": True}
        )
    return web.json_response(status)


@routes.post("/api/bot/{action}")
async def bot_action_handler(request: web.Request) -> Response:
    if not check_auth(request):
        return web.json_response({"error": "Unauthorized"}, status=401)
    action = request.match_info["action"]
    bot = get_bot(request)
    if action == "start":
        return web.json_response(await bot.start())
    elif action == "stop":
        return web.json_response(await bot.stop())
    return web.json_response({"error": "Invalid action"}, status=400)


@routes.get("/api/status")
