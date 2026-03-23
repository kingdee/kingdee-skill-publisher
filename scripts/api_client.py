"""
金蝶云苍穹API客户端 - 处理Token管理和API请求
"""

import json
import time
import uuid
import hashlib
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def _parse_json_response(response: requests.Response) -> Any:
    """
    安全解析 JSON 响应，强制使用 UTF-8 编码以避免中文乱码。

    requests 库在 Content-Type 未显式指定 charset 时，会回退到
    ISO-8859-1，导致中文变为乱码。此函数直接对原始字节做 UTF-8
    解码后再解析 JSON。
    """
    return json.loads(response.content.decode("utf-8"))

class KingdeeAPIClient:
    """金蝶云苍穹OpenAPI客户端"""
    
    # 认证方式常量
    AUTH_LOGIN_DO = "login_do"   # 经典认证: POST /api/login.do
    AUTH_OAUTH2 = "oauth2"       # 增强型Token认证: POST /kapi/oauth2/getToken

    def __init__(self,
                 server_url: str,
                 app_id: str = None,
                 app_secret: str = None,
                 account_id: str = None,
                 user: str = None,
                 auth_type: str = None,
                 client_id: str = None,
                 client_secret: str = None,
                 username: str = None,
                 language: str = "zh_CN"):
        """
        初始化API客户端

        Args:
            server_url: 服务器URL（例：https://xxx.kingdee.com/ierp）
            app_id: 应用ID（经典认证必填）
            app_secret: 应用密钥（经典认证必填）
            account_id: 账套ID（两种认证均必填）
            user: 操作用户（经典认证使用，可选）
            auth_type: 认证方式，"login_do"（默认）或 "oauth2"
            client_id: OAuth2认证的client_id（增强型认证必填）
            client_secret: OAuth2认证的AccessToken密钥（增强型认证必填）
            username: OAuth2认证的用户名/手机号（增强型认证必填）
            language: OAuth2认证的语言，默认 "zh_CN"
        """
        self.server_url = server_url.rstrip('/')
        self.app_id = app_id
        self.app_secret = app_secret
        self.account_id = account_id
        self.user = user or "admin"

        # 增强型Token认证参数
        self.auth_type = auth_type or self.AUTH_LOGIN_DO
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username or user or "admin"
        self.language = language
        
        self.token = None
        self.token_expire_time = None
        self.token_cache_file = None
        
        # Token有效期通常为120分钟
        self.token_validity = 120 * 60  # 秒
        
    def _verify_connection(self) -> bool:
        """验证服务器连接"""
        try:
            response = requests.head(
                f"{self.server_url}/kapi",
                verify=True,
                timeout=10
            )
            return response.status_code in [200, 404, 401]
        except Exception as e:
            logger.error(f"连接验证失败: {e}")
            return False
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        获取API Token
        
        Args:
            force_refresh: 是否强制刷新Token
            
        Returns:
            有效的API Token
        """
        # 检查缓存的Token是否仍有效
        if self.token and self.token_expire_time and not force_refresh:
            if datetime.now() < self.token_expire_time:
                logger.info("使用缓存的Token")
                return self.token
        
        # 获取新Token
        token_data = self._fetch_token()
        if token_data:
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', self.token_validity)
            self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 60)
            logger.info(f"成功获取新Token，有效期至 {self.token_expire_time}")
            return self.token
        
        raise Exception("无法获取API Token")
    
    def _fetch_token(self) -> Optional[Dict]:
        """根据认证方式从服务器获取新Token"""
        if self.auth_type == self.AUTH_OAUTH2:
            return self._fetch_token_oauth2()
        return self._fetch_token_login_do()

    def _fetch_token_login_do(self) -> Optional[Dict]:
        """经典认证：POST /api/login.do"""
        try:
            token_url = f"{self.server_url}/api/login.do"
            payload = {
                "user": self.user,
                "appId": self.app_id,
                "appSecret": self.app_secret,
                "accountId": self.account_id,
            }

            response = requests.post(
                token_url,
                json=payload,
                verify=True,
                timeout=30
            )

            if response.status_code == 200:
                result = _parse_json_response(response)
                data = result.get("data", {}) if isinstance(result, dict) else {}
                access_token = data.get("access_token") if isinstance(data, dict) else None

                if access_token:
                    token_data = {"access_token": access_token}

                    # 兼容服务端返回绝对过期时间戳（毫秒）
                    expire_time = data.get("expire_time")
                    if expire_time:
                        try:
                            expires_in = int(int(expire_time) / 1000 - time.time())
                            if expires_in > 0:
                                token_data["expires_in"] = expires_in
                        except (ValueError, TypeError):
                            pass

                    return token_data

                logger.error(f"Token响应缺少 data.access_token: {result}")
                return None
            else:
                logger.error(f"Token获取失败 (HTTP {response.status_code}): {response.text}")
                return None

        except Exception as e:
            logger.error(f"Token获取异常: {e}")
            return None

    def _fetch_token_oauth2(self) -> Optional[Dict]:
        """增强型Token认证：POST /kapi/oauth2/getToken"""
        try:
            token_url = f"{self.server_url}/kapi/oauth2/getToken"
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "accountId": self.account_id,
                "nonce": str(uuid.uuid4()),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "language": self.language,
            }

            response = requests.post(
                token_url,
                json=payload,
                verify=True,
                timeout=30
            )

            if response.status_code == 200:
                result = _parse_json_response(response)
                data = result.get("data", {}) if isinstance(result, dict) else {}
                access_token = data.get("access_token") if isinstance(data, dict) else None

                if access_token:
                    token_data = {"access_token": access_token}

                    # 兼容服务端返回绝对过期时间戳（毫秒）
                    expire_time = data.get("expire_time")
                    if expire_time:
                        try:
                            expires_in = int(int(expire_time) / 1000 - time.time())
                            if expires_in > 0:
                                token_data["expires_in"] = expires_in
                        except (ValueError, TypeError):
                            pass

                    return token_data

                logger.error(f"OAuth2 Token响应缺少 data.access_token: {result}")
                return None
            else:
                logger.error(f"OAuth2 Token获取失败 (HTTP {response.status_code}): {response.text}")
                return None

        except Exception as e:
            logger.error(f"OAuth2 Token获取异常: {e}")
            return None

    def _extract_multilang_text(self, value: Any) -> str:
        """提取多语言文本中的中文或可显示值"""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("zh_CN") or value.get("name") or next(
                (v for v in value.values() if isinstance(v, str)),
                "",
            )
        return ""

    def _normalize_api_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """将 queryByApp 返回的记录转换为 Skill 内部统一字段"""
        method_map = {
            "0": "GET",
            "1": "POST",
        }
        api_code = record.get("number", "")
        api_name = self._extract_multilang_text(record.get("name"))
        api_description = self._extract_multilang_text(record.get("discription"))
        method_code = str(record.get("httpmethod", "0"))
        method = method_map.get(method_code, method_code)

        normalized = dict(record)
        normalized.update({
            "api_code": api_code,
            "api_name": api_name,
            "api_description": api_description,
            "apiCode": api_code,
            "apiName": api_name,
            "apiDescription": api_description,
            "method": method,
            "form_id": record.get("bizobject_number"),
            "request_params": record.get("requestParams", []),
            "return_params": record.get("returnParams", []),
            "error_codes": record.get("errorCodes", {}),
        })
        return normalized

    def _filter_api_records(self,
                            apis: List[Dict[str, Any]],
                            search_keyword: str = None,
                            module: str = None) -> List[Dict[str, Any]]:
        """对 queryByApp 结果做本地过滤，兼容现有 search_apis 接口"""
        # 首先过滤：仅保留 enable=1 且 status='C' 的API
        filtered = [
            api for api in apis
            if api.get('enable') == '1' and api.get('status') == 'C'
        ]

        if search_keyword:
            keyword = search_keyword.lower()
            filtered = [
                api for api in filtered
                if keyword in api.get("api_code", "").lower()
                or keyword in api.get("api_name", "").lower()
                or keyword in api.get("api_description", "").lower()
            ]

        if module:
            module_key = module.lower()
            filtered = [
                api for api in filtered
                if module_key in str(api.get("bizobject_number", "")).lower()
                or module_key in str(api.get("urlformat", "")).lower()
                or module_key in api.get("api_code", "").lower()
            ]

        return filtered
    
    def call_api(self,
                 api_code: str,
                 method: str = "POST",
                 params: Dict[str, Any] = None,
                 form_id: str = None,
                 isv: str = "kingdee",
                 retry_count: int = 3,
                 api_url: str = None) -> Dict[str, Any]:
        """
        调用金蝶API
        
        Args:
            api_code: API编码
            method: 请求方法 (GET/POST)
            params: 请求参数
            form_id: 表单ID（如果有）
            isv: ISV标识
            retry_count: 重试次数
            api_url: 完整的API请求地址（优先使用，来自getDetail的urlformat字段）
                     如果提供则直接使用，不再拼接URL
            
        Returns:
            API响应结果
        """
        if params is None:
            params = {}
        
        # 自动获取Token
        try:
            token = self.get_token()
        except Exception as e:
            return {
                "success": False,
                "error_code": "AUTH_ERROR",
                "error_msg": f"认证失败: {str(e)}"
            }
        
        # 构造请求URL
        # 优先使用传入的完整URL（来自API详情的urlformat字段）
        if api_url:
            # api_url 可能是相对路径（如 /v2/basedata/bd_customer/query）
            # 也可能是完整路径，需要拼接 server_url + /kapi 前缀
            if api_url.startswith('http'):
                pass  # 已经是完整URL
            elif api_url.startswith('/kapi/'):
                api_url = f"{self.server_url}{api_url}"
            else:
                api_url = f"{self.server_url}/kapi{api_url}"
        elif form_id:
            api_url = f"{self.server_url}/kapi/v2/{isv}/{self.app_id}/{form_id}/{api_code}"
        else:
            api_url = f"{self.server_url}/kapi/v2/{isv}/{self.app_id}/{api_code}"
        
        # 添加通用参数
        request_params = {
            "accountId": self.account_id,
            "user": self.user,
            **params
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 重试机制
        for attempt in range(retry_count):
            try:
                if method.upper() == "GET":
                    response = requests.get(
                        api_url,
                        params=request_params,
                        headers=headers,
                        verify=True,
                        timeout=50
                    )
                else:  # POST
                    response = requests.post(
                        api_url,
                        json=request_params,
                        headers=headers,
                        verify=True,
                        timeout=50
                    )
                
                # 处理响应
                if response.status_code == 200:
                    result = _parse_json_response(response)
                    
                    # 检查Token是否过期
                    if result.get('error_code') == 401:
                        logger.warning("Token已过期，重新获取...")
                        token = self.get_token(force_refresh=True)
                        continue
                    
                    return result
                
                elif response.status_code == 401:
                    # Token过期，重新获取
                    logger.warning("收到401响应，重新获取Token...")
                    token = self.get_token(force_refresh=True)
                    continue
                
                else:
                    return {
                        "success": False,
                        "error_code": f"HTTP_{response.status_code}",
                        "error_msg": response.text
                    }
                    
            except requests.Timeout:
                if attempt < retry_count - 1:
                    logger.warning(f"请求超时，第 {attempt+1} 次重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    return {
                        "success": False,
                        "error_code": "TIMEOUT",
                        "error_msg": "请求超时，超过重试次数"
                    }
            
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(f"请求失败: {e}，第 {attempt+1} 次重试...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return {
                        "success": False,
                        "error_code": "REQUEST_ERROR",
                        "error_msg": str(e)
                    }
        
        return {
            "success": False,
            "error_code": "MAX_RETRIES",
            "error_msg": "超过最大重试次数"
        }
    
    def get_api_list(self,
                     appid_number: str,
                     search_keyword: str = None,
                     module: str = None,
                     page_no: int = 1,
                     page_size: int = 10) -> Dict[str, Any]:
        """
        查询金蝶开放平台的API列表
        
        使用官方API: kapi/v2/open/openapi_apilist/queryByApp
        参考: 根据应用编码查询API列表（queryByApp）
        
        Args:
            appid_number: 查询API列表所需的应用编码（必填）
            search_keyword: 搜索关键词（API名称或编码）
            module: API模块（如ar、ap、pm等）
            page_no: 页码（从1开始），默认1
            page_size: 每页数量（默认10，最多100）
            
        Returns:
            包含API列表和分页信息的字典
            {
                "success": True,
                "data": {
                    "total": 100,
                    "pageNo": 1,
                    "pageSize": 20,
                    "apis": [...]
                }
            }
        """
        try:
            if not appid_number:
                return {
                    'success': False,
                    'message': 'appid_number 为必填参数',
                    'total': 0,
                    'apis': []
                }

            token = self.get_token()

            api_url = f"{self.server_url}/kapi/v2/open/openapi_apilist/queryByApp"
            request_params = {
                "appid_number": appid_number,
                "pageNo": page_no,
                "pageSize": min(page_size, 100),  # 最多100条
            }
            headers = {
                "accesstoken": token,
                "Content-Type": "application/json"
            }

            response = requests.get(
                api_url,
                params=request_params,
                headers=headers,
                verify=True,
                timeout=50
            )

            if response.status_code == 401:
                headers["accesstoken"] = self.get_token(force_refresh=True)
                response = requests.get(
                    api_url,
                    params=request_params,
                    headers=headers,
                    verify=True,
                    timeout=50
                )

            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"获取API列表失败 (HTTP {response.status_code}): {error_msg}")
                return {
                    'success': False,
                    'message': f'查询失败: {error_msg}',
                    'total': 0,
                    'apis': []
                }

            result = _parse_json_response(response)
            if result.get('error_code') == 401 or result.get('errorCode') == "401":
                headers["accesstoken"] = self.get_token(force_refresh=True)
                response = requests.get(
                    api_url,
                    params=request_params,
                    headers=headers,
                    verify=True,
                    timeout=50
                )
                if response.status_code != 200:
                    error_msg = response.text
                    logger.error(f"获取API列表失败 (HTTP {response.status_code}): {error_msg}")
                    return {
                        'success': False,
                        'message': f'查询失败: {error_msg}',
                        'total': 0,
                        'apis': []
                    }
                result = _parse_json_response(response)

            if result.get('success') or result.get('status') or result.get('data'):
                data = result.get('data', {})
                if isinstance(data, list):
                    apis = [self._normalize_api_record(item) for item in data if isinstance(item, dict)]
                    apis = self._filter_api_records(apis, search_keyword=search_keyword, module=module)
                    return {
                        'success': True,
                        'total': result.get('total', len(apis)),
                        'pageNo': result.get('pageNo', page_no),
                        'pageSize': result.get('pageSize', page_size),
                        'apis': apis,
                        'message': '查询成功'
                    }

                rows = data.get('rows', []) if isinstance(data, dict) else []
                if rows:
                    apis = [self._normalize_api_record(item) for item in rows if isinstance(item, dict)]
                    apis = self._filter_api_records(apis, search_keyword=search_keyword, module=module)
                    return {
                        'success': True,
                        'total': data.get('totalCount', len(apis)),
                        'pageNo': data.get('pageNo', page_no),
                        'pageSize': data.get('pageSize', page_size),
                        'apis': apis,
                        'message': '查询成功'
                    }

                apis = data.get('apis', []) if isinstance(data, dict) else []
                apis = [self._normalize_api_record(item) for item in apis if isinstance(item, dict)]
                apis = self._filter_api_records(apis, search_keyword=search_keyword, module=module)
                return {
                    'success': True,
                    'total': data.get('total', len(apis)),
                    'pageNo': data.get('pageNo', page_no),
                    'pageSize': data.get('pageSize', page_size),
                    'apis': apis,
                    'message': '查询成功'
                }
            else:
                error_msg = result.get('error_msg', '未知错误')
                logger.error(f"获取API列表失败: {error_msg}")
                return {
                    'success': False,
                    'message': f'查询失败: {error_msg}',
                    'total': 0,
                    'apis': []
                }
                
        except Exception as e:
            logger.error(f"获取API列表异常: {e}")
            return {
                'success': False,
                'message': f'异常: {str(e)}',
                'total': 0,
                'apis': []
            }
    
    def get_api_detail(self, api_id: str, page_no: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        根据主键获取单条API详情
        
        使用官方API: GET /v2/open/openapi_apilist/getDetail
        获取API的完整定义，包括请求头、请求参数、返回参数、错误码等
        
        ⚠️ 重要提示: 此查询接口必须传递分页参数 pageSize 和 pageNo，即使只查询单条记录。
        
        Args:
            api_id: API的主键ID (id字段)
            page_no: 查询页码，默认为1
            page_size: 分页大小，默认为10
            
        Returns:
            API详情，包含以下关键字段:
            {
                "success": True,
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
                    ...
                }
            }
        """
        try:
            if not api_id:
                return {
                    'success': False,
                    'message': 'api_id 为必填参数',
                    'api_detail': None
                }
            
            token = self.get_token()
            
            # 构建请求URL和参数
            # ⚠️ 重要: 必须传递分页参数 pageSize 和 pageNo，即使只查询单条记录
            api_url = f"{self.server_url}/kapi/v2/open/openapi_apilist/getDetail"
            request_params = {
                "id": api_id,
                "pageNo": page_no,
                "pageSize": page_size
            }
            headers = {
                "accesstoken": token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                api_url,
                params=request_params,
                headers=headers,
                verify=True,
                timeout=50
            )
            
            if response.status_code == 401:
                headers["accesstoken"] = self.get_token(force_refresh=True)
                response = requests.get(
                    api_url,
                    params=request_params,
                    headers=headers,
                    verify=True,
                    timeout=50
                )
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"获取API详情失败 (HTTP {response.status_code}): {error_msg}")
                return {
                    'success': False,
                    'message': f'查询失败: {error_msg}',
                    'api_detail': None
                }
            
            result = _parse_json_response(response)
            
            # 处理Token过期
            if result.get('error_code') == 401 or result.get('errorCode') == "401":
                headers["accesstoken"] = self.get_token(force_refresh=True)
                response = requests.get(
                    api_url,
                    params=request_params,
                    headers=headers,
                    verify=True,
                    timeout=50
                )
                if response.status_code != 200:
                    error_msg = response.text
                    logger.error(f"获取API详情失败 (HTTP {response.status_code}): {error_msg}")
                    return {
                        'success': False,
                        'message': f'查询失败: {error_msg}',
                        'api_detail': None
                    }
                result = _parse_json_response(response)
            
            # 解析响应数据
            # 返回结构: { "data": { "rows": [...] }, "status": true, "errorCode": "" }
            if result.get('success') or result.get('status') or result.get('data'):
                data = result.get('data', {})
                
                # 从 data.rows 中获取API详情（这是金蝶标准返回结构）
                if isinstance(data, dict):
                    rows = data.get('rows', [])
                    if isinstance(rows, list) and len(rows) > 0:
                        api_detail = rows[0]
                    else:
                        # 如果没有rows，尝试直接使用data
                        api_detail = data
                elif isinstance(data, list) and len(data) > 0:
                    api_detail = data[0]
                else:
                    api_detail = result
                
                # 规范化API详情数据
                normalized_detail = self._normalize_api_detail(api_detail)
                
                return {
                    'success': True,
                    'message': '获取API详情成功',
                    'api_detail': normalized_detail
                }
            else:
                error_msg = result.get('message') or result.get('error_msg', '未知错误')
                logger.error(f"获取API详情失败: {error_msg}")
                return {
                    'success': False,
                    'message': f'获取失败: {error_msg}',
                    'api_detail': None
                }
                
        except Exception as e:
            logger.error(f"获取API详情异常: {e}")
            return {
                'success': False,
                'message': f'异常: {str(e)}',
                'api_detail': None
            }
    
    def _normalize_api_detail(self, api_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化API详情数据，提取关键字段
        
        根据金蝶OpenAPI文档，从 data.rows[0] 中提取并规范化以下参数：
        - headerentryentity: 请求头参数
        - urlparamentryentity: URL查询参数 (Query Parameters)
        - bodyentryentity: 请求体参数
        - respentryentity: 返回参数
        - errorcodeentity: 错误码定义
        
        Args:
            api_detail: 原始API详情数据（data.rows[0]）
            
        Returns:
            规范化后的API详情
        """
        if not isinstance(api_detail, dict):
            return api_detail
        
        normalized = dict(api_detail)
        
        # 1. 提取请求头参数 (headerentryentity)
        headers = api_detail.get('headerentryentity') or []
        normalized['request_headers'] = [
            {
                'name': h.get('headername'),
                'value': h.get('headervalue'),
                'description': h.get('headerdes'),
                'required': h.get('headername') in ['Content-Type', 'accesstoken']
            }
            for h in headers if isinstance(h, dict)
        ]

        # 2. 提取URL查询参数 (urlparamentryentity) - 注意：不是 filter_entity
        url_params = api_detail.get('urlparamentryentity') or []
        normalized['request_query_params'] = [
            {
                'name': p.get('urlparamname'),
                'type': p.get('urlparamtype'),
                'description': p.get('urlparamdes'),
                'required': p.get('urlparammust') == '1',
                'example': p.get('urlparamexample')
            }
            for p in url_params if isinstance(p, dict)
        ]
        
        # 3. 提取Body参数 (bodyentryentity)
        body_params = api_detail.get('bodyentryentity') or []
        normalized['request_body_params'] = [
            {
                'name': p.get('paramname'),
                'type': p.get('paramtype'),
                'description': p.get('bodyparamdes'),
                'required': p.get('must') == '1',
                'example': p.get('example'),
                'level': p.get('body_level'),
                'default_value': p.get('param_default_value')
            }
            for p in body_params if isinstance(p, dict)
        ]

        # 4. 提取返回参数 (respentryentity)
        resp_params = api_detail.get('respentryentity') or []
        normalized['response_params'] = [
            {
                'name': p.get('respparamname'),
                'type': p.get('respparamtype'),
                'description': p.get('respdes'),
                'required': p.get('respparammust') == '1',
                'level': p.get('resp_level'),
                'example': p.get('respexample')
            }
            for p in resp_params if isinstance(p, dict)
        ]

        # 5. 提取错误码定义 (errorcodeentity)
        error_codes = api_detail.get('errorcodeentity') or []
        normalized['error_codes'] = [
            {
                'code': e.get('errorcode'),
                'description': e.get('errorcodedesc')
            }
            for e in error_codes if isinstance(e, dict)
        ]

        # 6. 提取其他有用的实体
        # 排序规则
        orderby_rules = api_detail.get('orderby_entry') or []
        normalized['orderby_rules'] = [
            {
                'field': o.get('order_field'),
                'mode': o.get('order_mode'),
                'description': o.get('order_desc')
            }
            for o in orderby_rules if isinstance(o, dict)
        ]

        # 操作参数
        save_params = api_detail.get('saveparamentryentity') or []
        normalized['save_params'] = [
            {
                'key': s.get('saveparamkey'),
                'value': s.get('saveparamvalue'),
                'type': s.get('saveparamtype'),
                'remark': s.get('saveparamremark')
            }
            for s in save_params if isinstance(s, dict)
        ]
        
        # 7. 添加便捷字段
        normalized['api_code'] = api_detail.get('number')
        normalized['api_name'] = self._extract_multilang_text(api_detail.get('name'))
        normalized['api_description'] = self._extract_multilang_text(api_detail.get('discription'))
        normalized['method'] = 'GET' if api_detail.get('httpmethod') == '0' else 'POST'
        normalized['url'] = api_detail.get('urlformat')
        normalized['operation'] = api_detail.get('operation')
        normalized['cosmic_version'] = api_detail.get('cosmicver')
        normalized['api_status'] = api_detail.get('status')
        normalized['enable'] = api_detail.get('enable') == '1'
        
        return normalized

    def query_api_by_keyword(self,
                            keyword: str,
                            appid_number: str,
                            page_no: int = 10,
                            page_size: int = 50) -> List[Dict[str, Any]]:
        """
        按关键词搜索API（便利方法）
        
        Args:
            keyword: 搜索关键词（可以是API名称、编码等）
            page_size: 每页数量
            
        Returns:
            API列表
        """
        result = self.get_api_list(
            appid_number=appid_number,
            search_keyword=keyword,
            page_no=page_no,
            page_size=page_size
        )
        
        if result['success']:
            return result['apis']
        else:
            logger.error(f"搜索失败: {result['message']}")
            return []
    
    def get_all_apis(self,
                    appid_number: str,
                    module: str = None,
                    page_size: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有API（支持自动分页）
        
        Args:
            module: 可选的模块过滤
            page_size: 每页数量（最多100）
            
        Returns:
            完整的API列表
        """
        all_apis = []
        page_no = 1
        
        while True:
            result = self.get_api_list(
                appid_number=appid_number,
                module=module,
                page_no=page_no,
                page_size=page_size
            )
            
            if not result['success']:
                logger.warning(f"获取第{page_no}页失败: {result['message']}")
                break
            
            apis = result.get('apis', [])
            if not apis:
                break
            
            all_apis.extend(apis)
            
            # 检查是否有更多页
            total = result.get('total', 0)
            if len(all_apis) >= total:
                break
            
            page_no += 1
        
        logger.info(f"共获取{len(all_apis)}个API")
        return all_apis
    
    def validate_credentials(self) -> Dict[str, Any]:
        """
        验证凭证有效性
        
        Returns:
            验证结果
        """
        validation_result = {
            "connection": False,
            "authentication": False,
            "authorization": False,
            "errors": []
        }
        
        # 1. 验证连接
        if not self._verify_connection():
            validation_result["errors"].append("无法连接到服务器")
            return validation_result
        validation_result["connection"] = True
        
        # 2. 验证认证
        try:
            token = self.get_token()
            if token:
                validation_result["authentication"] = True
            else:
                validation_result["errors"].append("无法获取API Token")
        except Exception as e:
            validation_result["errors"].append(f"认证失败: {str(e)}")
        
        # 3. 验证权限（尝试调用一个简单的API）
        if validation_result["authentication"]:
            try:
                result = self.call_api(
                    api_code="getUserInfo",
                    method="GET",
                    params={}
                )
                if result.get('success') or result.get('data'):
                    validation_result["authorization"] = True
            except:
                validation_result["errors"].append("权限验证失败")
        
        return validation_result
