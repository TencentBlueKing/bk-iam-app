# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-权限中心(BlueKing-IAM) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import logging
import time
import traceback
from functools import partial
from typing import Any, Dict, List, Tuple, Union
from urllib.parse import urlparse

import requests
from aenum import LowerStrEnum, auto
from django.utils import translation
from django.utils.functional import SimpleLazyObject
from requests import auth

from backend.common.debug import http_trace
from backend.common.error_codes import error_codes
from backend.common.i18n import get_bk_language
from backend.common.local import local
from backend.util.cache import region

request_pool = requests.Session()
logger = logging.getLogger("component")


ResponseCodeToErrorDict = {
    401: {"error": error_codes.RESOURCE_PROVIDER_UNAUTHORIZED, "replace_message": False},
    404: {"error": error_codes.RESOURCE_PROVIDER_NOT_FOUND, "replace_message": False},
    406: {"error": error_codes.RESOURCE_PROVIDER_SEARCH_VALIDATE_ERROR, "replace_message": True},
    422: {"error": error_codes.RESOURCE_PROVIDER_DATA_TOO_LARGE, "replace_message": False},
    429: {"error": error_codes.RESOURCE_PROVIDER_API_REQUEST_FREQUENCY_EXCEEDED, "replace_message": False},
    500: {"error": error_codes.RESOURCE_PROVIDER_INTERNAL_SERVER_ERROR, "replace_message": False},
}


class AuthTypeEnum(LowerStrEnum):
    NONE = auto()
    BASIC = auto()
    DIGEST = auto()


def _generate_http_auth(auth_info: Dict[str, str]) -> Union[None, auth.HTTPBasicAuth, auth.HTTPDigestAuth]:
    # 无需认证
    if not auth_info:
        return None

    auth_type = auth_info["auth"]
    username = "bk_iam"
    password = auth_info["token"]

    # 不鉴权，一般测试联调时可能使用
    if auth_type == AuthTypeEnum.NONE.value:
        return None

    # http basic auth
    if auth_type == AuthTypeEnum.BASIC.value:
        return auth.HTTPBasicAuth(username, password)

    # http digest auth
    if auth_type == AuthTypeEnum.DIGEST.value:
        return auth.HTTPDigestAuth(username, password)

    # 后续可能支持Signature，可以继承auth.AuthBase类自定义相关子类
    # 可参考：https://requests.readthedocs.io/en/master/user/authentication/#new-forms-of-authentication

    raise error_codes.RESOURCE_PROVIDER_AUTH_INFO_VALID


class ResourceProviderClient:
    """资源提供者请求客户端"""

    def __init__(self, system_id: str, resource_type_id: str, url: str, auth_info: Dict[str, str]):
        """初始化请求需要的HTTP鉴权和其他HEADER"""
        self.system_id = system_id
        self.resource_type_id = resource_type_id
        self.url = url
        self.request_id = local.request_id
        self.headers = {
            "Content-Type": "application/json",
            "Request-Id": self.request_id,
            "Blueking-Language": get_bk_language(translation.get_language()),
        }
        self.http_auth = _generate_http_auth(auth_info)
        self.timeout = 30

    def _call_api(self, data):
        """调用请求API"""
        trace_func = partial(http_trace, method="post", url=self.url, data=data)

        kwargs = {
            "url": self.url,
            "json": data,
            "headers": self.headers,
            "auth": self.http_auth,
            "timeout": self.timeout,
            "verify": False,
        }

        # 由于request_id可能在请求返回header被更新，所以需要lazyObject
        # 该信息用于日志
        base_log_msg = SimpleLazyObject(
            lambda: "resource_provider[system: {}, resource_type: {}] API[request_id: {}]".format(
                self.system_id, self.resource_type_id, self.request_id
            )
        )

        # 回调请求的详细信息
        request_detail_info = (
            f"request detail info: system_id={self.system_id}, "
            f"resource_type_id={self.resource_type_id}, "
            f"url_path={urlparse(self.url).path}, "
            f"data.method={data['method']}"
        )

        try:
            st = time.time()
            resp = request_pool.request("post", **kwargs)
            # 接入系统可返回request_id便于排查，避免接入系统未使用权限中心请求头里的request_id而自行生成，所以需要再获取赋值
            self.request_id = resp.headers.get("X-Request-Id") or self.request_id
            latency = int((time.time() - st) * 1000)
            # 打印INFO日志，用于调试时使用
            logger.info(
                f"{base_log_msg}, latency: {latency} ms, info: {kwargs}, "
                f"status_code: {resp.status_code}, response_content: {resp.text}"
            )
        except requests.exceptions.RequestException:
            logger.exception(f"{base_log_msg} RequestException, info: {kwargs}")
            trace_func(exc=traceback.format_exc())
            # 接口不可达
            raise error_codes.RESOURCE_PROVIDER_ERROR.format(f"unreachable interface call, {request_detail_info}")

        try:
            # 非2xx类都会异常
            resp.raise_for_status()
            # 返回可能非JSON
            resp = resp.json()
        except requests.exceptions.HTTPError:
            logger.exception(f"{base_log_msg} StatusCodeException, info: {kwargs}")
            trace_func(exc=traceback.format_exc())
            # 接口状态码异常
            raise error_codes.RESOURCE_PROVIDER_ERROR.format(
                f"interface status code: `{resp.status_code}` error, {request_detail_info}"
            )
        except Exception as error:  # pylint: disable=broad-except
            logger.error(
                f"{base_log_msg} RespDataException, info: {kwargs}, response_content: {resp.text}， error: {error}"
            )
            trace_func(exc=traceback.format_exc())
            # 数据异常，JSON解析出错
            raise error_codes.RESOURCE_PROVIDER_JSON_LOAD_ERROR.format(f"error: {error}, {request_detail_info}")

        code = resp["code"]
        if code == 0:
            # TODO: 验证Data数据的schema是否正确，可能得放到每个具体method去定义并校验
            return resp["data"]

        logger.error(f"{base_log_msg} Return Code Not Zero, info: %s, resp: %s", kwargs, resp)

        # code不同值代表不同意思，401: 认证失败，404: 资源类型不存在，500: 接入系统异常，422: 资源内容过多，拒绝返回数据 等等
        if code not in ResponseCodeToErrorDict:
            trace_func(code=code)
            raise error_codes.RESOURCE_PROVIDER_ERROR.format(f"Unknown Error, {request_detail_info}")

        raise ResponseCodeToErrorDict[code]["error"].format(
            message=f"{resp.get('message', '')}, {request_detail_info}",
            replace=ResponseCodeToErrorDict[code]["replace_message"],
        )

    def _handle_empty_data(self, data, default_empty_data: Union[List, Dict]) -> Any:
        """处理兼容对方返回空数据为None、[]、{}、字符串"""
        if not data:
            return default_empty_data
        # 校验类型是否一致
        if type(data) != type(default_empty_data):
            raise error_codes.RESOURCE_PROVIDER_DATA_INVALID.format(
                f"the type of data must be {type(default_empty_data)}, data: {data}"
            )
        return data

    def _handle_data_valid(self, resp_data: Dict) -> Tuple[int, List[Dict[str, str]]]:
        count, results = resp_data["count"], resp_data["results"]
        if len(results) > count:
            logger.error("resource_provider data invalid, count: %d, results: %s", count, results)
            raise error_codes.RESOURCE_PROVIDER_DATA_INVALID.format(
                f"the count of data must be greater than or equal to the length of results, "
                f"count: {count}, len(results): {len(results)}"
            )
        return count, results

    def list_attr(self) -> List[Dict[str, str]]:
        """查询某个资源类型可用于配置权限的属性列表"""
        data = {"type": self.resource_type_id, "method": "list_attr"}
        return self._handle_empty_data(self._call_api(data), [])

    def list_attr_value(
        self, attr: str, filter_condition: Dict, page: Dict[str, int]
    ) -> Tuple[int, List[Dict[str, str]]]:
        """获取一个资源类型某个属性的值列表"""
        filter_condition["attr"] = attr
        data = {"type": self.resource_type_id, "method": "list_attr_value", "filter": filter_condition, "page": page}
        resp_data = self._handle_empty_data(self._call_api(data), default_empty_data={"count": 0, "results": []})
        return self._handle_data_valid(resp_data)

    def list_instance(self, filter_condition: Dict, page: Dict[str, int]) -> Tuple[int, List[Dict[str, str]]]:
        """根据过滤条件查询实例"""
        data = {"type": self.resource_type_id, "method": "list_instance", "filter": filter_condition, "page": page}
        resp_data = self._handle_empty_data(self._call_api(data), default_empty_data={"count": 0, "results": []})
        return self._handle_data_valid(resp_data)

    def fetch_instance_info(self, filter_condition: Dict) -> List[Dict]:
        """批量获取资源实例详情"""
        data = {"type": self.resource_type_id, "method": "fetch_instance_info", "filter": filter_condition}
        return self._handle_empty_data(self._call_api(data), [])

    def list_instance_by_policy(
        self, filter_condition: Dict, page: Dict[str, int]
    ) -> Tuple[int, List[Dict[str, str]]]:
        """根据策略表达式查询资源实例"""
        data = {
            "type": self.resource_type_id,
            "method": "list_instance_by_policy",
            "filter": filter_condition,
            "page": page,
        }
        resp_data = self._handle_empty_data(self._call_api(data), default_empty_data={"count": 0, "results": []})
        return self._handle_data_valid(resp_data)

    def search_instance(self, filter_condition: Dict, page: Dict[str, int]) -> Tuple[int, List[Dict[str, str]]]:
        """根据过滤条件且必须保证keyword不为空查询实例"""
        return self._search_instance(self.system_id, self.resource_type_id, filter_condition, page)

    @region.cache_on_arguments(expiration_time=60)  # 缓存1分钟
    def _search_instance(
        self, system_id: str, resource_type_id: str, filter_condition: Dict, page: Dict[str, int]
    ) -> Tuple[int, List[Dict[str, str]]]:
        """根据过滤条件且必须保证keyword不为空查询实例"""
        if not filter_condition["keyword"]:
            raise error_codes.RESOURCE_PROVIDER_VALIDATE_ERROR.format(
                f"search_instance[system:{system_id}] param keyword should not be empty"
            )
        data = {"type": resource_type_id, "method": "search_instance", "filter": filter_condition, "page": page}
        resp_data = self._handle_empty_data(self._call_api(data), default_empty_data={"count": 0, "results": []})
        return self._handle_data_valid(resp_data)
