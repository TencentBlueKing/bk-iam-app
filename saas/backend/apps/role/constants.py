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
from enum import Enum

from aenum import LowerStrEnum, auto, skip
from django.utils.translation import gettext as _

from backend.service.constants import PermissionCodeEnum, RoleType
from backend.util.enum import ChoicesEnum

# 角色默认权限
DEFAULT_ROLE_PERMISSIONS = {  # 超级管理员不能操作子集管理员
    RoleType.SUPER_MANAGER.value: [
        p.value
        for p in PermissionCodeEnum
        if p.value
        not in (
            PermissionCodeEnum.CREATE_SUBSET_MANAGER.value,
            PermissionCodeEnum.MANAGE_SUBSET_MANAGER.value,
            PermissionCodeEnum.TRANSFER_GROUP_BY_GRADE_MANAGER.value,
        )
    ],
    RoleType.SYSTEM_MANAGER.value: [
        PermissionCodeEnum.MANAGE_GROUP.value,
        PermissionCodeEnum.MANAGE_TEMPLATE.value,
        PermissionCodeEnum.CREATE_GRADE_MANAGER.value,
        PermissionCodeEnum.AUDIT.value,
        PermissionCodeEnum.CONFIGURE_APPROVAL_PROCESS.value,
        PermissionCodeEnum.MANAGE_SYSTEM_SETTING.value,
        PermissionCodeEnum.MANAGE_COMMON_ACTION.value,
        PermissionCodeEnum.MANAGE_SYSTEM_MANAGER_MEMBER.value,
    ],
    RoleType.GRADE_MANAGER.value: [
        PermissionCodeEnum.MANAGE_GROUP.value,
        PermissionCodeEnum.MANAGE_TEMPLATE.value,
        PermissionCodeEnum.CONFIGURE_APPROVAL_PROCESS.value,
        PermissionCodeEnum.MANAGE_COMMON_ACTION.value,
        PermissionCodeEnum.CREATE_SUBSET_MANAGER.value,
        PermissionCodeEnum.MANAGE_SUBSET_MANAGER.value,
        PermissionCodeEnum.TRANSFER_GROUP_BY_GRADE_MANAGER.value,
    ],
    RoleType.SUBSET_MANAGER.value: [
        PermissionCodeEnum.MANAGE_GROUP.value,
        PermissionCodeEnum.CONFIGURE_APPROVAL_PROCESS.value,
        PermissionCodeEnum.MANAGE_COMMON_ACTION.value,
    ],
}


class PermissionTypeEnum(ChoicesEnum, LowerStrEnum):
    """权限类型"""

    CUSTOM = auto()
    TEMPLATE = auto()
    RESOURCE_INSTANCE = auto()

    _choices_labels = skip(((CUSTOM, _("自定义权限")), (TEMPLATE, _("模板权限")), (RESOURCE_INSTANCE, _("资源实例"))))


class ManagementCommonActionNameEnum(Enum):
    OPS = "业务运维"
    READ = "业务只读"


class ManagementGroupNameSuffixEnum(Enum):
    OPS = "运维组"
    READ = "查看组"
