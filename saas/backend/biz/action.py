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
from typing import Dict, List, Optional, Set

from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic.tools import parse_obj_as

from backend.common.error_codes import error_codes
from backend.service.action import ActionList, ActionService
from backend.service.constants import ACTION_ALL, SubjectType
from backend.service.models import Action, RelatedResourceType, ResourceTypeDict, Subject
from backend.service.policy.query import PolicyQueryService
from backend.service.resource_type import ResourceTypeService
from backend.util.model import ExcludeModel

from .constants import ActionTag
from .role import RoleListQuery


class RelatedResourceTypeBean(RelatedResourceType, ExcludeModel):
    __exclude__ = ["instance_selections"]

    def need_fill_name(self):
        return not self.name or not self.name_en


class ActionBean(Action):
    related_resource_types: List[RelatedResourceTypeBean] = []

    expired_at: Optional[int] = None
    tag: str = ActionTag.UNCHECKED.value


class ActionSearchCondition(BaseModel):
    """操作的搜索条件"""

    keyword: Optional[str] = ""
    action_group_id: Optional[int] = 0


class ActionBeanList:
    def __init__(self, actions: List[ActionBean]) -> None:
        self.actions = actions
        self._action_dict = {action.id: action for action in actions}

    def get(self, action_id: str) -> Optional[ActionBean]:
        return self._action_dict.get(action_id, None)

    def fill_related_resource_type_name(self):
        system_ids = self._list_related_resource_type_system()
        name_provider = ResourceTypeService().get_resource_type_dict(system_ids)
        for action in self.actions:
            self._fill_action_related_resource_type_name(action, name_provider)

    def _list_related_resource_type_system(self):
        return list({rt.system_id for action in self.actions for rt in action.related_resource_types})

    def _fill_action_related_resource_type_name(self, action: ActionBean, name_provider: ResourceTypeDict):
        for rt in action.related_resource_types:
            if not rt.need_fill_name():
                continue
            rt.name, rt.name_en = name_provider.get_name(rt.system_id, rt.id)

    def filter_by_scope_action_ids(self, scope_action_ids: List[str]) -> List[ActionBean]:
        if ACTION_ALL in scope_action_ids:
            return self.actions

        return [action for action in self.actions if action.id in scope_action_ids]

    def filter_by_name(self, name: str) -> List[ActionBean]:
        return [a for a in self.actions if name.lower() in a.name.lower() or name in a.name_en.lower()]

    def fill_expired_at_and_tag(self, action_expired_at: Dict[str, int]):
        for action in self.actions:
            if action.id not in action_expired_at:
                continue

            action.expired_at = action_expired_at[action.id]
            action.tag = ActionTag.READONLY.value


class ActionBiz:
    action_svc = ActionService()
    resource_type_svc = ResourceTypeService()
    policy_svc = PolicyQueryService()

    def list(self, system_id: str) -> ActionBeanList:
        actions = self.action_svc.list(system_id)
        action_list = ActionBeanList(parse_obj_as(List[ActionBean], actions))
        action_list.fill_related_resource_type_name()

        return action_list

    def list_by_role(self, system_id: str, role) -> List[ActionBean]:
        action_list = self.list(system_id)
        scope_action_ids = RoleListQuery(role).list_scope_action_id(system_id)

        actions = action_list.filter_by_scope_action_ids(scope_action_ids)
        return actions

    def list_checked_action_by_role(self, system_id: str, role, checked_action_set: Set[str]) -> List[ActionBean]:
        """
        查询角色相关的操作列表, 并上标签
        """
        actions = self.list_by_role(system_id, role)
        for action in actions:
            action.tag = ActionTag.CHECKED.value if action.id in checked_action_set else ActionTag.UNCHECKED.value
        return actions

    def list_by_subject(self, system_id: str, role, subject: Subject) -> List[ActionBean]:
        """
        获取用户的操作列表
        """
        actions = self.list_by_role(system_id, role)
        action_list = ActionBeanList(actions)

        policies = self.policy_svc.list_by_subject(system_id, subject)
        action_expired_at = {policy.action_id: policy.expired_at for policy in policies}
        action_list.fill_expired_at_and_tag(action_expired_at)

        return action_list.actions

    def list_pre_application_actions(
        self, system_id: str, role, user_id: str, action_ids: List[str]
    ) -> List[ActionBean]:
        """
        获取用户预申请的操作列表
        """
        actions = self.list_by_subject(system_id, role, Subject(type=SubjectType.USER.value, id=user_id))

        action_set = set(action_ids)

        for action in actions:
            if action.id in action_set and action.tag == ActionTag.UNCHECKED.value:
                action.tag = ActionTag.CHECKED.value

        return actions

    def search(self, system_id: str, condition: ActionSearchCondition) -> List[ActionBean]:
        """搜索过滤某个系统下的操作"""
        action_list = self.list(system_id)
        # 搜索条件
        if condition.keyword:
            action_list = ActionBeanList(action_list.filter_by_name(condition.keyword))
        # 过滤条件
        if condition.action_group_id:
            from backend.biz.action_group import ActionGroupBiz

            actions = ActionGroupBiz().get_actions_by_frontend_id(
                system_id, action_list.actions, condition.action_group_id
            )
            action_list = ActionBeanList(actions)
        return action_list.actions


class RelatedResourceTypeForCheck(BaseModel):
    system_id: str = Field(alias="system")
    id: str = Field(alias="type")

    class Config:
        allow_population_by_field_name = True  # 支持alias字段同时传 type 与 id


class ActionForCheck(BaseModel):
    id: str = Field(alias="action_id")
    related_resource_types: List[RelatedResourceTypeForCheck]

    class Config:
        allow_population_by_field_name = True  # 支持alias字段同时传 action_id 与 id


class ActionCheckBiz:
    svc = ActionService()

    def check(self, system_id: str, actions: List[ActionForCheck]):
        """
        检查权限申请/模板创建的操作数据是否正确
        """
        action_list = self._get_action_list(system_id)

        for action in actions:
            self._check_action(action_list, action)

    def _get_action_list(self, system_id: str):
        svc_actions = self.svc.list(system_id)
        action_list = ActionList(svc_actions)
        return action_list

    def _check_action(self, action_list, action: ActionForCheck):
        svc_action = action_list.get(action.id)
        if not svc_action:
            raise error_codes.VALIDATE_ERROR.format("{} action not exists".format(action.id))
        self._check_action_related_resource_types(svc_action, action)

    def _check_action_related_resource_types(self, svc_action: Action, action: ActionForCheck):
        if len(action.related_resource_types) != len(svc_action.related_resource_types):
            raise error_codes.ACTION_VALIDATE_ERROR.format(
                "action `{}` related resource types wrong".format(action.id)
            )

        for index, rt in enumerate(action.related_resource_types):
            if index != svc_action.index_of_related_resource_type(rt.system_id, rt.id):
                raise error_codes.ACTION_VALIDATE_ERROR.format(
                    "action `{}` related resource types `{}` wrong".format(action.id, rt.id)
                )
