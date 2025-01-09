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
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Count

from backend.apps.policy.models import Policy as PolicyModel
from backend.apps.temporary_policy.models import TemporaryPolicy
from backend.common.error_codes import error_codes
from backend.common.time import PERMANENT_SECONDS
from backend.component import iam
from backend.service.constants import SubjectType
from backend.service.models import BackendThinPolicy, Policy, Subject, SystemCounter

logger = logging.getLogger("app")


class PolicyList:
    def __init__(self, policies: List[Policy]) -> None:
        self.policies = policies
        self._policy_dict = {p.action_id: p for p in policies}

    def get(self, action_id: str) -> Optional[Policy]:
        return self._policy_dict.get(action_id, None)

    @property
    def ids(self) -> List[int]:
        return [policy.policy_id for policy in self.policies]

    def pop_by_action_ids(self, action_ids: List[str]) -> List[Policy]:
        self.policies = [p for p in self.policies if p.action_id not in set(action_ids)]
        poped_policies = []
        for action_id in action_ids:
            policy = self._policy_dict.pop(action_id)
            poped_policies.append(policy)

        return poped_policies

    def extend_without_repeated(self, policies: List[Policy]) -> List[Policy]:
        """
        只新增不在已有列表中的策略
        """
        affected_policies = []
        for p in policies:
            if p.action_id in self._policy_dict:
                continue
            self._policy_dict[p.action_id] = p
            self.policies.append(p)
            # 顺便记录实际添加的策略
            affected_policies.append(p)

        return affected_policies


class BackendThinPolicyList:
    def __init__(self, policies: List[BackendThinPolicy]) -> None:
        self.policies = policies
        self._policy_dict = {policy.action_id: policy for policy in policies}

    def get(self, action_id: str) -> Optional[BackendThinPolicy]:
        return self._policy_dict.get(action_id, None)


class PolicyQueryService:
    """Policy Query Service"""

    def list_by_subject(
        self, system_id: str, subject: Subject, action_ids: Optional[List[str]] = None
    ) -> List[Policy]:
        """
        查询subject指定系统下的所有Policy
        """
        qs = PolicyModel.objects.filter(system_id=system_id, subject_type=subject.type, subject_id=subject.id)

        if action_ids is not None and len(action_ids) > 0:
            qs.filter(action_id__in=action_ids)

        return self._trans_from_queryset(system_id, subject, qs)

    def list_temporary_by_subject(self, system_id: str, subject: Subject) -> List[Policy]:
        """
        查询subject指定系统下的临时权限
        """
        qs = TemporaryPolicy.objects.filter(system_id=system_id, subject_type=subject.type, subject_id=subject.id)
        return [Policy.from_db_model(one, one.expired_at) for one in qs]

    def _trans_from_queryset(self, system_id: str, subject: Subject, queryset) -> List[Policy]:
        """
        db policy queryset 转换为List[Policy]
        """
        # 用户权限才有有效期，用户组与权限没有有效期的
        if subject.type == SubjectType.USER.value:
            backend_policy_list = new_backend_policy_list_by_subject(system_id, subject)
            policies = [
                Policy.from_db_model(one, backend_policy_list.get(one.action_id).expired_at)  # type: ignore
                for one in queryset
                if backend_policy_list.get(one.action_id)
            ]
            return policies

        return [Policy.from_db_model(one, PERMANENT_SECONDS) for one in queryset]

    def list_by_policy_ids(self, system_id: str, subject: Subject, policy_ids: List[int]) -> List[Policy]:
        """
        查询指定policy_ids的策略
        """
        qs = PolicyModel.objects.filter(
            system_id=system_id, subject_type=subject.type, subject_id=subject.id, id__in=policy_ids
        )
        return self._trans_from_queryset(system_id, subject, qs)

    def list_temporary_by_policy_ids(self, system_id: str, subject: Subject, policy_ids: List[int]) -> List[Policy]:
        """
        查询指定policy_ids的临时策略
        """
        qs = TemporaryPolicy.objects.filter(
            system_id=system_id, subject_type=subject.type, subject_id=subject.id, id__in=policy_ids
        )
        return [Policy.from_db_model(one, one.expired_at) for one in qs]

    def list_system_counter_by_subject(self, subject: Subject, hidden: bool = True) -> List[SystemCounter]:
        """
        查询subject有权限的系统-policy数量信息
        """
        qs = (
            PolicyModel.objects.filter(subject_type=subject.type, subject_id=subject.id)
            .values("system_id")
            .annotate(count=Count("system_id"))
        )

        if hidden:
            return [
                SystemCounter(id=one["system_id"], count=one["count"])
                for one in qs
                if one["system_id"] not in settings.HIDDEN_SYSTEM_LIST
            ]  # NOTE: 屏蔽掉需要隐藏的系统

        return [SystemCounter(id=one["system_id"], count=one["count"]) for one in qs]

    def list_temporary_system_counter_by_subject(self, subject: Subject) -> List[SystemCounter]:
        """
        查询subject有权限的系统-临时policy数量信息
        """
        qs = (
            TemporaryPolicy.objects.filter(subject_type=subject.type, subject_id=subject.id)
            .values("system_id")
            .annotate(count=Count("system_id"))
        )

        return [
            SystemCounter(id=one["system_id"], count=one["count"])
            for one in qs
            if one["system_id"] not in settings.HIDDEN_SYSTEM_LIST
        ]  # NOTE: 屏蔽掉需要隐藏的系统

    def get_policy_system_by_id(self, policy_id: int, subject: Subject) -> str:
        """根据策略ID获取system"""
        try:
            p = PolicyModel.objects.get(id=policy_id, subject_type=subject.type, subject_id=subject.id)
        except PolicyModel.DoesNotExist:
            raise error_codes.NOT_FOUND_ERROR.format("saas policy not found, id=%d", policy_id)

        return p.system_id

    def get_policy_by_id(self, policy_id: int, subject: Subject) -> Tuple[str, Policy]:
        """
        获取指定的Policy
        """
        try:
            db_policy = PolicyModel.objects.get(id=policy_id, subject_type=subject.type, subject_id=subject.id)
        except PolicyModel.DoesNotExist:
            raise error_codes.NOT_FOUND_ERROR.format("saas policy not found, id=%d", policy_id)

        # 用户策略需要有有效期，用户组策略默认是永久有效
        expired_at = PERMANENT_SECONDS
        if subject.type == SubjectType.USER.value:
            # 后台查询
            backend_policy_list = new_backend_policy_list_by_subject(db_policy.system_id, subject)
            if not backend_policy_list.get(db_policy.action_id):
                raise error_codes.NOT_FOUND_ERROR.format(
                    "backend policy not found, subject=%s, system_id=%s, action_id=%s" %
                    (subject, db_policy.system_id, db_policy.action_id)
                )
            expired_at = backend_policy_list.get(db_policy.action_id).expired_at  # type: ignore

        return db_policy.system_id, Policy.from_db_model(db_policy, expired_at)

    def list_backend_policy_before_expired_at(self, expired_at: int, subject: Subject) -> List[BackendThinPolicy]:
        """
        查询指定过期事件之前的Policy
        """
        backend_policies = iam.list_policy(subject.type, subject.id, expired_at)
        return [BackendThinPolicy(**policy) for policy in backend_policies]

    def get_action_id_dict(self, subject: Subject, action_ids: List[str]) -> Dict[Tuple[str, str], int]:
        """
        获取操作与saas policy id的dict

        key: tuple(system_id, action_id)
        value: saas policy id
        """
        policies = PolicyModel.objects.filter(
            subject_type=subject.type, subject_id=subject.id, action_id__in=action_ids
        ).only("system_id", "action_id", "id")
        return {(p.system_id, p.action_id): p.id for p in policies}

    def new_policy_list_by_subject(self, system_id: str, subject: Subject) -> PolicyList:
        return PolicyList(self.list_by_subject(system_id, subject))


def new_backend_policy_list_by_subject(
    system_id: str, subject: Subject, template_id: int = 0
) -> BackendThinPolicyList:
    """
    获取后端的Policy List
    Note: 只获取ABAC策略
    """
    backend_policies = iam.list_system_policy(system_id, subject.type, subject.id, template_id)
    return BackendThinPolicyList([BackendThinPolicy(**policy) for policy in backend_policies])
