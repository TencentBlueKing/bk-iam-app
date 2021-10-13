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
from typing import Dict

from django.conf import settings

from backend.common.error_codes import error_codes
from backend.common.local import local
from backend.util.url import url_join

from .http import http_get, http_post, logger


def _call_esb_api(http_func, url_path, data, timeout=30):
    # 默认请求头
    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": local.request_id,
    }
    # Note: 目前企业版ESB调用的鉴权信息都是与接口的参数一起的，并非在header头里
    common_params = {
        "bk_app_code": settings.APP_ID,
        "bk_app_secret": settings.APP_TOKEN,
        "bk_username": "admin",  # 存在后台任务，无法使用登录态的方式
        # 兼容TE版
        "app_code": settings.APP_ID,
        "app_secret": settings.APP_TOKEN,
    }
    data.update(common_params)

    url = url_join(settings.BK_COMPONENT_INNER_API_URL, url_path)
    kwargs = {"url": url, "data": data, "headers": headers, "timeout": timeout}

    ok, data = http_func(**kwargs)

    # process result
    if not ok:
        message = "esb api failed, method: %s, info: %s" % (http_func.__name__, kwargs)
        logger.error(message)
        raise error_codes.REMOTE_REQUEST_ERROR.format("request esb api error")

    code = data["code"]
    message = data["message"]

    if code == 0:
        return data["data"]

    logger.warning(
        "esb api warning, request_id: %s, method: %s, info: %s, code: %d, message: %s",
        local.request_id,
        http_func.__name__,
        kwargs,
        code,
        message,
    )
    raise error_codes.ESB_REQUEST_ERROR.format(message)


def get_api_public_key() -> Dict:
    """获取目录列表"""
    url_path = "/api/c/compapi/v2/esb/get_api_public_key/"
    return _call_esb_api(http_get, url_path, data={})


def send_mail(username, title, content, body_format="Html"):
    """发送邮件"""
    url_path = "/api/c/compapi/cmsi/send_mail/"
    data = {"receiver__username": username, "title": title, "content": content, "body_format": body_format}
    return _call_esb_api(http_post, url_path, data=data)
