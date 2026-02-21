# BettaFish 云数据库使用指南

## 🌐 可以使用的云数据库服务

### 选项 1：BettaFish 官方云数据库（推荐）

BettaFish 团队提供免费云数据库服务，包含日均 10万+ 真实舆情数据。

**申请方式**：
- 📧 邮箱：670939375@qq.com
- 📧 邮箱：670939375@qq.com

**包含内容**：
- ✅ 真实舆情数据（微博、小红书、抖音、B站等）
- ✅ 实时数据更新
- ✅ 多维度标签分类
- ✅ 高可用云端服务
- ✅ 专业技术支持

**获取信息**：
```
请发送邮件到 670939375@qq.com 申请免费云数据库访问权限
```

---

### 选项 2：阿里云 RDS MySQL

1. **创建实例**
   - 访问：https://rds.aliyun.com/
   - 选择 MySQL 8.0
   - 选择规格（建议：1核2G起步）
   - 创建数据库 `mindspider`

2. **获取连接信息**
   ```
   外网地址: rm-xxx.rds.aliyuncs.com
   端口: 3306
   用户名: root
   密码: your_password
   数据库: mindspider
   ```

3. **配置白名单**
   - 在 RDS 控制台添加你的 IP 到白名单
   - 或选择 0.0.0.0/0（不推荐生产环境）

4. **更新 .env 配置**

---

### 选项 3：腾讯云 MySQL

1. **创建实例**
   - 访问：https://console.cloud.tencent.com/cdb
   - 选择 MySQL 8.0
   - 创建数据库 `mindspider`

2. **获取连接信息**
   ```
   外网地址: xxx.mysql.tencentcdb.com
   端口: 3306
   用户名: root
   密码: your_password
   数据库: mindspider
   ```

3. **配置安全组**
   - 添加 MySQL 端口 3306 的入站规则
   - 允许你的 IP 访问

---

### 选项 4：AWS RDS MySQL

1. **创建实例**
   - 访问：https://console.aws.amazon.com/rds/
   - 选择 MySQL 8.0
   - 创建 Free Tier 实例（12个月免费）
   - 创建数据库 `mindspider`

2. **获取连接信息**
   ```
   Endpoint: xxx.us-east-1.rds.amazonaws.com
   端口: 3306
   用户名: admin
   密码: your_password
   数据库: mindspider
   ```

3. **配置安全组**
   - 添加 Inbound rule: MySQL (3306)
   - 允许你的 IP 访问

---

## 🔧 配置云数据库

### 1. 编辑 .env 文件

打开 `e:\NagaAgent\betta-fish-main\.env`：

```env
# 数据库配置
DB_HOST=your_cloud_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql
```

### 2. 示例配置

#### 阿里云 RDS
```env
DB_HOST=rm-bp123456.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourStrongPassword123!
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql
```

#### 腾讯云 MySQL
```env
DB_HOST=tencentdb-mysql-123456.tencentcdb.com
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourStrongPassword123!
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql
```

#### AWS RDS
```env
DB_HOST=mydb.c123456.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=YourStrongPassword123!
DB_NAME=mindspider
DB_CHARSET=utf8mb4
DB_DIALECT=mysql
```

---

## ✅ 验证云数据库连接

配置完成后运行：

```bash
python test_db_connection.py
```

---

## 🆚 云数据库 vs 本地数据库对比

| 特性 | 云数据库 | 本地数据库 |
|------|---------|-----------|
| **部署难度** | 简单 | 需要安装配置 |
| **数据量** | 10万+ 日均真实数据 | 空（需自己爬取） |
| **维护** | 云服务商维护 | 自己维护 |
| **网络** | 需要网络 | 本地访问快 |
| **成本** | 免费或有费用 | 免费 |
| **数据质量** | 真实舆情数据 | 需爬取 |
| **适合场景** | 快速开始、研究分析 | 完全控制、定制化 |

---

## 📌 推荐方案

### 场景 1：快速开始，想立即使用真实数据
**推荐：BettaFish 官方云数据库**

申请邮箱：670939375@qq.com

### 场景 2：已有云服务账号
**推荐：使用已有云服务**

阿里云/腾讯云/AWS RDS

### 场景 3：完全控制，本地开发
**推荐：本地 MySQL**

使用修复后的 `setup_mysql.bat`

---

## 🚨 注意事项

1. **安全性**
   - 云数据库密码要足够复杂
   - 配置 IP 白名单，不要 0.0.0.0/0
   - 使用 SSL 连接（如果支持）

2. **成本**
   - 注意免费额度限制
   - 监控流量和存储使用
   - 设置费用告警

3. **性能**
   - 选择合适的规格
   - 定期清理过期数据
   - 优化查询语句

4. **备份**
   - 开启自动备份
   - 定期导出数据
   - 测试恢复流程

---

## 📞 获取帮助

### BettaFish 官方支持
- 📧 邮箱：670939375@qq.com
- 📧 邮箱：670939375@qq.com

### 云服务商支持
- 阿里云：https://help.aliyun.com/
- 腾讯云：https://cloud.tencent.com/document/product
- AWS：https://docs.aws.amazon.com/

---

**选择最适合你的方式，配置后运行 `python test_db_connection.py` 验证！**
