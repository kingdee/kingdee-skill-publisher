---
name: kingdee-skill-publisher
description: |

  金蝶云苍穹业务Skill快速发布工具。这是一个元Skill，用于基于金蝶苍穹开放平台已发布的API和MCP服务，快速创建和发布财务凭证查询、供应链订单查询等业务Skill。
  
  使用此Skill时：
  1. 用户需要配置金蝶苍穹服务器URL和API认证凭证（user、appId、appSecret、accountId）
  2. Skill通过 `POST {baseUrl}/api/login.do` 获取 `access_token`
  3. Claude通过自然语言查询金蝶API清单，用户选择所需API
  4. Claude自动包装成Skill并发布
  5. 未来兼容MCP服务集成
  
  触发场景：当用户想要快速发布金蝶业务Skill、配置金蝶API接口、查询金蝶API清单时，使用此Skill。
---

# 金蝶云苍穹业务Skill发布器

这是一个元Skill（Meta Skill），用于快速发布基于金蝶云苍穹开放平台的业务Skill。它简化了从API集成到Skill发布的全流程。

---

## ⛔ 强制执行规则（最高优先级）

> **本 Skill 的所有操作（凭证验证、API 查询、API 详情获取、Skill 生成）都必须通过执行 Python 脚本完成。AI 不得自行编写、猜测或拼凑任何业务文件内容。**

### 必须遵守

1. **凭证验证** → 必须执行 `publisher.setup_credentials()` Python 代码
2. **API 列表查询** → 必须执行 `publisher.search_apis()` Python 代码
3. **API 详情获取** → 必须执行 `publisher.api_client.get_api_detail()` Python 代码
4. **Skill 生成** → 必须执行 `publisher.create_skill_from_api()` 或 `SkillGenerator.generate_skill()` Python 代码
5. **所有 API URL** → 必须来自服务器 `getDetail` 接口返回的 `urlformat` 字段，禁止猜测或拼凑

### 绝对禁止

- ❌ **禁止 AI 自行编写 SKILL.md、api_call.py 等业务文件**（必须由 Python 脚本生成）
- ❌ **禁止 AI 猜测 API 的 URL 地址**（必须从服务器获取）
- ❌ **禁止 AI 猜测 API 的请求参数和返回参数**（必须从 getDetail 获取）
- ❌ **禁止跳过 Python 脚本直接用 write_to_file 创建 Skill 文件**

### 执行方式

所有 Python 代码必须通过 `execute_command` 工具执行，示例：

```bash
cd /path/to/kingdee-skill-publisher && python3 -c "
from scripts import KingdeeSkillPublisher
publisher = KingdeeSkillPublisher()
publisher.setup_credentials(server_url=..., app_id=..., app_secret=..., account_id=..., user=...)
result = publisher.search_apis(appid_number='xxx', keyword='yyy')
print(result)
"
```

---

## 核心功能

### 1. 凭证管理
- 引导用户配置金蝶服务器连接信息
- 存储和验证API认证凭证（user、appId、appSecret、accountId）
- 按 `login.do` 协议获取并缓存 `access_token`
- 在Token失效时自动重新获取

### 2. API探索与选择
- 自然语言查询金蝶API清单
- 支持按模块、功能、API编码搜索
- 展示API文档细节和参数信息

### 3. Skill自动生成
- 基于选定的API自动生成Skill
- 智能包装参数校验和错误处理
- 生成Skill的README和使用说明

### 4. 发布与测试
- 打包Skill文件（.skill格式）
- 生成测试用例
- 提供Skill安装指引

## 工作流

```
┌─────────────────────────────────────────┐
│ 1. 配置凭证与连接                          │
│    - Server URL                          │
│    - user / appId / appSecret / accountId│
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 2. 询问 appid_number                     │
│    - 必须询问用户提供应用编码              │
│    - 未提供则停止执行                      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 3. 搜索API列表                            │
│    - 调用 queryByApp 获取API清单           │
│    - 展示API名称、编码、描述               │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 4. 用户选择API                            │
│    - 展示API列表供用户选择                 │
│    - 必须等待用户明确选择                  │
│    - 未选择则停止执行                      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 5. 获取API详情 (getDetail)                │
│    - 使用API ID调用详情接口                │
│    - 获取请求头、请求参数、返回参数         │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 6. 封装Skill                              │
│    - 根据详情生成请求头处理代码            │
│    - 生成参数验证和响应解析逻辑            │
│    - 生成完整Skill结构                     │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ 7. 测试与发布                             │
│    - 生成测试用例                         │
│    - 打包 Skill                           │
│    - 提供安装指引                         │
└─────────────────────────────────────────┘
```

## 快速开始

### 第一步：初始化配置

当用户开始使用此Skill时，引导进行以下操作：

**需要收集的信息：**
```
金蝶服务器配置：
├─ 服务器 URL（必须）
│  示例：https://xxx.kingdee.com:ierp
│
├─ appId（必须）
│  由金蝶开放平台第三方应用申请
│
├─ appSecret（必须）
│  需妥善保管，不应暴露
│
├─ accountId（必须）
│  租户账套ID
│
└─ User（必须）
   当前操作用户，用于 login.do 认证和业务接口调用
```

**配置验证步骤：**
1. 检查服务器连通性
2. 调用 `POST {baseUrl}/api/login.do` 获取 `access_token`
3. 使用 `Authorization: Bearer {access_token}` 调用测试接口验证权限
4. 列出可用的API清单（验证查询能力）

### 第二步：探索与查询API（⚠️ 必须执行 Python 脚本）

> ⛔ 必须通过 `execute_command` 执行 `publisher.search_apis()` Python 代码查询，禁止 AI 自行构造 HTTP 请求。

本Skill使用金蝶官方的 `queryByApp` 接口按应用编码查询API列表，确保返回结果与当前应用实际发布的API保持一致。

**接口路径**: `GET /kapi/v2/open/openapi_apilist/queryByApp`

**⚠️ 重要：查询前必须获取 appid_number**

在调用API查询前，**必须在对话框中询问用户提供 `appid_number`**（应用编码）。

- 如果用户提供了 `appid_number`：继续执行查询
- **如果用户未提供 `appid_number`：停止执行，不再进行后续任务**

**询问示例**：
```
我需要查询API列表，请提供应用编码（appid_number）。
例如：basedata、ar、ap、pm 等
```

用户可以通过多种方式查询API：

**方式1：按应用编码获取完整列表**
- 用户必须显式传入 `appid_number`
- `pageNo` 默认值为 `1`
- `pageSize` 默认值为 `10`

**方式2：对结果做本地过滤**
- 关键词过滤：匹配 API 编码、名称、描述
- 模块过滤：基于返回记录中的编码或 URL 做最佳努力过滤

**查询返回信息：**
- API编码 (apiCode) - 用于API调用
- API名称 (apiName) - 中文描述
- 请求方式 (method) - GET/POST
- API描述 (apiDescription) - 功能说明
- 所属模块 (module) - ar/ap/pm等
- API版本 (version) - 版本号
- API状态 (status) - 发布/草稿等
- 请求参数 (requestParams) - 完整的参数定义
- 返回参数 (returnParams) - 返回字段定义
- 错误码 (errorCodes) - 业务错误码

**示例查询结果：**

```python
# 注意：appid_number 必须询问用户提供
result = publisher.search_apis(
    appid_number="basedata",  # 用户提供的应用编码
    keyword="凭证"
)

# 输出示例：
{
    "success": True,
    "total": 5,
    "apis": [
        {
            "apiCode": "ar_getBillDetail",
            "apiName": "应收凭证详情",
            "method": "GET",
            "module": "ar",
            "apiDescription": "查询应收凭证的详细信息",
            "requestParams": [
                {"name": "billId", "type": "String", "required": True, "description": "凭证ID"}
            ],
            "returnParams": [
                {"name": "id", "type": "String", "description": "凭证ID"},
                {"name": "billNo", "type": "String", "description": "凭证号"}
            ]
        },
        # ... 更多API
    ]
}
```

**⚠️ 重要：必须等待用户选择API**

返回API列表后，**必须在对话框中展示API列表并询问用户选择**，示例如下：

```
找到以下API，请选择一个继续：

1. ar_getBillDetail - 应收凭证详情
   描述：查询应收凭证的详细信息
   
2. ar_getBillList - 应收凭证列表
   描述：查询应收凭证列表

请输入序号（1-2）或直接告诉我API名称：
```

**执行规则**：
- 如果用户**选择了API**：继续执行第三步获取API详情
- **如果用户没有选择API：停止执行，不再进行后续任务**

### 第三步：获取API详情（⚠️ 必须执行 Python 脚本）

> ⛔ 必须通过 `execute_command` 执行 `publisher.api_client.get_api_detail(api_id)` Python 代码获取详情，禁止 AI 自行猜测 API 的 URL、参数和返回值。

**前置条件：用户已明确选择了一个API**

用户选择API后，Claude必须通过执行Python代码调用详情接口获取完整的API定义（包括真实URL）：

**接口信息**：
- **接口地址**: `GET /v2/open/openapi_apilist/getDetail`
- **请求方式**: GET
- **请求头**: 
  - `Content-Type`: application/json
  - `accesstoken`: {access_token}
- **Query参数**:
  - `id`: API主键ID（必填，从第二步API列表中获取）
  - `pageSize`: 分页大小（**必填**，即使只查询单条记录，默认10）
  - `pageNo`: 查询页码（可选，默认1）

**⚠️ 重要提示**: 此查询接口**必须传递分页参数 `pageSize` 和 `pageNo`**，即使只查询单条记录。

**返回内容** (`data.rows[0]`):
```json
{
  "success": true,
  "api_detail": {
    "id": "API主键ID",
    "api_code": "API编码",
    "api_name": "API名称",
    "api_description": "API描述",
    "method": "GET/POST",
    "url": "/v2/open/...",
    "request_headers": [
      {"name": "Content-Type", "value": "application/json", "description": "内容格式", "required": true},
      {"name": "accesstoken", "value": "...", "description": "请求令牌", "required": true}
    ],
    "request_query_params": [
      {"name": "id", "type": "Long", "description": "主键ID", "required": true, "example": ""}
    ],
    "request_body_params": [
      {"name": "param1", "type": "String", "description": "参数说明", "required": true, "example": "..."}
    ],
    "response_params": [
      {"name": "field1", "type": "String", "description": "字段说明", "required": true, "level": "1"}
    ],
    "error_codes": [
      {"code": "400", "description": "参数错误"}
    ]
  }
}
```

**参数来源说明**（根据金蝶OpenAPI文档）：
| 规范化字段 | 原始字段 | 说明 |
|------------|----------|------|
| `request_headers` | `headerentryentity` | 请求头参数 |
| `request_query_params` | `urlparamentryentity` | URL查询参数 |
| `request_body_params` | `bodyentryentity` | 请求体参数 |
| `response_params` | `respentryentity` | 返回参数 |
| `error_codes` | `errorcodeentity` | 错误码定义 |
| `orderby_rules` | `orderby_entry` | 排序规则 |
| `save_params` | `saveparamentryentity` | 操作参数 |
```

### 第四步：封装Skill（⚠️ 必须通过 Python 代码生成）

**⚠️⚠️⚠️ 关键原则：必须通过执行 Python 代码生成 Skill，禁止手动编写文件内容**

获取到完整的API详情后，Claude **必须调用项目中的 Python 代码**来生成 Skill，而**不是自己直接编写文件内容**。Python 代码内置了 YAML 描述头生成和验证逻辑，能确保生成的 SKILL.md 格式正确。

**方式1（推荐）：使用 `KingdeeSkillPublisher.create_skill_from_api_id()`**

```python
from scripts import KingdeeSkillPublisher

publisher = KingdeeSkillPublisher()
publisher.setup_credentials(
    server_url=server_url,
    app_id=app_id,
    app_secret=app_secret,
    account_id=account_id,
    user=user
)

# 使用用户选择的 API 的主键 ID 直接生成 Skill
result = publisher.create_skill_from_api_id(
    api_id=selected_api['id'],           # 用户选择的 API 主键 ID
    skill_name="ar-bill-detail-query",    # 可选，默认使用 API 编码
    skill_description="查询应收凭证详情"    # 可选
)

if result['success']:
    print(f"✅ Skill 已生成: {result['skill_path']}")
else:
    print(f"❌ 生成失败: {result['message']}")
```

**方式2：使用 `KingdeeSkillPublisher.create_skill_from_api()`**

```python
# 使用 search_apis 返回的 api_info + use_detail=True 自动获取详情
result = publisher.create_skill_from_api(
    api_info=selected_api,               # 用户选择的 API（包含 id 字段）
    skill_name="ar-bill-detail-query",
    skill_description="查询应收凭证详情",
    use_detail=True                       # 自动调用 getDetail 获取完整详情
)
```

**方式3：直接使用 `SkillGenerator`**

```python
from scripts.skill_generator import SkillGenerator

generator = SkillGenerator(output_dir="./outputs")
skill_dir = generator.generate_skill(
    api_info=api_detail,                  # 完整的 API 详情字典
    custom_name="ar-bill-detail-query",
    custom_description="查询应收凭证详情"
)
print(f"✅ Skill 已生成: {skill_dir}")
```

**Python 代码会自动完成以下工作**：

1. **生成带 YAML 描述头的 SKILL.md**（内置 frontmatter 验证，确保 `name:` 和 `description: |` 字段完整）
2. 根据 `request_headers` 生成请求头处理代码（`scripts/api_call.py`）
3. 复制 API 客户端代码（`scripts/api_client.py`，含 Token 管理）
4. 根据 `request_query_params` 和 `request_body_params` 生成参数验证逻辑
5. 根据 `response_params` 生成 API schema（`references/api_schema.json`）
6. 根据 `error_codes` 生成错误码对照表（`references/error_codes.json`）
7. 生成使用示例（`references/examples.json`）
8. 生成 README.md 和 LICENSE.txt
9. **最终验证** SKILL.md 描述头完整性

**生成的 Skill 目录结构**：
```
${skill_name}/
├─ SKILL.md（包含 YAML 描述头，由 Python 代码自动生成并验证）
├─ scripts/
│  ├─ __init__.py
│  ├─ api_call.py（API 调用逻辑）
│  ├─ api_client.py（API 客户端，Token 管理）
│  └─ utils.py（工具函数）
├─ references/
│  ├─ api_schema.json（API 参数 schema）
│  ├─ error_codes.json（错误码对照）
│  └─ examples.json（使用示例）
├─ README.md
└─ LICENSE.txt
```

**⚠️ 禁止事项**：
- ❌ 禁止手动编写 SKILL.md 文件内容（会遗漏描述头）
- ❌ 禁止跳过 Python 代码直接创建文件
- ❌ 禁止修改生成的 SKILL.md 描述头格式

**API 详情字段说明**（Python 代码内部使用）：

| 规范化字段 | 原始字段 | 说明 |
|------------|----------|------|
| `request_headers` | `headerentryentity` | 请求头参数 |
| `request_query_params` | `urlparamentryentity` | URL 查询参数 |
| `request_body_params` | `bodyentryentity` | 请求体参数 |
| `response_params` | `respentryentity` | 返回参数 |
| `error_codes` | `errorcodeentity` | 错误码定义 |
| `orderby_rules` | `orderby_entry` | 排序规则 |
| `save_params` | `saveparamentryentity` | 操作参数 |

### 第五步：测试与发布

**自动生成的测试用例包括：**
- 参数验证测试
- 基本API调用测试
- 错误处理测试
- 权限控制测试

**发布输出：**
- `.skill` 打包文件
- 安装指引
- 使用示例代码
- API文档引用

## 配置示例

### 示例1：财务凭证查询Skill（完整 Python 流程）

```
用户输入：我想创建一个财务凭证查询的Skill
         告诉我有哪些相关的API

Claude执行：
1. 查询API清单（执行 Python 代码）
```

```python
from scripts import KingdeeSkillPublisher

publisher = KingdeeSkillPublisher()
publisher.setup_credentials(
    server_url=server_url,
    app_id=app_id,
    app_secret=app_secret,
    account_id=account_id,
    user=user
)

# 搜索API
apis_result = publisher.search_apis(appid_number="basedata", keyword="凭证")
```

```
2. 展示API列表供用户选择：
   - ar.getBillDetail（应收凭证详情）
   - ar.getBillList（应收凭证列表）

用户选择：选择 ar.getBillDetail

Claude执行：
3. 通过 Python 代码生成 Skill（⚠️ 禁止手动编写文件）
```

```python
# 使用 Python 代码生成 Skill（自动包含 YAML 描述头）
result = publisher.create_skill_from_api_id(
    api_id=selected_api['id'],
    skill_name="ar-bill-detail-query",
    skill_description="查询应收凭证详情"
)

if result['success']:
    print(f"✅ Skill 已生成: {result['skill_path']}")
    # Python 代码自动生成的 SKILL.md 包含完整的 YAML 描述头
    # Python 代码自动处理了 Token 管理、参数验证、错误处理等
```

### 示例2：供应链订单查询Skill

```
用户输入：我需要查询供应链的订单信息

Claude执行：
1. 搜索相关API（执行 publisher.search_apis）
2. 展示列表供用户选择

用户选择：选择 pm.getPurchaseOrderDetail

Claude执行：
3. 通过 Python 代码生成 Skill（⚠️ 禁止手动编写文件）
```

```python
result = publisher.create_skill_from_api_id(
    api_id=selected_api['id'],
    skill_name="purchase-order-detail",
    skill_description="查询采购订单详情"
)
```

## 金蝶API文档规范参考

此Skill基于金蝶云苍穹OpenAPI开放平台的规范实现：

### API请求规范
- **协议**: HTTPS
- **数据格式**: JSON（默认）
- **请求地址**: `/kapi/v2/{isv}/{appId}/{formId}/{apiCode}`
- **请求方式**: GET（查询）/ POST（新增/修改）

### 认证方式（当前实现）
- Token获取接口：`POST {baseUrl}/api/login.do`
- 请求体：

```json
{
  "user": "${config.user}",
  "appId": "${config.appId}",
  "appSecret": "${config.appSecret}",
  "accountId": "${config.accountId}"
}
```

- 成功响应：从 `data.access_token` 读取访问令牌
- 业务调用：通过请求头 `Authorization: Bearer {access_token}` 传递Token
- API列表查询：通过请求头 `accesstoken: {access_token}` 传递Token

### Token管理
- 默认缓存：内存缓存，不落盘
- 过期时间：优先使用 `data.expire_time` 反推剩余有效期；未返回时按120分钟处理
- 复用策略：Token未过期时直接复用缓存值
- 失效处理：收到401或业务响应中的401后自动重新获取Token

### 重要限制
- **单次请求最长响应时间**: 50秒
- **单次查询数据量**: 不超过1万条
- **单次保存数据量**: 不超过2000条
- **频率限制**: 
  - 公有云：每租户账套最多600次/分
  - 单个应用客户端最多30次/秒

### 错误码体系
```
0-999       OpenAPI引擎错误（0正常、400参数无效、401未授权、403禁止、404不存在、500服务异常）
appId.100001+ 应用业务错误
```

### 幂等性处理
两种方案支持：
1. **Idempotency-Key**: 在请求头中传递随机值，30秒内有效
2. **API配置**: 在金蝶平台打开防止重复请求开关

## 高级特性

### 1. MCP服务兼容性（未来扩展）

Skill发布器将来支持基于金蝶MCP服务创建Skill，允许：
- 直接调用MCP服务接口
- 组合多个MCP服务构建复杂业务流程
- 跨系统数据联动

### 2. 批量API包装

支持在一个Skill中包装多个相关API：
```
示例：订单完整流程Skill
├─ 订单查询（API）
├─ 订单详情（API）
├─ 订单状态变更（MCP）
└─ 库存扣减（MCP）
```

### 3. 参数智能映射

自动处理参数映射：
- 类型转换（字符串↔数字↔日期）
- 格式规范化（驼峰命名转下划线）
- 默认值填充
- 枚举值验证

### 4. 错误和日志

完整的错误处理链：
- 网络错误重试
- 业务错误提示
- Token过期自动重取
- 详细的调试日志

## 文件组织结构

生成的Skill遵循以下结构：

```
${skill_name}/
├── SKILL.md                    # ⚠️ Skill定义（必须包含 YAML 描述头）
├── scripts/
│   ├── __init__.py
│   ├── api_client.py          # API客户端（Token管理、请求）
│   ├── api_call.py            # 主要API调用逻辑
│   └── utils.py               # 工具函数
├── references/
│   ├── api_schema.json        # API请求/返回schema
│   ├── error_codes.json       # 错误码对照表
│   ├── examples.json          # 使用示例
│   └── kingdee_api_spec.md    # API文档快速参考
├── README.md                   # 使用说明
└── LICENSE.txt                # 许可证
```

## 内部处理流程

### 凭证初始化
1. 用户提供服务器信息和API凭证
2. 通过 `HEAD {baseUrl}/kapi` 验证基础连通性
3. 通过 `POST {baseUrl}/api/login.do` 获取初始 `access_token`
4. 将Token缓存在客户端内存中
5. 使用 `getUserInfo` 等轻量接口验证认证和权限

### API查询
1. 先确保存在有效 `access_token`
2. 通过 `GET /kapi/v2/open/openapi_apilist/queryByApp` 按 `appid_number` 查询当前应用API
3. 自动附带 `accesstoken` 请求头和分页参数 `pageNo/pageSize`
4. 将返回记录规范化为内部统一字段（如 `api_code/api_name/api_description`）
5. 按用户查询条件做本地过滤
6. 返回简化的列表视图并支持自然语言匹配

### Skill生成（⚠️ 必须执行 Python 代码）
1. **调用 `publisher.create_skill_from_api_id(api_id)` 或 `publisher.create_skill_from_api(api_info, use_detail=True)`**
2. Python 代码内部自动完成：
   - 解析API文档（参数、错误码等）
   - 生成带 YAML 描述头的 SKILL.md（内置 frontmatter 验证）
   - 生成 API 调用脚本（`scripts/api_call.py`）
   - 生成参考文档和示例（`references/`）
   - 生成 README.md 和 LICENSE.txt
   - **最终验证 SKILL.md 描述头完整性**
3. ❌ 禁止跳过 Python 代码手动编写文件

### 测试用例生成
1. 基于API参数生成正常用例
2. 基于错误码生成异常用例
3. 基于约束生成边界用例
4. 验证Token获取、请求头注入和接口调用链路

## 注意事项

### 安全性
- **凭证保护**: appSecret不应硬编码在Skill中，通过环境变量或密钥管理系统传递
- **Token缓存**: 仅在客户端缓存，不应持久化到磁盘
- **参数验证**: 严格验证所有用户输入，防止注入攻击
- **HTTPS强制**: 所有API调用使用HTTPS，验证证书有效性

### 可靠性
- **幂等性**: 关键操作启用幂等性检查，防止重复执行
- **重试策略**: 网络超时自动重试，可配置重试次数
- **Token重取**: 监测Token过期，自动重新获取新Token
- **错误恢复**: 明确的错误分类和恢复策略

### 性能
- **分页查询**: 大数据量自动分页，防止超时
- **缓存策略**: 缓存Token和元数据，减少冗余请求
- **批量操作**: 支持批量查询，优化网络效率
- **异步处理**: 长流程操作可配置异步模式

## 进阶：手动调整生成的Skill

生成的Skill可以进一步手动调整：

### 1. 自定义参数映射
修改 `scripts/api_call.py` 中的参数转换逻辑

### 2. 增强错误处理
在 `references/error_codes.json` 中添加业务特定的错误处理规则

### 3. 扩展功能
组合多个API实现更复杂的业务流程

### 4. 优化文档
补充业务场景说明和最佳实践

## 常见问题

**Q: 如何管理多个Skill的凭证？**
A: 每个Skill可以有独立的凭证配置，或者共享一个中央配置库。建议使用环境变量隔离凭证。

**Q: Skill支持哪些金蝶API？**
A: 所有金蝶云苍穹开放平台已发布的API都支持，包括标准预置API和ISV二开API。

**Q: 如何处理Token过期？**
A: 生成的Skill会优先复用内存中的Token；如果本地判断已过期，或接口返回HTTP 401/业务401，则自动重新调用 `POST {baseUrl}/api/login.do` 获取新Token。用户无需手动处理。

**Q: 可以同时调用多个API吗？**
A: 可以。生成的Skill支持组合调用多个API实现复杂业务流程。

**Q: 如何处理大数据量？**
A: 自动分页处理，单次查询最多1万条，保存2000条。

---

## 反馈与改进

如有建议或问题，请提出反馈，我们会持续改进此元Skill的功能和易用性。
