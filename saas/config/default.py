from __future__ import absolute_import

"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-权限中心(BlueKing-IAM) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import os

import djcelery
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "backend.account",
    "rest_framework",
    "django_filters",
    "drf_yasg",
    "corsheaders",
    "mptt",
    "django_prometheus",
    "djcelery",
    "apigw_manager.apigw",
    "backend.apps.system",
    "backend.apps.action",
    "backend.apps.policy",
    "backend.apps.application",
    "backend.apps.resource",
    "backend.apps.approval",
    "backend.apps.group",
    "backend.apps.subject",
    "backend.apps.template",
    "backend.apps.organization",
    "backend.api.authorization",
    "backend.api.admin",
    "backend.api.management",
    "backend.apps.role",
    "backend.apps.user",
    "backend.apps.model_builder",
    "backend.long_task",
    "backend.audit",
    "backend.debug",
    "backend.apps.handover",
    "backend.apps.mgmt",
]


MIDDLEWARE = [
    "backend.common.middlewares.CustomProfilerMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "backend.common.middlewares.RequestProvider",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "backend.account.middlewares.LoginMiddleware",
    "backend.account.middlewares.TimezoneMiddleware",
    "backend.account.middlewares.RoleAuthenticationMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "backend.common.middlewares.AppExceptionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]


ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "resources/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# DB router
DATABASE_ROUTERS = ["backend.audit.routers.AuditRouter"]


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = ("backend.account.backends.TokenBackend",)

AUTH_USER_MODEL = "account.User"

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

LANGUAGE_COOKIE_NAME = "blueking_language"

LANGUAGE_COOKIE_PATH = "/"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (os.path.join(BASE_DIR, "resources/locale"),)


# static
STATIC_VERSION = "1.0"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

WHITENOISE_STATIC_PREFIX = "/staticfiles/"


# cookie
SESSION_COOKIE_NAME = "bkiam_sessionid"

SESSION_COOKIE_AGE = 60 * 60 * 24  # 1天

# cors
CORS_ALLOW_CREDENTIALS = True  # 在 response 添加 Access-Control-Allow-Credentials, 即允许跨域使用 cookies


# restframework
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "backend.common.exception_handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "backend.common.pagination.CustomLimitOffsetPagination",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.SessionAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("backend.common.renderers.BKAPIRenderer",),
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}


# CELERY 开关，使用时请改为 True，否则请保持为False。启动方式为以下两行命令：
# worker: python manage.py celery worker -l info
# beat: python manage.py celery beat -l info
IS_USE_CELERY = True

# 连接 BROKER 超时时间
BROKER_CONNECTION_TIMEOUT = 1  # 单位秒
# CELERY与RabbitMQ增加60秒心跳设置项
BROKER_HEARTBEAT = 60

# CELERY 并发数，默认为 2，可以通过环境变量或者 Procfile 设置
CELERYD_CONCURRENCY = os.getenv("BK_CELERYD_CONCURRENCY", 2)

# CELERY 配置，申明任务的文件路径，即包含有 @task 装饰器的函数文件
CELERY_IMPORTS = (
    "backend.apps.organization.tasks",
    "backend.apps.role.tasks",
    "backend.apps.application.tasks",
    "backend.apps.user.tasks",
    "backend.apps.group.tasks",
    "backend.apps.action.tasks",
    "backend.apps.policy.tasks",
    "backend.audit.tasks",
    "backend.publisher.tasks",
    "backend.long_task.tasks",
)

CELERYBEAT_SCHEDULE = {
    "periodic_sync_organization": {
        "task": "backend.apps.organization.tasks.sync_organization",
        "schedule": crontab(minute=0, hour=0),  # 每天凌晨执行
    },
    "periodic_sync_new_users": {
        "task": "backend.apps.organization.tasks.sync_new_users",
        "schedule": crontab(),  # 每1分钟执行一次
    },
    "periodic_sync_system_manager": {
        "task": "backend.apps.role.tasks.sync_system_manager",
        "schedule": crontab(minute="*/5"),  # 每5分钟执行一次
    },
    "periodic_check_or_update_application_status": {
        "task": "backend.apps.application.tasks.check_or_update_application_status",
        "schedule": crontab(minute="*/30"),  # 每30分钟执行一次
    },
    "periodic_user_group_policy_expire_remind": {
        "task": "backend.apps.user.tasks.user_group_policy_expire_remind",
        "schedule": crontab(minute=0, hour=11),  # 每天早上11时执行
    },
    "periodic_role_group_expire_remind": {
        "task": "backend.apps.role.tasks.role_group_expire_remind",
        "schedule": crontab(minute=0, hour=11),  # 每天早上11时执行
    },
    "periodic_user_expired_policy_cleanup": {
        "task": "backend.apps.user.tasks.user_cleanup_expired_policy",
        "schedule": crontab(minute=0, hour=2),  # 每天凌晨2时执行
    },
    "periodic_group_expired_member_cleanup": {
        "task": "backend.apps.group.tasks.group_cleanup_expired_member",
        "schedule": crontab(minute=0, hour=2),  # 每天凌晨0时执行
    },
    "periodic_pre_create_audit_model": {
        "task": "backend.audit.tasks.pre_create_audit_model",
        "schedule": crontab(0, 0, day_of_month="25"),  # 每月25号执行
    },
    "periodic_generate_action_aggregate": {
        "task": "backend.apps.action.tasks.generate_action_aggregate",
        "schedule": crontab(minute=0, hour=1),  # 每天凌晨1时执行
    },
    "periodic_execute_model_change_event": {
        "task": "backend.apps.policy.tasks.execute_model_change_event",
        "schedule": crontab(minute="*/30"),  # 每30分钟执行一次
    },
    "periodic_retry_long_task": {
        "task": "backend.long_task.tasks.retry_long_task",
        "schedule": crontab(minute=0, hour=3),  # 每天凌晨3时执行
    },
    "periodic_delete_unreferenced_expressions": {
        "task": "backend.apps.policy.tasks.delete_unreferenced_expressions",
        "schedule": crontab(minute=0, hour=4),  # 每天凌晨4时执行
    },
}

CELERY_ENABLE_UTC = True

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

CELERY_TASK_DEFAULT_QUEUE = "bk_iam"

# close celery hijack root logger
CELERYD_HIJACK_ROOT_LOGGER = False

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"


# 环境变量中有rabbitmq时使用rabbitmq, 没有时使用BK_BROKER_URL
# V3 Smart可能会配RABBITMQ_HOST或者BK_BROKER_URL
# V2 Smart只有BK_BROKER_URL
if "RABBITMQ_HOST" in os.environ:
    BROKER_URL = "amqp://{user}:{password}@{host}:{port}/{vhost}".format(
        user=os.getenv("RABBITMQ_USER"),
        password=os.getenv("RABBITMQ_PASSWORD"),
        host=os.getenv("RABBITMQ_HOST"),
        port=os.getenv("RABBITMQ_PORT"),
        vhost=os.getenv("RABBITMQ_VHOST"),
    )
else:
    BROKER_URL = os.getenv("BK_BROKER_URL")


djcelery.setup_loader()


# tracing: sentry support
SENTRY_DSN = os.getenv("SENTRY_DSN")

# tracing: otel 相关配置
# if enable, default false
ENABLE_OTEL_TRACE = os.getenv("BKAPP_ENABLE_OTEL_TRACE", "False").lower() == "true"
BKAPP_OTEL_INSTRUMENT_DB_API = os.getenv("BKAPP_OTEL_INSTRUMENT_DB_API", "True").lower() == "true"
BKAPP_OTEL_SERVICE_NAME = os.getenv("BKAPP_OTEL_SERVICE_NAME") or "bk-iam"
BKAPP_OTEL_SAMPLER = os.getenv("BKAPP_OTEL_SAMPLER", "parentbased_always_off")
BKAPP_OTEL_BK_DATA_ID = int(os.getenv("BKAPP_OTEL_BK_DATA_ID", "-1"))
BKAPP_OTEL_GRPC_HOST = os.getenv("BKAPP_OTEL_GRPC_HOST")

if ENABLE_OTEL_TRACE or SENTRY_DSN:
    INSTALLED_APPS += ("backend.tracing",)


# debug trace的过期时间
MAX_DEBUG_TRACE_TTL = 7 * 24 * 60 * 60  # 7天
# debug trace的最大数量
MAX_DEBUG_TRACE_COUNT = 1000


# profile record
ENABLE_PYINSTRUMENT = os.getenv("BKAPP_ENABLE_PYINSTRUMENT", "False").lower() == "true"  # 需要开启时则配置环境变量
PYINSTRUMENT_PROFILE_DIR = os.path.join(BASE_DIR, "profiles")


# ---------------
# app 自定义配置
# ---------------


# 初始化管理员列表，列表中的人员将拥有预发布环境和正式环境的管理员权限
# 注意：请在首次提测和上线前修改，之后的修改将不会生效
INIT_SUPERUSER = []


# 是否是smart部署方式
IS_SMART_DEPLOY = os.getenv("BKAPP_IS_SMART_DEPLOY", "True").lower() == "true"


# version log
VERSION_LOG_MD_FILES_DIR = os.path.join(BASE_DIR, "resources/version_log")


# iam host
BK_IAM_HOST = os.getenv("BK_IAM_V3_INNER_HOST", "http://bkiam.service.consul:9081")
BK_IAM_HOST_TYPE = os.getenv("BKAPP_IAM_HOST_TYPE", "direct")  # direct/apigateway


# iam engine host
BK_IAM_ENGINE_HOST = os.getenv("BKAPP_IAM_ENGINE_HOST")
BK_IAM_ENGINE_HOST_TYPE = os.getenv("BKAPP_IAM_ENGINE_HOST_TYPE", "direct")  # direct/apigateway


# authorization limit
# 授权对象授权用户组, 模板的最大限制
SUBJECT_AUTHORIZATION_LIMIT = {
    # 用户能加入的用户组的最大数量
    "default_subject_group_limit": int(os.getenv("BKAPP_DEFAULT_SUBJECT_GROUP_LIMIT", 100)),
    # 用户组能加入同一个系统的权限模板的最大数量
    "default_subject_system_template_limit": int(os.getenv("BKAPP_DEFAULT_SUBJECT_SYSTEM_TEMPLATE_LIMIT", 10)),
    "subject_system_template_limit": {
        # key: system_id, value: int
    },  # 系统可自定义配置的 用户组能加入同一个系统的权限模板的最大数量
    # 用户组成员最大数量
    "group_member_limit": int(os.getenv("BKAPP_GROUP_MEMBER_LIMIT", 500)),
    # 用户组单次授权模板数
    "group_auth_template_once_limit": int(os.getenv("BKAPP_GROUP_AUTH_TEMPLATE_ONCE_LIMIT", 10)),
    # 用户组单次授权的系统数
    "group_auth_system_once_limit": int(os.getenv("BKAPP_GROUP_AUTH_SYSTEM_ONCE_LIMIT", 10)),
}

# 授权的实例最大数量限制
AUTHORIZATION_INSTANCE_LIMIT = int(os.getenv("BKAPP_AUTHORIZATION_INSTANCE_LIMIT", 200))

# 策略中实例数量的最大限制
SINGLE_POLICY_MAX_INSTANCES_LIMIT = int(os.getenv("BKAPP_SINGLE_POLICY_MAX_INSTANCES_LIMIT", 10000))

# 一次申请策略中中新增实例数量限制
APPLY_POLICY_ADD_INSTANCES_LIMIT = int(os.getenv("BKAPP_APPLY_POLICY_ADD_INSTANCES_LIMIT", 20))

# 最长已过期权限删除期限
MAX_EXPIRED_POLICY_DELETE_TIME = 365 * 24 * 60 * 60  # 1年

# 用于发布订阅的Redis
PUB_SUB_REDIS_HOST = os.getenv("BKAPP_PUB_SUB_REDIS_HOST")
PUB_SUB_REDIS_PORT = os.getenv("BKAPP_PUB_SUB_REDIS_PORT")
PUB_SUB_REDIS_PASSWORD = os.getenv("BKAPP_PUB_SUB_REDIS_PASSWORD")
PUB_SUB_REDIS_DB = os.getenv("BKAPP_PUB_SUB_REDIS_DB", 0)

# 前端页面功能开关
ENABLE_FRONT_END_FEATURES = {
    "enable_model_build": os.getenv("BKAPP_ENABLE_FRONT_END_MODEL_BUILD", "False").lower() == "true",
    "enable_permission_handover": os.getenv("BKAPP_ENABLE_FRONT_END_PERMISSION_HANDOVER", "True").lower() == "true",
}

# Open API接入APIGW后，需要对APIGW请求来源认证，使用公钥解开jwt
BK_APIGW_PUBLIC_KEY = os.getenv("BKAPP_APIGW_PUBLIC_KEY")

# apigateway 相关配置
# NOTE: it sdk will read settings.APP_CODE and settings.APP_SECRET, so you should set it
BK_APIGW_NAME = "bk-iam"
BK_API_URL_TMPL = os.getenv("BK_API_URL_TMPL", "")
BK_IAM_BACKEND_SVC = os.getenv("BK_IAM_BACKEND_SVC", "bkiam-web")
BK_IAM_SAAS_API_SVC = os.getenv("BK_IAM_SAAS_API_SVC", "bkiam-saas-api")
BK_IAM_ENGINE_SVC = os.getenv("BK_IAM_ENGINE_SVC", "bkiam-search-engine")
BK_APIGW_RESOURCE_DOCS_BASE_DIR = os.path.join(BASE_DIR, "resources/apigateway/docs/")


# Requests pool config
REQUESTS_POOL_CONNECTIONS = int(os.getenv("REQUESTS_POOL_CONNECTIONS", 20))
REQUESTS_POOL_MAXSIZE = int(os.getenv("REQUESTS_POOL_MAXSIZE", 20))
