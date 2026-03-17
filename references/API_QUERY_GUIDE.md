# 金蝶官方根据应用编码查询API列表接口集成

## 概述

本文档说明如何使用金蝶开放平台的官方 `queryByApp` 接口，按应用编码获取可用API列表。

## API接口信息

### 接口名称
- **API编码**: queryByApp
- **API名称**: 根据应用编码查询API列表
- **请求方式**: GET
- **数据格式**: JSON

### 完整请求URL
```
https://xxx.kingdee.com/ierp/kapi/v2/open/openapi_apilist/queryByApp
```

## 请求参数

### Query参数

```json
{
  "appid_number": "basedata",     // 所属应用编码（必填）
  "pageNo": 10,                   // 默认页码，用户可自行修改
  "pageSize": 20                  // 每页数量（查询类接口必传）
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| appid_number | String | 是 | - | 所属应用编码 |
| pageNo | Integer | 是 | 10 | 页码，从1开始，默认10 |
| pageSize | Integer | 是 | 20 | 每页数量，建议50-100 |

### 常见模块代码

```
ar     应收模块
ap     应付模块
pm     采购管理
so     销售管理
ic     库存管理
ps     生产管理
jc     成本管理
gl     总账
bd     基础资料
```

## 响应格式

### 成功响应

```json
{
  "status": true,
  "data": {
    "filter": "[appid.number = 'your_app_id']",
    "lastPage": true,
    "pageNo": 1,
    "pageSize": 20,
    "rows": [
      {
        "number": "pm_queryOrder",
        "name": {"zh_CN": "采购订单查询"},
        "discription": {"zh_CN": "查询采购订单"},
        "httpmethod": "0",
        "urlformat": "/kapi/v2/kingdee/your_app_id/order/query"
      }
    ],
    "totalCount": 1
  },
  "errorCode": "0",
  "message": null
}
```

### 失败响应

```json
{
  "success": false,
  "errorCode": 400,
  "errorMessage": "参数无效"
}
```

## Python使用示例

### 基础使用

```python
from scripts import KingdeeSkillPublisher

# 初始化发布器
publisher = KingdeeSkillPublisher()

# 配置凭证
publisher.setup_credentials(
    server_url="https://xxx.kingdee.com/ierp",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id"
)

# 搜索API
result = publisher.search_apis(appid_number="basedata", keyword="凭证")

if result['success']:
    print(f"找到 {result['total']} 个API")
    for api in result['apis']:
        print(f"  {api['apiCode']}: {api['apiName']}")
else:
    print(f"搜索失败: {result['message']}")
```

### 按关键词做本地过滤

```python
# 先按应用编码获取当前应用下的API，再按关键词本地过滤
result = publisher.search_apis(appid_number="basedata", keyword="订单", page_size=100)
```

### 分页获取所有API

```python
# 使用API客户端直接获取（支持完整的分页信息）
client = publisher.client

# 获取第一页
result = client.get_api_list(appid_number="basedata", page_no=10, page_size=100)
print(f"总共 {result['total']} 个API")
print(f"第 {result['pageNo']} 页，每页 {result['pageSize']} 条")

# 自动获取所有API（自动处理分页）
all_apis = client.get_all_apis(appid_number="basedata", page_size=100)
print(f"获取了 {len(all_apis)} 个API")
```

### 按关键词搜索

```python
# 便利方法：按关键词搜索
apis = publisher.client.query_api_by_keyword("凭证", appid_number="basedata", page_size=50)
for api in apis:
    print(f"{api['apiCode']}: {api['apiName']}")
```

## 实现细节

### api_client.py 中的实现

```python
def get_api_list(self, 
                 search_keyword: str = None,
                 module: str = None,
                 page_no: int = 1,
                 page_size: int = 20) -> Dict[str, Any]:
    """查询金蝶开放平台的API列表"""
    
    response = requests.post(
        f"{self.server_url}/kapi/v2/open/openapi_apilist/queryByApp",
        json={
            "appid_number": self.app_id,
            "pageNo": page_no,
            "pageSize": min(page_size, 100),
        },
        headers={
            "Content-Type": "application/json",
            "accesstoken": token,
        }
    )
    
    # 处理响应...
    return {
        'success': result.get('success', False),
        'total': result.get('data', {}).get('total', 0),
        'pageNo': result.get('data', {}).get('pageNo', page_no),
        'apis': result.get('data', {}).get('apis', []),
        'message': result.get('error_msg', '查询成功')
    }
```

## 响应数据解析

### API对象结构

每个API对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | API的唯一标识 |
| apiCode | String | API编码（用于调用API） |
| apiName | String | API显示名称（中文） |
| apiDescription | String | API详细描述 |
| method | String | HTTP方法（GET/POST） |
| formId | String | 表单ID（如果有） |
| module | String | 所属模块代码 |
| version | String | API版本 |
| status | String | API状态（published/draft/deprecated等） |
| requestParams | Array | 请求参数列表 |
| returnParams | Array | 返回参数列表 |
| errorCodes | Array | 错误码列表 |
| createTime | String | 创建时间 |
| updateTime | String | 更新时间 |

### 参数对象结构

```json
{
  "name": "billId",           // 参数名
  "type": "String",           // 数据类型
  "required": true,           // 是否必填
  "description": "凭证ID",    // 参数描述
  "defaultValue": null,       // 默认值
  "example": "123456"         // 示例值
}
```

## 搜索技巧

### 1. 按功能搜索

```python
# 搜索所有凭证相关API
apis = publisher.search_apis(keyword="凭证")

# 搜索所有列表API
apis = publisher.search_apis(keyword="getList")

# 搜索所有详情API
apis = publisher.search_apis(keyword="getDetail")
```

### 2. 本地过滤查询

```python
# 获取当前应用的订单相关API
order_apis = publisher.search_apis(keyword="订单", page_size=100)
```

### 3. 组合搜索

```python
# 搜索应收模块的查询类API
ar_query = publisher.search_apis(
    keyword="get",
    module="ar",
    page_size=50
)
```

## 常见用例

### 用例1：查找特定功能的API

```python
# 场景：我想查询财务凭证
publisher = KingdeeSkillPublisher()
publisher.setup_credentials(...)

# 搜索凭证相关的API
result = publisher.search_apis(keyword="凭证")

# 从结果中选择需要的API
for api in result['apis']:
    print(f"{api['apiCode']}: {api['apiName']}")
    # 选择ar_getBillDetail来创建Skill
    
# 创建Skill
selected_api = result['apis'][0]
publisher.create_skill_from_api(selected_api)
```

### 用例2：批量创建模块相关的Skills

```python
# 场景：为当前应用中的查询类API创建多个Skill

# 获取当前应用的所有API
ar_apis = publisher.search_apis(page_size=100)

# 为每个重要API创建Skill
for api in ar_apis:
    if "get" in api['apiCode'].lower():  # 只创建查询类API
        result = publisher.create_skill_from_api(
            api_info=api,
            skill_name=f"ar-{api['apiCode'].lower()}"
        )
        print(f"创建Skill: {result['skill_name']}")
```

### 用例3：探索可用的API

```python
# 场景：发现系统中有哪些API可用

# 获取所有已发布的API
all_apis = publisher.client.get_all_apis(page_size=100)

# 按 URL 前缀做近似分组
from collections import defaultdict
apis_by_module = defaultdict(list)

for api in all_apis:
    module = api.get('urlformat', 'unknown').split('/')[1] if api.get('urlformat') else 'unknown'
    apis_by_module[module].append(api)

# 显示模块统计
for module, apis in sorted(apis_by_module.items()):
    print(f"{module}: {len(apis)} 个API")
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 400 | 参数无效 | 检查请求参数格式 |
| 401 | 未授权 | 检查Token是否过期 |
| 403 | 禁止访问 | 检查权限配置 |
| 429 | 限流 | 稍后重试或减少请求频率 |
| 500 | 服务器错误 | 联系金蝶技术支持 |

### 错误处理示例

```python
result = publisher.search_apis(keyword="凭证")

if not result['success']:
    if "401" in result['message']:
        print("Token已过期，请重新配置凭证")
        publisher.setup_credentials(...)
    elif "429" in result['message']:
        print("请求过于频繁，请稍后再试")
        import time
        time.sleep(5)
    else:
        print(f"搜索失败: {result['message']}")
```

## 性能优化建议

### 1. 缓存API列表

```python
import json

# 第一次查询后缓存
all_apis = publisher.client.get_all_apis(page_size=100)
with open('api_cache.json', 'w') as f:
    json.dump(all_apis, f)

# 后续使用缓存
with open('api_cache.json', 'r') as f:
    all_apis = json.load(f)
```

### 2. 批量查询

```python
# 一次查询获取100条（而不是多次查询20条）
result = publisher.search_apis(keyword="", page_size=100)

# 自动获取所有API
all_apis = publisher.client.get_all_apis(page_size=100)
```

### 3. 模块级别的缓存

```python
# 为当前应用缓存API列表
import json

api_cache = publisher.search_apis(page_size=100)['apis']

# 保存缓存
with open('api_cache.json', 'w') as f:
    json.dump(api_cache, f, ensure_ascii=False, indent=2)
```

## 官方资源

- **接口路径**: `/kapi/v2/open/openapi_apilist/queryByApp`
- **开放平台**: https://dev.kingdee.com/
- **API列表**: https://dev.kingdee.com/open/list/api

## 总结

通过使用金蝶官方的 `queryByApp` 接口，我们能够：

✅ 直接查询当前应用下的API列表  
✅ 兼容关键词本地过滤  
✅ 获取完整的API元数据（名称、编码、URL等）  
✅ 自动处理分页和批量查询  
✅ 为自动生成Skill提供精准的API信息  

这样保证了Skill发布器始终与金蝶平台上的最新API保持同步。
