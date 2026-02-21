-- BettaFish 数据库创建脚本
-- 使用方法: mysql -uroot -p < create_database.sql

-- 创建 mindspider 数据库
CREATE DATABASE IF NOT EXISTS mindspider
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 选择数据库
USE mindspider;

-- 显示创建结果
SELECT 'Database mindspider created successfully!' AS status;
