# BettaFish 数据库配置快速开始指南

## 📋 配置清单

- ✅ 64G 内存（充足）
- ⬜ MySQL 数据库
- ⬜ 数据库配置文件
- ⬜ 表结构初始化

---

## 🚀 快速开始（3步配置）

### 方式 A：使用 Docker（推荐，最简单）

#### 步骤 1：一键安装 MySQL

```bash
# 在 NagaAgent 根目录运行
setup_mysql.bat
```

这个脚本会：
- 检查 Docker 是否安装
- 创建 MySQL 容器
- 设置数据库 `mindspider`
- 自动启动服务

#### 步骤 2：配置数据库密码

```bash
# 更新 .env 文件中的密码
python update_env_password.py
```

输入在步骤 1 中设置的 MySQL root 密码。

#### 步骤 3：初始化数据库表结构

```bash
# 创建所有必需的表
python init_betta_fish_db.py
```

---

### 方式 B：手动安装 MySQL

#### 步骤 1：安装 MySQL

下载并安装 MySQL Community Server：
- 访问：https://dev.mysql.com/downloads/mysql/
- 选择 Windows MSI Installer
- 安装时记住 root 密码

#### 步骤 2：创建数据库

打开 MySQL 命令行或使用 MySQL Workbench：

```sql
CREATE DATABASE mindspider CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 步骤 3：配置 .env 文件

编辑 `betta-fish-main\.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_password
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql
```

#### 步骤 4：初始化表结构

```bash
python init_betta_fish_db.py
```

---

## ✅ 验证配置

运行测试脚本验证一切正常：

```bash
python test_db_connection.py
```

应该看到：
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
✅ 数据库表存在，共 XX 张表:
   - daily_news
   - daily_topics
   - crawling_tasks
   ...

======================================================
✅ 数据库配置验证通过！
======================================================
```

---

## 🔧 常见问题

### Q1: Docker 启动失败

**症状**：`docker run` 命令报错

**解决**：
1. 确保 Docker Desktop 已启动
2. 检查端口 3306 是否被占用：`netstat -ano | findstr 3306`
3. 查看容器日志：`docker logs mysql-bettafish`

### Q2: 数据库连接失败

**症状**：`Access denied for user 'root'@'localhost'`

**解决**：
1. 检查 .env 文件中的密码是否正确
2. 测试密码：`docker exec mysql-bettafish mysql -uroot -p`
3. 如果忘记密码，重置容器：
   ```bash
   docker stop mysql-bettafish
   docker rm mysql-bettafish
   setup_mysql.bat
   ```

### Q3: 表结构未创建

**症状**：测试脚本显示"数据库为空"

**解决**：
1. 确保有数据库写入权限
2. 手动运行初始化：
   ```bash
   cd betta-fish-main/MindSpider/schema
   python init_database.py
   ```

### Q4: 缺少依赖包

**症状**：`ModuleNotFoundError: No module named 'aiomysql'`

**解决**：
```bash
pip install aiomysql asyncpg sqlalchemy python-dotenv
```

---

## 📊 数据库表结构

配置成功后，数据库会包含以下表：

### MindSpider 核心表
- `daily_news` - 每日新闻数据
- `daily_topics` - 每日话题数据
- `topic_news_relation` - 话题-新闻关联
- `crawling_tasks` - 爬虫任务记录

### MediaCrawler 平台表
- `weibo_note` - 微博笔记
- `weibo_note_comment` - 微博评论
- `xhs_note` - 小红书笔记
- `xhs_note_comment` - 小红书评论
- `douyin_aweme` - 抖音视频
- `douyin_aweme_comment` - 抖音评论
- `kuaishou_video` - 快手视频
- `kuaishou_video_comment` - 快手评论
- `bilibili_video` - B站视频
- `bilibili_video_comment` - B站评论
- 等等...

---

## 🎯 下一步

数据库配置完成后，您可以：

1. **使用数据库查询功能**：
   - BettaFish Agent 可以查询真实舆情数据
   - 比单纯 LLM 生成更准确

2. **配置爬虫功能**（可选）：
   - 配置 Tavily/Bocha API
   - 启用全网爬虫

3. **配置独立 LLM**（可选）：
   - 为各个 Agent 配置专门的 LLM
   - 实现多 Agent 协作

---

## 📝 配置文件位置

- `.env`: `e:\NagaAgent\betta-fish-main\.env`
- 初始化脚本: `e:\NagaAgent\init_betta_fish_db.py`
- 测试脚本: `e:\NagaAgent\test_db_connection.py`

---

**配置完成后，重启 NagaAgent 即可使用数据库功能！**
