# Docker 或 MySQL 安装选择指南

## 🤔 两个选择

### 选项 1：Docker Desktop（推荐）

**优点**：
- ✅ 安装简单，一键运行
- ✅ 容器化管理，易于维护
- ✅ 不会污染系统
- ✅ 可以轻松删除/重建
- ✅ 跨平台一致

**缺点**：
- ⚠️ 需要下载 500MB+ 的软件
- ⚠️ 占用较多资源
- ⚠️ 需要重启电脑

**适合**：
- 想要快速安装
- 经常测试/重置数据库
- 不想搞乱系统环境

---

### 选项 2：手动安装 MySQL

**优点**：
- ✅ 直接安装，性能更好
- ✅ 更少的资源占用
- ✅ 可以使用 MySQL Workbench GUI

**缺点**：
- ⚠️ 安装步骤多
- ⚠️ 难以卸载/重装
- ⚠️ 可能与其他软件冲突

**适合**：
- 不想安装 Docker
- 需要 MySQL 做其他用途
- 想要更精细的控制

---

## 🚀 快速安装指南

### 选项 1：安装 Docker Desktop

#### 步骤 1：下载

访问：https://www.docker.com/products/docker-desktop/

下载 Windows 版本

#### 步骤 2：安装

1. 双击 Docker Desktop Installer.exe
2. 等待安装完成
3. **重启电脑**（重要！）
4. 启动 Docker Desktop

#### 步骤 3：验证

打开命令提示符或 PowerShell：

```bash
docker --version
```

应该显示类似：`Docker version 26.x.x`

#### 步骤 4：运行设置脚本

```bash
cd e:\NagaAgent
setup_mysql.bat
```

---

### 选项 2：手动安装 MySQL

#### 步骤 1：下载 MySQL

访问：https://dev.mysql.com/downloads/mysql/

选择：
- **Product Version**: 8.0.x (推荐)
- **Operating System**: Windows
- **OS Version**: Windows (x86, 64-bit), MSI Installer

点击 **Download** 下载

#### 步骤 2：安装 MySQL

1. 运行下载的 MSI 安装包
2. 选择 **Developer Default**
3. 点击 **Next** 直到配置页面
4. 设置 root 密码（记住它！）
5. 点击 **Execute** 开始安装
6. 等待安装完成，点击 **Finish**

#### 步骤 3：创建数据库

打开 **MySQL Command Line Client**（安装后会在开始菜单）：

输入 root 密码登录，然后运行：

```sql
CREATE DATABASE mindspider CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或者运行自动化脚本：

```bash
cd e:\NagaAgent
setup_mysql_manual.bat
```

#### 步骤 4：配置密码

```bash
python update_env_password.py
```

输入你在步骤 2 设置的 root 密码

#### 步骤 5：初始化表结构

```bash
python init_betta_fish_db.py
```

---

## ✅ 验证安装

运行测试脚本：

```bash
python test_db_connection.py
```

应该看到所有测试通过：

```
======================================================
BettaFish 数据库连接测试
======================================================

[测试1] 检查 .env 配置文件...
✅ .env 文件存在: ...

[测试2] 检查 MySQL 服务...
✅ MySQL 服务正在运行 (端口 3306)

[测试3] 读取数据库配置...
   数据库类型: mysql
   主机: localhost:3306
   用户: root
   数据库: mindspider
   密码: 已设置

[测试4] 测试数据库连接...
✅ MySQL 连接成功

[测试5] 检查数据库表结构...
✅ 数据库表存在，共 XX 张表

======================================================
✅ 数据库配置验证通过！
======================================================
```

---

## 🔧 故障排查

### Docker 相关问题

**问题**：Docker 启动失败

**解决**：
1. 确保 Windows 版本较新（Windows 10/11）
2. 启用 WSL 2：`wsl --install`
3. 重启电脑

**问题**：Docker 占用端口 3306

**解决**：
```bash
docker stop mysql-bettafish
docker rm mysql-bettafish
setup_mysql.bat
```

### MySQL 相关问题

**问题**：MySQL 服务未启动

**解决**：
1. 打开服务管理器（services.msc）
2. 找到 "MySQL80"
3. 右键点击，选择"启动"

**问题**：Access denied for user 'root'

**解决**：
1. 检查密码是否正确
2. 重置密码或重新安装

**问题**：端口 3306 被占用

**解决**：
1. 检查是否有其他 MySQL 实例在运行
2. 停止或卸载其他 MySQL 版本

---

## 💡 我的推荐

**如果你：**

- 想要快速开始 → **选 Docker**
- 经常重置数据库 → **选 Docker**
- 是新手 → **选 Docker**

- 需要最佳性能 → **选手动安装**
- 不想安装 Docker → **选手动安装**
- 需要多个 MySQL 实例 → **选手动安装**

---

## 📚 相关文件

- `setup_mysql.bat` - Docker 自动化安装
- `setup_mysql_manual.bat` - 手动安装 MySQL
- `create_database.sql` - 数据库创建 SQL 脚本
- `update_env_password.py` - 更新配置密码

---

**选择一个方式开始安装吧！** 🚀
