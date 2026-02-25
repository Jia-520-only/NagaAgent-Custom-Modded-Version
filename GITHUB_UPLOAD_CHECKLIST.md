# GitHub 上传检查清单

## 上传前准备

### 1. 敏感信息清理

确保 `config.json` 中不包含真实的敏感信息：
- [ ] 移除或修改所有 `api_key` 为占位符
- [ ] 移除或修改 `token` 相关配置
- [ ] 检查所有密码字段

### 2. 配置文件检查

- [ ] `config.json.example` 已同步到最新版本
- [ ] `Undefined/config.toml` 中的敏感信息已清理
- [ ] 所有 `.env` 文件已添加到 `.gitignore`

### 3. 文件删除确认

以下远程同步和自动更新相关文件已删除：

**VCPToolBox**:
- [ ] `update.bat` - 已删除
- [ ] `update_with_no_dependency.bat` - 已删除

**Undefined**:
- [ ] `src/Undefined/utils/self_update.py` - 已删除
- [ ] `src/Undefined/main.py` - 已移除 self_update 调用
- [ ] `src/Undefined/webui/routes.py` - 已移除 update_restart_handler
- [ ] `src/Undefined/webui/routes/_bot.py` - 已移除 self_update 导入和 update_restart_handler
- [ ] `src/Undefined/webui/app.py` - 已移除 self_update 自动更新逻辑

### 4. 新增文件确认

**Undefined 依赖安装**:
- [ ] `Undefined/install_dependencies.bat` - 已创建
- [ ] `Undefined/install_dependencies.sh` - 已创建
- [ ] `Undefined/DEPENDENCIES_INSTALL.md` - 已创建

**文档**:
- [ ] `PROJECT_CLEANUP_REPORT.md` - 已创建
- [ ] `GITHUB_UPLOAD_CHECKLIST.md` - 已创建

### 5. 功能测试

测试以下功能是否正常：
- [ ] Undefined 模块可以正常导入
- [ ] config.toml 可以正常加载
- [ ] 依赖安装脚本可以运行
- [ ] 项目可以正常启动

### 6. Git 配置检查

- [ ] `.gitignore` 已正确配置
- [ ] 敏感文件不会被提交
- [ ] README 文件已更新（如果有变更说明）

## 项目版本

- **当前版本**: 5.0.0
- **魔改标识**: Custom-Modded-Version

## 主要变更说明

### 移除功能
- ✅ 移除 Git 自动拉取更新
- ✅ 移除远程仓库同步功能
- ✅ 移除自动检测官方更新
- ✅ 移除 VCPToolBox 自动更新功能

### 新增功能
- ✅ 添加 Undefined 一键安装依赖脚本 (Windows/Linux/macOS)
- ✅ 添加依赖安装说明文档
- ✅ 同步 config.json.example 到魔改版本

### 保留功能
- ✅ 项目备份工具 (backup_project.py)
- ✅ TTS 引擎部署工具 (voice/deploy_tts_engines.py)
- ✅ 手动依赖安装
- ✅ 配置文件热重载

## Git 提交建议

### 第一次提交（初始化仓库）
```bash
git init
git add .
git commit -m "Initial commit: NagaAgent Custom Modded Version 5.0.0"
```

### 上传到 GitHub
```bash
# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/NagaAgent-Custom-Modded-Version.git

# 推送代码
git branch -M main
git push -u origin main
```

### 提交信息模板
```
feat: 更新项目版本到 5.0.0 (魔改版)

主要变更：
- 同步 config.json.example 到魔改版本
- 添加 Undefined 一键依赖安装脚本
- 移除所有自动更新和远程同步功能
- 清理敏感信息准备上传

详细内容见 PROJECT_CLEANUP_REPORT.md
```

## 重要提醒

1. **不要提交敏感信息**:
   - `config.json` 中的真实 API Key
   - `.env` 文件
   - 任何密码或密钥

2. **确认 .gitignore**:
   ```
   config.json
   .env
   *.log
   logs/
   data/cache/
   data/history/
   venv/
   __pycache__/
   *.pyc
   ```

3. **使用 README.md 说明变更**:
   更新主 README 添加魔改版本说明和变更记录

## 上传后

上传完成后，用户可以通过以下方式获取：
1. 克隆项目：`git clone https://github.com/YOUR_USERNAME/NagaAgent-Custom-Modded-Version.git`
2. 安装依赖：运行 `Undefined/install_dependencies.bat` (Windows)
3. 配置项目：复制 `config.json.example` 为 `config.json` 并填入配置
4. 启动项目：运行 `start.bat` 或 `start.sh`
