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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins

from backend.api.admin.constants import AdminAPIEnum
from backend.api.admin.filters import GroupFilter
from backend.api.admin.permissions import AdminAPIPermission
from backend.api.admin.serializers import AdminGroupBasicSLZ, AdminGroupMemberSLZ
from backend.api.authentication import ESBAuthentication
from backend.apps.group.models import Group
from backend.biz.group import GroupBiz
from backend.common.pagination import CompatiblePagination


class AdminGroupViewSet(mixins.ListModelMixin, GenericViewSet):
    """用户组"""

    authentication_classes = [ESBAuthentication]
    permission_classes = [AdminAPIPermission]

    admin_api_permission = {"list": AdminAPIEnum.GROUP_LIST.value}

    queryset = Group.objects.all()
    serializer_class = AdminGroupBasicSLZ
    filterset_class = GroupFilter
    pagination_class = CompatiblePagination

    @swagger_auto_schema(
        operation_description="用户组列表",
        responses={status.HTTP_200_OK: AdminGroupBasicSLZ(label="用户组信息", many=True)},
        tags=["admin.group"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AdminGroupMemberViewSet(GenericViewSet):
    """用户组成员"""

    authentication_classes = [ESBAuthentication]
    permission_classes = [AdminAPIPermission]

    admin_api_permission = {"list": AdminAPIEnum.GROUP_MEMBER_LIST.value}

    queryset = Group.objects.all()
    lookup_field = "id"
    pagination_class = CompatiblePagination

    biz = GroupBiz()

    @swagger_auto_schema(
        operation_description="用户组成员列表",
        responses={status.HTTP_200_OK: AdminGroupMemberSLZ(label="用户组成员信息", many=True)},
        tags=["admin.group.member"],
    )
    def list(self, request, *args, **kwargs):
        group = self.get_object()

        # 分页参数
        limit, offset = CompatiblePagination().get_limit_offset_pair(request)

        count, group_members = self.biz.list_paging_thin_group_member(group.id, limit, offset)
        results = [one.dict(include={"type", "id", "name", "expired_at"}) for one in group_members]
        return Response({"count": count, "results": results})
