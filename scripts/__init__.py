"""
金蝶业务Skill发布器工具
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from scripts.api_client import KingdeeAPIClient
from scripts.skill_generator import SkillGenerator

logger = logging.getLogger(__name__)

class KingdeeSkillPublisher:
    """金蝶业务Skill发布器主类"""
    
    def __init__(self):
        self.client: Optional[KingdeeAPIClient] = None
        self.generator: Optional[SkillGenerator] = None
        self.config: Dict[str, Any] = {}
    
    def setup_credentials(self,
                         server_url: str,
                         account_id: str,
                         app_id: str = None,
                         app_secret: str = None,
                         user: str = None,
                         auth_type: str = None,
                         client_id: str = None,
                         client_secret: str = None,
                         username: str = None,
                         language: str = "zh_CN") -> Dict[str, Any]:
        """
        配置和验证金蝶API凭证

        支持两种认证方式：

        经典认证（auth_type="login_do"，默认）：
            所需参数：server_url, app_id, app_secret, account_id, user

        增强型Token认证（auth_type="oauth2"）：
            所需参数：server_url, account_id, client_id, client_secret, username

        Args:
            server_url: 金蝶服务器URL
            account_id: 账套ID（两种认证均必填）
            app_id: 应用ID（经典认证必填）
            app_secret: 应用密钥（经典认证必填）
            user: 操作用户（经典认证可选，默认admin）
            auth_type: 认证方式，"login_do"（默认）或 "oauth2"
            client_id: OAuth2认证的client_id（增强型认证必填）
            client_secret: OAuth2认证的AccessToken密钥（增强型认证必填）
            username: OAuth2认证的用户名/手机号（增强型认证必填）
            language: OAuth2认证的语言，默认 "zh_CN"

        Returns:
            验证结果
        """
        try:
            # 创建客户端
            self.client = KingdeeAPIClient(
                server_url=server_url,
                app_id=app_id,
                app_secret=app_secret,
                account_id=account_id,
                user=user,
                auth_type=auth_type,
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                language=language,
            )
            
            # 验证凭证
            validation = self.client.validate_credentials()
            
            if validation['connection'] and validation['authentication']:
                self.config = {
                    'server_url': server_url,
                    'app_id': app_id,
                    'account_id': account_id,
                    'user': user or 'admin'
                }
                return {
                    'success': True,
                    'message': '凭证验证成功',
                    'details': validation
                }
            else:
                return {
                    'success': False,
                    'message': '凭证验证失败',
                    'details': validation
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'配置失败: {str(e)}',
                'details': None
            }
    
    def search_apis(self,
                    appid_number: str,
                    keyword: str = None,
                    module: str = None,
                    page_no: int = 1,
                    page_size: int = 10) -> Dict[str, Any]:
        """
        搜索可用的API
        
        Args:
            appid_number: 应用编码（必填）
            keyword: 搜索关键词（API名称、编码等）
            module: API模块（ar、ap、pm等）
            page_no: 页码，默认1
            page_size: 每页数量，默认10
            
        Returns:
            搜索结果，包含API列表和分页信息
            {
                "success": True,
                "total": 50,
                "apis": [...],
                "message": "找到50个API"
            }
        """
        if not self.client:
            return {
                'success': False,
                'message': '请先配置凭证',
                'apis': []
            }

        if not appid_number:
            return {
                'success': False,
                'message': 'appid_number 为必填参数',
                'apis': []
            }
        
        try:
            result = self.client.get_api_list(
                appid_number=appid_number,
                search_keyword=keyword,
                module=module,
                page_no=page_no,
                page_size=page_size
            )
            
            # 格式化返回结果
            return {
                'success': result.get('success', False),
                'total': result.get('total', 0),
                'apis': result.get('apis', []),
                'message': result.get('message', '查询成功')
            }
        except Exception as e:
            logger.error(f"搜索API失败: {e}")
            return {
                'success': False,
                'message': f'搜索失败: {str(e)}',
                'apis': []
            }
    
    def get_api_detail(self, api_id: str, page_no: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        根据API主键ID获取API详情
        
        调用金蝶官方接口：GET /v2/open/openapi_apilist/getDetail
        获取API的完整定义，包括请求头、请求参数、返回参数、错误码等详细信息
        
        ⚠️ 重要提示: 此查询接口必须传递分页参数 pageSize 和 pageNo，即使只查询单条记录。
        
        Args:
            api_id: API的主键ID（从search_apis返回的api中取得的id字段）
            page_no: 查询页码，默认为1
            page_size: 分页大小，默认为10
            
        Returns:
            {
                "success": True/False,
                "message": "提示信息",
                "api_detail": {
                    "id": "API主键",
                    "api_code": "API编码",
                    "api_name": "API名称",
                    "api_description": "API描述",
                    "method": "GET/POST",
                    "url": "请求地址",
                    "request_headers": ["请求头参数列表"],
                    "request_query_params": ["URL查询参数列表"],
                    "request_body_params": ["Body参数列表"],
                    "response_params": ["返回参数列表"],
                    "error_codes": ["错误码列表"],
                    "orderby_rules": ["排序规则"],
                    "save_params": ["操作参数"]
                }
            }
        """
        if not self.client:
            return {
                'success': False,
                'message': '请先配置凭证',
                'api_detail': None
            }
        
        if not api_id:
            return {
                'success': False,
                'message': 'api_id 为必填参数',
                'api_detail': None
            }
        
        return self.client.get_api_detail(api_id, page_no, page_size)
    
    def create_skill_from_api(self,
                             api_info: Dict[str, Any],
                             skill_name: str = None,
                             skill_description: str = None,
                             use_detail: bool = False) -> Dict[str, Any]:
        """
        基于API信息创建Skill
        
        Args:
            api_info: API信息字典（从search_apis返回或包含id的API信息）
            skill_name: 自定义Skill名称
            skill_description: 自定义Skill描述
            use_detail: 是否先调用getDetail接口获取完整API详情后再创建Skill
            
        Returns:
            Skill创建结果
        """
        if not self.generator:
            self.generator = SkillGenerator()
        
        try:
            # 如果需要获取完整API详情
            if use_detail and 'id' in api_info:
                detail_result = self.get_api_detail(api_info['id'])
                if detail_result['success'] and detail_result['api_detail']:
                    # 合并API详情到api_info
                    api_info = {**api_info, **detail_result['api_detail']}
                else:
                    logger.warning(f"获取API详情失败，将使用列表中的基本信息: {detail_result['message']}")
            
            skill_dir = self.generator.generate_skill(
                api_info=api_info,
                custom_name=skill_name,
                custom_description=skill_description
            )
            
            return {
                'success': True,
                'message': 'Skill创建成功',
                'skill_path': skill_dir,
                'skill_name': os.path.basename(skill_dir)
            }
        
        except Exception as e:
            logger.error(f"创建Skill失败: {e}")
            return {
                'success': False,
                'message': f'Skill创建失败: {str(e)}'
            }
    
    def create_skill_from_api_id(self,
                                api_id: str,
                                skill_name: str = None,
                                skill_description: str = None) -> Dict[str, Any]:
        """
        根据API主键ID获取详情并创建Skill
        
        这是便捷的批量操作：先调用getDetail获取API详情，然后直接封装成Skill
        
        Args:
            api_id: API的主键ID
            skill_name: 自定义Skill名称（可选，默认使用API编码）
            skill_description: 自定义Skill描述（可选）
            
        Returns:
            Skill创建结果
        """
        # 第一步：获取API详情
        detail_result = self.get_api_detail(api_id)
        
        if not detail_result['success']:
            return {
                'success': False,
                'message': f'获取API详情失败: {detail_result["message"]}',
                'skill_path': None
            }
        
        api_detail = detail_result['api_detail']
        if not api_detail:
            return {
                'success': False,
                'message': 'API详情为空',
                'skill_path': None
            }
        
        # 第二步：使用API详情创建Skill
        return self.create_skill_from_api(
            api_info=api_detail,
            skill_name=skill_name or api_detail.get('api_code'),
            skill_description=skill_description or api_detail.get('api_description')
        )
    
    def publish_skill(self, skill_dir: str) -> Dict[str, Any]:
        """
        发布Skill
        
        Args:
            skill_dir: Skill目录路径
            
        Returns:
            发布结果
        """
        try:
            # 检查Skill目录完整性
            required_files = ['SKILL.md', 'README.md', 'scripts/api_call.py']
            for file_path in required_files:
                full_path = os.path.join(skill_dir, file_path)
                if not os.path.exists(full_path):
                    return {
                        'success': False,
                        'message': f'缺少必要文件: {file_path}'
                    }
            
            # 这里可以添加真实的发布逻辑
            # 例如：上传到Skill库、生成安装包等
            
            return {
                'success': True,
                'message': 'Skill已准备就绪',
                'skill_path': skill_dir,
                'next_steps': [
                    '1. 检查SKILL.md中的Skill定义',
                    '2. 在README.md中调整使用说明',
                    '3. 在scripts/api_call.py中添加参数验证',
                    '4. 测试API调用逻辑',
                    '5. 安装到Claude中使用'
                ]
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'发布失败: {str(e)}'
            }
    
    def get_setup_guide(self) -> str:
        """获取初始化配置指南"""
        return """
=== 金蝶业务Skill发布器 初始化指南 ===

第一步：收集金蝶服务器信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需要从金蝶云苍穹开放平台获取以下信息：

1. 服务器URL
   - 公有云用户：https://xxx.kingdee.com/ierp
   - 私有云用户：请联系管理员获取

2. 应用凭证
   - appId: 第三方应用的唯一标识
   - appSecret: 应用的私钥（需妥善保管）
   - 获取地址：开放平台 → 第三方应用 → 应用详情

3. 账套信息
   - accountId: 租户账套ID
   - user: 操作用户（可选，默认为admin）

第二步：配置凭证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方式1：环境变量（推荐）

export KINGDEE_SERVER_URL="https://xxx.kingdee.com/ierp"
export KINGDEE_APP_ID="your_app_id"
export KINGDEE_APP_SECRET="your_app_secret"
export KINGDEE_ACCOUNT_ID="your_account_id"

方式2：Python代码

from kingdee_skill_publisher import KingdeeSkillPublisher

publisher = KingdeeSkillPublisher()
result = publisher.setup_credentials(
    server_url="https://xxx.kingdee.com/ierp",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id"
)

第三步：测试连接
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

确保凭证配置正确后，系统将自动验证：
- 服务器连通性
- API认证有效性
- 账套权限

第四步：开始使用
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 搜索API
   publisher.search_apis(keyword="凭证")

2. 选择API创建Skill
   publisher.create_skill_from_api(api_info)

3. 发布Skill
   publisher.publish_skill(skill_dir)

更多信息请参考SKILL.md文档。
"""


if __name__ == '__main__':
    publisher = KingdeeSkillPublisher()
    print(publisher.get_setup_guide())
