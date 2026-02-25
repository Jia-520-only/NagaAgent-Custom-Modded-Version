#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务器 - 独立的MCP工具调度服务
基于博弈论的MCPServer设计，提供MCP工具调用的统一调度和管理
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .mcp_scheduler import MCPScheduler
from system.config import config, logger
# 能力发现逻辑已由注册中心承担，移除独立能力管理器
# 精简：移除流式工具调用与独立工具解析执行，统一走调度器与管理器

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI应用生命周期：替代 on_event startup/shutdown"""
    # startup
    logger.info("MCP服务器启动中...")

    # 初始化MCP管理器（用于工具调用执行）
    try:
        from mcpserver.mcp_manager import get_mcp_manager
        Modules.mcp_manager = get_mcp_manager()
        logger.info("MCP管理器初始化完成")

        # 手动触发MCP服务注册，避免循环导入死锁
        from mcpserver.mcp_registry import auto_register_mcp
        registered = auto_register_mcp()
        logger.info(f"MCP服务自动注册完成: {registered}")

        # 自动初始化QQ/微信Agent（如果启用）
        await initialize_qq_wechat_agent()

        # 自动初始化Undefined Agent
        await initialize_undefined_agent()

        # 自动初始化自我优化Agent
        await initialize_self_optimization_agent()

        # 自动初始化包豆AI视觉自动化Agent（如果启用）
        await initialize_baodou_agent()

        # 自动初始化应用启动器Agent（预扫描应用列表）
        await initialize_app_launcher_agent()

    except Exception as e:
        logger.warning(f"MCP管理器初始化失败: {e}")
        Modules.mcp_manager = None
    
    # 初始化调度器（注入mcp_manager）
    Modules.scheduler = MCPScheduler(Modules.mcp_manager)
    
    logger.info("MCP服务器启动完成")
    
    yield
    
    # shutdown
    logger.info("MCP服务器关闭中...")
    if Modules.scheduler:
        await Modules.scheduler.shutdown()
    logger.info("MCP服务器已关闭")


app = FastAPI(
    title="Naga MCP Server",
    description="独立的MCP工具调度服务",
    version="1.0.0",
    lifespan=lifespan
)

async def initialize_qq_wechat_agent():
    """自动初始化QQ/微信Agent的消息监听"""
    try:
        import json
        from mcpserver.mcp_registry import get_service_info
        import os
        from nagaagent_core.vendors.charset_normalizer import from_path
        from nagaagent_core.vendors import json5  # 支持带注释的JSON解析

        # 使用与 system.config 相同的配置加载逻辑
        config_path = "config.json"
        config_dict = None

        if os.path.exists(config_path):
            try:
                # 使用Charset Normalizer自动检测编码
                charset_results = from_path(config_path)
                if charset_results:
                    best_match = charset_results.best()
                    if best_match:
                        detected_encoding = best_match.encoding
                        logger.debug(f"检测到配置文件编码: {detected_encoding}")

                        # 使用检测到的编码直接打开文件,然后使用json5读取
                        with open(config_path, 'r', encoding=detected_encoding) as f:
                            try:
                                config_dict = json5.load(f)
                            except Exception as json5_error:
                                logger.warning(f"json5解析失败: {json5_error}")
                                # 回退到标准JSON库,去除注释
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
                                config_dict = json.loads(cleaned_content)
                else:
                    logger.warning(f"无法检测 {config_path} 的编码")
                    # 使用默认UTF-8
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_dict = json5.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")

        if not config_dict:
            logger.error("无法加载配置文件 config.json")
            return

        qq_wechat_config = config_dict.get("qq_wechat", {})
        qq_config = qq_wechat_config.get("qq", {})
        wechat_config = qq_wechat_config.get("wechat", {})

        # 检查QQ是否启用且需要自动回复
        if qq_config.get("enabled") and qq_config.get("enable_auto_reply"):
            logger.info("正在初始化QQ自动回复功能...")

            # 尝试两种可能的名称: agent_qq_wechat (文件夹名) 或 QQ/微信集成 (displayName)
            service_info = get_service_info("agent_qq_wechat")
            if not service_info:
                service_info = get_service_info("QQ/微信集成")

            if service_info:
                agent = service_info.get("instance")
                if agent and hasattr(agent, 'initialize'):
                    logger.info(f"找到Agent实例: {service_info.get('display_name', service_info.get('name'))}")
                    await agent.initialize(qq_wechat_config)
                    logger.info("✅ QQ/微信Agent初始化完成，消息监听已启用")
                else:
                    logger.warning("⚠️ agent_qq_wechat实例不存在或缺少initialize方法")
            else:
                logger.warning("⚠️ agent_qq_wechat未注册到MCP注册表")
        elif qq_config.get("enabled"):
            logger.info("QQ已启用但未启用自动回复 (enable_auto_reply=false)")
        else:
            logger.info("QQ未启用 (enabled=false)")

        # 检查微信
        if wechat_config.get("enabled") and wechat_config.get("enable_auto_reply"):
            logger.info("微信自动回复功能已启用")

    except Exception as e:
        logger.error(f"初始化QQ/微信Agent失败: {e}", exc_info=True)


async def initialize_undefined_agent():
    """自动初始化Undefined Agent"""
    try:
        import json
        import os
        from mcpserver.mcp_registry import get_service_info
        from nagaagent_core.vendors.charset_normalizer import from_path
        from nagaagent_core.vendors import json5  # 支持带注释的JSON解析

        # 使用与 system.config 相同的配置加载逻辑
        config_path = "config.json"
        config_dict = None

        if os.path.exists(config_path):
            try:
                # 使用Charset Normalizer自动检测编码
                charset_results = from_path(config_path)
                if charset_results:
                    best_match = charset_results.best()
                    if best_match:
                        detected_encoding = best_match.encoding
                        logger.debug(f"检测到配置文件编码: {detected_encoding}")

                        # 使用检测到的编码直接打开文件,然后使用json5读取
                        with open(config_path, 'r', encoding=detected_encoding) as f:
                            try:
                                config_dict = json5.load(f)
                            except Exception as json5_error:
                                logger.warning(f"json5解析失败: {json5_error}")
                                # 回退到标准JSON库,去除注释
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
                                config_dict = json.loads(cleaned_content)
                else:
                    logger.warning(f"无法检测 {config_path} 的编码")
                    # 使用默认UTF-8
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_dict = json5.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")

        if not config_dict:
            logger.error("无法加载配置文件 config.json")
            return

        qq_wechat_config = config_dict.get("qq_wechat", {})
        qq_config = qq_wechat_config.get("qq", {})

        # 检查是否启用了Undefined工具
        if qq_config.get("enable_undefined_tools", False):
            logger.info("正在初始化Undefined工具集...")

            service_info = get_service_info("agent_undefined")
            if not service_info:
                service_info = get_service_info("Undefined工具集")

            if service_info:
                agent = service_info.get("instance")
                if agent and hasattr(agent, 'initialize'):
                    logger.info(f"找到Undefined实例: {service_info.get('display_name', service_info.get('name'))}")
                    # 使用同步初始化方法
                    if hasattr(agent, 'initialize_sync'):
                        agent.initialize_sync()
                    else:
                        # 创建新事件循环运行异步初始化
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(agent.initialize())
                        finally:
                            loop.close()
                    # 获取工具数量（同步方法）
                    tool_count = 0
                    if hasattr(agent, 'get_available_tools'):
                        try:
                            tools = agent.get_available_tools()
                            tool_count = len(tools)
                        except Exception as e:
                            logger.warning(f"获取Undefined工具列表失败: {e}")
                    logger.info(f"✅ Undefined工具集初始化完成，共 {tool_count} 个工具")
                else:
                    logger.warning("⚠️ agent_undefined实例不存在或缺少initialize方法")
            else:
                logger.warning("⚠️ agent_undefined未注册到MCP注册表")
        else:
            logger.info("Undefined工具集未启用 (enable_undefined_tools=false)")

    except Exception as e:
        logger.error(f"初始化Undefined Agent失败: {e}", exc_info=True)


async def initialize_self_optimization_agent():
    """自动初始化自我优化Agent"""
    try:
        from mcpserver.mcp_registry import get_service_info

        service_info = get_service_info("自我优化系统")

        if service_info:
            agent = service_info.get("instance")
            if agent and hasattr(agent, 'initialize'):
                # AgentSelfOptimization的initialize是同步方法
                agent.initialize()
                logger.info("✅ 自我优化Agent初始化完成")
            else:
                logger.warning("⚠️ agent_self_optimization实例不存在或缺少initialize方法")
        else:
            logger.debug("自我优化系统未注册到MCP注册表")

    except Exception as e:
        logger.error(f"初始化自我优化Agent失败: {e}", exc_info=True)


async def initialize_baodou_agent():
    """自动初始化包豆AI视觉自动化Agent"""
    try:
        import json
        import os
        from mcpserver.mcp_registry import get_service_info
        from nagaagent_core.vendors.charset_normalizer import from_path
        from nagaagent_core.vendors import json5  # 支持带注释的JSON解析

        # 使用与 system.config 相同的配置加载逻辑
        config_path = "config.json"
        config_dict = None

        if os.path.exists(config_path):
            try:
                # 使用Charset Normalizer自动检测编码
                charset_results = from_path(config_path)
                if charset_results:
                    best_match = charset_results.best()
                    if best_match:
                        detected_encoding = best_match.encoding
                        logger.debug(f"检测到配置文件编码: {detected_encoding}")

                        # 使用检测到的编码直接打开文件,然后使用json5读取
                        with open(config_path, 'r', encoding=detected_encoding) as f:
                            try:
                                config_dict = json5.load(f)
                            except Exception as json5_error:
                                logger.warning(f"json5解析失败: {json5_error}")
                                # 回退到标准JSON库,去除注释
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
                                config_dict = json.loads(cleaned_content)
                else:
                    logger.warning(f"无法检测 {config_path} 的编码")
                    # 使用默认UTF-8
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_dict = json5.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")

        if not config_dict:
            logger.error("无法加载配置文件 config.json")
            return

        baodou_config = config_dict.get("baodou_ai", {})

        # 检查包豆AI是否启用
        if baodou_config.get("enabled", False):
            logger.info("正在初始化包豆AI视觉自动化服务...")

            # 尝试两种可能的名称: agent_baodou (文件夹名) 或 包豆AI视觉自动化 (displayName)
            service_info = get_service_info("agent_baodou")
            if not service_info:
                service_info = get_service_info("包豆AI视觉自动化")

            if service_info:
                agent = service_info.get("instance")
                if agent and hasattr(agent, 'initialize'):
                    logger.info(f"找到Agent实例: {service_info.get('display_name', service_info.get('name'))}")
                    # 调用initialize方法，传入完整配置
                    result = agent.initialize(config_dict)
                    if result:
                        logger.info("✅ 包豆AI视觉自动化服务初始化完成")
                    else:
                        logger.warning("⚠️ 包豆AI视觉自动化服务初始化失败")
                else:
                    logger.warning("⚠️ agent_baodou实例不存在或缺少initialize方法")
            else:
                logger.warning("⚠️ agent_baodou未注册到MCP注册表")
        else:
            logger.info("包豆AI视觉自动化服务未启用 (baodou_ai.enabled=false)")

    except Exception as e:
        logger.error(f"初始化包豆AI Agent失败: {e}", exc_info=True)


async def initialize_app_launcher_agent():
    """自动初始化应用启动器Agent，预先扫描应用列表"""
    try:
        from mcpserver.mcp_registry import get_service_info

        service_info = get_service_info("应用启动服务")
        if not service_info:
            service_info = get_service_info("agent_open_launcher")

        if service_info:
            agent = service_info.get("instance")
            if agent:
                logger.info("找到应用启动器实例，正在预先扫描应用列表...")

                # 异步预扫描应用列表，设置超时保护
                try:
                    # 使用wait_for设置超时，如果扫描时间超过30秒就跳过
                    # 首次使用时再扫描，避免启动阻塞
                    await asyncio.wait_for(agent.scanner.ensure_scan_completed(), timeout=30.0)
                    app_count = len(agent.scanner.apps_cache)
                    logger.info(f"✅ 应用启动器预扫描完成，共 {app_count} 个应用")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 应用启动器预扫描超时（>30秒），将在首次使用时异步扫描")
                except Exception as scan_error:
                    logger.warning(f"应用启动器预扫描失败: {scan_error}")
                    logger.info("应用列表将在首次使用时扫描")
            else:
                logger.warning("⚠️ 应用启动器实例不存在")
        else:
            logger.debug("应用启动服务未注册到MCP注册表")

    except Exception as e:
        logger.error(f"初始化应用启动器Agent失败: {e}", exc_info=True)


class Modules:
    """全局模块管理"""
    scheduler: Optional[MCPScheduler] = None
    # 任务注册表
    task_registry: Dict[str, Dict[str, Any]] = {}
    # 幂等性缓存
    completed_requests: Dict[str, Dict[str, Any]] = {}
    # MCP管理器（用于工具调用执行）
    mcp_manager: Optional[Any] = None

def _now_iso() -> str:
    """获取当前时间ISO格式"""
    return datetime.utcnow().isoformat() + "Z"

# （已迁移至 lifespan 上下文）

@app.post("/schedule")
async def schedule_mcp_task(payload: Dict[str, Any]):
    """
    调度MCP任务 - 主要入口点
    基于博弈论的MCPServer设计，提供统一的MCP工具调用调度
    """
    try:
        # 提取请求参数
        query = payload.get("query", "")
        tool_calls = payload.get("tool_calls", [])
        session_id = payload.get("session_id")
        request_id = payload.get("request_id", str(uuid.uuid4()))
        callback_url = payload.get("callback_url")
        
        if not query and not tool_calls:
            raise HTTPException(400, "query或tool_calls不能同时为空")
        
        # 幂等性检查
        if request_id in Modules.completed_requests:
            logger.info(f"幂等请求命中: {request_id}")
            return Modules.completed_requests[request_id]
        
        # 任务去重检查
        if Modules.scheduler:
            is_duplicate, matched_id = await Modules.scheduler.check_duplicate(query, tool_calls)
            if is_duplicate:
                logger.info(f"任务重复，跳过: {query[:50]}... (匹配: {matched_id})")
                response = {
                    "success": True,
                    "task_id": matched_id,
                    "message": "任务重复，已跳过",
                    "idempotent": True,
                    "request_id": request_id
                }
                Modules.completed_requests[request_id] = response
                return response
        
        # 并发控制
        if Modules.scheduler and len(Modules.scheduler.active_tasks) >= 50:
            raise HTTPException(429, "MCP调度器繁忙，请稍后再试")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task_info = {
            "id": task_id,
            "query": query,
            "tool_calls": tool_calls,
            "session_id": session_id,
            "request_id": request_id,
            "callback_url": callback_url,
            "status": "queued",
            "created_at": _now_iso(),
            "result": None,
            "error": None
        }
        
        Modules.task_registry[task_id] = task_info
        
        # 调度执行
        if Modules.scheduler:
            result = await Modules.scheduler.schedule_task(task_info)
            task_info.update(result)

            # 缓存结果
            response = {
                "success": result.get("success", False),
                "task_id": task_id,
                "message": result.get("message", ""),
                "result": result.get("result"),
                "request_id": request_id
            }
            Modules.completed_requests[request_id] = response
            return response
        else:
            raise HTTPException(500, "MCP调度器未初始化")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP任务调度失败: {e}")
        raise HTTPException(500, f"内部服务器错误: {str(e)}")

@app.get("/status")
async def get_mcp_status():
    """获取MCP服务器状态"""
    try:
        status = {
            "server": "running",
            "timestamp": _now_iso(),
            "tasks": {
                "total": len(Modules.task_registry),
                "active": len([t for t in Modules.task_registry.values() if t.get("status") == "running"]),
                "completed": len([t for t in Modules.task_registry.values() if t.get("status") == "completed"]),
                "failed": len([t for t in Modules.task_registry.values() if t.get("status") == "failed"])
            }
        }
        
        if Modules.scheduler:
            scheduler_status = await Modules.scheduler.get_status()
            status["scheduler"] = scheduler_status
            
    # 能力统计可由注册中心提供（此处先省略）
        
        return status
        
    except Exception as e:
        logger.error(f"获取MCP状态失败: {e}")
        raise HTTPException(500, f"获取状态失败: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取特定任务状态"""
    if task_id not in Modules.task_registry:
        raise HTTPException(404, "任务不存在")
    
    return Modules.task_registry[task_id]

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, session_id: Optional[str] = None):
    """列出任务"""
    tasks = list(Modules.task_registry.values())
    
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    
    if session_id:
        tasks = [t for t in tasks if t.get("session_id") == session_id]
    
    return {"tasks": tasks, "count": len(tasks)}

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id not in Modules.task_registry:
        raise HTTPException(404, "任务不存在")
    
    task = Modules.task_registry[task_id]
    if task.get("status") in ["completed", "failed"]:
        raise HTTPException(400, "任务已完成，无法取消")
    
    if Modules.scheduler:
        await Modules.scheduler.cancel_task(task_id)
    
    task["status"] = "cancelled"
    task["cancelled_at"] = _now_iso()
    
    return {"success": True, "message": "任务已取消"}

# 流式处理统一通过 /schedule 进入调度流程
# 工具结果回调由apiserver统一处理

if __name__ == "__main__":
    import uvicorn
    try:
        from system.config import get_server_port
        port = get_server_port("mcp_server")
    except ImportError:
        port = 8003  # 回退默认值
    uvicorn.run(app, host="0.0.0.0", port=port)
