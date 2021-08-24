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

from redis.exceptions import RedisError

from backend.component import iam, resource_provider
from backend.util.basic import chunked
from backend.util.cache import redis_region, region

from .models import (
    ResourceAttribute,
    ResourceAttributeValue,
    ResourceInstanceBaseInfo,
    ResourceInstanceInfo,
    ResourceTypeProviderConfig,
    SystemProviderConfig,
)

# 只暴露ResourceProvider，其他只是辅助ResourceProvider的
__all__ = ["ResourceProvider"]

logger = logging.getLogger(__name__)


class SystemProviderConfigService:
    """提供系统配置"""

    @region.cache_on_arguments(expiration_time=60)  # 缓存1分钟
    def get_provider_config(self, system_id) -> SystemProviderConfig:
        """获取接入系统的回调信息，包括鉴权和Host"""
        system_info = iam.get_system(system_id, fields="provider_config")
        provider_config = system_info["provider_config"]
        return SystemProviderConfig(**provider_config)


class ResourceTypeProviderConfigService:
    """提供资源类型配置"""

    # TODO: 这里需要由后台提供查询某个系统某个资源类型的API，而不是使用批量查询系统资源类型
    @region.cache_on_arguments(expiration_time=60)  # 一分钟
    def _list_resource_type_provider_config(self, system_id: str) -> Dict[str, Dict]:
        """提供给provider_config使用的获取某个系统所有资源类型"""
        resource_types = iam.list_resource_type([system_id], fields="id,provider_config")[system_id]
        provider_config_dict = {i["id"]: i["provider_config"] for i in resource_types}
        return provider_config_dict

    def get_provider_config(self, system_id: str, resource_type_id: str) -> ResourceTypeProviderConfig:
        """获取资源类型的回调配置"""
        provider_config_dict = self._list_resource_type_provider_config(system_id)
        return ResourceTypeProviderConfig(**provider_config_dict[resource_type_id])


class ResourceProviderConfig:
    """资源提供者配置"""

    def __init__(self, system_id: str, resource_type_id: str):
        self.system_id = system_id
        self.resource_type_id = resource_type_id
        self.auth_info, self.host = self._get_auth_info_and_host()
        self.path = self._get_path()

    def _get_auth_info_and_host(self) -> Tuple[Dict[str, str], str]:
        """iam后台获取系统的provider config"""
        provider_config = SystemProviderConfigService().get_provider_config(self.system_id)
        return {"auth": provider_config.auth, "token": provider_config.token}, provider_config.host

    def _get_path(self) -> str:
        """iam后台获取请求该资源类型所需的URL Path"""
        provider_config = ResourceTypeProviderConfigService().get_provider_config(
            self.system_id, self.resource_type_id
        )
        return provider_config.path


class ResourceIDNameCache:
    """资源的ID和Name缓存"""

    def __init__(self, system_id: str, resource_type_id: str):
        self.system_id = system_id
        self.resource_type_id = resource_type_id

    def _generate_id_cache_key(self, resource_id: str) -> str:
        """
        生成Cache Key
        # TODO: 后面重构整个Cache模块时，将这些Key统一到一处，便于管理和避免key冲突
        """
        prefix = "bk_iam:rp:id_name"
        return f"{prefix}:{self.system_id}:{self.resource_type_id}:{resource_id}"

    def set(self, id_name_map: Dict[str, str]):
        """Cache所有短时间内使用list_instance/fetch_instance/search_instance的数据，用于校验和查询id与name使用"""
        # 缓存有问题，不影响正常逻辑
        try:
            with redis_region.backend.client.pipeline() as pipe:
                for _id, name in id_name_map.items():
                    # 只缓存name是字符串的，其他非法的不缓存
                    if isinstance(name, str):
                        pipe.set(self._generate_id_cache_key(_id), name, ex=5 * 60)  # 缓存5分钟
                pipe.execute()
        except RedisError as error:
            logger.exception(f"set resource id name cache error: {error}")

    def get(self, ids: List[str]) -> Dict[str, Optional[str]]:
        """
        获取缓存内容，对于缓存不存在的，则返回为空
        """
        # 缓存有问题，不影响正常逻辑
        try:
            with redis_region.backend.client.pipeline() as pipe:
                for _id in ids:
                    # 如果不存在，则None
                    pipe.get(self._generate_id_cache_key(_id))
                # 有序的列表
                result = pipe.execute()

        except RedisError as error:
            logger.exception(f"get resource id name cache error: {error}")
            result = [None] * len(ids)

        return {_id: name for _id, name in zip(ids, result)}


class ResourceProvider:
    """资源提供者"""

    name_attribute = "display_name"

    def __init__(self, system_id: str, resource_type_id: str):
        """初始化：认证信息、请求客户端"""
        self.system_id = system_id
        self.resource_type_id = resource_type_id
        # 根据系统和资源类型获取相关认证信息和Host、URL_PATH
        provider_config = ResourceProviderConfig(system_id, resource_type_id)
        auth_info, host, url_path = provider_config.auth_info, provider_config.host, provider_config.path
        url = f"{host}{url_path}"
        self.client = resource_provider.ResourceProviderClient(system_id, resource_type_id, url, auth_info)
        # 缓存服务
        self.id_name_cache = ResourceIDNameCache(system_id, resource_type_id)

    def list_attr(self) -> List[ResourceAttribute]:
        """查询某个资源类型可用于配置权限的属性列表"""
        return [
            ResourceAttribute(**i)
            for i in self.client.list_attr()
            # 由于存在接入系统将内置属性_bk_xxx，包括_bk_iam_path_或将id的返回，防御性过滤掉
            if not i["id"].startswith("_bk_") and i["id"] != "id"
        ]

    def list_attr_value(
        self, attr: str, keyword: str = "", limit: int = 10, offset: int = 0
    ) -> Tuple[int, List[ResourceAttributeValue]]:
        """获取一个资源类型某个属性的值列表"""
        filter_condition = {"keyword": keyword}
        page = {"limit": limit, "offset": offset}
        count, results = self.client.list_attr_value(attr, filter_condition, page)
        return count, [ResourceAttributeValue(**i) for i in results]

    def list_instance(
        self, parent_type: str = "", parent_id: str = "", limit: int = 10, offset: int = 0
    ) -> Tuple[int, List[ResourceInstanceBaseInfo]]:
        """根据上级资源获取某个资源实例列表"""
        filter_condition = {}
        if parent_type and parent_id:
            filter_condition["parent"] = {"type": parent_type, "id": parent_id}
        page = {"limit": limit, "offset": offset}
        count, results = self.client.list_instance(filter_condition, page)

        # 转换成需要的数据
        instance_results = [ResourceInstanceBaseInfo(**i) for i in results]
        # Cache 查询到的信息
        if instance_results:
            self.id_name_cache.set({i.id: i.display_name for i in instance_results})

        return count, instance_results

    def search_instance(
        self, keyword: str, parent_type: str = "", parent_id: str = "", limit: int = 10, offset: int = 0
    ) -> Tuple[int, List[ResourceInstanceBaseInfo]]:
        """根据上级资源和Keyword搜索某个资源实例列表"""
        # Note: 虽然与list_instance很相似，但在制定回调接口协议时特意分开为两个API，这样方便后续搜索的扩展
        filter_condition: Dict = {"keyword": keyword}
        if parent_type and parent_id:
            filter_condition["parent"] = {"type": parent_type, "id": parent_id}
        page = {"limit": limit, "offset": offset}
        count, results = self.client.search_instance(filter_condition, page)

        # 转换成需要的数据
        instance_results = [ResourceInstanceBaseInfo(**i) for i in results]
        # Cache 查询到的信息
        if instance_results:
            self.id_name_cache.set({i.id: i.display_name for i in instance_results})

        return count, instance_results

    def fetch_instance_info(
        self, ids: List[str], attributes: Optional[List[str]] = None
    ) -> List[ResourceInstanceInfo]:
        """批量查询资源实例属性，包括display_name等"""
        # fetch_instance_info 接口的批量限制
        fetch_limit = 1000
        # 分页查询资源实例属性
        results = []
        page_ids_list = chunked(ids, fetch_limit)
        for page_ids in page_ids_list:
            filter_condition = {"ids": page_ids, "attrs": attributes} if attributes else {"ids": page_ids}
            page_results = self.client.fetch_instance_info(filter_condition)
            results.extend(page_results)

        # Dict转为struct
        instance_results = []
        for i in results:
            instance_results.append(
                ResourceInstanceInfo(
                    id=i["id"],
                    # 容错处理：接入系统实现的回调接口可能将所有属性都返回，所以只过滤需要的属性即可
                    attributes={k: v for k, v in i.items() if not attributes or k in attributes},
                )
            )

        # IDNameCache，对于查询所有属性或者包括name属性，则进行缓存
        if instance_results and (not attributes or self.name_attribute in attributes):
            self.id_name_cache.set(
                {
                    i.id: i.attributes[self.name_attribute]
                    # 只有包括name属性才进行缓存
                    for i in instance_results
                    if self.name_attribute in i.attributes
                }
            )

        return instance_results

    def fetch_instance_name(self, ids: List[str]) -> List[ResourceInstanceBaseInfo]:
        """批量查询资源实例的Name属性"""
        # 先从缓存取，取不到的则再查询
        cache_id_name_map = self.id_name_cache.get(ids)
        results = [
            ResourceInstanceBaseInfo(id=_id, display_name=name) for _id, name in cache_id_name_map.items() if name
        ]
        # 未被缓存的需要实时查询
        not_cached_ids = [_id for _id, name in cache_id_name_map.items() if name is None]
        not_cached_results = self.fetch_instance_info(not_cached_ids, [self.name_attribute])
        results.extend(
            [
                ResourceInstanceBaseInfo(id=i.id, display_name=i.attributes[self.name_attribute])
                for i in not_cached_results
            ]
        )

        return results
