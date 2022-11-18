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
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.authentication import ESBAuthentication
from backend.api.management.constants import ManagementAPIEnum, VerifyAPIParamLocationEnum
from backend.api.management.mixins import ManagementAPIPermissionCheckMixin
from backend.api.management.v2.permissions import ManagementAPIPermission
from backend.api.management.v2.serializers import ManagementGradeManagerCreateSLZ
from backend.apps.role.audit import RoleCreateAuditProvider, RoleUpdateAuditProvider
from backend.apps.role.models import Role, RoleSource
from backend.apps.role.serializers import RoleIdSLZ
from backend.audit.audit import audit_context_setter, view_audit_decorator
from backend.biz.group import GroupBiz
from backend.biz.role import RoleBiz, RoleCheckBiz
from backend.service.constants import RoleSourceTypeEnum, RoleType
from backend.trans.open_management import GradeManagerTrans


class ManagementGradeManagerViewSet(ManagementAPIPermissionCheckMixin, GenericViewSet):
    """分级管理员"""

    authentication_classes = [ESBAuthentication]
    permission_classes = [ManagementAPIPermission]
    management_api_permission = {
        "create": (VerifyAPIParamLocationEnum.SYSTEM_IN_BODY.value, ManagementAPIEnum.V2_GRADE_MANAGER_CREATE.value),
        "update": (VerifyAPIParamLocationEnum.ROLE_IN_PATH.value, ManagementAPIEnum.V2_GRADE_MANAGER_UPDATE.value),
    }

    lookup_field = "id"
    queryset = Role.objects.filter(type=RoleType.GRADE_MANAGER.value).order_by("-updated_time")

    biz = RoleBiz()
    group_biz = GroupBiz()
    role_check_biz = RoleCheckBiz()
    trans = GradeManagerTrans()

    @swagger_auto_schema(
        operation_description="创建分级管理员",
        request_body=ManagementGradeManagerCreateSLZ(label="创建分级管理员"),
        responses={status.HTTP_201_CREATED: RoleIdSLZ(label="分级管理员ID")},
        tags=["management.role"],
    )
    @view_audit_decorator(RoleCreateAuditProvider)
    def create(self, request, *args, **kwargs):
        """
        创建分级管理员
        """
        serializer = ManagementGradeManagerCreateSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # API里数据鉴权: 不可超过接入系统可管控的授权系统范围
        source_system_id = kwargs["system_id"]
        auth_system_ids = list({i["system"] for i in data["authorization_scopes"]})
        self.verify_system_scope(source_system_id, auth_system_ids)

        # 名称唯一性检查
        self.role_check_biz.check_grade_manager_unique_name(data["name"])
        # 检查该系统可创建的分级管理员数量是否超限
        self.role_check_biz.check_grade_manager_of_system_limit(source_system_id)

        # 兼容member格式
        data["members"] = [{"username": username} for username in data["members"]]

        # 转换为RoleInfoBean，用于创建时使用
        role_info = self.trans.to_role_info(data, source_system_id=source_system_id)

        with transaction.atomic():
            # 创建角色
            role = self.biz.create_grade_manager(role_info, request.user.username)

            # 记录role创建来源信息
            RoleSource.objects.create(
                role_id=role.id, source_type=RoleSourceTypeEnum.API.value, source_system_id=source_system_id
            )

            # 创建同步权限用户组
            if role_info.sync_perm:
                self.group_biz.create_sync_perm_group_by_role(role, request.user.username)

        # 审计
        audit_context_setter(role=role)

        return Response({"id": role.id})

    @swagger_auto_schema(
        operation_description="更新分级管理员",
        request_body=ManagementGradeManagerCreateSLZ(label="更新分级管理员"),
        responses={status.HTTP_200_OK: serializers.Serializer()},
        tags=["management.role"],
    )
    @view_audit_decorator(RoleUpdateAuditProvider)
    def update(self, request, *args, **kwargs):
        """
        更新分级管理员
        """
        role = self.get_object()

        serializer = ManagementGradeManagerCreateSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 数据校验
        # 名称唯一性检查
        self.role_check_biz.check_grade_manager_unique_name(data["name"], role.name)

        # API里数据鉴权: 不可超过接入系统可管控的授权系统范围
        role_source = RoleSource.objects.get(source_type=RoleSourceTypeEnum.API.value, role_id=role.id)
        auth_system_ids = list({i["system"] for i in data["authorization_scopes"]})
        self.verify_system_scope(role_source.source_system_id, auth_system_ids)

        # 兼容member格式
        data["members"] = [{"username": username} for username in data["members"]]

        # 转换为RoleInfoBean
        role_info = self.trans.to_role_info(data, source_system_id=kwargs["system_id"])

        # 更新
        self.biz.update(role, role_info, request.user.username)

        # 更新同步权限用户组信息
        self.group_biz.update_sync_perm_group_by_role(
            self.get_object(), request.user.username, sync_members=True, sync_prem=True
        )

        # 审计
        audit_context_setter(role=role)

        return Response({})
