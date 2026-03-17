# 金蝶云苍穹OpenAPI开发规范参考

本文档是根据官方规范的快速参考，详细信息请查阅官方文档。

## 1. API请求规范

### 协议与数据格式
- **传输协议**: HTTPS（必须）
- **数据格式**: JSON（默认）
- **字符编码**: UTF-8

### 请求URL结构
```
https://{server}/kapi/v2/{isv}/{appId}/{formId}/{apiCode}
```

**参数说明**:
- `server`: 服务器地址（如xxx.kingdee.com/ierp）
- `isv`: ISV标识（kingdee为标准产品，其他为ISV二开）
- `appId`: 应用ID
- `formId`: 表单ID（自定义API无此项）
- `apiCode`: API编码（动宾短语，如 save、getList、getDetail）

### 请求方式

#### GET请求
- **用途**: 查询数据
- **参数位置**: URL查询字符串
- **限制**: 参数长度不超过2048字符
- **例子**:
  ```
  GET /kapi/v2/kingdee/app_id/form_id/getList?pageNo=1&pageSize=10
  ```

#### POST请求
- **用途**: 新增、修改、删除数据
- **参数位置**: Request Body（JSON格式）
- **优势**: 参数无长度限制，安全性更高
- **例子**:
  ```
  POST /kapi/v2/kingdee/app_id/form_id/save
  
  {
    "fieldName": "fieldValue"
  }
  ```

## 2. 认证方式

### AccessToken认证（推荐）

最常见的认证方式，使用客户端凭证获取Token。

**获取Token**:
```
POST /kapi/v2/user/oauth/token

{
  "grant_type": "client_credentials",
  "client_id": "{appId}",
  "client_secret": "{appSecret}",
  "scope": "api"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 7200
}
```

**使用Token**:
```
Authorization: Bearer {access_token}
```

**Token有效期**:
- 默认: 120分钟
- 可配置: 通过MC参数apptoken.timeout
- **建议**: 客户端缓存Token，避免频繁请求
- **限制**: 每小时重新获取不超过100次

### 其他认证方式

1. **JWT认证**: 自签名JWT Token
2. **签名认证**: 双向签名+加密（最安全，适合金融场景）
3. **摘要认证**: MD5摘要认证
4. **基本认证**: HTTP Basic Auth

详见金蝶官方文档: https://vip.kingdee.com/knowledge/

## 3. 请求和响应格式

### 通用请求头
```
Content-Type: application/json
Authorization: Bearer {accessToken}
```

### 通用请求体
```json
{
  "accountId": "账套ID",
  "user": "操作用户",
  // 业务参数
}
```

### 标准响应格式
```json
{
  "success": true,
  "data": {
    // 业务数据
  },
  "errorCode": 0,
  "errorMessage": null
}
```

### 错误响应格式
```json
{
  "success": false,
  "data": null,
  "errorCode": 400,
  "errorMessage": "参数无效"
}
```

## 4. 错误码体系

### OpenAPI引擎错误码（0-999）

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 0 | OK | 成功 |
| 400 | INVALID_PARAM | 参数无效 |
| 401 | UNAUTHORIZED | Token无效或过期 |
| 403 | FORBIDDEN | 禁止访问（IP限制等） |
| 404 | NOT_FOUND | API不存在 |
| 429 | RATE_LIMIT | 超出频率限制 |
| 500 | SERVER_ERROR | 服务内部错误 |
| 601 | DUPLICATE | 数据重复 |
| 602 | DATA_NOT_FOUND | 找不到数据 |
| 701 | SCRIPT_ERROR | 脚本执行错误 |
| 702 | PLUGIN_ERROR | 插件执行异常 |

### 应用业务错误码（appId.100001+）

```
ar.100001 - 客户余额不足
ar.100002 - 应收凭证不存在
ap.100001 - 供应商不存在
pm.100001 - 采购订单不存在
```

## 5. 调用规范

### 参数设计原则

1. **最小化原则**
   - 只发布必要的核心属性
   - 非必要字段不要预置
   - 敏感字段谨慎预置

2. **字段命名**
   - 使用驼峰式命名（camelCase）
   - 英文字段名，中文描述
   - 避免特殊字符和保留字

3. **必填字段标记**
   - 清晰标记哪些字段为必填
   - 提供默认值时说明
   - 类型和约束条件必须明确

### 数据量限制

| 限制项 | 限制值 | 说明 |
|--------|--------|------|
| 单次查询数据量 | 10000条 | 包含分录，超过应分页 |
| 单次保存数据量 | 2000条 | 防止超时和性能问题 |
| 单个请求超时 | 50秒 | 华为云WAF为60秒 |
| 请求头大小 | 8KB | 标准HTTP限制 |

### 频率限制

**公有云**:
- 每租户账套: 最多600次/分钟
- 每应用客户端: 最多30次/秒

**私有云**:
- 可自定义配置
- 按应用、API URL维度

### 幂等性处理

**问题**: 高并发或网络异常时可能重复提交

**解决方案1: Idempotency-Key**
```
请求头添加:
Idempotency-Key: {随机GUID}

说明:
- 30秒内有效
- 同一Key的重复请求会被拒绝
- 版本要求: V5.0.005及以上
```

**解决方案2: API防重复配置**
```
在金蝶平台API配置界面:
- 打开"防止重复请求"开关
- 30秒内相同参数的重复请求被拒绝
- 版本要求: V5.0.018及以上
```

## 6. 安全规范

### Token安全

1. **客户端缓存Token**
   - 不应每次调用都请求新Token
   - 监测Token过期，自动刷新
   - 建议缓存到Redis或内存

2. **Token存储**
   - 不应硬编码在代码中
   - 通过环境变量或密钥管理系统传递
   - 限制访问权限

3. **Token传输**
   - 必须使用HTTPS
   - 建议放在Authorization请求头而不是URL参数

### 凭证安全

1. **appSecret保护**
   - 严禁硬编码在客户端代码
   - 不要在版本控制中提交
   - 定期轮换密钥

2. **权限控制**
   - 遵循最小权限原则
   - 为不同应用创建不同凭证
   - 限制应用的IP和API访问范围

### 数据安全

1. **敏感信息加密**
   - 密码、支付信息必须加密
   - 手机号、身份证等信息需脱敏
   - 使用平台加密策略和隐私中心

2. **输入验证**
   - 严格验证所有用户输入
   - 防止SQL注入和XSS攻击
   - 参数类型和长度限制

3. **审计日志**
   - 记录所有API调用
   - 包括请求参数和响应结果
   - 便于问题追查和安全审计

## 7. API文档规范

### 必须包含的信息

| 项目 | 说明 |
|------|------|
| API编码 | 如getList、save、getDetail |
| API名称 | 中文描述，简明扼要 |
| 请求方式 | GET或POST |
| API状态 | 内测/发布/维护/禁用 |
| 请求参数 | 参数名、类型、是否必填、说明 |
| 返回参数 | 返回字段、类型、说明 |
| 错误码 | 业务相关的错误码和说明 |
| 使用示例 | 完整的调用示例 |
| 版本要求 | 最低苍穹版本 |

### 文档示例

```markdown
## getList - 获取订单列表

### 基本信息
- **编码**: getList
- **请求方式**: GET
- **状态**: 发布
- **版本**: v2

### 功能说明
分页获取订单列表，支持按状态、日期等条件过滤。

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| pageNo | Int | 是 | 页码，从1开始 |
| pageSize | Int | 否 | 页大小，默认20，最大100 |
| status | String | 否 | 订单状态(DRAFT/ISSUED/CONFIRMED) |

### 返回参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| total | Int | 总记录数 |
| pageNo | Int | 当前页码 |
| items | Array | 订单列表 |

### 错误码
| 错误码 | 说明 |
|--------|------|
| 400 | pageNo或pageSize参数无效 |
| 602 | 未找到符合条件的数据 |

### 请求示例
```

## 8. API兼容性维护

### 版本策略

1. **兼容性承诺**
   - API一旦发布，新版本必须向下兼容
   - 业务逻辑变动不应影响接口调用

2. **参数变更**
   - 参数名和类型不得更改
   - 不可删除已有参数
   - 新增参数必须设置默认值

3. **版本升级**
   - 重大变更创建新API版本
   - 在API编码上增加版本标识：save/ver2
   - 同时维护旧版本一段时间

### 测试要求

1. **单元测试**
   - 每个接口应有配套的自动化测试
   - 覆盖正常场景和异常场景
   - 测试用例作为文档的补充

2. **回归测试**
   - 升级时进行兼容性测试
   - 测试旧客户端调用新API
   - 确保无破坏性变更

## 9. 常见最佳实践

### 查询优化

```
// 不好的做法 - 一次性加载所有数据
GET /kapi/v2/.../getList
响应: 100000条记录

// 良好的做法 - 分页查询
GET /kapi/v2/.../getList?pageNo=1&pageSize=100
响应: 100条记录
```

### Token管理

```python
# 不好做法
class API:
    def call(self):
        token = get_new_token()  # 每次调用都获取新Token
        return request(token)

# 良好做法
class API:
    def __init__(self):
        self.token = None
        self.expires = None
    
    def call(self):
        if not self._is_token_valid():
            self.token = get_new_token()
        return request(self.token)
```

### 错误处理

```python
# 不好做法
try:
    result = call_api(params)
except Exception as e:
    print("出错了")

# 良好做法
try:
    result = call_api(params)
    if result['errorCode'] == 401:
        # Token过期，重新获取
        refresh_token()
    elif result['errorCode'] == 429:
        # 限流，等待后重试
        wait_and_retry()
    elif result['errorCode'] != 0:
        # 业务错误，返回给用户
        return error_response(result)
except ConnectionTimeout:
    # 超时，重试
    retry()
except Exception as e:
    # 日志记录，告知用户
    log_error(e)
```

## 10. 参考资源

- **官方文档**: https://vip.kingdee.com/knowledge/
- **认证指南**: API认证开发指南
- **API列表**: 开放平台控制台 → API管理
- **社区支持**: 金蝶云社区论坛

---

**最后更新**: 2024年
**适用版本**: 金蝶云苍穹 6.0+
