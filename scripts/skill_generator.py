"""
业务Skill自动生成器 - 基于金蝶API自动创建Skill
"""

import json
import os
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class SkillGenerator:
    """生成业务Skill的工具类"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化Skill生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or "/tmp/kingdee_skills"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_skill(self,
                      api_info: Dict[str, Any],
                      custom_name: str = None,
                      custom_description: str = None) -> str:
        """
        生成完整的Skill
        
        Args:
            api_info: API信息字典
            custom_name: 自定义Skill名称
            custom_description: 自定义Skill描述
            
        Returns:
            Skill目录路径
        """
        # 生成Skill标识
        api_code = api_info.get('api_code', 'unknown')
        api_name = api_info.get('api_name', 'API')
        
        skill_name = custom_name or self._generate_skill_name(api_code, api_name)
        skill_dir = os.path.join(self.output_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        
        # 创建目录结构
        os.makedirs(os.path.join(skill_dir, 'scripts'), exist_ok=True)
        os.makedirs(os.path.join(skill_dir, 'references'), exist_ok=True)
        
        # 生成文件
        self._generate_skill_md(skill_dir, skill_name, api_info, custom_description)
        self._generate_api_call_py(skill_dir, skill_name, api_info)
        self._generate_api_schema(skill_dir, api_info)
        self._generate_error_codes(skill_dir, api_info)
        self._generate_examples(skill_dir, api_info)
        self._generate_readme(skill_dir, skill_name, api_info)
        self._generate_init_files(skill_dir)
        
        # 最终验证：确保 SKILL.md 描述头完整
        self._final_validate_skill_md(skill_dir, skill_name, api_info)
        
        return skill_dir
    
    def _final_validate_skill_md(self, skill_dir: str, skill_name: str, api_info: Dict[str, Any]):
        """
        最终验证 SKILL.md 描述头，如果不完整则强制修复
        
        Args:
            skill_dir: Skill 目录路径
            skill_name: Skill 名称
            api_info: API 信息字典
        """
        skill_md_path = os.path.join(skill_dir, 'SKILL.md')
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查描述头
        needs_fix = False
        
        if not content.startswith('---'):
            needs_fix = True
            print(f"⚠️ 检测到 SKILL.md 缺少描述头开头标记 '---'")
        else:
            # 提取 frontmatter 部分
            parts = content.split('---', 2)
            if len(parts) < 3:
                needs_fix = True
                print(f"⚠️ 检测到 SKILL.md 描述头格式不完整")
            else:
                frontmatter = parts[1]
                if 'name:' not in frontmatter:
                    needs_fix = True
                    print(f"⚠️ 检测到 SKILL.md 描述头缺少 'name' 字段")
                if 'description:' not in frontmatter:
                    needs_fix = True
                    print(f"⚠️ 检测到 SKILL.md 描述头缺少 'description' 字段")
        
        if needs_fix:
            # 强制修复
            print(f"🔧 正在强制修复 SKILL.md 描述头...")
            fixed_content = self._validate_and_fix_frontmatter(content, skill_name, api_info)
            
            with open(skill_md_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"✅ SKILL.md 描述头已修复")
        else:
            print(f"✅ SKILL.md 描述头验证通过")
    
    def _generate_skill_name(self, api_code: str, api_name: str) -> str:
        """从API信息生成Skill名称"""
        # 转换为kebab-case
        name = api_name.lower().strip()
        name = re.sub(r'[\s\-_]+', '-', name)
        # 保留字母、数字、中文和连字符
        name = re.sub(r'[^a-z0-9\u4e00-\u9fa5-]', '', name)
        if len(name) > 40:
            name = name[:40]
        # 如果名称为空（如全是特殊字符），使用api_code
        return name or f"api-{api_code.lower().replace('_', '-')}"
    
    def _validate_and_fix_frontmatter(self, content: str, skill_name: str, 
                                       api_info: Dict[str, Any]) -> str:
        """
        验证并修复 SKILL.md 的描述头
        
        Args:
            content: 原始 SKILL.md 内容
            skill_name: Skill 名称
            api_info: API 信息字典
            
        Returns:
            修复后的内容（包含正确的描述头）
        """
        api_code = api_info.get('api_code', 'unknown')
        api_name = api_info.get('api_name', 'API')
        api_desc = api_info.get('api_description', '')
        method = api_info.get('method', 'POST')
        
        # 检查是否已有描述头
        has_frontmatter = content.startswith('---')
        has_name = 'name:' in content.split('---')[1] if has_frontmatter and len(content.split('---')) > 1 else False
        has_description = 'description:' in content.split('---')[1] if has_frontmatter and len(content.split('---')) > 1 else False
        
        if has_frontmatter and has_name and has_description:
            # 描述头完整，无需修复
            return content
        
        # 需要生成新的描述头
        frontmatter = f"""---
name: {skill_name}
description: |
  金蝶云苍穹API Skill - {api_name}。
  
  此Skill提供对金蝶云苍穹 {api_name} 接口的访问。
  
  触发场景：当用户想要通过自然语言查询{api_name}、查看相关数据时，使用此Skill。
  
  API详情：
  - 代码: {api_code}
  - 方法: {method}
  - 描述: {api_desc}
---

"""
        
        if has_frontmatter:
            # 有描述头但不完整，移除旧的并添加新的
            # 找到第一个 --- 之后的内容
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # 保留描述头后面的内容（跳过第一个 --- 和描述头内容）
                body_content = parts[2].lstrip()
                return frontmatter + body_content
        
        # 完全没有描述头，直接添加
        return frontmatter + content
    
    def _generate_skill_md(self, 
                           skill_dir: str,
                           skill_name: str,
                           api_info: Dict[str, Any],
                           custom_description: str = None):
        """生成SKILL.md文件（带描述头强制检查）"""
        
        api_code = api_info.get('api_code', '')
        api_name = api_info.get('api_name', '')
        description = custom_description or api_info.get('api_description', '')
        method = api_info.get('method', 'POST')
        
        skill_md = f"""---
name: {skill_name}
description: |
  金蝶云苍穹API Skill - {api_name}。
  
  此Skill提供对金蝶云苍穹 {api_name} 接口的访问。
  
  触发场景：当用户想要通过自然语言查询{api_name}、查看相关数据时，使用此Skill。
  
  API详情：
  - 代码: {api_code}
  - 方法: {method}
  - 描述: {description}
---

# {api_name}

基于金蝶云苍穹开放平台的 {api_code} API 创建的业务Skill。

---

## ⛔ 强制执行规则（最高优先级）

> **调用本 Skill 的 API 时，必须通过 `execute_command` 执行 Python 脚本，禁止 AI 直接构造 HTTP 请求或自行调用接口。**

### 必须遵守

1. **调用 API** → 必须通过 `execute_command` 执行 `scripts/api_call.py` 中的 `call_kingdee_api()` 函数
2. **所有参数** → 必须来自 `references/api_schema.json` 中定义的参数，禁止猜测
3. **凭证配置** → 必须通过环境变量传入，禁止硬编码

### 绝对禁止

- ❌ **禁止 AI 直接使用 requests/curl/fetch 等方式调用金蝶 API**
- ❌ **禁止 AI 猜测 API 的 URL、参数或返回值格式**
- ❌ **禁止跳过 Python 脚本直接构造 HTTP 请求**

### 正确的调用方式

```bash
cd /path/to/{skill_name} && python3 -c "
from scripts.api_call import call_kingdee_api
import json

result = call_kingdee_api(params={{
    # 根据 references/api_schema.json 填写参数
}})
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

---

## 功能说明

{description}

## 快速开始

### 环境要求

- Python 3.7+
- requests 库
- 金蝶云苍穹服务器访问权限

### 凭证配置

需要配置以下环境变量或参数：

```
KINGDEE_SERVER_URL    - 金蝶服务器URL（如：https://xxx.kingdee.com/ierp）
KINGDEE_APP_ID        - 应用ID
KINGDEE_APP_SECRET    - 应用密钥
KINGDEE_ACCOUNT_ID    - 账套ID
KINGDEE_USER          - 操作用户（可选，默认admin）
```

### 使用方式

```python
from scripts.api_call import call_kingdee_api

# 调用 {api_code} API
result = call_kingdee_api(
    api_code="{api_code}",
    params={{
        # 参数详见 references/api_schema.json
    }}
)

if result.get('success'):
    data = result.get('data')
    # 处理响应数据
else:
    error = result.get('error_msg')
    # 处理错误
```

## 请求参数

详见 `references/api_schema.json` 中的完整参数定义。

## 返回参数

API返回JSON格式数据，包含以下顶级字段：

- `success`: boolean - 调用是否成功
- `data`: object - 返回的业务数据
- `error_code`: string - 错误码（如果有）
- `error_msg`: string - 错误信息（如果有）

## 错误处理

错误码对照表详见 `references/error_codes.json`。

常见错误：
- `401` - Token已过期或无效（自动刷新）
- `400` - 参数无效
- `402` - 权限不足
- `602` - 数据未找到

## 使用示例

详见 `references/examples.json`

## 金蝶API规范

此Skill遵循金蝶云苍穹OpenAPI开发规范：

- **协议**: HTTPS
- **数据格式**: JSON
- **认证**: AccessToken认证（自动管理）
- **超时**: 最长50秒
- **频率限制**: 
  - 每租户账套：最多600次/分
  - 每应用客户端：最多30次/秒

## 幂等性

关键操作支持幂等性处理，通过 `Idempotency-Key` 请求头防止重复提交。

## 限制

- 单次查询数据量不超过10000条
- 单次保存数据量不超过2000条
- 单个请求最长响应时间不超过50秒

## 高级用法

### 批量数据处理

对于大数据量查询，自动分页处理：

```python
result = call_kingdee_api(
    api_code="{api_code}",
    params={{
        "pageNo": 1,
        "pageSize": 100
    }}
)
```

### Token管理

Token由Skill自动获取和缓存，有效期120分钟。过期后自动刷新。

### 错误重试

网络异常或超时会自动重试，最多3次。

## 常见问题

**Q: 如何处理大数据量查询？**
A: Skill自动支持分页，建议pageSize为100-500之间。

**Q: Token过期了怎么办？**
A: 无需手动处理，Skill自动检测并刷新Token。

**Q: 如何添加自定义参数验证？**
A: 修改 `scripts/api_call.py` 中的 `validate_params()` 函数。

**Q: 支持批量操作吗？**
A: 支持，通过分多次请求实现。

## 许可证

MIT

## 支持与反馈

如有问题，请参考金蝶云苍穹OpenAPI文档：
https://vip.kingdee.com/knowledge/
"""
        
        # 强制检查并修复描述头
        original_md = skill_md
        skill_md = self._validate_and_fix_frontmatter(skill_md, skill_name, api_info)
        
        # 如果修复了，记录日志
        if original_md != skill_md:
            print(f"⚠️ 警告: SKILL.md 描述头不完整，已自动修复")
        
        # 最终验证
        if not skill_md.startswith('---'):
            raise ValueError("SKILL.md 缺少必要的描述头（YAML frontmatter）")
        
        frontmatter_part = skill_md.split('---')[1] if len(skill_md.split('---')) > 1 else ''
        if 'name:' not in frontmatter_part or 'description:' not in frontmatter_part:
            raise ValueError("SKILL.md 描述头缺少 name 或 description 字段")
        
        with open(os.path.join(skill_dir, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write(skill_md)
        
        print(f"✅ SKILL.md 生成完成（已验证描述头）")
    
    def _generate_api_call_py(self,
                              skill_dir: str,
                              skill_name: str,
                              api_info: Dict[str, Any]):
        """生成API调用脚本"""
        
        api_code = api_info.get('api_code', 'unknown')
        method = api_info.get('method', 'POST')
        form_id = api_info.get('form_id')
        # ⚠️ 使用 API 详情返回的真实 URL（来自 getDetail 的 urlformat 字段）
        api_url = api_info.get('url') or api_info.get('urlformat')
        
        # 从详情字段获取参数（优先使用 getDetail 返回的详细参数）
        body_params = api_info.get('request_body_params', [])
        query_params = api_info.get('request_query_params', [])
        # 兼容旧的 request_params 字段
        legacy_params = api_info.get('request_params', [])
        all_params = body_params + query_params + legacy_params
        
        # 生成参数验证代码
        param_validations = []
        for param in all_params:
            param_name = param.get('name', '')
            param_required = param.get('required', False)
            if param_required and param_name:
                param_validations.append(
                    f'    if not params.get("{param_name}"):\n'
                    f'        raise ValueError("参数 {param_name} 为必填项")'
                )
        
        param_validation_code = '\n'.join(param_validations) if param_validations else '    pass'
        
        # 生成 api_url 行：优先使用真实 URL，否则回退到 form_id + api_code
        if api_url:
            api_url_line = f'API_URL = "{api_url}"  # 来自 API 详情的真实地址（urlformat）'
        else:
            api_url_line = f'API_URL = None  # 未获取到 API 详情地址，将使用 api_code 拼接'
        
        form_id_str = form_id if form_id else ''
        
        api_call_py = f'''"""
{api_code} API 调用模块

API地址: {api_url or '（未从详情获取，将由 api_code 拼接）'}
请求方式: {method}
"""

import os
import logging
from typing import Dict, Any, Optional
from .api_client import KingdeeAPIClient

logger = logging.getLogger(__name__)

# API 配置（来自服务器 getDetail 接口返回的真实信息）
API_CODE = "{api_code}"
API_METHOD = "{method}"
{api_url_line}
API_FORM_ID = "{form_id_str}" or None

def get_api_client() -> KingdeeAPIClient:
    """获取API客户端实例"""
    return KingdeeAPIClient(
        server_url=os.getenv('KINGDEE_SERVER_URL', 'https://xxx.kingdee.com/ierp'),
        app_id=os.getenv('KINGDEE_APP_ID'),
        app_secret=os.getenv('KINGDEE_APP_SECRET'),
        account_id=os.getenv('KINGDEE_ACCOUNT_ID'),
        user=os.getenv('KINGDEE_USER', 'admin')
    )

def validate_params(params: Dict[str, Any]) -> None:
    """
    验证请求参数

    Args:
        params: 请求参数字典

    Raises:
        ValueError: 参数验证失败
    """
{param_validation_code}

def call_kingdee_api(api_code: str = None,
                     method: str = None,
                     params: Dict[str, Any] = None,
                     **kwargs) -> Dict[str, Any]:
    """
    调用 {api_code} API

    Args:
        api_code: API编码（默认使用配置值）
        method: HTTP方法（默认使用配置值）
        params: 请求参数
        **kwargs: 其他参数

    Returns:
        API响应结果
    """
    if params is None:
        params = {{}}
    if api_code is None:
        api_code = API_CODE
    if method is None:
        method = API_METHOD

    try:
        # 参数验证
        validate_params(params)

        # 获取API客户端
        client = get_api_client()

        # 调用API — 优先使用从服务器获取的真实 URL
        result = client.call_api(
            api_code=api_code,
            method=method,
            params=params,
            form_id=API_FORM_ID,
            api_url=API_URL,
            **kwargs
        )

        # 处理响应
        if result.get('success'):
            logger.info(f"API调用成功: {{api_code}}")
            return {{
                'success': True,
                'data': result.get('data'),
                'message': '调用成功'
            }}
        else:
            error_code = result.get('error_code', 'UNKNOWN')
            error_msg = result.get('error_msg', '未知错误')
            logger.error(f"API调用失败 ({{error_code}}): {{error_msg}}")
            return {{
                'success': False,
                'error_code': error_code,
                'error_msg': error_msg
            }}

    except ValueError as e:
        logger.error(f"参数验证失败: {{e}}")
        return {{
            'success': False,
            'error_code': 'PARAM_ERROR',
            'error_msg': f'参数验证失败: {{str(e)}}'
        }}

    except Exception as e:
        logger.error(f"调用异常: {{e}}")
        return {{
            'success': False,
            'error_code': 'CALL_ERROR',
            'error_msg': f'调用异常: {{str(e)}}'
        }}

# 导出主函数
__all__ = ['call_kingdee_api', 'get_api_client', 'validate_params']
'''
        
        with open(os.path.join(skill_dir, 'scripts', 'api_call.py'), 'w', encoding='utf-8') as f:
            f.write(api_call_py)
    
    def _generate_api_schema(self, skill_dir: str, api_info: Dict[str, Any]):
        """生成API请求/返回schema"""
        
        schema = {
            "api_code": api_info.get('api_code'),
            "api_name": api_info.get('api_name'),
            "description": api_info.get('api_description'),
            "method": api_info.get('method', 'POST'),
            "url": api_info.get('url') or api_info.get('urlformat'),
            "form_id": api_info.get('form_id'),
            # 优先使用 getDetail 返回的详细参数
            "request_headers": api_info.get('request_headers', []),
            "request_query_params": api_info.get('request_query_params', []),
            "request_body_params": api_info.get('request_body_params', []),
            "response_params": api_info.get('response_params', []),
            # 兼容旧字段
            "request_parameters": api_info.get('request_params', []),
            "return_parameters": api_info.get('return_params', []),
            # 其他
            "orderby_rules": api_info.get('orderby_rules', []),
            "error_codes": api_info.get('error_codes', []),
            "version": api_info.get('version', 'v2'),
            "status": api_info.get('status', 'published')
        }
        
        with open(os.path.join(skill_dir, 'references', 'api_schema.json'), 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
    
    def _generate_error_codes(self, skill_dir: str, api_info: Dict[str, Any]):
        """生成错误码对照表"""
        
        # 标准错误码
        standard_errors = {
            "0": {"name": "OK", "description": "成功"},
            "400": {"name": "INVALID_PARAM", "description": "参数无效"},
            "401": {"name": "UNAUTHORIZED", "description": "未授权或Token无效"},
            "403": {"name": "FORBIDDEN", "description": "禁止访问"},
            "404": {"name": "NOT_FOUND", "description": "API不存在"},
            "429": {"name": "RATE_LIMITED", "description": "超出频率限制"},
            "500": {"name": "SERVER_ERROR", "description": "服务内部错误"},
            "601": {"name": "DUPLICATE", "description": "数据重复"},
            "602": {"name": "DATA_NOT_FOUND", "description": "数据未找到"},
            "701": {"name": "SCRIPT_ERROR", "description": "脚本执行错误"},
            "702": {"name": "PLUGIN_ERROR", "description": "插件执行异常"}
        }
        
        # 合并业务错误码
        error_codes = {**standard_errors}
        if api_info.get('error_codes'):
            error_codes.update(api_info.get('error_codes', {}))
        
        with open(os.path.join(skill_dir, 'references', 'error_codes.json'), 'w', encoding='utf-8') as f:
            json.dump(error_codes, f, ensure_ascii=False, indent=2)
    
    def _generate_examples(self, skill_dir: str, api_info: Dict[str, Any]):
        """生成使用示例"""
        
        api_code = api_info.get('api_code', 'unknown')
        
        examples = {
            "basic_usage": {
                "description": "基本调用示例",
                "code": f'''from scripts.api_call import call_kingdee_api

# 基本调用
result = call_kingdee_api(
    params={{
        # 在此添加API所需参数
    }}
)

if result.get('success'):
    print("成功:", result.get('data'))
else:
    print("失败:", result.get('error_msg'))
'''
            },
            "with_error_handling": {
                "description": "包含错误处理的示例",
                "code": f'''from scripts.api_call import call_kingdee_api
import json

try:
    result = call_kingdee_api(
        params={{
            # 参数
        }}
    )
    
    if result.get('success'):
        data = result.get('data')
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        error_code = result.get('error_code')
        error_msg = result.get('error_msg')
        print(f"错误 {{error_code}}: {{error_msg}}")
        
except Exception as e:
    print(f"调用异常: {{e}}")
'''
            }
        }
        
        with open(os.path.join(skill_dir, 'references', 'examples.json'), 'w', encoding='utf-8') as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)
    
    def _generate_readme(self, skill_dir: str, skill_name: str, api_info: Dict[str, Any]):
        """生成README说明文件"""
        
        api_code = api_info.get('api_code')
        api_name = api_info.get('api_name')
        
        readme = f"""# {skill_name}

基于金蝶云苍穹开放平台的业务Skill

## 功能简介

此Skill提供对金蝶云苍穹 **{api_code}** 接口的简化访问。

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置凭证

设置以下环境变量：

```bash
export KINGDEE_SERVER_URL="https://xxx.kingdee.com/ierp"
export KINGDEE_APP_ID="your_app_id"
export KINGDEE_APP_SECRET="your_app_secret"
export KINGDEE_ACCOUNT_ID="your_account_id"
```

或在代码中直接配置：

```python
import os
os.environ['KINGDEE_SERVER_URL'] = 'https://your-server.com:1026'
os.environ['KINGDEE_APP_ID'] = 'your_app_id'
os.environ['KINGDEE_APP_SECRET'] = 'your_app_secret'
os.environ['KINGDEE_ACCOUNT_ID'] = 'your_account_id'
```

### 3. 使用Skill

```python
from scripts.api_call import call_kingdee_api

result = call_kingdee_api(
    params={{
        # API所需的参数
    }}
)

if result['success']:
    print(result['data'])
else:
    print(f"错误: {{result['error_msg']}}")
```

## API参数详情

详见 `references/api_schema.json`

## 错误处理

详见 `references/error_codes.json`

## 常见问题

### Q: Token过期了怎么办？
A: Skill会自动检测并刷新Token，无需手动处理。

### Q: 如何调试API调用？
A: 检查日志输出，所有API调用都会记录详细日志。

### Q: 支持批量操作吗？
A: 支持，可以多次调用API实现批量操作。建议添加适当的延迟。

### Q: 如何处理大数据量？
A: 使用分页参数进行分页查询。

## 文件结构

```
{skill_name}/
├── SKILL.md               # Skill定义
├── scripts/
│   ├── __init__.py
│   ├── api_call.py       # API调用逻辑
│   └── api_client.py     # API客户端（基础）
├── references/
│   ├── api_schema.json   # API详细说明
│   ├── error_codes.json  # 错误码表
│   └── examples.json     # 使用示例
├── README.md             # 本文件
└── LICENSE.txt           # 许可证
```

## 进阶用法

### 自定义参数验证

编辑 `scripts/api_call.py` 中的 `validate_params()` 函数：

```python
def validate_params(params: Dict[str, Any]) -> None:
    # 添加自定义验证逻辑
    if params.get('amount') and params['amount'] < 0:
        raise ValueError("金额不能为负数")
```

### 使用自定义API客户端

```python
from scripts.api_client import KingdeeAPIClient

client = KingdeeAPIClient(
    server_url="https://your-server.com:1026",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id"
)

result = client.call_api(
    api_code="{api_code}",
    method="POST",
    params={{...}}
)
```

## 性能优化建议

1. **复用客户端**: 在应用生命周期内保持单一客户端实例
2. **缓存Token**: Token自动缓存，有效期120分钟
3. **批量请求**: 对于多个请求，考虑使用批量API（如有）
4. **分页查询**: 大数据量使用分页，避免单次请求过大

## 安全建议

1. **保护凭证**: 不要在代码中硬编码secret，使用环境变量
2. **HTTPS**: 所有API调用自动使用HTTPS
3. **幂等性**: 关键操作支持幂等性，自动防止重复提交
4. **权限控制**: 使用最小权限原则配置应用权限

## 更新日志

### v1.0.0 (2024)
- 初始版本

## 支持

如有问题，请参考：
- 金蝶云苍穹OpenAPI文档: https://vip.kingdee.com/knowledge/
- Skill文档: SKILL.md

## 许可证

MIT

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(os.path.join(skill_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)
    
    def _generate_init_files(self, skill_dir: str):
        """生成初始化文件"""
        
        # scripts/__init__.py
        init_py = '''"""
金蝶API调用模块
"""

from .api_call import call_kingdee_api, get_api_client, validate_params
from .api_client import KingdeeAPIClient

__all__ = ['call_kingdee_api', 'get_api_client', 'validate_params', 'KingdeeAPIClient']
'''
        
        with open(os.path.join(skill_dir, 'scripts', '__init__.py'), 'w', encoding='utf-8') as f:
            f.write(init_py)
        
        # 复制 api_client.py（生成的 Skill 必须包含此文件才能调用 API）
        src_api_client = os.path.join(os.path.dirname(__file__), 'api_client.py')
        dst_api_client = os.path.join(skill_dir, 'scripts', 'api_client.py')
        if os.path.exists(src_api_client):
            shutil.copy2(src_api_client, dst_api_client)
            print(f"✅ api_client.py 已复制到生成的 Skill 目录")
        else:
            print(f"⚠️ 警告: 未找到 api_client.py ({src_api_client})，生成的 Skill 可能无法调用 API")
        
        # LICENSE.txt
        license_txt = '''MIT License

Copyright (c) 2024 Kingdee Skill Publisher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
        
        with open(os.path.join(skill_dir, 'LICENSE.txt'), 'w', encoding='utf-8') as f:
            f.write(license_txt)
