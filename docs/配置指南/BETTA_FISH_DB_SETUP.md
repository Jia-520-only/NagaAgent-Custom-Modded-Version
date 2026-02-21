"""
BettaFish 本地 MySQL 数据库配置指南

第1步：安装和配置 MySQL
======================

Windows 上安装 MySQL：

1. 下载 MySQL Community Server
   - 访问：https://dev.mysql.com/downloads/mysql/
   - 下载 Windows MSI Installer
   - 安装时记住设置的 root 密码

2. 或者使用 Docker（推荐，更简单）
   - 确保已安装 Docker Desktop
   - 运行以下命令：
     docker run -d --name mysql-bettafish -p 3306:3306 ^
       -e MYSQL_ROOT_PASSWORD=your_password ^
       -e MYSQL_DATABASE=mindspider ^
       mysql:8.0

第2步：创建 .env 配置文件
===========================

在 e:\NagaAgent\betta-fish-main 目录下创建 .env 文件：

[数据库配置]
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql

[LLM配置 - 可选，不配置则使用 NagaAgent 的 LLM]
# 暂时留空，后续配置

第3步：初始化数据库
==================

运行以下命令初始化数据库表结构：

cd e:\NagaAgent\betta-fish-main\MindSpider
python schema/init_database.py

第4步：验证数据库连接
======================

测试脚本 test_db_connection.py 会验证：
- MySQL 是否运行
- 数据库连接是否正常
- 表结构是否创建成功

配置完成后运行：python test_db_connection.py
"""

print(__doc__)
