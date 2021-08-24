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
from datetime import datetime
from itertools import groupby
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _
from pydantic import BaseModel, parse_obj_as
from rest_framework import serializers

from backend.apps.group.models import Group, GroupAuthorizeLock
from backend.apps.policy.models import Policy as PolicyModel
from backend.apps.role.models import Role, RoleRelatedObject
from backend.apps.template.models import PermTemplatePolicyAuthorized, PermTemplatePreUpdateLock
from backend.biz.policy import PolicyBean, PolicyBeanList, PolicyOperationBiz
from backend.biz.resource import ResourceBiz
from backend.biz.role import RoleAuthorizationScopeChecker, RoleSubjectScopeChecker
from backend.biz.template import TemplateBiz, TemplateCheckBiz
from backend.common.error_codes import APIException, CodeException, error_codes
from backend.common.time import PERMANENT_SECONDS, expired_at_display
from backend.long_task.constants import TaskType
from backend.long_task.models import TaskDetail
from backend.long_task.task import TaskFactory
from backend.service.constants import RoleRelatedObjectType, SubjectType
from backend.service.engine import EngineService
from backend.service.group import GroupCreate, GroupMemberExpiredAt, GroupService, SubjectGroup
from backend.service.group_saas_attribute import GroupAttributeService
from backend.service.models import Policy, Subject
from backend.service.policy.query import PolicyQueryService
from backend.service.role import RoleService, UserRole
from backend.service.system import SystemService
from backend.service.template import TemplateService
from backend.util.time import utc_string_to_local
from backend.util.uuid import gen_uuid

from .action import ActionCheckBiz, ActionForCheck
from .subject import SubjectInfoList


class GroupSystemCounterBean(BaseModel):
    id: str
    name: str
    name_en: str

    custom_policy_count: int = 0
    template_count: int = 0


class SubjectGroupBean(BaseModel):
    id: int
    name: str
    description: str

    expired_at: int
    expired_at_display: str
    created_time: datetime

    # 从部门继承的信息
    department_id: int = 0
    department_name: str = ""


class GroupMemberBean(BaseModel):
    type: str
    id: str
    name: str = ""
    full_name: str = ""
    member_count: int = 0

    expired_at: int
    expired_at_display: str
    created_time: datetime

    # 从部门继承的信息
    department_id: int = 0
    department_name: str = ""


class GroupRoleDict(BaseModel):
    data: Dict[int, UserRole]

    def get(self, group_id: int) -> Optional[UserRole]:
        return self.data.get(group_id)


class GroupMemberExpiredAtBean(GroupMemberExpiredAt):
    pass


class GroupCreateBean(GroupCreate):
    readonly: bool = True


class GroupTemplateGrantBean(BaseModel):
    system_id: str
    template_id: int
    policies: List[PolicyBean]


class GroupBiz:
    policy_query_svc = PolicyQueryService()
    template_svc = TemplateService()
    system_svc = SystemService()
    group_svc = GroupService()
    group_attribute_svc = GroupAttributeService()
    engine_svc = EngineService()
    role_svc = RoleService()

    # TODO 这里为什么是biz?
    action_check_biz = ActionCheckBiz()
    policy_operation_biz = PolicyOperationBiz()
    template_biz = TemplateBiz()
    resource_biz = ResourceBiz()
    template_check_biz = TemplateCheckBiz()

    # 直通的方法
    add_members = GroupService.__dict__["add_members"]
    remove_members = GroupService.__dict__["remove_members"]
    update = GroupService.__dict__["update"]
    get_member_count_before_expired_at = GroupService.__dict__["get_member_count_before_expired_at"]
    list_exist_groups_before_expired_at = GroupService.__dict__["list_exist_groups_before_expired_at"]
    batch_get_attributes = GroupAttributeService.__dict__["batch_get_attributes"]

    def create_and_add_members(
        self, role_id: int, name: str, description: str, creator: str, subjects: List[Subject], expired_at: int
    ) -> Group:
        """
        创建用户组
        """
        with transaction.atomic():
            group = self.group_svc.create(name, description, creator)
            RoleRelatedObject.objects.create_group_relation(role_id, group.id)
            if subjects:
                self.group_svc.add_members(group.id, subjects, expired_at)

        return group

    def batch_create(self, role_id: int, infos: List[GroupCreateBean], creator: str) -> List[Group]:
        """
        批量创建用户组
        用于管理api
        """
        with transaction.atomic():
            groups = self.group_svc.batch_create(parse_obj_as(List[GroupCreate], infos), creator)
            group_attrs = {group.id: {"readonly": info.readonly} for group, info in zip(groups, infos)}
            self.group_attribute_svc.batch_set_attributes(group_attrs)
            RoleRelatedObject.objects.batch_create_group_relation(role_id, [group.id for group in groups])

        return groups

    def list_system_counter(self, group_id: int) -> List[GroupSystemCounterBean]:
        """
        查询用户组授权的系统信息, 返回自定义权限/模板的数量
        """
        subject = Subject(type=SubjectType.GROUP.value, id=str(group_id))
        policy_systems_count = self.policy_query_svc.list_system_counter_by_subject(subject)
        template_system_count = self.template_svc.list_system_counter_by_subject(subject)
        policy_system_count_dict = {system.id: system.count for system in policy_systems_count}
        template_system_count_dict = {system.id: system.count for system in template_system_count}

        if len(policy_systems_count) == 0 and len(template_system_count) == 0:
            return []

        systems = self.system_svc.list()
        group_systems: List[GroupSystemCounterBean] = []
        for system in systems:
            if system.id not in policy_system_count_dict and system.id not in template_system_count_dict:
                continue

            group_system = GroupSystemCounterBean.parse_obj(system)

            # 填充系统自定义权限策略数量与模板数量
            if system.id in policy_system_count_dict:
                group_system.custom_policy_count = policy_system_count_dict.get(system.id)

            if system.id in template_system_count_dict:
                group_system.template_count = template_system_count_dict.get(system.id)

            group_systems.append(group_system)

        return group_systems

    def check_update_policies_resource_name(
        self, system_id: str, template_id: int, policies: List[PolicyBean], subject: Subject
    ):
        # 查询已授权的策略数据
        if template_id == 0:
            old_policies = parse_obj_as(List[PolicyBean], self.policy_query_svc.list_by_subject(system_id, subject))
        else:
            authorized_template = PermTemplatePolicyAuthorized.objects.get_by_subject_template(subject, template_id)
            old_policies = parse_obj_as(List[PolicyBean], authorized_template.data["actions"])

        # 筛选出新增的策略数据
        added_policy_list = PolicyBeanList(system_id, policies).sub(PolicyBeanList(system_id, old_policies))

        # 校验新增数据资源实例名称是否正确
        added_policy_list.check_resource_name()

    def preprocess_group_policies(self, role, system_id: str, policies: List[PolicyBean]):
        """
        用户组的policies预处理
        """
        # 校验权限是否满足角色的管理范围
        scope_checker = RoleAuthorizationScopeChecker(role)
        scope_checker.check_policies(system_id, policies)

        self.action_check_biz.check(system_id, [ActionForCheck.parse_obj(p.dict()) for p in policies])

        policy_list = PolicyBeanList(system_id, policies, need_ignore_path=True)

        # 设置过期时间为永久
        for p in policy_list.policies:
            p.set_expired_at(PERMANENT_SECONDS)

        return policy_list.policies

    def update_policies(self, role, group_id: int, system_id: str, template_id: int, policies: List[PolicyBean]):
        """
        更新用户组单个权限
        """
        subject = Subject(type=SubjectType.GROUP.value, id=str(group_id))
        self.check_update_policies_resource_name(system_id, template_id, policies, subject)
        policies = self.preprocess_group_policies(role, system_id, policies)

        # 自定义权限
        if template_id == 0:
            self.policy_operation_biz.update(system_id, subject, policies)
        # 权限模板权限
        else:
            self.template_svc.update_template_auth(subject, template_id, parse_obj_as(List[Policy], policies))

    def _convert_to_subject_group_beans(self, relations: List[SubjectGroup]) -> List[SubjectGroupBean]:
        """
        转换类型
        """
        groups = Group.objects.filter(id__in=[int(one.id) for one in relations if one.type == SubjectType.GROUP.value])
        relation_dict = {one.id: one for one in relations}
        relation_beans: List[SubjectGroupBean] = []
        for group in groups:
            relation = relation_dict.get(str(group.id))
            if not relation:
                continue
            relation_beans.append(
                SubjectGroupBean(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    expired_at=relation.policy_expired_at,
                    expired_at_display=expired_at_display(relation.policy_expired_at),
                    created_time=utc_string_to_local(relation.created_at),
                    department_id=relation.department_id,
                    department_name=relation.department_name,
                )
            )
        return relation_beans

    def list_subject_group(self, subject: Subject, is_recursive: bool = False) -> List[SubjectGroupBean]:
        """
        查询subject所属的用户组
        """
        relations = self.group_svc.list_subject_group(subject, is_recursive)
        return self._convert_to_subject_group_beans(relations)

    def list_subject_group_before_expired_at(self, subject: Subject, expired_at: int) -> List[SubjectGroupBean]:
        """
        查询指定过期时间之前的用户组
        """
        relations = self.group_svc.list_subject_group_before_expired_at(subject, expired_at)
        return self._convert_to_subject_group_beans(relations)

    def update_members_expired_at(self, group_id: int, members: List[GroupMemberExpiredAtBean]):
        """
        更新用户组成员的过期时间
        """
        self.group_svc.update_members_expired_at(group_id, parse_obj_as(List[GroupMemberExpiredAt], members))

    def delete(self, group_id: int):
        """
        删除用户组
        """
        if GroupAuthorizeLock.objects.filter(group_id=group_id).exists():
            raise error_codes.VALIDATE_ERROR.format(_("用户组正在授权, 不能删除!"))

        subject = Subject(type=SubjectType.GROUP.value, id=str(group_id))
        with transaction.atomic():
            # 删除分级管理员与用户组的关系
            RoleRelatedObject.objects.delete_group_relation(group_id)
            # 删除权限模板与用户组的关系
            self.template_biz.delete_template_auth_by_subject(subject)
            # 删除所有的自定义策略
            PolicyModel.objects.filter(subject_type=subject.type, subject_id=subject.id).delete()
            # 删除用户组的属性
            self.group_attribute_svc.batch_delete_attributes([group_id])
            # 删除用户组本身
            self.group_svc.delete(group_id)

    def _convert_to_group_members(self, relations: List[SubjectGroup]) -> List[GroupMemberBean]:
        subjects = parse_obj_as(List[Subject], relations)
        subject_info_list = SubjectInfoList(subjects)

        # 组合数据结构
        group_member_beans = []
        for subject, relation in zip(subjects, relations):
            subject_info = subject_info_list.get(subject)
            if not subject_info:
                continue

            group_member_bean = GroupMemberBean(
                expired_at=relation.policy_expired_at,
                expired_at_display=expired_at_display(relation.policy_expired_at),
                created_time=utc_string_to_local(relation.created_at),
                department_id=relation.department_id,
                department_name=relation.department_name,
                **subject_info.dict(),
            )
            group_member_beans.append(group_member_bean)

        return group_member_beans

    def list_paging_group_member(self, group_id: int, limit: int, offset: int) -> Tuple[int, List[GroupMemberBean]]:
        """分页查询用户组成员，并给成员填充name/full_named等相关信息"""
        count, relations = self.group_svc.list_paging_group_member(group_id, limit, offset)
        return count, self._convert_to_group_members(relations)

    def list_paging_members_before_expired_at(
        self, group_id: int, expired_at: int, limit: int = 10, offset: int = 0
    ) -> Tuple[int, List[GroupMemberBean]]:
        """
        分页查询用户组过期的成员
        """
        count, relations = self.group_svc.list_paging_members_before_expired_at(group_id, expired_at, limit, offset)
        return count, self._convert_to_group_members(relations)

    def list_pre_application_groups(self, policy_list: PolicyBeanList) -> List[int]:
        """
        获取用户预申请的用户组列表
        """
        system_id, policies = policy_list.system_id, policy_list.policies

        try:
            policy_resources = self.engine_svc.gen_search_policy_resources(policies)
            # 填充资源实例的属性
            for pr in policy_resources:
                if len(pr.resources) != 0:
                    self._fill_resources_attribute(pr.resources)

            results = self.engine_svc.query_subjects_by_policy_resources(
                system_id, policy_resources, SubjectType.GROUP.value
            )
        except APIException:
            return []

        # 取结果的交集
        subject_id_set = None
        for res in results:
            ids = {subject["id"] for subject in res}
            if subject_id_set is None:
                subject_id_set = ids
            else:
                subject_id_set = subject_id_set & ids

        return [int(_id) for _id in subject_id_set] if subject_id_set else []

    def _fill_resources_attribute(self, resources: List[Dict[str, Any]]):
        """
        用户组通过policy查询subjects的资源填充属性
        """
        need_fetch_resources = []
        for resource in resources:
            if resource["id"] != "*" and not resource["attribute"]:
                need_fetch_resources.append(resource)

        if not need_fetch_resources:
            return

        for key, parts in groupby(need_fetch_resources, key=lambda resource: (resource["system"], resource["type"])):
            self._exec_fill_resources_attribute(key[0], key[1], list(parts))

    def _exec_fill_resources_attribute(self, system_id, resource_type_id, resources):
        # 查询属性
        resource_ids = list({resource["id"] for resource in resources})
        resource_info_dict = self.resource_biz.fetch_auth_attributes(
            system_id, resource_type_id, resource_ids, raise_api_exception=False
        )
        # 填充属性
        for resource in resources:
            _id = resource["id"]
            if not resource_info_dict.has(_id):
                continue
            attrs = resource_info_dict.get_attributes(_id, ignore_none_value=True)
            # 填充
            resource["attribute"] = attrs

    def _check_before_grant(self, group: Group, templates: List[GroupTemplateGrantBean]):
        """
        检查用户组是否满足授权条件
        """
        # 权限模板
        template_ids = [template.template_id for template in templates if template.template_id != 0]
        # 自定义权限涉及的系统
        custom_action_system_ids = [template.system_id for template in templates if template.template_id == 0]
        # 判断是否有权限模板正在同步更新
        if PermTemplatePreUpdateLock.objects.filter(template_id__in=template_ids).exists():
            raise error_codes.VALIDATE_ERROR.format(_("部分权限模板正在更新, 不能授权!"))
        # 判断该用户组在长时任务里是否正在添加涉及到的权限模板和自定义权限
        if (
            GroupAuthorizeLock.objects.filter(group_id=group.id)
            .filter(Q(template_id__in=template_ids) | (Q(template_id=0) & Q(system_id__in=custom_action_system_ids)))
            .exists()
        ):
            raise error_codes.VALIDATE_ERROR.format(_("部分权限模板或自定义权限已经在授权中, 不能重复授权!"))

    def _valid_grant_actions_not_exists(self, subject: Subject, system_id, action_ids: List[str]):
        """
        校验授权的操作没有重复授权
        """
        policy_list = self.policy_query_svc.new_policy_list_by_subject(system_id, subject)
        for action_id in action_ids:
            if policy_list.get(action_id):
                raise error_codes.VALIDATE_ERROR.format(_("系统: {} 的操作: {} 权限已存在").format(system_id, action_id))

    def _gen_grant_lock(
        self, subject: Subject, template: GroupTemplateGrantBean, role: Role, uuid: str
    ) -> GroupAuthorizeLock:
        """
        生成用户组授权的信息锁
        """
        action_ids = [p.action_id for p in template.policies]
        if template.template_id != 0:
            # 检查操作列表是否与模板一致
            self.template_check_biz.check_add_member(template.template_id, subject, action_ids)
        else:
            # 检查操作列表是否为新增自定义权限
            self._valid_grant_actions_not_exists(subject, template.system_id, action_ids)

        try:
            # 校验资源的名称是否一致
            template_policy_list = PolicyBeanList(system_id=template.system_id, policies=template.policies)
            template_policy_list.check_resource_name()
            # 检查策略是否在role的授权范围内
            scope_checker = RoleAuthorizationScopeChecker(role)
            scope_checker.check_policies(template.system_id, template.policies)
        except CodeException as e:
            raise error_codes.VALIDATE_ERROR.format(
                _("系统: {} 模板: {} 校验错误: {}").format(template.system_id, template.template_id, e.message), replace=True
            )

        # 设置过期时间为永久
        for p in template.policies:
            p.set_expired_at(PERMANENT_SECONDS)

        lock = GroupAuthorizeLock(
            template_id=template.template_id, group_id=int(subject.id), system_id=template.system_id, key=uuid
        )
        lock.data = {"actions": [p.dict() for p in template.policies]}  # type: ignore
        return lock

    def grant(self, role: Role, group: Group, templates: List[GroupTemplateGrantBean]):
        """
        用户组授权
        """
        # 检查用户组是否满足授权条件
        self._check_before_grant(group, templates)

        subject = Subject(type=SubjectType.GROUP.value, id=str(group.id))

        locks = []
        uuid = gen_uuid()
        for template in templates:
            # 生成授权数据锁
            lock = self._gen_grant_lock(subject, template, role, uuid)
            locks.append(lock)

        with transaction.atomic():
            GroupAuthorizeLock.objects.bulk_create(locks, batch_size=100)
            task = TaskDetail.create(TaskType.GROUP_AUTHORIZATION.value, [subject.dict(), uuid])

        # 执行授权流程
        TaskFactory().delay(task.id)

    def get_group_role_dict_by_ids(self, group_ids: List[int]) -> GroupRoleDict:
        """
        获取group_id: UserRole的字典
        """
        related_objects = RoleRelatedObject.objects.filter(
            object_type=RoleRelatedObjectType.GROUP.value, object_id__in=group_ids
        )

        # 查询所有关联的role对象
        role_dict = {one.id: one for one in self.role_svc.list_by_ids(list({ro.role_id for ro in related_objects}))}

        # 生成用户组id -> role对象的映射
        return GroupRoleDict(
            data={ro.object_id: role_dict.get(ro.role_id) for ro in related_objects if role_dict.get(ro.role_id)}
        )


class GroupCheckBiz:
    svc = GroupService()
    policy_svc = PolicyQueryService()

    def check_member_count(self, group_id: int, new_member_count: int):
        """
        检查用户组成员数量未超限
        """
        group = Group.objects.get(id=group_id)
        exists_count = group.user_count + group.department_count
        member_limit = settings.SUBJECT_AUTHORIZATION_LIMIT.get("group_member_limit", 1000)
        if exists_count + new_member_count > member_limit:
            raise error_codes.VALIDATE_ERROR.format(
                _("用户组({})已有{}个成员，不可再添加{}个成员，否则超出用户组最大成员数量{}的限制").format(
                    group.name, exists_count, new_member_count, member_limit
                ),
                True,
            )

    def check_subject_group_limit(self, subject: Subject):
        """
        检查subject授权的group数量是否超限
        """
        limit = settings.SUBJECT_AUTHORIZATION_LIMIT["default_subject_group_limit"]
        relations = self.svc.list_subject_group(subject)
        if len(relations) >= limit:
            raise serializers.ValidationError(
                _("被授权对象: {} {} 加入的用户组数量已超过最大值 {}").format(subject.type, subject.id, limit)
            )

    def check_role_group_name_unique(self, role_id: int, name: str, group_id: int = 0):
        """
        检查角色的用户组名字是否已存在
        """
        role_group_ids = RoleRelatedObject.objects.list_role_object_ids(role_id, RoleRelatedObjectType.GROUP.value)
        if group_id in role_group_ids:
            role_group_ids.remove(group_id)
        if Group.objects.filter(name=name, id__in=role_group_ids).exists():
            raise error_codes.CONFLICT_ERROR.format(_("用户组名称已存在"))

    def batch_check_role_group_names_unique(self, role_id: int, names: List[str]):
        """
        批量检查角色的用户组名字是否唯一
        """
        role_group_ids = RoleRelatedObject.objects.list_role_object_ids(role_id, RoleRelatedObjectType.GROUP.value)
        if Group.objects.filter(name__in=names, id__in=role_group_ids).exists():
            raise error_codes.CONFLICT_ERROR.format(_("用户组名称已存在"))

    def check_role_subject_scope(self, role, subjects: List[Subject]):
        """
        检查role的subject scope
        """
        scope_checker = RoleSubjectScopeChecker(role)
        scope_checker.check(subjects)

    def check_grant_policies_without_update(self, group_id: int, system_id: str, policies: List[PolicyBean]):
        """
        检查用户组自定义授权时只能新增不能修改
        """
        subject = Subject(type=SubjectType.GROUP.value, id=str(group_id))
        policies = self.policy_svc.list_by_subject(system_id, subject)
        policy_list = PolicyBeanList(system_id, parse_obj_as(List[PolicyBean], policies))
        for p in policies:
            if policy_list.get(p.action_id):
                raise error_codes.VALIDATE_ERROR.format(
                    _("系统: {} 的操作: {} 权限已存在, 只能新增, 不能修改!").format(system_id, p.action_id)
                )
