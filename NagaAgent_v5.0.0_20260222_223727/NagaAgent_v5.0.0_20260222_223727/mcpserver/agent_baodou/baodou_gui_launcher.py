"""
包豆AI GUI启动器模块
在弥娅启动时自动启动包豆GUI，实现统一交互界面
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional
import time

# 项目根目录 (从 mcpserver/agent_baodou/ 向上两级到达项目根目录)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BAODOU_PATH = PROJECT_ROOT / "baodou_AI"


class BaodouGUILauncher:
    """包豆GUI启动器"""

    def __init__(self):
        self.gui_process: Optional[subprocess.Popen] = None
        self.startup_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._startup_completed = False

    def is_running(self) -> bool:
        """检查GUI是否运行中"""
        return self._is_running and self.gui_process is not None and self.gui_process.poll() is None

    def is_startup_completed(self) -> bool:
        """检查启动是否完成"""
        return self._startup_completed

    def start_gui(self, wait_ready: bool = False) -> bool:
        """启动包豆GUI

        Args:
            wait_ready: 是否等待GUI完全启动后再返回

        Returns:
            bool: 是否启动成功
        """
        if self.is_running():
            print("[包豆GUI] 包豆GUI已在运行中")
            return True

        try:
            # 检查包豆GUI程序是否存在
            gui_script = BAODOU_PATH / "pyqt_main.py"
            if not gui_script.exists():
                print(f"[包豆GUI] 包豆GUI脚本不存在: {gui_script}")
                return False

            print(f"[包豆GUI] 正在准备启动包豆GUI...")
            print(f"   脚本路径: {gui_script}")
            print(f"   工作目录: {BAODOU_PATH}")

            # 在新线程中启动GUI，避免阻塞主程序
            def _start_in_thread():
                try:
                    print("[包豆GUI] 正在启动包豆GUI进程...")

                    # Windows下不使用CREATE_NO_WINDOW，这样可以看到输出
                    creation_flags = 0
                    if os.name == 'nt':
                        # 不使用CREATE_NO_WINDOW，允许GUI显示
                        pass

                    # 使用subprocess启动独立的Python进程运行包豆GUI
                    # 使用当前Python解释器
                    # Windows GUI程序不需要重定向stdout/stderr
                    self.gui_process = subprocess.Popen(
                        [sys.executable, str(gui_script)],
                        cwd=str(BAODOU_PATH),
                        creationflags=creation_flags
                    )

                    self._is_running = True
                    print(f"[包豆GUI] 包豆GUI进程已创建 (PID: {self.gui_process.pid})")

                    # 简单等待一下，让GUI有时间初始化
                    time.sleep(2)

                    self._startup_completed = True
                    print("[包豆GUI] 包豆GUI启动完成")

                    # 等待进程结束
                    self.gui_process.wait()
                    self._is_running = False
                    print("[包豆GUI] 包豆GUI已关闭")

                except Exception as e:
                    print(f"[包豆GUI] 启动包豆GUI失败: {e}")
                    self._is_running = False
                    self._startup_completed = False

            # 启动线程
            self.startup_thread = threading.Thread(target=_start_in_thread, daemon=True)
            self.startup_thread.start()

            if wait_ready:
                # 等待启动完成（最多等待10秒）
                max_wait = 10
                waited = 0
                while not self._startup_completed and waited < max_wait:
                    time.sleep(0.5)
                    waited += 0.5

                if not self._startup_completed:
                    print(f"[包豆GUI] 包豆GUI启动超时（等待{max_wait}秒）")
                    return False

            return True

        except Exception as e:
            print(f"[包豆GUI] 启动包豆GUI异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop_gui(self) -> bool:
        """停止包豆GUI

        Returns:
            bool: 是否停止成功
        """
        if not self.is_running():
            print("[包豆GUI] 包豆GUI未运行")
            return True

        try:
            if self.gui_process:
                # 优雅关闭
                self.gui_process.terminate()
                # 等待进程结束
                try:
                    self.gui_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制关闭
                    self.gui_process.kill()
                    self.gui_process.wait()

                self._is_running = False
                self._startup_completed = False
                print("[包豆GUI] 包豆GUI已停止")
                return True

        except Exception as e:
            print(f"[包豆GUI] 停止包豆GUI失败: {e}")
            return False

        return False

    def restart_gui(self) -> bool:
        """重启包豆GUI

        Returns:
            bool: 是否重启成功
        """
        print("[包豆GUI] 正在重启包豆GUI...")
        self.stop_gui()
        time.sleep(1)
        return self.start_gui()


# 全局启动器实例
_launcher: Optional[BaodouGUILauncher] = None


def get_launcher() -> BaodouGUILauncher:
    """获取启动器单例"""
    global _launcher
    if _launcher is None:
        _launcher = BaodouGUILauncher()
    return _launcher


def initialize_launcher():
    """初始化启动器"""
    global _launcher
    _launcher = BaodouGUILauncher()
    return _launcher


def check_baodou_enabled() -> bool:
    """检查包豆是否在配置中启用"""
    try:
        config_path = PROJECT_ROOT / "config.json"
        print(f"[检查包豆] 配置文件路径: {config_path}")
        print(f"[检查包豆] 文件是否存在: {config_path.exists()}")

        if not config_path.exists():
            print(f"[检查包豆] 配置文件不存在")
            return False

        # 使用项目已有的json5模块读取配置
        try:
            from nagaagent_core.vendors import json5
            # 自动检测编码并读取配置
            config_text = config_path.read_text(encoding='utf-8')
            config_data = json5.loads(config_text)
            print(f"[检查包豆] 使用json5成功读取配置")
        except UnicodeDecodeError:
            # 回退到UTF-16编码
            from nagaagent_core.vendors import json5
            config_data = json5.loads(config_path.read_text(encoding='utf-16'))
            print(f"[检查包豆] 使用json5 (UTF-16) 成功读取配置")
        except ImportError:
            # 如果json5不可用，回退到标准json
            import json
            try:
                config_data = json.loads(config_path.read_text(encoding='utf-8'))
                print(f"[检查包豆] 使用json成功读取配置")
            except UnicodeDecodeError:
                config_data = json.loads(config_path.read_text(encoding='utf-16'))
                print(f"[检查包豆] 使用json (UTF-16) 成功读取配置")

        baodou_config = config_data.get("baodou_ai", {})
        print(f"[检查包豆] 包豆配置: {baodou_config}")

        # 只检查 enabled 标志，不检查 API 密钥（GUI可以独立配置）
        enabled = baodou_config.get("enabled", False)
        print(f"[检查包豆] 包豆启用状态: {enabled}")

        return enabled

    except Exception as e:
        print(f"[检查包豆] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def auto_start_baodou_gui():
    """自动启动包豆GUI（如果在配置中启用）"""
    print("=" * 50)
    print("[包豆GUI] 开始自动启动检查")
    print("=" * 50)

    if not check_baodou_enabled():
        print("[包豆GUI] 包豆AI未启用，跳过GUI启动")
        print("   提示: 如需启用，请在config.json中设置 baodou_ai.enabled = true")
        print("=" * 50)
        return False

    try:
        print("[包豆GUI] 包豆AI已启用，准备启动...")
        launcher = get_launcher()

        # 检查包豆GUI脚本是否存在
        gui_script = BAODOU_PATH / "pyqt_main.py"
        print(f"[包豆GUI] 检查GUI脚本: {gui_script}")
        print(f"[包豆GUI] 脚本存在: {gui_script.exists()}")

        if not gui_script.exists():
            print(f"[包豆GUI] 包豆GUI脚本不存在: {gui_script}，跳过启动")
            print("=" * 50)
            return False

        print("[包豆GUI] 开始启动GUI进程...")
        result = launcher.start_gui(wait_ready=True)

        if result:
            print("[包豆GUI] 包豆GUI已自动启动")
        else:
            print("[包豆GUI] 包豆GUI启动失败（可能是依赖缺失或配置问题）")
            print(f"   提示: 你可以手动运行: python {gui_script}")

        print("=" * 50)
        return result

    except Exception as e:
        print(f"[包豆GUI] 自动启动失败: {e}")
        print(f"   提示: 你可以手动运行: python {BAODOU_PATH / 'pyqt_main.py'}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return False
