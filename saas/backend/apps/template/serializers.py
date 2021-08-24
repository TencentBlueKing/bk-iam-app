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
from typing import List

from django.db.models.query import QuerySet
from django.utils.translation import gettext as _
from pydantic.tools import parse_obj_as
from rest_framework import serializers

from backend.apps.action.serializers import ActionSLZ
from backend.apps.application.serializers import SystemInfoSLZ
from backend.apps.group.models import Group
from backend.apps.policy.serializers import BasePolicyActionSLZ
from backend.apps.template.models import PermTemplate, PermTemplatePolicyAuthorized, PermTemplatePreUpdateLock
from backend.biz.policy import PolicyBean, PolicyBeanList
from backend.biz.system import SystemBiz
from backend.service.constants import SubjectType

from .constants import TemplateTag


class TemplateCreateSLZ(serializers.Serializer):
    name = serializers.CharField(label="模板名称", max_length=128)
    system_id = serializers.CharField(label="系统id", max_length=32)
    action_ids = serializers.ListField(label="操作策略", child=serializers.CharField(), required=True, allow_empty=False)
    description = serializers.CharField(label="描述", max_length=255, allow_blank=True)

    def validate(self, data):
        if len(data["action_ids"]) != len(set(data["action_ids"])):
            raise serializers.ValidationError("action_ids must not repeat")

        return data


class TemplateIdSLZ(serializers.Serializer):
    """
    模板id
    """

    id = serializers.IntegerField(label="模板id")


class TemplateListSLZ(serializers.ModelSerializer):
    system = serializers.SerializerMethodField(label="系统信息")
    tag = serializers.SerializerMethodField(label="标签")
    is_lock = serializers.SerializerMethodField(label="是否锁定")

    def __init__(self, *args, **kwargs):
        self.authorized_template = kwargs.pop("authorized_template", set())
        super().__init__(*args, **kwargs)
        self._system_list = SystemBiz().new_system_list()

        self._lock_ids = set()
        if isinstance(self.instance, (QuerySet, list)) and self.instance:
            template_ids = [template.id for template in self.instance]
            self._lock_ids = set(
                PermTemplatePreUpdateLock.objects.filter(template_id__in=template_ids).values_list(
                    "template_id", flat=True
                )
            )

    class Meta:
        model = PermTemplate
        fields = (
            "id",
            "system",
            "name",
            "description",
            "subject_count",
            "tag",
            "is_lock",
            "updater",
            "updated_time",
            "creator",
            "created_time",
        )

    def get_system(self, obj):
        system_id = obj.system_id
        system = self._system_list.get(system_id)

        return {
            "id": system_id,
            "name": system.name if system else "",
            "name_en": system.name_en if system else "",
        }

    def get_tag(self, obj):
        return TemplateTag.CHECKED.value if obj.id in self.authorized_template else TemplateTag.UNCHECKED.value

    def get_is_lock(self, obj):
        return obj.id in self._lock_ids


class TemplateListSchemaSLZ(serializers.ModelSerializer):
    system = SystemInfoSLZ(label="系统信息", required=True)
    tag = serializers.CharField(label="标签")
    is_lock = serializers.BooleanField(label="是否锁定")

    class Meta:
        model = PermTemplate
        fields = ("id", "system", "name", "description", "subject_count", "tag", "is_lock", "updater", "updated_time")


class TemplateRetrieveSchemaSLZ(TemplateListSchemaSLZ):
    actions = serializers.ListField(child=ActionSLZ())

    class Meta:
        model = PermTemplate
        fields = ("id", "system", "name", "actions", "description", "subject_count", "updater", "updated_time")


class TemplateMemberListSLZ(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(label="成员类型", source="subject_type")
    id = serializers.ReadOnlyField(label="成员ID", source="subject_id")

    class Meta:
        model = PermTemplatePolicyAuthorized
        fields = (
            "template_id",
            "type",
            "id",
            "system_id",
            "updated_time",
        )


class TemplateMemberListSchemaSLZ(TemplateMemberListSLZ):
    name = serializers.CharField(label="成员名称")
    full_name = serializers.CharField(label="全名(仅部门有)")
    member_count = serializers.IntegerField(label="成员数量(仅部门和用户组有)")

    class Meta:
        model = PermTemplatePolicyAuthorized
        fields = (
            "template_id",
            "type",
            "id",
            "system_id",
            "full_name",
            "member_count",
            "updated_time",
            "name",
        )


class TemplateMemberSLZ(serializers.Serializer):
    type = serializers.ChoiceField(label="成员类型", choices=[(SubjectType.GROUP.value, _("用户组"))])
    id = serializers.CharField(label="成员id")


class TemplateDeleteMemberSLZ(serializers.Serializer):
    members = serializers.ListField(
        label="成员列表", child=TemplateMemberSLZ(label="成员"), required=True, allow_empty=False
    )


class TemplateDetailQuerySLZ(serializers.Serializer):
    grouping = serializers.BooleanField(label="是否分组", required=False, default=True)


class TemplatePartialUpdateSLZ(serializers.Serializer):
    name = serializers.CharField(label="模板名称", max_length=128)
    description = serializers.CharField(label="描述", max_length=255, allow_blank=True)


class TemplatePreUpdateSLZ(serializers.Serializer):
    action_ids = serializers.ListField(label="操作ID", child=serializers.CharField(), required=True, allow_empty=False)


class GroupAuthorationPreUpdateSLZ(serializers.Serializer):
    id = serializers.IntegerField(label="用户组id")
    actions = serializers.ListField(
        label="操作策略", child=BasePolicyActionSLZ(label="策略"), required=True, allow_empty=False
    )

    def validate(self, data):
        action_ids = {action["id"] for action in data["actions"]}
        if len(data["actions"]) != len(action_ids):
            raise serializers.ValidationError("actions must not repeat")
        return data


class TemplateGroupAuthorationPreUpdateSLZ(serializers.Serializer):
    """
    用户组同步信息预提交结构
    """

    groups = serializers.ListField(
        label="用户组更新信息", child=GroupAuthorationPreUpdateSLZ(), required=True, allow_empty=False
    )


class GroupCopyActionInstanceSLZ(serializers.Serializer):
    """
    用户组列表从已授权的操作中copy实例
    """

    action_id = serializers.CharField(label="新操作ID")
    clone_from_action_id = serializers.CharField(label="复制的操作ID")
    group_ids = serializers.ListField(
        label="用户组ID列表", child=serializers.IntegerField(), required=True, allow_empty=False
    )


class TemplatePreUpdateGroupSyncSchemaSLZ(TemplateListSchemaSLZ):
    actions = serializers.ListField(child=ActionSLZ())

    class Meta:
        model = PermTemplate
        fields = ("id", "system", "name", "actions", "description", "subject_count", "updater", "updated_time")


class TemplateGroupPreViewSLZ(serializers.ModelSerializer):
    delete_actions = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "delete_actions",
        )

    def __init__(self, *args, **kwargs):
        authorized_templates = kwargs.pop("authorized_templates")
        self.authorized_template_dict = {int(one.subject_id): one for one in authorized_templates}
        self.delete_action_ids = kwargs.pop("delete_action_ids")
        super().__init__(*args, **kwargs)

    def get_delete_actions(self, obj):
        authorized_template = self.authorized_template_dict[obj.id]
        policy_list = PolicyBeanList(
            authorized_template.system_id, parse_obj_as(List[PolicyBean], authorized_template.data["actions"])
        )
        delete_policies = [p for p in policy_list.policies if p.action_id in self.delete_action_ids]
        delete_policy_list = PolicyBeanList(
            authorized_template.system_id, delete_policies, need_fill_empty_fields=True
        )
        return [p.dict() for p in delete_policy_list.policies]


class TemplateGroupPreViewSchemaSLZ(TemplateGroupPreViewSLZ):
    delete_actions = serializers.ListField(child=BasePolicyActionSLZ())

    def __init__(self, *args, **kwargs):
        serializers.ModelSerializer.__init__(self, *args, **kwargs)


class TemplatePreUpdateSchemaSLZ(serializers.Serializer):
    action_ids = serializers.ListField(label="操作策略", child=serializers.CharField(), required=True, allow_empty=False)
