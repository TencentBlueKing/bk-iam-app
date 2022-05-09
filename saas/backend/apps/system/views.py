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
from rest_framework.viewsets import GenericViewSet

from backend.biz.resource_type import ResourceTypeBiz
from backend.biz.role import RoleListQuery

from .serializers import QueryResourceTypeSLZ, SystemResourceTypeSLZ, SystemSLZ


class SystemViewSet(GenericViewSet):

    pagination_class = None  # 去掉swagger中的limit offset参数

    @swagger_auto_schema(
        operation_description="系统列表",
        responses={status.HTTP_200_OK: SystemSLZ(label="系统", many=True)},
        tags=["system"],
    )
    def list(self, request, *args, **kwargs):
        systems = RoleListQuery(request.role).list_system()
        data = [i.dict(include={"id", "name", "name_en"}) for i in systems]
        return Response(data)


class ResourceTypeViewSet(GenericViewSet):

    pagination_class = None  # 去掉swagger中的limit offset参数

    biz = ResourceTypeBiz()

    @swagger_auto_schema(
        operation_description="资源类别列表",
        query_serializer=QueryResourceTypeSLZ(label="系统ID"),
        responses={status.HTTP_200_OK: SystemResourceTypeSLZ(label="资源类别", many=True)},
        tags=["system"],
    )
    def list_resource_types(self, request, *args, **kwargs):
        system_id = request.query_params["system_id"]
        data = self.biz.list_resource_types_by_system_id(system_id=system_id)
        return Response(data)
