# Undefined 配置文件修复说明

## 问题说明

上传到GitHub后，Undefined MCP Server 初始化失败，原因是：

1. **配置文件占位符格式错误**
   - `bot_qq = YOUR_BOT_QQ` - 应该是整数，不能是字符串
   - `superadmin_qq = YOUR_SUPERADMIN_QQ` - 同样的问题
   - `admin_qq = [YOUR_ADMIN_QQ]` - 列表元素必须是整数
   - `api_key = "YOUR_API_KEY"` - 字符串格式可以，但不是有效API key格式

2. **配置解析失败**
   - Undefined 在加载配置时会进行类型检查
   - 无效的占位符会导致配置加载失败
   - 进而导致 Undefined MCP Server 初始化失败

## 解决方案

### 1. 配置文件占位符格式

**正确的占位符格式：**

```toml
# QQ号使用有效的整数占位符
bot_qq = 1234567890
superadmin_qq = 9876543210
admin_qq = [9876543210]

# API Key使用有效的字符串占位符
api_key = "sk-your-api-key-here-replace-this"
```

**错误的占位符格式：**

```toml
# 错误：字符串作为数字
bot_qq = YOUR_BOT_QQ
superadmin_qq = YOUR_SUPERADMIN_QQ
admin_qq = [YOUR_ADMIN_QQ]

# 错误：看起来像变量名的字符串
api_key = "YOUR_API_KEY"
```

### 2. 如何修复本地配置

如果你在本地遇到 Undefined MCP Server 初始化失败，请检查你的 `Undefined/config.toml`：

1. 确保 `bot_qq`、`superadmin_qq` 是有效的QQ号（整数）
2. 确保 `admin_qq` 列表中的元素都是整数
3. 确保 `api_key` 是有效的API key格式

### 3. 推荐的配置方式

**开发环境：**
- 复制 `config.toml.example` 到 `config.toml`
- 修改为你的真实配置值

**GitHub模板：**
- 使用示例配置文件 `config.toml.example`
- 不要在仓库中包含真实的 `config.toml`

## .gitignore 配置

确保 `Undefined/config.toml` 在 `.gitignore` 中，避免泄露真实配置：

```
Undefined/config.toml
```

## 验证配置

修复后，可以通过以下方式验证配置是否正确：

```bash
cd Undefined
uv run python -c "from Undefined.config import get_config; config = get_config(strict=False); print('配置加载成功')"
```

## 相关文件

- `Undefined/config.toml` - 本地配置文件（不应提交）
- `Undefined/config.toml.example` - 示例配置文件（可提交）
- `mcpserver/agent_undefined_mcp/undefined_mcp.py` - Undefined MCP Server 实现
