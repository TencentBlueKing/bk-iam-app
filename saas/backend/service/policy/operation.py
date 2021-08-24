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
from typing import List, Optional

from django.db import transaction

from backend.apps.policy.models import Policy as PolicyModel
from backend.component import iam
from backend.util.json import json_dumps

from ..models import Policy, PolicyIDExpiredAt, Subject
from .query import PolicyList, new_backend_policy_list_by_subject


class PolicyOperationService:
    def delete_by_ids(self, system_id: str, subject: Subject, policy_ids: List[int]):
        """
        删除指定policy_id的策略
        """
        with transaction.atomic():
            self._delete_db_policies(system_id, subject, policy_ids)
            iam.delete_policies(system_id, subject.type, subject.id, policy_ids)

    def alter(
        self,
        system_id: str,
        subject: Subject,
        create_policies: Optional[List[Policy]] = None,
        update_policies: Optional[List[Policy]] = None,
        delete_policy_ids: Optional[List[int]] = None,
    ):
        """
        变更subject的Policies
        """
        create_policies = create_policies or []
        update_policies = update_policies or []
        delete_policy_ids = delete_policy_ids or []

        with transaction.atomic():
            if create_policies:
                self._create_db_policies(system_id, subject, create_policies)

            if update_policies:
                self._update_db_policies(system_id, subject, update_policies)

            if delete_policy_ids:
                self._delete_db_policies(system_id, subject, delete_policy_ids)

            if create_policies or update_policies or delete_policy_ids:
                self._alter_backend_policies(system_id, subject, create_policies, update_policies, delete_policy_ids)

        if create_policies:
            self._sync_db_policy_id(system_id, subject)

    def _alter_backend_policies(
        self,
        system_id: str,
        subject: Subject,
        create_policies: List[Policy],
        update_policies: List[Policy],
        delete_policy_ids: List[int],
    ):
        """
        执行对policies的创建, 更新, 删除操作, 调用后端批量操作接口
        """
        # 组装backend变更策略的数据
        backend_create_policies = [p.to_backend_dict() for p in create_policies]
        backend_update_policies = [p.to_backend_dict() for p in update_policies]

        return iam.alter_policies(
            system_id, subject.type, subject.id, backend_create_policies, backend_update_policies, delete_policy_ids
        )

    def _create_db_policies(self, system_id: str, subject: Subject, policies: List[Policy]) -> None:
        """
        创建新的策略
        """
        db_policies = [p.to_db_model(system_id, subject) for p in policies]
        PolicyModel.objects.bulk_create(db_policies, batch_size=100)

    def _update_db_policies(self, system_id: str, subject: Subject, policies: List[Policy]) -> None:
        """
        更新已有的策略
        """
        policy_list = PolicyList(policies)

        db_policies = PolicyModel.objects.filter(
            subject_id=subject.id, subject_type=subject.type, system_id=system_id, policy_id__in=policy_list.ids
        ).only("id", "action_id")

        # 使用主键更新, 避免死锁
        for p in db_policies:
            update_policy = policy_list.get(p.action_id)
            if not update_policy:
                continue
            PolicyModel.objects.filter(id=p.id).update(
                _resources=json_dumps([rt.dict() for rt in update_policy.related_resource_types])
            )

    def _delete_db_policies(self, system_id: str, subject: Subject, policy_ids: List[int]):
        """
        删除db Policies
        """
        PolicyModel.objects.filter(
            system_id=system_id, subject_type=subject.type, subject_id=subject.id, policy_id__in=policy_ids
        ).delete()

    def _sync_db_policy_id(self, system_id: str, subject: Subject) -> None:
        """
        同步SaaS-后端策略的policy_id
        """
        db_policies = PolicyModel.objects.filter(
            system_id=system_id, subject_type=subject.type, subject_id=subject.id, policy_id=0
        ).defer("_resources", "_environment")

        if len(db_policies) == 0:
            return

        backend_policy_list = new_backend_policy_list_by_subject(system_id, subject)
        for p in db_policies:
            backend_policy = backend_policy_list.get(p.action_id)
            if not backend_policy:
                continue
            p.policy_id = backend_policy.id

        PolicyModel.objects.bulk_update(db_policies, fields=["policy_id"], batch_size=100)

    def renew(self, subject: Subject, thin_policies: List[PolicyIDExpiredAt]):
        """
        权策续期
        """
        iam.update_policy_expired_at(subject.type, subject.id, [one.dict() for one in thin_policies])
