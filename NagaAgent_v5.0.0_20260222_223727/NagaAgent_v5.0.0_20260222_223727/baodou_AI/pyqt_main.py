import sys
import time
import ctypes
import os
import json
import platform
import re
from mac_app_utils import is_mac_app, get_app_resource_path, get_resource_file_path

# 仅在开发环境中设置Qt平台插件路径，打包时自动处理
if os.path.exists('venv/Lib/site-packages'):
    sys.path.append('venv/Lib/site-packages')

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QPushButton, QLabel, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QCursor

# Windows API常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x00000080  # 工具窗口样式，不会在任务栏显示，也不会被Alt+Tab切换到

# 新增：SetWindowDisplayAffinity 常量，用于防止窗口被截图
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# 定义AI坐标监测常量
AI_COORDINATE_THRESHOLD = 500  # AI输出坐标与窗口的安全距离
WINDOW_MOVE_DISTANCE = 600  # 窗口移动距离，超过500像素

# 导入AI控制相关函数
import vl_model_test_doubao2
from vl_model_test_doubao2 import auto_control_computer, set_coordinate_callback

# 导入日志窗口模块
from log_window import init_log_window

# 导入任务队列系统
from task_queue import get_task_queue

# 创建一个工作线程来运行AI控制逻辑
class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    ai_coordinate = pyqtSignal(float, float)  # 发送AI输出的坐标信号，使用浮点数类型
    
    def __init__(self, user_content, parent=None):
        super().__init__(parent)
        self.user_content = user_content
        
    def run(self):
        try:
            # 设置坐标回调函数
            def coordinate_callback(coords):
                # 将坐标发送给主线程
                self.ai_coordinate.emit(coords[0], coords[1])
            
            set_coordinate_callback(coordinate_callback)
            
            # 获取时间字符串，年月日时分
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
            # 用户输入内容添加时间
            user_content2 = "当前时间为:"+time_str + "\n" + "用户任务为:"+self.user_content
            print(f"=============用户输入内容为:{user_content2}")
            result = auto_control_computer(user_content2)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class AIWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ai_thread = None
        self.is_ai_controlling = False  # 标记是否由AI控制鼠标
        self.mouse_monitor_timer = None  # 鼠标监测定时器
        self._current_naya_task_id = None  # 当前执行的弥娅任务ID
        self.initUI()

        # 启动任务队列定时器，每2秒检查一次是否有新任务
        self.task_check_timer = QTimer(self)
        self.task_check_timer.timeout.connect(self.check_and_process_naya_tasks)
        self.task_check_timer.start(2000)  # 2000ms = 2秒

        # 启动清理定时器，每60秒清理一次旧任务
        self.task_cleanup_timer = QTimer(self)
        self.task_cleanup_timer.timeout.connect(self.cleanup_old_tasks)
        self.task_cleanup_timer.start(60000)  # 60000ms = 60秒

        print("[包豆GUI] 任务队列定时器已启动，每2秒检查一次新任务")
        print("[包豆GUI] 任务清理定时器已启动，每60秒清理一次旧任务")
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('包豆电脑')
        self.setGeometry(100, 100, 520, 320)
        
        # 设置窗口标志：
        # - Qt.WindowStaysOnTopHint: 窗口始终在最顶层
        # - Qt.Window: 标准窗口样式
        # - Qt.WindowCloseButtonHint: 显示关闭按钮
        # - Qt.WindowMinimizeButtonHint: 显示最小化按钮
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window | 
                          Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 设置窗口透明度，使其更加隐蔽
        self.setWindowOpacity(0.9)
        
        # 显示窗口
        self.show()
        
        # 获取当前操作系统
        current_os = platform.system()
        
        if current_os == "Windows":
            # 获取窗口句柄
            hwnd = self.winId().__int__()
            
            # 使用Windows API设置窗口为分层窗口
            user32 = ctypes.windll.user32
            
            # 获取当前扩展样式
            current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # 设置新的扩展样式：添加WS_EX_LAYERED
            new_style = current_style | WS_EX_LAYERED
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            # 设置窗口为透明，但允许鼠标事件
            user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.9), 0x00000002)
            
            # 新增：使用SetWindowDisplayAffinity使窗口不被CV2等截图工具捕捉
            # 这是Windows 10版本1803及以上支持的功能
            try:
                user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                print("窗口已设置为不可被截图")
            except Exception as e:
                print(f"设置窗口不可被截图时出错: {e}")
        elif current_os == "Darwin":  # macOS
            # 在macOS上，Qt的setWindowOpacity方法应该可以正常工作
            print("macOS系统：窗口透明度设置已应用")
            
            # 尝试设置窗口不可被截图（macOS特定方法）
            try:
                # 尝试导入objc模块（需要安装pyobjc库）
                import objc
                from AppKit import NSWindow, NSWindowSharingNone, NSApplication
                
                # 获取当前应用程序
                app = NSApplication.sharedApplication()
                
                # 获取所有窗口
                windows = app.windows()
                
                # 查找当前PyQt窗口对应的NSWindow
                pyqt_win_id = self.winId()
                
                for window in windows:
                    # 比较窗口标题
                    if window.title() == self.windowTitle():
                        # 设置窗口为不可共享
                        window.setSharingType_(NSWindowSharingNone)
                        print("macOS系统：窗口已设置为不可被截图")
                        
                        # 尝试设置窗口级别为最高，减少被截图的可能性
                        window.setLevel_(1000)  # 使用数值设置窗口级别，1000足够高
                        print("macOS系统：窗口级别已设置为最高")
                        break
                
                # 额外尝试：使用Core Graphics设置窗口属性
                try:
                    from Quartz import (CGWindowLevelForKey, kCGMaximumWindowLevelKey,
                                      CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
                                      kCGNullWindowID, CGSNewWindowWithOpaqueShape)
                    
                    # 获取窗口信息
                    window_info = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                    
                    for info in window_info:
                        if 'kCGWindowName' in info and info['kCGWindowName'] == self.windowTitle():
                            # 获取窗口ID
                            window_id = info['kCGWindowNumber']
                            print(f"macOS系统：找到窗口ID: {window_id}")
                            break
                    
                except ImportError:
                    print("macOS系统：Quartz模块未安装，跳过额外防截图设置")
                
            except Exception as e:
                print(f"macOS系统：设置窗口不可被截图时出错: {e}")
                print("注意：需要安装pyobjc库才能启用防截图功能")
        else:
            print(f"{current_os}系统：使用默认窗口设置")
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)  # 设置组件间距
        main_layout.setContentsMargins(15, 10, 15, 10)  # 设置边距
        
        # 创建标题标签 - 蓝色清新主题
        title_label = QLabel('包豆电脑')
        title_font = QFont('Microsoft YaHei', 16, QFont.Bold)  # 使用微软雅黑，稍大但不过大
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                padding: 8px;
                margin-bottom: 8px;
                background-color: #e3f2fd;
                border-radius: 10px;
                font-weight: bold;
                border: 2px solid #bbdefb;
            }
        """)
        main_layout.addWidget(title_label)
        
        # API密钥设置区域
        api_layout = QHBoxLayout()
        api_layout.setSpacing(8)
        
        # API密钥输入框 - 蓝色清新主题
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)  # 密码形式显示
        self.api_key_input.setPlaceholderText('请输入API密钥...')
        self.api_key_input.textChanged.connect(self.save_api_key)  # 文本变化时自动保存
        api_key_font = QFont('Microsoft YaHei', 11)  # 增大字体
        self.api_key_input.setFont(api_key_font)
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #90caf9;
                border-radius: 8px;
                background-color: #f5f9ff;
                color: #1565c0;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #2196f3;
                background-color: #ffffff;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #90caf9;
            }
        """)
        api_layout.addWidget(self.api_key_input)
        
        # 获取API密钥按钮 - 蓝色清新主题
        self.get_api_key_btn = QPushButton('获取密钥')
        self.get_api_key_btn.clicked.connect(self.open_api_key_url)
        button_font = QFont('Microsoft YaHei', 10, QFont.Bold)
        self.get_api_key_btn.setFont(button_font)
        self.get_api_key_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2);
                color: white;
                border: none;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #64b5f6, stop:1 #2196f3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976d2, stop:1 #0d47a1);
            }
        """)
        api_layout.addWidget(self.get_api_key_btn)
        
        main_layout.addLayout(api_layout)
        
        # 创建输入框 - 蓝色清新主题
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText('请输入您的需求，AI将帮您执行...')
        self.input_text.setFixedHeight(120)  # 增加高度
        input_font = QFont('Microsoft YaHei', 11)  # 增大字体
        self.input_text.setFont(input_font)
        self.input_text.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #90caf9;
                border-radius: 10px;
                background-color: #f5f9ff;
                color: #1565c0;
                font-size: 11pt;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #2196f3;
                background-color: #ffffff;
                outline: none;
            }
            QTextEdit::placeholder {
                color: #90caf9;
            }
        """)
        main_layout.addWidget(self.input_text)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 创建上传按钮 - 蓝色清新主题
        self.upload_btn = QPushButton('🚀 开始执行')
        self.upload_btn.clicked.connect(self.start_ai)
        upload_font = QFont('Microsoft YaHei', 12, QFont.Bold)  # 更大字体
        self.upload_btn.setFont(upload_font)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 40px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #64b5f6, stop:1 #2196f3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976d2, stop:1 #0d47a1);
            }
            QPushButton:disabled {
                background: #cfd8dc;
                color: #90a4ae;
            }
        """)
        button_layout.addWidget(self.upload_btn)
        
        # 创建停止按钮 - 蓝色清新主题（浅蓝色取消样式）
        self.stop_btn = QPushButton('⏹ 停止执行')
        self.stop_btn.clicked.connect(self.stop_ai)
        self.stop_btn.setEnabled(False)
        stop_font = QFont('Microsoft YaHei', 12, QFont.Bold)  # 更大字体
        self.stop_btn.setFont(stop_font)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #90caf9, stop:1 #42a5f5);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 40px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bbdefb, stop:1 #64b5f6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2);
            }
            QPushButton:disabled {
                background: #cfd8dc;
                color: #90a4ae;
            }
        """)
        button_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(button_layout)
        
        # 创建状态标签 - 蓝色清新主题
        self.status_label = QLabel('🎯 准备就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont('Microsoft YaHei', 11, QFont.Bold)  # 增大字体
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                background-color: #e3f2fd;
                padding: 12px;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                border: 2px solid #bbdefb;
                font-size: 11pt;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # 加载API密钥
        self.load_api_key()
        
        # 设置布局
        self.setLayout(main_layout)
        
        # 设置窗口整体样式 - 蓝色清新背景
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f8ff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8fdff, stop:1 #e6f7ff);
            }
        """)
        
    def open_api_key_url(self):
        """
        打开API密钥获取页面
        """
        import webbrowser
        webbrowser.open('https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey')
    
    def load_api_key(self):
        """
        从config.json加载API密钥
        """
        try:
            # 使用get_resource_file_path函数获取config.json的完整路径
            config_path = get_resource_file_path('config.json')
            print(f"尝试加载配置文件: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key = config.get('api_config', {}).get('api_key', '')
            self.api_key_input.setText(api_key)
        except Exception as e:
            print(f"加载API密钥失败: {e}")
            print(f"错误路径: {config_path if 'config_path' in locals() else '未知'}")
    
    def save_api_key(self, text):
        """
        保存API密钥到config.json
        """
        try:
            # 使用get_resource_file_path函数获取config.json的完整路径
            config_path = get_resource_file_path('config.json')
            print(f"尝试保存配置文件: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新API密钥
            if 'api_config' not in config:
                config['api_config'] = {}
            config['api_config']['api_key'] = text
            
            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"保存API密钥失败: {e}")
            print(f"错误路径: {config_path if 'config_path' in locals() else '未知'}")
    
    def start_ai(self):
        # 获取API密钥和用户输入
        api_key = self.api_key_input.text().strip()
        user_input = self.input_text.toPlainText().strip()
        
        # 检查是否都已填写
        if not api_key or not user_input:
            self.status_label.setText('⚠️ 请正确填入密钥和需求')
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    background-color: #ffebee;
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 8px;
                    font-weight: bold;
                    border: 2px solid #ffcdd2;
                    font-size: 11pt;
                }
            """)
            return
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 更新状态
        self.status_label.setText('🤖 AI正在执行中...')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                background-color: #e3f2fd;
                padding: 12px;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                border: 2px solid #bbdefb;
                font-size: 11pt;
            }
        """)
        self.upload_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 隐藏API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(False)
        self.get_api_key_btn.setVisible(False)
        
        # 设置AI控制鼠标标志
        self.is_ai_controlling = True
        
        # 创建并启动AI线程
        self.ai_thread = AIWorker(user_input)
        self.ai_thread.finished.connect(self.ai_finished)
        self.ai_thread.error.connect(self.ai_error)
        self.ai_thread.start()
        
        # 连接AI坐标信号
        self.ai_thread.ai_coordinate.connect(self.handle_ai_coordinate)
        
    def stop_ai(self):
        # 发送 Ctrl+C 信号（SIGINT）来停止AI执行
        try:
            # 这会触发 vl_model_test_doubao2 中的 signal_handler
            vl_model_test_doubao2.stop_client()
            # vl_model_test_doubao2.should_exit = True
        except Exception as e:
            # 如果发送信号失败，回退到设置全局变量
            print(f"发送信号失败: {e}，使用备用方法")
            vl_model_test_doubao2.should_exit = True
        
        # 更新状态
        self.status_label.setText('⏹️ 正在停止AI执行...')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #f57c00;
                background-color: #fff3e0;
                padding: 12px;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                border: 2px solid #ffe0b2;
                font-size: 11pt;
            }
        """)
        
    def ai_finished(self, result):
        # AI执行完成
        self.status_label.setText('✅ AI执行完成')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                background-color: #e3f2fd;
                padding: 12px;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                border: 2px solid #bbdefb;
                font-size: 11pt;
            }
        """)
        self.upload_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 显示API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(True)
        self.get_api_key_btn.setVisible(True)
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 重置AI控制鼠标标志
        self.is_ai_controlling = False
        
        # 如果是弥娅的任务,标记为完成
        if hasattr(self, '_current_naya_task_id') and self._current_naya_task_id:
            try:
                task_queue = get_task_queue()
                task_queue.mark_task_completed(self._current_naya_task_id, result)
                print(f"弥娅任务 {self._current_naya_task_id} 已完成")
                self._current_naya_task_id = None
            except Exception as e:
                print(f"标记任务完成时出错: {e}")
        
        # 检查是否有来自弥娅的任务
        self.check_and_process_naya_tasks()
        
    def check_and_process_naya_tasks(self):
        """检查并处理来自弥娅的任务"""
        try:
            task_queue = get_task_queue()
            pending_tasks = task_queue.get_pending_tasks()
            running_tasks = task_queue.get_running_tasks()

            # 检查是否有卡住的running任务(超过5分钟未完成)
            import time
            current_time = time.time()
            for running_task in running_tasks[:]:  # 使用副本进行迭代
                try:
                    start_time_str = running_task.get("start_time", "")
                    if start_time_str:
                        from datetime import datetime
                        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timestamp()
                        # 如果任务运行超过5分钟(300秒),标记为失败并清理
                        if current_time - start_time > 300:
                            print(f"[弥娅任务] 检测到卡住的任务 {running_task['id']}, 超过5分钟未完成,将清理")
                            task_queue.mark_task_failed(running_task['id'], "任务执行超时(5分钟)")
                except Exception as e:
                    print(f"[弥娅任务] 清理卡住任务时出错: {e}")

            # 重新获取running任务(可能已被清理)
            running_tasks = task_queue.get_running_tasks()

            # 如果有正在运行的任务,不启动新任务
            if running_tasks:
                print(f"[弥娅任务] 当前有 {len(running_tasks)} 个任务正在执行,跳过新任务")
                return

            if pending_tasks:
                print(f"[弥娅任务] 检测到 {len(pending_tasks)} 个待处理任务")

                # 处理第一个待处理任务
                task = pending_tasks[0]
                task_id = task["id"]
                task_description = task["task"]

                print(f"[弥娅任务] 开始执行任务 ID:{task_id} - {task_description}")

                # 标记任务开始
                task_queue.mark_task_started(task_id)

                # 自动执行任务
                QTimer.singleShot(1000, lambda: self.execute_naya_task(task_id, task_description))

        except Exception as e:
            print(f"[弥娅任务] 检查任务失败: {e}")

    def cleanup_old_tasks(self):
        """清理旧任务"""
        try:
            task_queue = get_task_queue()

            # 加载所有任务
            all_tasks = task_queue._load_tasks()
            original_count = len(all_tasks)

            # 只保留最近的任务(最多保留5个已完成/失败的任务)
            completed_tasks = [t for t in all_tasks if t["status"] in ["completed", "failed"]]
            active_tasks = [t for t in all_tasks if t["status"] in ["pending", "running"]]

            # 按时间排序,保留最新的5个已完成/失败的任务
            completed_tasks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            recent_completed = completed_tasks[:5]

            # 合并任务
            final_tasks = active_tasks + recent_completed

            if len(final_tasks) < original_count:
                task_queue._save_tasks(final_tasks)
                print(f"[弥娅任务] 已清理 {original_count - len(final_tasks)} 个旧任务,保留 {len(final_tasks)} 个任务")

        except Exception as e:
            print(f"[弥娅任务] 清理任务失败: {e}")
    
    def execute_naya_task(self, task_id: int, task_description: str):
        """执行来自弥娅的任务"""
        try:
            print(f"执行弥娅任务 ID:{task_id} - {task_description}")
            
            # 保存当前任务ID
            self._current_naya_task_id = task_id
            
            # 设置输入框内容
            self.input_text.setPlainText(task_description)
            
            # 自动开始执行
            QTimer.singleShot(500, self.start_ai)
            
        except Exception as e:
            print(f"执行弥娅任务失败: {e}")
            # 标记任务失败
            task_queue = get_task_queue()
            task_queue.mark_task_failed(task_id, str(e))
        
    def ai_error(self, error):
        # AI执行出错
        self.status_label.setText('❌ AI执行错误，可能密钥错误或欠费')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                background-color: #ffebee;
                padding: 12px;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                border: 2px solid #ffcdd2;
                font-size: 11pt;
            }
        """)
        self.upload_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 显示API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(True)
        self.get_api_key_btn.setVisible(True)
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 重置AI控制鼠标标志
        self.is_ai_controlling = False
        
        # 如果是弥娅的任务,标记为失败
        if hasattr(self, '_current_naya_task_id') and self._current_naya_task_id:
            try:
                task_queue = get_task_queue()
                task_queue.mark_task_failed(self._current_naya_task_id, error)
                print(f"弥娅任务 {self._current_naya_task_id} 执行失败: {error}")
                self._current_naya_task_id = None
            except Exception as e:
                print(f"标记任务失败时出错: {e}")
        
    def handle_ai_coordinate(self, x, y):
        # 只有当AI控制鼠标时才处理
        if not self.is_ai_controlling:
            return
        
        print(f"收到AI输出的坐标: ({x}, {y})")
        
        # 获取窗口几何信息
        window_rect = self.geometry()
        
        # 计算AI输出坐标与窗口中心的距离
        window_center_x = window_rect.center().x()
        window_center_y = window_rect.center().y()
        print(f"窗口中心坐标：({window_center_x},{window_center_y})")
        
        distance = ((x - window_center_x) ** 2 + (y - window_center_y) ** 2) ** 0.5
        print(f"AI坐标与窗口中心的距离: {distance:.2f}像素")
        
        # 如果距离小于阈值，移动窗口
        if distance < AI_COORDINATE_THRESHOLD:
            # 创建QPoint对象表示AI坐标，将float转换为int
            ai_pos = QPoint(int(x), int(y))
            # 移动窗口避开AI坐标
            self.move_window_away(ai_pos, window_rect)
    
    def move_window_away(self, ai_pos, window_rect):
        # 计算窗口新位置，避开AI输出的坐标
        screen_geometry = QApplication.desktop().availableGeometry()
        
        # 窗口尺寸
        win_width = window_rect.width()
        win_height = window_rect.height()
        
        # AI坐标位置
        ai_x = ai_pos.x()
        ai_y = ai_pos.y()
        
        # 计算窗口中心位置
        win_center_x = window_rect.center().x()
        win_center_y = window_rect.center().y()
        
        # 确定移动方向：远离AI坐标
        new_x = win_center_x
        new_y = win_center_y
        
        # 水平方向移动
        if (new_x + WINDOW_MOVE_DISTANCE) < (screen_geometry.width() - win_width/2):
            new_x += WINDOW_MOVE_DISTANCE

        else:
            new_x -= WINDOW_MOVE_DISTANCE
        
        # 垂直方向移动
        if (new_y + WINDOW_MOVE_DISTANCE) < (screen_geometry.height() - win_height/2):
            new_y += WINDOW_MOVE_DISTANCE
        else:
            new_y -= WINDOW_MOVE_DISTANCE
        
        # 确保窗口不会移出屏幕
        new_x = max(0, min(new_x - win_width // 2, screen_geometry.width() - win_width))
        new_y = max(0, min(new_y - win_height // 2, screen_geometry.height() - win_height))
        
        print(f"窗口从 ({window_rect.left()}, {window_rect.top()}) 快速移动到 ({new_x}, {new_y})")
        # 快速移动窗口
        self.move(new_x, new_y)
    
    def closeEvent(self, event):
        # 关闭窗口时停止AI
        self.stop_ai()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 初始化并显示日志窗口
    log_window = init_log_window()

    # 创建并显示AI主窗口
    window = AIWindow()
    window.show()  # 确保窗口可见

    sys.exit(app.exec_())

    # 打包命令： pyinstaller pyqt_main.spec