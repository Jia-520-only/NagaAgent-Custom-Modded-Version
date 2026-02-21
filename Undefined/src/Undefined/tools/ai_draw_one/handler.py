from typing import Any, Dict
import httpx
import logging
from pathlib import Path
import uuid
import sys
import base64
from os.path import dirname, join, abspath

logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
project_root = dirname(dirname(dirname(dirname(dirname(abspath(__file__))))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def execute(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    # 支持 prompt 和 param_name 两种参数名
    prompt = args.get("prompt") or args.get("param_name", "")
    model = args.get("model", "")
    size = args.get("size", "")
    target_id = args.get("target_id")
    message_type = args.get("message_type")

    # 检查必要参数
    if not prompt or not prompt.strip():
        return "错误：缺少绘图提示词（prompt参数）"

    # 尝试从配置读取 API 设置
    try:
        from system.config import get_config
        config = get_config()
        url = config.online_ai_draw.api_url
        api_key = config.online_ai_draw.api_key
        default_model = config.online_ai_draw.default_model
        default_size = config.online_ai_draw.default_size
        timeout = config.online_ai_draw.timeout
    except Exception as e:
        logger.warning(f"无法读取配置，使用默认值: {e}")
        url = "https://api.xingzhige.com/API/DrawOne/"
        api_key = ""
        default_model = "anything-v5"
        default_size = "1:1"
        timeout = 60

    # 使用配置中的默认值，如果参数未提供
    if not model:
        model = default_model
    if not size:
        size = default_size

    try:
        # 判断 API 类型
        if "bigmodel.cn" in url:
            # 智谱 GLM 绘图 API
            return await _call_zhipu_ai_draw(url, api_key, prompt, model, size, timeout, target_id, message_type, context)
        else:
            # 通用绘图 API (GET 请求)
            return await _call_generic_draw_api(url, api_key, prompt, model, size, timeout, target_id, message_type, context)
    except Exception as e:
        logger.exception(f"AI 绘图失败: {e}")
        return f"AI 绘图失败: {e}"

async def _call_zhipu_ai_draw(url: str, api_key: str, prompt: str, model: str, size: str, timeout: int, target_id: int, message_type: str, context: Dict[str, Any]) -> str:
    """调用智谱 GLM 绘图 API"""
    try:
        # 智谱 GLM 绘图 API 路径
        draw_url = "https://open.bigmodel.cn/api/paas/v4/images/generations"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 智谱 API 基础参数
        payload = {
            "model": model if model else "cogview-3",
            "prompt": prompt
        }

        # 智谱 API 可能不使用 size 参数，或者格式不同
        # 尝试添加 size 参数，如果失败则不添加
        if size and size.strip():
            width, height = _parse_size_for_zhipu(size)
            # 尝试标准格式
            payload["size"] = f"{width}*{height}"

        logger.info(f"智谱API调用参数: model={payload.get('model')}, size={payload.get('size', '未设置')}, prompt={prompt[:50] if prompt else '未设置'}")

        # 打印完整的请求payload用于调试
        logger.debug(f"智谱API完整请求: {payload}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(draw_url, json=payload, headers=headers)

            if response.status_code != 200:
                error_text = response.text
                # 如果是 size 参数错误，尝试不使用 size 参数
                if "size" in error_text.lower():
                    logger.warning("智谱API拒绝size参数，尝试不带size重新请求")
                    payload_without_size = {
                        "model": payload["model"],
                        "prompt": payload["prompt"]
                    }
                    response = await client.post(draw_url, json=payload_without_size, headers=headers)

                    if response.status_code != 200:
                        return f"智谱API调用失败: {response.status_code} - {response.text}"
                else:
                    return f"智谱API调用失败: {response.status_code} - {response.text}"

            data = response.json()

            # 智谱返回的图片是 base64 编码的
            if "data" not in data or not data["data"]:
                return f"智谱API返回数据格式错误: {data}"

            # 获取第一张图片
            image_b64 = data["data"][0].get("b64_json")
            if not image_b64:
                # 尝试 url 字段
                image_url = data["data"][0].get("url")
                if image_url:
                    return await _download_and_send_image(image_url, target_id, message_type, context, "智谱AI绘图")
                return f"未找到图片数据: {data}"

            # 解码 base64 图片
            image_data = base64.b64decode(image_b64)

            # 保存图片
            filename = f"ai_draw_{uuid.uuid4().hex[:8]}.png"
            filepath = Path.cwd() / "img" / filename
            filepath.parent.mkdir(exist_ok=True)

            with open(filepath, "wb") as f:
                f.write(image_data)

            return await _send_image_callback(filepath, target_id, message_type, context, "智谱AI绘图")

    except Exception as e:
        logger.exception(f"智谱绘图失败: {e}")
        return f"智谱绘图失败: {e}"

async def _call_generic_draw_api(url: str, api_key: str, prompt: str, model: str, size: str, timeout: int, target_id: int, message_type: str, context: Dict[str, Any]) -> str:
    """调用通用绘图 API (GET 请求)"""
    try:
        params = {
            "prompt": prompt,
            "model": model,
            "size": size
        }

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params, headers=headers)

            try:
                data = response.json()
            except Exception:
                return f"API 返回错误 (非JSON): {response.text[:100]}"

            image_url = data.get("url") or data.get("image") or data.get("img")

            if not image_url and "data" in data and isinstance(data["data"], str):
                image_url = data["data"]

            if not image_url:
                return f"未找到图片链接: {data}"

            return await _download_and_send_image(image_url, target_id, message_type, context, "云端AI绘图")

    except Exception as e:
        logger.exception(f"通用绘图失败: {e}")
        return f"通用绘图失败: {e}"

async def _download_and_send_image(image_url: str, target_id: int, message_type: str, context: Dict[str, Any], source_name: str = "AI绘图") -> str:
    """下载并发送图片"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            img_response = await client.get(image_url)
            img_response.raise_for_status()

        # 保存图片
        filename = f"ai_draw_{uuid.uuid4().hex[:8]}.jpg"
        filepath = Path.cwd() / "img" / filename
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(img_response.content)

        return await _send_image_callback(filepath, target_id, message_type, context, source_name)
    except Exception as e:
        logger.exception(f"下载图片失败: {e}")
        return f"下载图片失败: {e}"

async def _send_image_callback(filepath: Path, target_id: int, message_type: str, context: Dict[str, Any], source_name: str) -> str:
    """发送图片回调"""
    try:
        logger.info(f"[图片回调] 准备发送图片: filepath={filepath}, target_id={target_id}, message_type={message_type}")
        logger.info(f"[图片回调] context中的key: {list(context.keys()) if context else 'None'}")

        # 尝试使用 context 中的回调函数
        send_image_callback = context.get("send_image_callback")
        if send_image_callback:
            logger.info(f"[图片回调] 找到send_image_callback，开始发送...")
            await send_image_callback(target_id, message_type, str(filepath))
            logger.info(f"[图片回调] send_image_callback调用完成")
            # 返回空字符串，表示图片已通过回调发送，不需要再发送文本
            return ""
        else:
            # 没有回调函数，返回文件路径
            logger.warning(f"[图片回调] 未找到send_image_callback，context={context}")
            return f"{source_name}成功，图片已保存: {filepath.name}"
    except Exception as e:
        logger.exception(f"发送图片回调失败: {e}")
        return f"{source_name}成功，但发送失败: {e}"

def _parse_size_for_zhipu(size_str: str) -> tuple:
    """解析尺寸字符串为智谱API要求的宽高"""
    # 智谱 API 支持的尺寸（根据官方文档）:
    # "1024*1024", "1024*768", "768*1024", "864*1152", "1152*864"
    size_str = size_str.lower().strip()

    # 比例映射到智谱支持的像素尺寸
    ratio_map = {
        "1:1": (1024, 1024),
        "16:9": (1024, 576),   # 16:9 接近
        "9:16": (576, 1024),   # 9:16 接近
        "4:3": (1024, 768),
        "3:4": (768, 1024)
    }

    # 直接匹配比例
    if size_str in ratio_map:
        return ratio_map[size_str]

    # 尝试解析 "1024x1024" 或 "1024*1024" 格式
    if "x" in size_str or "*" in size_str:
        parts = size_str.replace("*", "x").split("x")
        if len(parts) == 2:
            try:
                w, h = int(parts[0]), int(parts[1])
                # 限制在合理范围内
                w = min(max(w, 512), 2048)
                h = min(max(h, 512), 2048)
                return w, h
            except ValueError:
                pass

    # 默认返回 1024x1024（最常用的尺寸）
    logger.warning(f"无法解析尺寸 '{size_str}'，使用默认值 1024*1024")
    return 1024, 1024

def _parse_size(size_str: str) -> tuple:
    """解析尺寸字符串为宽高（通用API）"""
    # 支持的格式: "1:1", "16:9", "512x512", "1024*768"
    size_str = size_str.lower()

    # 比例映射
    ratio_map = {
        "1:1": (1024, 1024),
        "16:9": (1024, 576),
        "9:16": (576, 1024),
        "4:3": (1024, 768),
        "3:4": (768, 1024)
    }

    if size_str in ratio_map:
        return ratio_map[size_str]

    # 尝试解析 "1024x1024" 格式
    if "x" in size_str:
        parts = size_str.split("x")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                pass

    # 默认返回 1024x1024
    return 1024, 1024
