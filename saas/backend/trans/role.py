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
from typing import Any, Dict, Optional

from backend.biz.policy import PolicyBeanList
from backend.biz.role import RoleInfoBean

from .policy import PolicyTrans


class RoleTrans:
    """
    转换Role的创建/更新信息
    """

    policy_trans = PolicyTrans()

    def from_role_data(
        self, data: Dict[str, Any], old_system_policy_list: Optional[Dict[str, PolicyBeanList]] = None
    ) -> RoleInfoBean:
        """
        data: {
            "name": str,
            "description": str,
            "members": List[str],
            "subject_scopes": [
                {
                    "type": str,
                    "id": str
                }
            ],
            "authorization_scopes": [
                {
                    "system_id": str,
                    "actions": [],
                    "aggregations": []
                }
            ]
        }

        old_system_policy_list: 更新的数据提供
        """
        for system in data["authorization_scopes"]:
            system_id = system["system_id"]

            policy_list = self.policy_trans.from_aggregate_actions_and_actions(system_id, system)

            if old_system_policy_list and system_id in old_system_policy_list:
                # 更新范围信息时只需检查新增部分的实例名称
                added_policy_list = policy_list.sub(old_system_policy_list[system_id])
                added_policy_list.check_resource_name()
            else:
                policy_list.check_resource_name()

            system["actions"] = [p.dict() for p in policy_list.policies]

        return RoleInfoBean.parse_obj(data)
