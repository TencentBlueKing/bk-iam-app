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
from datetime import timedelta

from celery import task
from django.utils import timezone

from backend.audit.models import get_event_model


@task(ignore_result=True)
def pre_create_audit_model():
    """
    预创建下一个月的审计模型
    """
    next_month = (timezone.now() + timedelta(days=15)).strftime("%Y%m")
    get_event_model(next_month)


@task(ignore_result=True)
def log_audit_event(suffix: str, id: int):
    """
    记录审计事件到审计中心规范的日志文件
    """
    AuditModel = get_event_model(suffix)
    event = AuditModel.objects.get(id=id)

    # TODO 处理审计事件转换成日志, 并记录日志
    print(event)
