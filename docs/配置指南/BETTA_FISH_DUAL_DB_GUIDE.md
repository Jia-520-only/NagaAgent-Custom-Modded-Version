# BettaFish 本地+云数据库双配置指南

## 🎯 配置目标

同时配置本地数据库和云数据库，并支持快速切换。

---

## 📋 配置步骤

### 第 1 步：配置本地数据库

#### 使用 Docker（推荐）

```bash
setup_mysql.bat
```

按提示输入密码（如：bettafish123）

#### 或者手动安装

安装 MySQL Community Server 并创建数据库：
```sql
CREATE DATABASE mindspider CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 第 2 步：申请云数据库

发送邮件到 **670939375@qq.com** 申请免费云数据库，提供：
- 你的姓名
- 用途（学习/研究/测试）
- 预计使用时长

获取以下信息：
- 数据库主机地址
- 端口（通常 3306）
- 用户名
- 密码
- 数据库名

---

### 第 3 步：配置 .env.local 文件

编辑 `betta-fish-main\.env.local` 文件：

```env
# ====================== 本地数据库配置 ======================
DB_HOST_LOCAL=localhost
DB_PORT_LOCAL=3306
DB_USER_LOCAL=root
DB_PASSWORD_LOCAL=你的本地密码
DB_NAME_LOCAL=mindspider
DB_CHARSET_LOCAL=utf8mb4
DB_DIALECT_LOCAL=mysql

# ====================== 云数据库配置 ======================
# 填入从 BettaFish 官方获取的信息
DB_HOST_CLOUD=云数据库地址
DB_PORT_CLOUD=3306
DB_USER_CLOUD=云数据库用户名
DB_PASSWORD_CLOUD=云数据库密码
DB_NAME_CLOUD=mindspider
DB_CHARSET_CLOUD=utf8mb4
DB_DIALECT_CLOUD=mysql

# ====================== 数据库选择 ======================
# 选择使用的数据库: local 或 cloud
DB_MODE=local
```

---

### 第 4 步：初始化表结构

#### 初始化本地数据库

```bash
# 先切换到本地模式
python betta-fish-main/config_db_mode.py local

# 初始化表结构
python init_betta_fish_db.py
```

#### 初始化云数据库（如果需要）

```bash
# 切换到云数据库模式
python betta-fish-main/config_db_mode.py cloud

# 初始化表结构
python init_betta_fish_db.py
```

---

### 第 5 步：验证连接

```bash
# 测试当前数据库
python test_db_connection.py
```

---

## 🔄 快速切换数据库

### 查看当前状态

```bash
python betta-fish-main/config_db_mode.py status
```

输出示例：
```
======================================================
BettaFish 数据库模式切换工具
======================================================

当前数据库模式: local

配置状态:
------------------------------------------------------------
本地数据库: ✅ 已配置
  主机: localhost
  数据库: mindspider
云数据库:   ✅ 已配置
  主机: bettafish.mysql.rds.aliyuncs.com
  数据库: mindspider
------------------------------------------------------------
```

### 切换到本地数据库

```bash
python betta-fish-main/config_db_mode.py local
```

输出：
```
切换到本地数据库模式...
✅ 已切换到本地数据库
  主机: localhost
  数据库: mindspider

下一步: 运行 python test_db_connection.py 验证连接
```

### 切换到云数据库

```bash
python betta-fish-main/config_db_mode.py cloud
```

输出：
```
切换到云数据库模式...
✅ 已切换到云数据库
  主机: bettafish.mysql.rds.aliyuncs.com
  数据库: mindspider

下一步: 运行 python test_db_connection.py 验证连接
```

---

## 📊 使用场景建议

### 场景 1：日常使用本地数据库
**优势**：
- ✅ 快速响应
- ✅ 无需网络
- ✅ 完全控制
- ✅ 适合开发和测试

**配置**：
```bash
python betta-fish-main/config_db_mode.py local
```

### 场景 2：分析真实舆情数据
**优势**：
- ✅ 10万+ 日均真实数据
- ✅ 多平台数据
- ✅ 实时更新
- ✅ 数据质量高

**配置**：
```bash
python betta-fish-main/config_db_mode.py cloud
```

### 场景 3：数据对比分析
**优势**：
- ✅ 对比本地爬取数据 vs 云端真实数据
- ✅ 验证爬虫准确性
- ✅ 补充缺失数据

**配置**：频繁切换

### 场景 4：备份与恢复
**优势**：
- ✅ 云端备份到本地
- ✅ 本地数据上传云端
- ✅ 双重保险

---

## 🎁 额外工具

### 创建快捷切换脚本

#### Windows (toggle_db.bat)

```batch
@echo off
echo BettaFish Database Switcher
echo.
echo 1. Local Database
echo 2. Cloud Database
echo 3. Show Status
echo.
set /p choice="Select option (1-3): "

if "%choice%"=="1" (
    python betta-fish-main/config_db_mode.py local
    echo.
    echo Testing connection...
    python test_db_connection.py
) else if "%choice%"=="2" (
    python betta-fish-main/config_db_mode.py cloud
    echo.
    echo Testing connection...
    python test_db_connection.py
) else if "%choice%"=="3" (
    python betta-fish-main/config_db_mode.py status
) else (
    echo Invalid choice
)

pause
```

#### Linux/macOS (toggle_db.sh)

```bash
#!/bin/bash
echo "BettaFish Database Switcher"
echo ""
echo "1. Local Database"
echo "2. Cloud Database"
echo "3. Show Status"
echo ""
read -p "Select option (1-3): " choice

case $choice in
    1)
        python betta-fish-main/config_db_mode.py local
        echo ""
        echo "Testing connection..."
        python test_db_connection.py
        ;;
    2)
        python betta-fish-main/config_db_mode.py cloud
        echo ""
        echo "Testing connection..."
        python test_db_connection.py
        ;;
    3)
        python betta-fish-main/config_db_mode.py status
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
```

---

## 🔍 验证双配置

运行完整验证：

```bash
# 测试本地数据库
python betta-fish-main/config_db_mode.py local
python test_db_connection.py

# 测试云数据库
python betta-fish-main/config_db_mode.py cloud
python test_db_connection.py

# 切回本地（日常使用）
python betta-fish-main/config_db_mode.py local
```

---

## 📝 配置文件说明

### .env.local
双配置文件，包含本地和云数据库的所有信息。

### .env
实际使用的配置文件，由切换工具自动更新。

### 配置优先级
1. 程序首先读取 .env（当前激活的配置）
2. .env.local 作为配置源和管理文件
3. 不要手动编辑 .env，使用切换工具

---

## 🚨 注意事项

1. **密码安全**
   - 不要将 .env.local 提交到 Git
   - 使用强密码
   - 定期更换密码

2. **网络要求**
   - 云数据库需要稳定的网络连接
   - 本地数据库可以离线使用

3. **数据一致性**
   - 本地和云端是两个独立的数据库
   - 切换不会同步数据
   - 如需同步，需要手动导出/导入

4. **性能差异**
   - 本地数据库：响应快，适合频繁操作
   - 云数据库：响应稍慢，但数据真实丰富

---

## 📚 相关文档

- BETTA_FISH_DB_QUICKSTART.md - 快速开始
- BETTA_FISH_CLOUD_DB_GUIDE.md - 云数据库配置
- BETTA_FISH_TEST_GUIDE.md - 功能测试

---

## 🎉 总结

你现在拥有：
- ✅ 本地数据库（Docker MySQL）
- ✅ 云数据库（BettaFish 官方）
- ✅ 一键切换工具
- ✅ 双重保障

**开始配置吧！先运行 setup_mysql.bat，然后申请云数据库！**
