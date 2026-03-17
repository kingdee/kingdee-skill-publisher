# 金蝶云苍穹业务Skill发布器

一个强大的元Skill工具，用于基于金蝶云苍穹开放平台的API快速创建和发布业务Skill。

## 📋 概览

金蝶业务Skill发布器简化了从金蝶API集成到Claude Skill发布的整个流程：

1. **配置凭证** - 连接到金蝶云苍穹服务器
2. **探索API** - 通过自然语言搜索所需的API
3. **生成Skill** - 自动创建包含所有必要代码的Skill
4. **发布使用** - 直接在Claude中使用生成的Skill

## 🎯 核心特性

### ✨ 自动化生成

- 📝 自动生成完整的SKILL.md定义
- 🔧 生成生产级别的API调用代码
- 📚 生成API文档和使用示例
- 🧪 生成测试框架和示例

### 🔐 开箱即用的安全性

- 🔑 自动Token管理和缓存
- 🛡️ 参数验证和错误处理
- 🔄 自动重试和幂等性支持
- ⚠️ 详细的错误码对照表

### 🚀 灵活的API支持

- 📊 支持查询类API（GET）
- 💾 支持修改类API（POST）
- 🔐 基于 `login.do` 的Token认证
- 🌐 兼容标准预置API和ISV二开API

### 📈 完整的文档

- 📖 金蝶API规范快速参考
- 💡 丰富的使用示例
- 🎓 最佳实践指南
- 🐛 常见问题解答

## 🚀 快速开始

### 第一步：安装依赖

```bash
pip install requests python-dotenv PyYAML
```

### 第二步：配置金蝶凭证

**方式1：环境变量（推荐）**

```bash
export KINGDEE_SERVER_URL="https://xxx.kingdee.com/ierp"
export KINGDEE_USER="your_user"
export KINGDEE_APP_ID="your_app_id"
export KINGDEE_APP_SECRET="your_app_secret"
export KINGDEE_ACCOUNT_ID="your_account_id"
```

**方式2：代码配置**

```python
import os
os.environ['KINGDEE_SERVER_URL'] = 'https://your-server.com:1026'
os.environ['KINGDEE_USER'] = 'your_user'
os.environ['KINGDEE_APP_ID'] = 'your_app_id'
os.environ['KINGDEE_APP_SECRET'] = 'your_app_secret'
os.environ['KINGDEE_ACCOUNT_ID'] = 'your_account_id'
```

### 第三步：理解认证流程

当前实现与 `scripts/api_client.py` 保持一致：

1. 先通过 `HEAD {baseUrl}/kapi` 验证服务器连通性
2. 调用 `POST {baseUrl}/api/login.do` 获取 `data.access_token`
3. 调用业务接口时，在请求头中附带 `Authorization: Bearer {access_token}`
4. 同时自动附带 `accountId` 和 `user` 作为通用业务参数
5. 如果本地Token过期，或接口返回 HTTP 401 / 业务响应 `error_code=401`，客户端会自动重新获取Token

API 列表查询接口使用专用地址，不走普通业务 API 的 URL 拼接规则：
`GET {baseUrl}/kapi/v2/open/openapi_apilist/queryByApp`

**⚠️ 重要：查询前必须询问用户提供 `appid_number`**

在查询API列表前，**必须在对话框中询问用户提供 `appid_number`**（应用编码）：
- 如果用户提供了 `appid_number`：继续执行查询
- **如果用户未提供 `appid_number`：停止执行，不再进行后续任务**

这个接口按应用编码查询 API 列表，核心 query 参数如下：

```json
{
  "appid_number": "${user_input.appid_number}",  // 必填，需询问用户提供
  "pageNo": 1,                                    // 默认1
  "pageSize": 10                                  // 默认10
}
```

其中：
- `appid_number` 为**必填**，**必须在对话框中询问用户提供**
- `pageNo` 默认使用 `1`
- `pageSize` 默认使用 `10`

列表接口的认证头也和普通业务 API 不同，按文档要求使用：

```http
Content-Type: application/json
accesstoken: ${access_token}
```

`login.do` 的请求体如下：

```json
{
  "user": "${config.user}",
  "appId": "${config.appId}",
  "appSecret": "${config.appSecret}",
  "accountId": "${config.accountId}"
}
```

### 第四步：使用发布器

```python
from scripts import KingdeeSkillPublisher

# 创建发布器实例
publisher = KingdeeSkillPublisher()

# 配置凭证
result = publisher.setup_credentials(
    server_url="https://xxx.kingdee.com/ierp",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id",
    user="your_user"
)

if result['success']:
    print("✓ 凭证配置成功")
    
    # 搜索API（appid_number 需询问用户提供）
    apis = publisher.search_apis(
        appid_number="basedata",  # 用户提供
        keyword="凭证"
    )
    for api in apis:
        print(f"- {api['api_code']}: {api['api_name']}")
    
    # ⚠️ 必须在对话框中询问用户选择API
    # 如果用户未选择，不要继续执行
    
    # 创建Skill（用户选择API后执行）
    skill_result = publisher.create_skill_from_api(
        api_info=apis[0],  # 用户选择的API
        skill_name="my-bill-query"
    )
    
    if skill_result['success']:
        print(f"✓ Skill创建成功: {skill_result['skill_path']}")
else:
    print(f"✗ 凭证配置失败: {result['message']}")
```

## 📁 生成的Skill结构

每个生成的Skill都包含以下文件：

```
my-skill/
├── SKILL.md                   # Skill定义（用于Claude识别）
├── README.md                  # 使用说明
├── LICENSE.txt                # 许可证
├── scripts/
│   ├── __init__.py
│   ├── api_call.py           # API调用主逻辑
│   ├── api_client.py         # API客户端（Token管理）
│   └── utils.py              # 工具函数
└── references/
    ├── api_schema.json       # API参数定义
    ├── error_codes.json      # 错误码对照表
    ├── examples.json         # 使用示例
    └── kingdee_api_spec.md   # 规范参考
```

## 💡 使用示例

### 示例1：财务凭证查询Skill（新流程 - 获取API详情后封装）

```python
publisher = KingdeeSkillPublisher()
publisher.setup_credentials(...)

# 1. 搜索财务凭证相关API
apis = publisher.search_apis(
    appid_number="basedata",
    keyword="应收凭证"
)

# 2. ⚠️ 在对话框中展示API列表并询问用户选择
# 必须等待用户明确选择一个API后才能继续

# 3. 获取用户选择的API（包含id字段）
api_info = apis[0]  # 用户选择第一个API
print(f"用户选择: {api_info['api_name']} (ID: {api_info['id']})")

# 4. 使用API ID获取完整详情（包含请求头、请求参数、返回参数）
detail_result = publisher.get_api_detail(api_info['id'])
if detail_result['success']:
    api_detail = detail_result['api_detail']
    print(f"API详情获取成功")
    print(f"  - 请求方式: {api_detail['method']}")
    print(f"  - 请求地址: {api_detail['url']}")
    print(f"  - 请求头参数: {len(api_detail['request_headers'])}个")
    print(f"  - Query参数: {len(api_detail['request_query_params'])}个")
    print(f"  - Body参数: {len(api_detail['request_body_params'])}个")
    print(f"  - 返回参数: {len(api_detail['response_params'])}个")

# 5. 根据API详情封装Skill（自动包含完整的请求头、参数定义）
result = publisher.create_skill_from_api(
    api_info=api_info,  # 传入基本信息
    skill_name="ar-bill-detail-query",
    skill_description="查询应收凭证的详细信息",
    use_detail=True  # 自动调用getDetail获取完整详情
)

# 或使用API ID直接创建（便捷方法）
result = publisher.create_skill_from_api_id(
    api_id=api_info['id'],
    skill_name="ar-bill-detail-query",
    skill_description="查询应收凭证的详细信息"
)

# 6. 发布Skill
if result['success']:
    publish_result = publisher.publish_skill(result['skill_path'])
    print(f"发布结果: {publish_result['message']}")
```

### 示例2：供应链订单查询Skill

```python
# 1. 搜索采购订单API
apis = publisher.search_apis(
    appid_number="basedata",
    keyword="采购订单"
)

# 2. ⚠️ 在对话框中展示API列表并询问用户选择
# 必须等待用户明确选择一个API后才能继续

# 3. 选择采购订单详情查询（用户选择后，获取包含id的api_info）
api_info = [api for api in apis if "详情" in api['api_name']][0]

# 4. 使用API ID直接创建Skill（自动获取完整详情并封装）
result = publisher.create_skill_from_api_id(
    api_id=api_info['id'],
    skill_name="purchase-order-detail",
    skill_description=f"{api_info['api_name']} - {api_info.get('api_description', '')}"
)

# 5. 获取生成的Skill路径
if result['success']:
    skill_path = result['skill_path']
    print(f"Skill已生成: {skill_path}")
    print(f"包含完整的API请求头、请求参数、返回参数定义")
```

## 🔧 配置选项

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| KINGDEE_SERVER_URL | 金蝶服务器地址 | https://xxx.kingdee.com/ierp |
| KINGDEE_USER | 操作用户 | admin |
| KINGDEE_APP_ID | 应用ID | app_123456 |
| KINGDEE_APP_SECRET | 应用密钥 | secret_xyz |
| KINGDEE_ACCOUNT_ID | 账套ID | accountId_789 |

### API客户端参数

```python
client = KingdeeAPIClient(
    server_url="https://server.com:1026",      # 服务器URL
    user="admin",                               # 操作用户
    app_id="app_id",                           # 应用ID
    app_secret="app_secret",                   # 应用密钥
    account_id="account_id"                    # 账套ID
)
```

## 📊 支持的API类型

### 标准预置API

- ✅ 财务模块（应收、应付、总账等）
- ✅ 采购管理（采购订单、收货等）
- ✅ 销售管理（销售订单、发货等）
- ✅ 库存管理（库存查询、盘点等）
- ✅ 生产管理（订单、工艺等）
- 更多模块支持中...

### ISV二开API

- ✅ 自定义API
- ✅ 扩展API
- ✅ 集成API

## 🔐 安全特性

### Token管理

```
✓ 自动获取和缓存Token
✓ 优先使用服务端返回的expire_time推导有效期
✓ Token失效后自动重新获取
✓ Token不硬编码在代码中
```

### 参数验证

```
✓ 自动验证必填参数
✓ 类型检查和转换
✓ 值范围验证
✓ 自定义验证规则
```

### 错误处理

```
✓ 详细的错误码对照
✓ 自动重试机制
✓ 完整的日志记录
✓ 友好的错误提示
```

### 数据安全

```
✓ HTTPS强制使用
✓ 请求/响应加密
✓ 敏感信息脱敏
✓ 审计日志记录
```

## 📚 文档

### 主文档
- **SKILL.md** - 完整的Skill定义和使用指南
- **README.md** - 快速开始和基本用法

### 参考文档
- **references/kingdee_api_spec.md** - 金蝶API规范详解
- **references/api_schema.json** - 生成的Skill的API定义
- **references/error_codes.json** - 错误码对照表
- **references/examples.json** - 完整的使用示例

## 🎓 最佳实践

### 1. 凭证管理

```python
# ✗ 不要这样做
app_secret = "my_secret"

# ✓ 应该这样做
import os
app_secret = os.getenv('KINGDEE_APP_SECRET')
```

### 2. Token缓存

```python
# ✗ 不要每次都获取新Token
token = get_token()

# ✓ 应该复用客户端缓存，并在失效时自动重取
token = client.get_token()
```

### 3. 错误处理

```python
# ✗ 不要忽略错误
result = call_api(params)

# ✓ 应该处理不同类型的错误
result = call_api(params)
if result['error_code'] == 401:
    token = client.get_token(force_refresh=True)
elif result['error_code'] == 429:
    wait_and_retry()
```

### 4. 数据量控制

```python
# ✗ 一次加载所有数据
result = get_all_records()

# ✓ 应该分页查询
for page in range(1, total_pages + 1):
    result = get_records(page_no=page, page_size=100)
```

## 🚦 故障排除

### 问题1：凭证验证失败

**症状**: `凭证验证失败: 无法连接到服务器`

**解决**:
1. 检查KINGDEE_SERVER_URL是否正确
2. 确认网络连接正常
3. 检查防火墙/代理设置

### 问题2：Token过期

**症状**: `401 - Token无效或过期`

**解决**:
- Skill会自动重新调用 `POST {baseUrl}/api/login.do` 获取新Token
- 如果频繁出现，检查 `user/appId/appSecret/accountId` 是否正确
- 也可以检查服务端返回的 `expire_time` 是否符合预期

### 问题3：数据量超限

**症状**: `请求超时`

**解决**:
1. 减小pageSize（如100条）
2. 添加日期范围限制
3. 分批查询而不是一次性加载

### 问题4：API不存在

**症状**: `404 - API不存在`

**解决**:
1. 检查api_code是否正确
2. 确认API已在金蝶平台发布
3. 验证应用权限范围

## 🤝 贡献

欢迎提交问题报告和改进建议！

## 📝 许可证

MIT License - 详见LICENSE.txt

## 📞 支持

### 官方资源
- [金蝶云苍穹开放平台](https://vip.kingdee.com/)
- [OpenAPI文档](https://vip.kingdee.com/knowledge/)
- [社区论坛](https://vip.kingdee.com/community/)

### 本项目
- SKILL.md - 详细功能说明
- references/ - 详细参考文档
- examples.json - 使用示例

## 🎯 未来规划

- [ ] MCP服务支持
- [ ] 批量API包装
- [ ] 工作流编排
- [ ] Web UI配置界面
- [ ] Skill市场集成
- [ ] CI/CD集成

---

**版本**: 1.0.0  
**最后更新**: 2024年3月  
**作者**: Kingdee Integration Team  
**许可证**: MIT
