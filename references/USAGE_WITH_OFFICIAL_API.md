# 使用官方queryByApp接口的完整使用指南

## 📝 简介

本指南展示如何使用金蝶业务Skill发布器的更新方案，该方案现在直接使用金蝶官方的按应用编码查询API列表接口。

## 🎯 核心改进

### 旧方案 vs 新方案对比

| 方面 | 旧方案 | 新方案 |
|------|--------|---------|
| **数据来源** | 本地缓存/框架实现 | 金蝶官方queryByApp接口 |
| **实时性** | 需要手动更新 | 实时同步 |
| **准确性** | 可能过时 | 始终最新 |
| **参数信息** | 简化版 | 完整版（包含所有参数定义） |
| **搜索功能** | 基础关键词搜索 | 支持关键词+模块搜索 |
| **分页支持** | 否 | 是（完整分页支持） |

## 🚀 快速开始

### 基本使用示例

```python
from scripts import KingdeeSkillPublisher

# 1. 创建发布器实例
publisher = KingdeeSkillPublisher()

# 2. 配置金蝶凭证
publisher.setup_credentials(
    server_url="https://xxx.kingdee.com/ierp",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id"
)

# 3. 搜索API（使用官方queryByApp接口）
result = publisher.search_apis(appid_number="basedata", keyword="凭证")

# 4. 检查结果
if result['success']:
    print(f"找到 {result['total']} 个API")
    
    # 显示找到的API
    for api in result['apis']:
        print(f"  {api['apiCode']}: {api['apiName']}")
        print(f"    - 请求方式: {api['method']}")
        print(f"    - 模块: {api['module']}")
        print(f"    - 描述: {api['apiDescription']}")
else:
    print(f"搜索失败: {result['message']}")

# 5. 创建Skill
if result['apis']:
    selected_api = result['apis'][0]
    skill_result = publisher.create_skill_from_api(selected_api)
    
    if skill_result['success']:
        print(f"✓ Skill创建成功: {skill_result['skill_path']}")
```

## 📚 详细用法

### 1. 按关键词搜索API

```python
# 搜索凭证相关API
result = publisher.search_apis(keyword="凭证")

# 搜索列表类API
result = publisher.search_apis(keyword="getList")

# 搜索详情查询API
result = publisher.search_apis(keyword="getDetail")

# 搜索保存类API
result = publisher.search_apis(keyword="save")
```

### 2. 按关键词过滤API

```python
order_apis = publisher.search_apis(appid_number="basedata", keyword="订单")
detail_apis = publisher.search_apis(appid_number="basedata", keyword="详情")
```

### 3. 组合过滤（关键词+最佳努力模块过滤）

```python
result = publisher.search_apis(
    appid_number="basedata",
    keyword="订单",
    module="pm"
)
```

### 4. 处理搜索结果

```python
result = publisher.search_apis(keyword="凭证")

if result['success']:
    # 总结果数
    print(f"找到 {result['total']} 个API")
    
    # 遍历API列表
    for i, api in enumerate(result['apis'], 1):
        print(f"\n{i}. {api['apiName']}")
        print(f"   编码: {api['apiCode']}")
        print(f"   方法: {api['method']}")
        print(f"   模块: {api['module']}")
        print(f"   版本: {api.get('version', 'v2')}")
        print(f"   描述: {api['apiDescription']}")
        
        # 显示请求参数
        if api.get('requestParams'):
            print(f"   请求参数:")
            for param in api['requestParams']:
                required = "必填" if param.get('required') else "可选"
                print(f"     - {param['name']} ({param.get('type', 'String')}) {required}")
        
        # 显示返回参数
        if api.get('returnParams'):
            print(f"   返回参数:")
            for param in api['returnParams'][:3]:  # 只显示前3个
                print(f"     - {param['name']} ({param.get('type', 'String')})")
```

### 5. 使用API客户端直接查询

```python
# 获取API客户端
client = publisher.client

# 直接调用get_api_list（获取更详细的分页信息）
result = client.get_api_list(
    appid_number="basedata",
    search_keyword="凭证",
    page_no=10,
    page_size=20
)

print(f"当前页: {result['pageNo']}")
print(f"总数: {result['total']}")
print(f"API数: {len(result['apis'])}")

# 获取下一页
result2 = client.get_api_list(
    appid_number="basedata",
    search_keyword="凭证",
    page_no=11,
    page_size=20
)
```

### 6. 自动获取所有API

```python
# 自动处理分页，获取所有API
all_apis = publisher.client.get_all_apis(page_size=100)

print(f"当前应用共有 {len(all_apis)} 个API")

# 按功能分类
query_apis = [api for api in all_apis if "get" in api['apiCode'].lower()]
save_apis = [api for api in all_apis if "save" in api['apiCode'].lower()]
delete_apis = [api for api in all_apis if "delete" in api['apiCode'].lower()]

print(f"查询类: {len(query_apis)}")
print(f"保存类: {len(save_apis)}")
print(f"删除类: {len(delete_apis)}")
```

## 💡 实际应用场景

### 场景1：批量为一个模块创建Skill

```python
# 为当前应用下的查询类API创建Skill

publisher.setup_credentials(...)

# 获取当前应用的所有API
ar_apis = publisher.search_apis(page_size=100)

# 为每个查询类API创建Skill
created_skills = []
for api in ar_apis['apis']:
    if "getDetail" in api['apiCode']:  # 只创建详情查询API
        skill_result = publisher.create_skill_from_api(
            api_info=api,
            skill_name=f"ar-{api['apiCode'].lower()}"
        )
        if skill_result['success']:
            created_skills.append(skill_result)
            print(f"✓ 创建Skill: {api['apiName']}")

print(f"\n共创建了 {len(created_skills)} 个Skill")
```

### 场景2：探索系统中的所有API

```python
# 发现系统中有哪些API可用

publisher.setup_credentials(...)

# 获取所有API并按模块分组
from collections import defaultdict

all_apis = publisher.client.get_all_apis(page_size=100)
apis_by_module = defaultdict(list)

for api in all_apis:
    module = api.get('module', 'unknown')
    apis_by_module[module].append(api)

# 显示模块统计
print("金蝶云苍穹 API 统计\n")
print("模块\tAPI数\t首个API")
print("-" * 40)

for module in sorted(apis_by_module.keys()):
    apis = apis_by_module[module]
    first_api = apis[0]['apiName'] if apis else '-'
    print(f"{module}\t{len(apis)}\t{first_api}")

total = sum(len(apis) for apis in apis_by_module.values())
print(f"\n总计: {total} 个API")
```

### 场景3：为特定功能创建Skill

```python
# 场景：创建一个"财务报表查询"Skill

publisher.setup_credentials(...)

# 搜索报表相关API
result = publisher.search_apis(keyword="报表", page_size=50)

print(f"找到 {result['total']} 个报表相关API:")
for api in result['apis']:
    print(f"  - {api['apiCode']}: {api['apiName']}")

# 用户选择特定的API
selected_api = result['apis'][0]

# 创建Skill
skill_result = publisher.create_skill_from_api(
    api_info=selected_api,
    skill_name="report-query",
    skill_description="财务报表查询工具"
)

if skill_result['success']:
    print(f"\n✓ Skill创建成功!")
    print(f"路径: {skill_result['skill_path']}")
    print(f"名称: {skill_result['skill_name']}")
```

## 🔧 高级用法

### 自定义页面大小和分页

```python
# 获取第一页（每页100条）
result1 = publisher.client.get_api_list(
    page_no=1,
    page_size=100
)

# 获取第二页
result2 = publisher.client.get_api_list(
    page_no=2,
    page_size=100
)

# 合并结果
all_apis = result1['apis'] + result2['apis']
```

### 缓存API列表以提高性能

```python
import json
import os

cache_file = 'api_cache.json'

# 检查缓存
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        apis_cache = json.load(f)
    print("使用缓存的API列表")
else:
    # 从服务器获取
    publisher.setup_credentials(...)
    all_apis = publisher.client.get_all_apis(page_size=100)
    
    # 保存缓存
    with open(cache_file, 'w') as f:
        json.dump(all_apis, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(all_apis)} 个API的缓存")
```

### 监听API更新

```python
import json
import hashlib
from datetime import datetime

def get_api_list_hash(apis):
    """计算API列表的哈希值"""
    data = json.dumps(apis, sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()

# 获取最新API列表
publisher.setup_credentials(...)
all_apis = publisher.client.get_all_apis()

new_hash = get_api_list_hash(all_apis)

# 读取上次的哈希值
cache_file = 'api_cache.json'
old_hash = None

if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cached_apis = json.load(f)
    old_hash = get_api_list_hash(cached_apis)

# 检查是否有更新
if new_hash != old_hash:
    print(f"✓ API列表已更新！发现 {len(all_apis)} 个API")
    # 保存新缓存
    with open(cache_file, 'w') as f:
        json.dump(all_apis, f, ensure_ascii=False, indent=2)
else:
    print("API列表未变化")
```

## 🎯 API查询接口细节

### 官方接口信息

- **接口名称**: queryByApp
- **请求URL**: `GET /kapi/v2/open/openapi_apilist/queryByApp`
- **请求方法**: GET
- **官方文档**: https://dev.kingdee.com/open/detail/api/1758916618966010880

### 请求参数

```json
{
  "appid_number": "your_app_id",
  "pageNo": 1,
  "pageSize": 20
}
```

### 响应参数

```json
{
  "status": true,
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "totalCount": 1,
    "rows": [
      {
        "number": "pm_queryOrder",
        "name": {"zh_CN": "采购订单查询"},
        "discription": {"zh_CN": "查询采购订单"},
        "urlformat": "/kapi/v2/kingdee/your_app_id/order/query"
      }
    ]
  }
}
```

## 📖 相关文档

- **详细指南**: 参考 `references/API_QUERY_GUIDE.md`
- **完整SKILL说明**: 参考 `SKILL.md`
- **项目README**: 参考 `README.md`

## ✅ 总结

新方案的主要优势：

✅ **实时同步** - 直接从金蝶官方接口获取，始终最新  
✅ **完整信息** - 获取完整的API元数据（参数、返回值等）  
✅ **兼容过滤** - 支持关键词过滤和最佳努力模块过滤  
✅ **自动分页** - 自动处理分页，支持获取所有API  
✅ **生产级质量** - 使用官方接口，确保可靠性  

现在你可以立即开始使用，快速为任何金蝶API创建Skill！
