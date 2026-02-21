# Docker Desktop 安装步骤

## 📥 步骤 1：下载 Docker Desktop

### 官方下载地址

**主站**：https://www.docker.com/products/docker-desktop/

**备用镜像下载（更快）**：
- 阿里云镜像：https://mirrors.aliyun.com/docker-ce/
- 网易镜像：https://mirrors.163.com/docker/

### 选择正确的版本

1. 访问官网下载页面
2. 选择 **Windows**
3. 下载 **Docker Desktop for Windows**

文件名通常是：`Docker Desktop Installer.exe`

---

## 🖥️ 步骤 2：系统要求检查

在安装前，确认你的系统满足要求：

### 必需条件

- ✅ Windows 10 64-bit: Pro, Enterprise, or Education (Build 16299 or later)
- ✅ 或 Windows 11 64-bit: Home or Pro version 21H2 or later
- ✅ BIOS 中启用虚拟化（VT-x/AMD-V）

### 如何检查虚拟化是否启用

**方法 1：任务管理器**
1. 按 `Ctrl + Shift + Esc` 打开任务管理器
2. 切换到"性能"标签
3. 点击"CPU"
4. 查看右下角是否有"虚拟化: 已启用"

**方法 2：命令提示符**
```cmd
systeminfo
```
查找"Hyper-V 要求"部分，应该显示"虚拟监视器模式已启用"

### 如果虚拟化未启用

**重启进入 BIOS**：
1. 重启电脑
2. 启动时按 `F2`、`F10`、`Delete` 或 `Esc`（取决于品牌）
3. 找到以下选项之一：
   - Intel VT-x / Intel VT-d
   - AMD-V / AMD-SVM
   - Virtualization Technology
   - SVM Mode
4. 启用它并保存设置

---

## 📦 步骤 3：安装 Docker Desktop

### 安装过程

1. **运行安装程序**
   - 双击下载的 `Docker Desktop Installer.exe`
   - 如果提示权限，点击"是"

2. **选择安装选项**
   ✅ Use WSL 2 instead of Hyper-V (推荐，性能更好)
   ✅ Add shortcut to desktop
   ✅ Automatically check for updates

3. **等待安装完成**
   - 安装过程可能需要 5-10 分钟
   - 不要关闭窗口

4. **重启电脑**（重要！）
   - 安装完成后会提示重启
   - 点击"Close and restart"

---

## 🚀 步骤 4：启动 Docker Desktop

### 首次启动

1. **重启后自动启动**
   - 登录 Windows 后，Docker Desktop 会自动启动
   - 或者从开始菜单搜索"Docker Desktop"

2. **接受许可协议**
   - 阅读并接受服务协议

3. **等待初始化**
   - 首次启动需要初始化
   - 等待状态栏的 Docker 图标变为绿色

4. **验证状态**
   - 右下角任务栏应该有 Docker 🐋 图标
   - 图标应该是绿色（表示运行中）
   - 悬停显示"Docker Desktop is running"

---

## ✅ 步骤 5：验证 Docker 安装

### 打开命令提示符或 PowerShell

按 `Win + R`，输入 `cmd` 或 `powershell`

### 运行测试命令

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 运行测试容器
docker run hello-world
```

### 预期输出

```
docker --version
Docker version 26.1.4, build 5650f9b

docker run hello-world
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

---

## ⚙️ 步骤 6：配置 Docker（可选）

### 设置 Docker 镜像加速器（中国用户推荐）

1. 打开 Docker Desktop
2. 点击右上角齿轮图标 ⚙️
3. 选择"Docker Engine"
4. 在 JSON 配置中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

5. 点击"Apply & Restart"

### 调整资源限制

1. 打开 Docker Desktop
2. 点击右上角齿轮图标 ⚙️
3. 选择"Resources" → "Advanced"
4. 根据你的 64G 内存调整：
   - CPUs: 至少 4 核心
   - Memory: 至少 8 GB（可以设置为 16 GB）

---

## 🐋 步骤 7：安装 BettaFish MySQL 数据库

Docker 安装完成后，运行自动化脚本：

```bash
cd e:\NagaAgent
setup_mysql.bat
```

脚本会自动：
1. 检查 Docker 是否运行
2. 创建 MySQL 容器
3. 设置数据库 `mindspider`
4. 配置端口映射

---

## 🔧 故障排查

### 问题 1：Docker Desktop 无法启动

**错误**："Docker Desktop requires a newer version of Windows"

**解决**：
- 更新 Windows 到最新版本
- 或下载旧版本 Docker Desktop（不推荐）

### 问题 2：WSL 2 未安装

**错误**："WSL 2 installation is incomplete"

**解决**：
```bash
wsl --install
```
然后重启电脑

### 问题 3：Docker 启动失败

**错误**："Docker service stopped"

**解决**：
1. 打开"应用和功能" → "启用或关闭 Windows 功能"
2. 启用以下选项：
   - ✅ Hyper-V
   - ✅ Windows Subsystem for Linux
   - ✅ Virtual Machine Platform
3. 重启电脑

### 问题 4：端口被占用

**错误**："bind: address already in use"

**解决**：
```bash
# 查看占用 3306 端口的进程
netstat -ano | findstr 3306

# 停止该进程（替换 PID）
taskkill /PID <进程ID> /F
```

### 问题 5：Docker 占用太多资源

**解决**：
1. 打开 Docker Desktop 设置
2. 调整资源限制
3. 清理未使用的容器和镜像：
```bash
docker system prune -a
```

---

## 📚 常用 Docker 命令

```bash
# 查看运行的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 停止容器
docker stop mysql-bettafish

# 启动容器
docker start mysql-bettafish

# 查看容器日志
docker logs mysql-bettafish

# 进入容器
docker exec -it mysql-bettafish bash

# 删除容器
docker rm mysql-bettafish

# 查看镜像
docker images

# 删除镜像
docker rmi mysql:8.0
```

---

## ✅ 安装检查清单

完成以下检查：

- [ ] 下载了 Docker Desktop Installer.exe
- [ ] 系统满足要求（Windows 10/11）
- [ ] BIOS 虚拟化已启用
- [ ] Docker Desktop 安装成功
- [ ] 重启了电脑
- [ ] Docker Desktop 已启动（图标为绿色）
- [ ] `docker --version` 命令输出版本信息
- [ ] `docker run hello-world` 运行成功
- [ ] 运行了 `setup_mysql.bat` 安装 MySQL

---

## 🎉 下一步

Docker Desktop 安装并验证成功后：

1. 运行 `setup_mysql.bat` 创建 MySQL 容器
2. 运行 `python update_env_password.py` 配置密码
3. 运行 `python init_betta_fish_db.py` 初始化表结构
4. 运行 `python test_db_connection.py` 验证连接

**准备好开始了吗？下载 Docker Desktop 然后按步骤操作！** 🚀
