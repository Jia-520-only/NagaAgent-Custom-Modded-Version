from __future__ import annotations

import html
import logging
import re
from typing import Any

import httpx

from Undefined.bilibili.downloader import get_video_info, _check_ffmpeg
from Undefined.bilibili.parser import normalize_to_bvid
from Undefined.bilibili.sender import send_bilibili_video
from Undefined.bilibili.wbi import parse_cookie_string
from Undefined.bilibili.wbi_request import request_with_wbi_fallback
from Undefined.config import get_config

logger = logging.getLogger(__name__)

_SEARCH_TYPE_ENDPOINT = "https://api.bilibili.com/x/web-interface/wbi/search/type"
_SEARCH_ALL_ENDPOINT = "https://api.bilibili.com/x/web-interface/wbi/search/all/v2"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}

_VALID_SEARCH_TYPES = {
    "video",
    "media_bangumi",
    "media_ft",
    "live",
    "live_room",
    "live_user",
    "article",
    "topic",
    "bili_user",
    "photo",
}


def _sanitize_text(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    text = re.sub(r"<[^>]+>", "", text)
    return text


def _to_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed


def _error_message(payload: dict[str, Any]) -> str:
    return _sanitize_text(payload.get("message") or payload.get("msg") or "未知错误")


def _endpoint_for_mode(mode: str) -> str:
    return _SEARCH_ALL_ENDPOINT if mode == "all" else _SEARCH_TYPE_ENDPOINT


def _params_for_mode(args: dict[str, Any], mode: str) -> tuple[dict[str, Any], str]:
    msg = _sanitize_text(args.get("msg"))
    if not msg:
        raise ValueError("请提供搜索内容")

    if mode == "all":
        params = {
            "keyword": msg,
            "page": _to_positive_int(args.get("page", 1), 1),
        }
        return params, "video"

    search_type = _sanitize_text(args.get("search_type") or "video").lower()
    if search_type not in _VALID_SEARCH_TYPES:
        raise ValueError(f"不支持的 search_type: {search_type}")

    params = {
        "search_type": search_type,
        "keyword": msg,
        "page": _to_positive_int(args.get("page", 1), 1),
    }

    if "order" in args and str(args["order"]).strip():
        params["order"] = _sanitize_text(args["order"])
    if "duration" in args and str(args["duration"]).strip():
        params["duration"] = _to_positive_int(args["duration"], 0)
    if "tids" in args and str(args["tids"]).strip():
        params["tids"] = _to_positive_int(args["tids"], 0)

    return params, search_type


def _extract_type_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []

    result = data.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        merged: list[dict[str, Any]] = []
        for value in result.values():
            if isinstance(value, list):
                merged.extend(item for item in value if isinstance(item, dict))
        return merged
    return []


def _extract_all_items(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return [], ""

    modules = data.get("result")
    if not isinstance(modules, list):
        return [], ""

    for module in modules:
        if not isinstance(module, dict):
            continue
        result_type = _sanitize_text(module.get("result_type"))
        items = module.get("data")
        if result_type == "video" and isinstance(items, list):
            return [item for item in items if isinstance(item, dict)], result_type

    for module in modules:
        if not isinstance(module, dict):
            continue
        result_type = _sanitize_text(module.get("result_type"))
        items = module.get("data")
        if isinstance(items, list) and items:
            return [item for item in items if isinstance(item, dict)], result_type

    return [], ""


def _item_url(item: dict[str, Any]) -> str:
    bvid = _sanitize_text(item.get("bvid"))
    if bvid:
        return f"https://www.bilibili.com/video/{bvid}"

    arcurl = _sanitize_text(item.get("arcurl"))
    if arcurl:
        return arcurl.replace("http://", "https://", 1)

    mid = _sanitize_text(item.get("mid"))
    if mid:
        return f"https://space.bilibili.com/{mid}"

    return ""


def _item_title(item: dict[str, Any]) -> str:
    for key in ("title", "uname", "name", "roomname"):
        text = _sanitize_text(item.get(key))
        if text:
            return text
    return "(无标题)"


def _item_author(item: dict[str, Any]) -> str:
    for key in ("author", "uname", "name"):
        text = _sanitize_text(item.get(key))
        if text:
            return text
    return ""


def _item_meta(item: dict[str, Any]) -> str:
    parts: list[str] = []
    duration = _sanitize_text(item.get("duration"))
    if duration:
        parts.append(f"时长 {duration}")

    play = _sanitize_text(item.get("play"))
    if play:
        parts.append(f"播放 {play}")

    pubdate = _sanitize_text(item.get("pubdate"))
    if pubdate and pubdate.isdigit():
        parts.append(f"发布时间戳 {pubdate}")

    if not parts:
        return ""
    return "（" + "，".join(parts) + "）"


def _format_items(
    *,
    query: str,
    mode: str,
    items: list[dict[str, Any]],
    limit: int,
    result_type: str,
) -> str:
    if not items:
        return f'未找到与"{query}"相关的结果。'

    header_type = result_type or ("video" if mode == "type" else "unknown")
    lines = [f"🔍 B站搜索结果（mode={mode}, type={header_type}）", ""]

    for idx, item in enumerate(items[:limit], start=1):
        title = _item_title(item)
        author = _item_author(item)
        link = _item_url(item)
        meta = _item_meta(item)

        lines.append(f"{idx}. {title}{meta}")
        if author:
            lines.append(f"   UP主: {author}")
        # 链接单独一行，使用特殊标记确保AI不会忽略
        if link:
            lines.append(f"   视频链接: {link}")

    return "\n".join(lines)


def _format_api_error(payload: dict[str, Any], cookie_ready: bool) -> str:
    code = payload.get("code")
    message = _error_message(payload)
    tips: list[str] = []
    if int(code or 0) == -412:
        tips.append("请求被风控拦截（-412）")
        if not cookie_ready:
            tips.append("当前未配置 bilibili.cookie（建议填完整浏览器 Cookie）")
        else:
            tips.append("已使用 Cookie，建议刷新最新完整 Cookie 后再试")
        tips.append("确保 Cookie 中包含 buvid3，且请求带 Referer/UA")
    elif int(code or 0) in (-352, -403):
        tips.append("触发风控或权限限制")

    details = f"B站搜索失败: {message} (code={code})"
    if not tips:
        return details
    return details + "\n" + "\n".join(f"- {tip}" for tip in tips)


async def execute(args: dict[str, Any], context: dict[str, Any]) -> str:
    query = _sanitize_text(args.get("msg"))
    if not query:
        return "请提供搜索内容。"

    # 检查是否为B站视频链接，使用 parser.normalize_to_bvid 统一解析
    bvid = await normalize_to_bvid(query)
    if bvid:
        # 成功解析到BV号，获取视频信息并自动下载发送
        try:
            config = get_config(strict=False)
            cookie_raw = str(config.bilibili_cookie or "").strip()

            video_info = await get_video_info(bvid, cookie=cookie_raw)

            # 格式化视频时长
            duration_min = video_info.duration // 60
            duration_sec = video_info.duration % 60
            duration_str = f"{duration_min}:{duration_sec:02d}"

            # 自动下载并发送视频
            sender = context.get("sender")
            onebot = context.get("onebot_client") or context.get("onebot")
            if not onebot and sender is not None and hasattr(sender, "onebot"):
                onebot = getattr(sender, "onebot")

            logger.info(f"[BilibiliSearch] sender={type(sender) if sender else None}, onebot={type(onebot) if onebot else None}")
            logger.info(f"[BilibiliSearch] context keys={list(context.keys())}")

            # 检查 ffmpeg 是否可用
            ffmpeg_available = await _check_ffmpeg()
            logger.info(f"[BilibiliSearch] ffmpeg_available={ffmpeg_available}")

            if sender and onebot and ffmpeg_available:
                # 解析目标会话
                request_type = context.get("request_type")
                target_type = None
                target_id = None

                if request_type == "group":
                    group_id = context.get("group_id")
                    if group_id:
                        target_type = "group"
                        target_id = int(group_id)
                elif request_type == "private":
                    user_id = context.get("user_id")
                    if user_id:
                        target_type = "private"
                        target_id = int(user_id)
                else:
                    # 兜底逻辑
                    group_id = context.get("group_id")
                    if group_id:
                        target_type = "group"
                        target_id = int(group_id)
                    user_id = context.get("user_id")
                    if user_id:
                        target_type = "private"
                        target_id = int(user_id)

                if target_type and target_id:
                    try:
                        # 获取运行时配置
                        runtime_config = context.get("runtime_config", {})
                        prefer_quality = getattr(runtime_config, "bilibili_prefer_quality", 80)
                        max_duration = getattr(runtime_config, "bilibili_max_duration", 600)
                        max_file_size = getattr(runtime_config, "bilibili_max_file_size", 100)
                        oversize_strategy = getattr(runtime_config, "bilibili_oversize_strategy", "downgrade")

                        # 调用 send_bilibili_video 下载并发送视频
                        result = await send_bilibili_video(
                            video_id=bvid,
                            sender=sender,
                            onebot=onebot,
                            target_type=target_type,  # type: ignore
                            target_id=target_id,
                            cookie=cookie_raw,
                            prefer_quality=prefer_quality,
                            max_duration=max_duration,
                            max_file_size=max_file_size,
                            oversize_strategy=oversize_strategy,
                        )

                        # 返回视频信息（send_bilibili_video 已经发送了视频和卡片）
                        info_lines = [
                            f"📺 已获取到B站视频信息：",
                            f"**视频标题**：{video_info.title}",
                            f"**UP主**：{video_info.up_name}",
                            f"**视频时长**：{duration_str}",
                            f"**视频封面**：{video_info.cover_url}",
                            f"**视频链接**：https://www.bilibili.com/video/{video_info.bvid}",
                        ]
                        # 添加视频简介（如果有的话）
                        if video_info.desc:
                            info_lines.append(f"**视频简介**：{video_info.desc[:500]}")  # 限制长度避免过长
                        # 添加发送结果提示
                        if result and "失败" in result and "ffmpeg" in result.lower():
                            info_lines.append(f"\n⚠️ 视频下载失败（需要安装 ffmpeg），已发送视频信息卡片")
                        elif result and "失败" not in result:
                            info_lines.append(f"\n✅ {result}")
                        return "\n".join(info_lines)

                    except Exception as exc:
                        logger.warning(f"下载发送视频失败 {bvid}: {exc}")
                        # 即使下载失败，也返回视频信息
                        info_lines = [
                            f"📺 已获取到B站视频信息：",
                            f"**视频标题**：{video_info.title}",
                            f"**UP主**：{video_info.up_name}",
                            f"**视频时长**：{duration_str}",
                            f"**视频封面**：{video_info.cover_url}",
                            f"**视频链接**：https://www.bilibili.com/video/{video_info.bvid}",
                        ]
                        # 添加视频简介（如果有的话）
                        if video_info.desc:
                            info_lines.append(f"**视频简介**：{video_info.desc[:500]}")  # 限制长度避免过长
                        return "\n".join(info_lines)
                else:
                    # 即使无法发送，也返回视频信息
                    info_lines = [
                        f"📺 已获取到B站视频信息：",
                        f"**视频标题**：{video_info.title}",
                        f"**UP主**：{video_info.up_name}",
                        f"**视频时长**：{duration_str}",
                        f"**视频封面**：{video_info.cover_url}",
                        f"**视频链接**：https://www.bilibili.com/video/{video_info.bvid}",
                    ]
                    # 添加视频简介（如果有的话）
                    if video_info.desc:
                        info_lines.append(f"**视频简介**：{video_info.desc[:500]}")  # 限制长度避免过长
                    return "\n".join(info_lines)
            else:
                # 即使无法发送，也返回视频信息
                info_lines = [
                    f"📺 已获取到B站视频信息：",
                    f"**视频标题**：{video_info.title}",
                    f"**UP主**：{video_info.up_name}",
                    f"**视频时长**：{duration_str}",
                    f"**视频封面**：{video_info.cover_url}",
                    f"**视频链接**：https://www.bilibili.com/video/{video_info.bvid}",
                ]
                # 添加视频简介（如果有的话）
                if video_info.desc:
                    info_lines.append(f"**视频简介**：{video_info.desc[:500]}")  # 限制长度避免过长
                return "\n".join(info_lines)

        except Exception as exc:
            logger.warning(f"获取视频信息失败 {bvid}: {exc}")
            # 即使获取失败，也返回视频链接
            lines = [
                f"📺 已获取到B站视频信息：",
                f"**视频链接**：https://www.bilibili.com/video/{bvid}",
            ]
            return "\n".join(lines)

    limit = _to_positive_int(args.get("n", 5), 5)
    limit = max(1, min(limit, 20))

    mode = _sanitize_text(args.get("mode") or "type").lower()
    if mode not in {"type", "all"}:
        return "mode 仅支持 type 或 all。"

    try:
        params, search_type = _params_for_mode(args, mode)
    except ValueError as exc:
        return str(exc)

    config = get_config(strict=False)
    cookie_raw = str(config.bilibili_cookie or "").strip()
    cookies = parse_cookie_string(cookie_raw)
    cookie_ready = bool(cookies)

    timeout_raw = float(config.network_request_timeout)
    timeout = timeout_raw if timeout_raw > 0 else 30.0
    endpoint = _endpoint_for_mode(mode)

    try:
        async with httpx.AsyncClient(
            headers=_HEADERS,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            payload = await request_with_wbi_fallback(
                client,
                endpoint=endpoint,
                params=params,
                log_prefix=f"[BilibiliSearch] mode={mode}",
            )

        if int(payload.get("code", -1)) != 0:
            return _format_api_error(payload, cookie_ready)

        if mode == "all":
            items, result_type = _extract_all_items(payload)
            return _format_items(
                query=query,
                mode=mode,
                items=items,
                limit=limit,
                result_type=result_type,
            )

        items = _extract_type_items(payload)
        return _format_items(
            query=query,
            mode=mode,
            items=items,
            limit=limit,
            result_type=search_type,
        )

    except Exception as exc:
        logger.exception("B站搜索失败: %s", exc)
        return "B站搜索失败，请稍后重试"

