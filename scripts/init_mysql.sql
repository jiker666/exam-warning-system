-- 考试预警系统 MySQL 初始化脚本
-- 用法: mysql -u root < scripts/init_mysql.sql
CREATE DATABASE IF NOT EXISTS exam_warning
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
