from typing import Any, Dict
import httpx
import logging
import json
from pathlib import Path
import uuid
import asyncio

logger = logging.getLogger(__name__)

async def execute(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    使用本地 AI 绘图模型生成图片
    
    支持的本地服务：
    - Stable Diffusion WebUI (AUTOMATIC1111)
    - ComfyUI
    - Fooocus
    """
    prompt = args.get("prompt")
    if not prompt:
        return "请提供绘图提示词"
    
    negative_prompt = args.get("negative_prompt", "")
    width = args.get("width", 512)
    height = args.get("height", 512)
    steps = args.get("steps", 20)
    cfg_scale = args.get("cfg_scale", 7.0)
    model = args.get("model", "")
    
    target_id = args.get("target_id", 0)
    message_type = args.get("message_type", "private")
    
    try:
        # 从配置文件读取本地绘图服务地址
        # handler.py 在 e:/NagaAgent/Undefined/src/Undefined/tools/local_ai_draw/handler.py
        # 需要向上 6 级到 e:/NagaAgent/
        config_path = Path(__file__).parent.parent.parent.parent.parent.parent / "config.json"
        logger.info(f"[local_ai_draw] 尝试读取配置文件: {config_path}")
        logger.info(f"[local_ai_draw] __file__ = {__file__}")
        logger.info(f"[local_ai_draw] 文件是否存在: {config_path.exists()}")

        # 如果文件不存在,尝试其他可能的路径
        if not config_path.exists():
            # 尝试从当前工作目录
            cwd_config = Path.cwd() / "config.json"
            logger.info(f"[local_ai_draw] 尝试CWD配置文件: {cwd_config}, 存在: {cwd_config.exists()}")
            if cwd_config.exists():
                config_path = cwd_config
            else:
                # 尝试使用 resolve() 获取绝对路径
                config_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "config.json"
                logger.info(f"[local_ai_draw] 尝试resolve配置文件: {config_path}, 存在: {config_path.exists()}")

        if config_path.exists():
            # 使用 charset_normalizer 检测编码
            from nagaagent_core.vendors.charset_normalizer import from_path
            from nagaagent_core.vendors import json5  # 支持带注释的JSON

            charset_results = from_path(str(config_path))
            if charset_results:
                best_match = charset_results.best()
                if best_match:
                    detected_encoding = best_match.encoding
                    logger.debug(f"检测到配置文件编码: {detected_encoding}")

                    with open(config_path, 'r', encoding=detected_encoding) as f:
                        try:
                            config = json5.load(f)
                        except Exception as json5_error:
                            logger.warning(f"json5解析失败: {json5_error}, 尝试标准JSON")
                            f.seek(0)
                            content = f.read()
                            lines = content.split('\n')
                            cleaned_lines = []
                            for line in lines:
                                if '#' in line:
                                    line = line.split('#')[0].rstrip()
                                if line.strip():
                                    cleaned_lines.append(line)
                            cleaned_content = '\n'.join(cleaned_lines)
                            config = json.loads(cleaned_content)
                    local_draw_config = config.get("local_ai_draw", {})
                    logger.info(f"[local_ai_draw] 读取到的local_ai_draw配置: {local_draw_config}")
                else:
                    logger.warning(f"无法检测配置文件编码,使用默认配置")
                    local_draw_config = {}
            else:
                logger.warning(f"无法检测配置文件编码,使用默认配置")
                local_draw_config = {}
        else:
            logger.error(f"[local_ai_draw] 配置文件不存在: {config_path}")
            local_draw_config = {}

        # 获取服务地址（支持多种后端）
        service_url = local_draw_config.get("service_url", "")
        logger.info(f"[local_ai_draw] service_url = {service_url}")

        if not service_url:
            return "本地绘图服务未配置，请在 config.json 中配置 local_ai_draw.service_url"
        
        service_type = local_draw_config.get("service_type", "auto")
        
        # 根据服务类型选择API端点
        if service_type == "auto":
            # 自动检测服务类型
            if "api/sdapi/v1" in service_url or "sdapi" in service_url:
                service_type = "sd_webui"
            elif "api/prompt" in service_url or "comfyui" in service_url:
                service_type = "comfyui"
            else:
                service_type = "sd_webui"  # 默认
        
        logger.info(f"使用本地绘图服务: {service_type} at {service_url}")
        
        # Stable Diffusion WebUI API
        if service_type == "sd_webui":
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "sampler_name": local_draw_config.get("sampler", "Euler a"),
            }
            
            if model:
                payload["override_settings"] = {"sd_model_checkpoint": model}
            
            api_url = f"{service_url.rstrip('/')}/sdapi/v1/txt2img"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # 从响应中提取图片
                if "images" in data and len(data["images"]) > 0:
                    import base64
                    image_data = base64.b64decode(data["images"][0])
                else:
                    return f"API 返回格式异常: {data}"
        
        # ComfyUI API
        elif service_type == "comfyui":
            # 构建 ComfyUI prompt
            payload = {
                "prompt": {
                    "3": {
                        "inputs": {
                            "seed": 0,
                            "steps": steps,
                            "cfg": cfg_scale,
                            "sampler_name": local_draw_config.get("sampler", "euler"),
                            "scheduler": "normal",
                            "denoise": 1,
                            "model": local_draw_config.get("model", "") or ["4", 0],
                            "positive": ["6", 0],
                            "negative": ["7", 0],
                            "latent_image": ["5", 0],
                        },
                        "class_type": "KSampler"
                    },
                    "4": {
                        "inputs": {
                            "width": width,
                            "height": height,
                            "batch_size": 1
                        },
                        "class_type": "EmptyLatentImage"
                    },
                    "5": {
                        "inputs": {
                            "text": prompt,
                            "clip": ["1", 1]
                        },
                        "class_type": "CLIPTextEncode"
                    },
                    "6": {
                        "inputs": {
                            "text": negative_prompt,
                            "clip": ["1", 1]
                        },
                        "class_type": "CLIPTextEncode"
                    },
                    "7": {
                        "inputs": {
                            "samples": ["3", 0],
                            "vae": ["1", 2]
                        },
                        "class_type": "VAEDecode"
                    },
                    "8": {
                        "inputs": {
                            "filename_prefix": f"naga_{uuid.uuid4().hex[:8]}",
                            "images": ["7", 0]
                        },
                        "class_type": "SaveImage"
                    },
                    "1": {
                        "inputs": {
                            "ckpt_name": model or local_draw_config.get("model", "v1-5-pruned.ckpt")
                        },
                        "class_type": "CheckpointLoaderSimple"
                    }
                }
            }
            
            api_url = f"{service_url.rstrip('/')}/api/prompt"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # ComfyUI 会保存图片到磁盘，这里简化处理
                # 实际应该查询历史记录获取图片
                prompt_id = data.get("prompt_id", "")
                return f"ComfyUI 已接受绘图请求 (ID: {prompt_id})，请在服务目录查看生成的图片"
        
        else:
            return f"不支持的服务类型: {service_type}"
        
        # 保存图片到本地
        filename = f"local_draw_{uuid.uuid4().hex[:8]}.png"
        filepath = Path.cwd() / "img" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        logger.info(f"图片已保存: {filepath}")
        
        # 发送图片到QQ
        send_image_callback = context.get("send_image_callback")
        if send_image_callback:
            await send_image_callback(int(target_id), message_type, str(filepath))
            return f"本地 AI 绘图已生成并发送到 {message_type} {target_id}"
        else:
            return f"图片已生成并保存到: {filepath}"
    
    except httpx.HTTPStatusError as e:
        logger.exception(f"本地绘图服务 HTTP 错误: {e}")
        return f"绘图服务请求失败: {e.response.status_code} - 请检查服务是否运行"
    except httpx.ConnectError as e:
        logger.exception(f"无法连接到本地绘图服务: {e}")
        return f"无法连接到绘图服务，请确认服务地址正确且服务正在运行"
    except Exception as e:
        logger.exception(f"本地 AI 绘图失败: {e}")
        return f"绘图失败: {str(e)}"
