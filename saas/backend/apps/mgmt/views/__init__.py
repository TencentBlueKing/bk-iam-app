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

from backend.apps.group.views import GroupSystemViewSet
from backend.apps.mgmt.views.action import ActionViewSet
from backend.apps.mgmt.views.group import (
    GroupMemberUpdateExpiredAtViewSet,
    GroupMemberViewSet,
    GroupPolicyViewSet,
    GroupTemplateViewSet,
    GroupTransferView,
    GroupViewSet,
)
from backend.apps.mgmt.views.long_task import LongTaskViewSet
from backend.apps.mgmt.views.role import RoleAuthorizationScopeView, RoleSubjectScopeView
from backend.apps.mgmt.views.system import SystemViewSet
from backend.apps.mgmt.views.template import TemplateViewSet
from backend.apps.mgmt.views.white_list import (
    AdminApiWhiteListViewSet,
    ApiViewSet,
    AuthorizationApiWhiteListViewSet,
    ManagementApiWhiteListViewSet,
)

__all__ = [
    "ApiViewSet",
    "AdminApiWhiteListViewSet",
    "AuthorizationApiWhiteListViewSet",
    "ManagementApiWhiteListViewSet",
    "LongTaskViewSet",
    "GroupViewSet",
    "GroupMemberViewSet",
    "GroupMemberUpdateExpiredAtViewSet",
    "GroupTemplateViewSet",
    "GroupPolicyViewSet",
    "GroupSystemViewSet",
    "GroupTransferView",
    "RoleSubjectScopeView",
    "RoleAuthorizationScopeView",
    "TemplateViewSet",
    "SystemViewSet",
    "ActionViewSet",
    ]
