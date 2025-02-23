"""
Django settings for researchhub project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import stripe
import os
import requests
import sys
import sentry_sdk
from celery.task.schedules import crontab
from sentry_sdk.integrations.django import DjangoIntegration


APP_ENV = os.environ.get('APP_ENV') or 'development'
DEVELOPMENT = 'development' in APP_ENV
PRODUCTION = 'production' in APP_ENV
STAGING = 'staging' in APP_ENV
CELERY_WORKER = os.environ.get('CELERY_WORKER', False)
ELASTIC_APM_OFF = os.environ.get('ELASTIC_APM_OFF', False)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CI = "GITHUB_ACTIONS" in os.environ
CLOUD = PRODUCTION or STAGING or CI
TESTING = ('test' in APP_ENV) or ('test' in sys.argv)
PYTHONPATH = '/var/app/current:$PYTHONPATH'
DJANGO_SETTINGS_MODULE = 'researchhub.settings'
ELASTIC_BEANSTALK = (APP_ENV in ['production', 'staging', 'development'])
NO_SILK = os.environ.get('NO_SILK', False)
CONFIG = os.environ.get('CONFIG')

if CLOUD or CONFIG:
    CONFIG_BASE_DIR = 'config'
    from config import db, keys, twitter
else:
    CONFIG_BASE_DIR = 'config_local'
    from config_local import db, keys, twitter

if DEVELOPMENT or TESTING:
    BASE_FRONTEND_URL = 'http://localhost:3000'
elif PRODUCTION:
    BASE_FRONTEND_URL = 'https://researchhub.com'
elif CLOUD:
    BASE_FRONTEND_URL = 'https://staging-web.researchhub.com'


# Django Debug Toolbar
USE_DEBUG_TOOLBAR = False
try:
    USE_DEBUG_TOOLBAR = keys.USE_DEBUG_TOOLBAR
except:
    pass

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', keys.SECRET_KEY)

# python manage.py check --deploy
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if not (PRODUCTION or STAGING):
    DEBUG = True

ALLOWED_HOSTS = [
    '.quantfive.org',
    '.elasticbeanstalk.com',
    '.researchhub.com',
    'localhost',
]

if not (PRODUCTION or STAGING):
    ALLOWED_HOSTS += [
        '.ngrok.io',
        'localhost',
        '10.0.2.2',
        '10.0.3.2'
    ]

if ELASTIC_BEANSTALK:
    # This is for health checks
    try:
        EC2_METADATA_HEADERS = {
            'X-aws-ec2-metadata-token-ttl-seconds': '21600'
        }

        EC2_METADATA_TOKEN = requests.put(
            'http://169.254.169.254/latest/api/token',
            timeout=0.01,
            headers=EC2_METADATA_HEADERS
        ).text

        EC2_METADATA_TOKEN_HEADER = {
            'X-aws-ec2-metadata-token': EC2_METADATA_TOKEN
        }

        ALLOWED_HOSTS.append(
            requests.get(
                'http://169.254.169.254/latest/meta-data/local-ipv4',
                timeout=0.01,
                headers=EC2_METADATA_TOKEN_HEADER
            ).text
        )
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.19.162/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # ALLOWED_HOSTS.append(
        #     requests.get('http://54.200.83.4/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # # Production private ips
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.0.82/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.9.43/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # # Staging private ips
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.8.17/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.6.81/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )
        # ALLOWED_HOSTS.append(
        #     requests.get('http://172.31.5.32/latest/meta-data/local-ipv4',
        #                  timeout=0.01).text
        # )

    except requests.exceptions.RequestException:
        pass

# Cors

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://localhost:3003",
    'https://dev.researchhub.com',
    'https://researchnow.researchhub.com',
    'https://www.researchhub.com',
    'https://staging-web.researchhub.com',
    'https://staging-web2.researchhub.com',
    'https://researchhub.com',
    'http://10.0.2.2:3000',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_filters',

    # https://github.com/django-extensions/django-extensions
    'django_extensions',

    # CORS
    'corsheaders',

    # Postgres
    'django.contrib.postgres',

    # Rest framework
    'rest_framework',

    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.orcid',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Storage
    'storages',

    # Search
    'django_elasticsearch_dsl',
    'django_elasticsearch_dsl_drf',

    # Emails
    'django_ses',
    'django_inlinecss',

    # Channels
    'channels',

    # Django Celery Results
    'django_celery_results',


    # Custom apps
    'analytics',
    'bullet_point',
    'discussion',
    'ethereum',
    'google_analytics',
    'hub',
    'hypothesis',
    'invite',
    'mailing_list',
    'note',
    'notification',
    'oauth',
    'paper',
    'profiler',
    'purchase',
    'reputation',
    'researchhub_case',
    'researchhub_document',
    'researchhub_access_group',
    'search',
    'summary',
    'user',
    'new_feature_release',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'researchhub.middleware.csrf_disable.DisableCSRF',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'researchhub.middleware.detect_spam.DetectSpam',
]

# if not TESTING:
#     MIDDLEWARE.append('profiler.middleware.profiler.ProfileMiddleware')

if not CLOUD and not NO_SILK == 'True':
    INSTALLED_APPS += [
        'silk',
        'dbbackup'
    ]

    MIDDLEWARE += [
        'silk.middleware.SilkyMiddleware',
    ]

    DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
    DBBACKUP_STORAGE_OPTIONS = {'location': 'backups'}

ROOT_URLCONF = 'researchhub.urls'

FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400 * 2.1 # ~55MB max data allowed

PAGINATION_PAGE_SIZE = 10

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.AllowAny',  # FOR TESTING ONLY
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': PAGINATION_PAGE_SIZE,
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer',
        'utils.renderers.PlainTextRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '50/minute',
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'researchhub.wsgi.application'

# Authentication

AUTH_USER_MODEL = 'user.User'

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

OAUTH_METHOD = 'token'

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'user.serializers.RegisterSerializer',
}


# Django AllAuth setup
# https://django-allauth.readthedocs.io/en/latest/configuration.html

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
if STAGING or PRODUCTION:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
LOGIN_REDIRECT_URL = 'http://localhost:3000/orcid'
if STAGING:
    LOGIN_REDIRECT_URL = 'https://staging-web.researchhub.com/orcid'
if PRODUCTION:
    LOGIN_REDIRECT_URL = 'https://researchhub.com/orcid'
SOCIALACCOUNT_ADAPTER = 'oauth.adapters.SocialAccountAdapter'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    'orcid': {
        # Defaults to 'orcid.org' for the production API
        'BASE_DOMAIN': 'orcid.org',
        'MEMBER_API': False,  # Defaults to False for the Public API
        'CLIENT_ID': os.environ.get(
            'ORCID_CLIENT_ID',
            keys.ORCID_CLIENT_ID
        ),
        'CLIENT_SECRET': os.environ.get(
            'ORCID_CLIENT_SECRET',
            keys.ORCID_CLIENT_SECRET
        ),
        # not expiring for approximately 20 years
        'ACCESS_TOKEN': os.environ.get(
            'ORCID_ACCESS_TOKEN',
            keys.ORCID_ACCESS_TOKEN
        ),
        'REFRESH_TOKEN': '',
    }
}

GOOGLE_REDIRECT_URL = 'http://localhost:8000/auth/google/login/callback/'
GOOGLE_YOLO_REDIRECT_URL = 'http://localhost:8000/auth/google/yolo/callback/'
if PRODUCTION:
    GOOGLE_REDIRECT_URL = (
        'https://backend.researchhub.com/auth/google/login/callback/'
    )
    GOOGLE_YOLO_REDIRECT_URL = (
        'https://backend.researchhub.com/auth/google/yolo/callback/'
    )
if STAGING:
    GOOGLE_REDIRECT_URL = (
        'https://staging-backend.researchhub.com/auth/google/login/callback/'
    )
    GOOGLE_YOLO_REDIRECT_URL = (
        'https://staging-backend.researchhub.com/auth/google/yolo/callback/'
    )


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DB_NAME = os.environ.get('DB_NAME', db.NAME)
DB_HOST = os.environ.get('DB_HOST', db.HOST)
DB_PORT = os.environ.get('DB_PORT', db.PORT)
DB_USER = os.environ.get('DB_USER', db.USER)
DB_PASS = os.environ.get('DB_PASS', db.PASS)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'TEST': {
            'NAME': 'test_researchhub',
        }        
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    'stylesheets'
]


# AWS

AWS_ACCESS_KEY_ID = os.environ.get(
    'AWS_ACCESS_KEY_ID',
    keys.AWS_ACCESS_KEY_ID
)
AWS_SECRET_ACCESS_KEY = os.environ.get(
    'AWS_SECRET_ACCESS_KEY',
    keys.AWS_SECRET_ACCESS_KEY
)


# Storage

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_QUERYSTRING_EXPIRE = 604800
AWS_STORAGE_BUCKET_NAME = os.environ.get(
    'AWS_STORAGE_BUCKET_NAME',
    'researchhub-paper-dev1'
)
if PRODUCTION:
    AWS_STORAGE_BUCKET_NAME = 'researchhub-paper-prod'
AWS_S3_REGION_NAME = 'us-west-2'

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# Email

AWS_SES_REGION_NAME = 'us-west-2'
AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'

EMAIL_BACKEND = 'django_ses.SESBackend'
if TESTING:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_WHITELIST = [
    'calvinhlee@quantfive.org',
    'craig@quantfive.org',
    'joey@quantfive.org',
    'leosun@quantfive.org',
    'patrick@quantfive.org',
    'val@quantfive.org',
    'patrick.lu@berkeley.edu',
    'calvinhlee@berkeley.edu',
    'pdj7@georgetown.edu',
    'bank@researchhub.com',
    'kobeattias@gmail.com',
    'kobe@researchhub.com',
    'kobe+1@researchhub.com',
    'contact@notesalong.com',
    'patricklu@researchhub.com',
    'thomazvu@gmail.com',
    'thomas@researchhub.com',
    'pat@researchhub.com'
]

# Whitelist for distributing RSC
DIST_WHITELIST = [
    'pdj7@georgetown.edu',
    'patricklu@researchhub.com',
]

# Sentry

SENTRY_ENVIRONMENT = APP_ENV

if PRODUCTION or STAGING:
    def before_send(event, hint):
        log_record = hint.get('log_record')
        if log_record and 'Invalid HTTP_HOST header' in log_record.message:
            return None
        return event
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN', keys.SENTRY_DSN),
        before_send=before_send,
        integrations=[DjangoIntegration()],
        environment=SENTRY_ENVIRONMENT
    )

# Search (Elastic)

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'http://localhost:9200',
    },
}

ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST', keys.ELASTICSEARCH_HOST)
if PRODUCTION:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ELASTICSEARCH_HOST,  # noqa: E501
            'port': 443,
            'use_ssl': True,
            'max_retries': 5,
        },
    }

if STAGING:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ELASTICSEARCH_HOST,  # noqa: E501
            'port': 443,
            'use_ssl': True,
            'max_retries': 5,
        },
    }


ELASTICSEARCH_AUTO_REINDEX = True
ELASTICSEARCH_DSL_PARALLEL = True
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'search.celery.CelerySignalProcessor'


# Web3
# https://web3py.readthedocs.io/en/stable/

WEB3_SHARED_SECRET = os.environ.get(
    'WEB3_SHARED_SECRET',
    '0x0000000000000000000000000000000000000000000000000000000000000000'
)

# Mainnet
WEB3_RSC_ADDRESS = os.environ.get(
    'WEB3_RSC_ADDRESS',
    '0xD101dCC414F310268c37eEb4cD376CcFA507F571'
)

if STAGING:
    # Testnet addresses
    WEB3_RSC_ADDRESS = os.environ.get(
        'WEB3_RSC_ADDRESS',
        '0x2275736dfEf93a811Bb32156724C1FCF6FFd41be'
    )

# Redis
# redis://:password@hostname:port/db_number

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Cache Settings
if TESTING:
    CACHES = {
        'default': {
            'BACKEND': 'researchhub.TestCache.TestCache',
            'LOCATION': f'{REDIS_HOST}:{REDIS_PORT}',
            'KEY_PREFIX': APP_ENV
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': f'{REDIS_HOST}:{REDIS_PORT}',
            'KEY_PREFIX': APP_ENV
        },
    }

# Celery

CELERY_BROKER_URL = 'redis://{}:{}/0'.format(REDIS_HOST, REDIS_PORT)
# CELERY_RESULT_BACKEND = 'db+postgresql://{}:{}@{}:{}/{}'.format(
#     DB_USER,
#     DB_PASS,
#     DB_HOST,
#     DB_PORT,
#     DB_NAME
# )
CELERY_TIMEZONE = 'US/Pacific'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_ROUTES = {
    '*.tasks.*': {
        'queue': f'{APP_ENV}_core_queue'
    }
}
CELERY_TASK_DEFAULT_QUEUE = f'{APP_ENV}_core_queue'

REDBEAT_REDIS_URL = 'redis://{}:{}/0'.format(REDIS_HOST, REDIS_PORT)

# Django Channels
ASGI_APPLICATION = 'researchhub.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Async service

if PRODUCTION:
    ASYNC_SERVICE_HOST = (
        'http://ec2-52-37-62-135.us-west-2.compute.amazonaws.com'
    )
elif STAGING:
    ASYNC_SERVICE_HOST = (
        'http://ec2-52-38-164-185.us-west-2.compute.amazonaws.com'
    )
else:
    ASYNC_SERVICE_HOST = os.environ.get("ASYNC_SERVICE_HOST", 'http://localhost:8080')


# APM

elastic_token = os.environ.get('ELASTIC_APM_SECRET_TOKEN', '')
if elastic_token:
    if not CELERY_WORKER:
        INSTALLED_APPS += [
            # Monitoring
            'elasticapm.contrib.django',
        ]
    if not CELERY_WORKER and not TESTING:
        MIDDLEWARE = [
            'elasticapm.contrib.django.middleware.TracingMiddleware',
        ] + MIDDLEWARE

    ELASTIC_APM = {
        # Set required service name. Allowed characters:
        # # a-z, A-Z, 0-9, -, _, and space
        'SERVICE_NAME': f'researchhub-{APP_ENV}',

        # Use if APM Server requires a token
        'SECRET_TOKEN': os.environ.get('ELASTIC_APM_SECRET_TOKEN', ''),

        # Set custom APM Server URL (default: http://localhost:8200)
        'SERVER_URL': os.environ.get('APM_URL', keys.APM_URL),  # noqa

        'ENVIRONMENT': APP_ENV,
        'DJANGO_AUTOINSERT_MIDDLEWARE': False,
        'DISABLE_SEND': CELERY_WORKER or TESTING,
        'PROCESSORS': (
            'utils.elastic_apm.filter_processor',
            'elasticapm.processors.sanitize_stacktrace_locals',
            'elasticapm.processors.sanitize_http_request_cookies',
            'elasticapm.processors.sanitize_http_headers',
            'elasticapm.processors.sanitize_http_wsgi_env',
            # 'elasticapm.processors.sanitize_http_request_querystring',  Breaking in elasticapm 6.x
            'elasticapm.processors.sanitize_http_request_body',
        ),
    }

# Twitter

TWITTER_CONSUMER_KEY = os.environ.get(
    'TWITTER_CONSUMER_KEY',
    twitter.TWITTER_CONSUMER_KEY
)
TWITTER_CONSUMER_SECRET = os.environ.get(
    'TWITTER_CONSUMER_SECRET',
    twitter.TWITTER_CONSUMER_SECRET
)
TWITER_ACCESS_TOKEN = os.environ.get(
    'TWITER_ACCESS_TOKEN',
    twitter.TWITER_ACCESS_TOKEN
)
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get(
    'TWITTER_ACCESS_TOKEN_SECRET',
    twitter.TWITTER_ACCESS_TOKEN_SECRET
)
TWITTER_CONSUMER_KEY_ALT = os.environ.get(
    'TWITTER_CONSUMER_KEY_ALT',
    twitter.TWITTER_CONSUMER_KEY_ALT
)
TWITTER_CONSUMER_SECRET_ALT = os.environ.get(
    'TWITTER_CONSUMER_SECRET_ALT',
    twitter.TWITTER_CONSUMER_SECRET_ALT
)
TWITER_ACCESS_TOKEN_ALT = os.environ.get(
    'TWITER_ACCESS_TOKEN_ALT',
    twitter.TWITER_ACCESS_TOKEN_ALT
)
TWITTER_ACCESS_TOKEN_SECRET_ALT = os.environ.get(
    'TWITTER_ACCESS_TOKEN_SECRET_ALT',
    twitter.TWITTER_ACCESS_TOKEN_SECRET_ALT
)

# MailChimp
MAILCHIMP_SERVER = 'us4'
MAILCHIMP_LIST_ID = os.environ.get('MAILCHIMP_LIST_ID', keys.MAILCHIMP_LIST_ID)

MORALIS_API_KEY = os.environ.get('MORALIS_API_KEY', keys.MORALIS_API_KEY)

# Recaptcha
RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_SECRET_KEY = os.environ.get(
    'RECAPTCHA_SECRET_KEY',
    keys.RECAPTCHA_SECRET_KEY
)

# Sift Science
SIFT_ACCOUNT_ID = os.environ.get('SIFT_ACCOUNT_ID', keys.SIFT_ACCOUNT_ID)
SIFT_REST_API_KEY = os.environ.get('SIFT_REST_API_KEY', keys.SIFT_REST_API_KEY)
SIFT_WEBHOOK_SECRET_KEY = os.environ.get('SIFT_WEBHOOK_SECRET_KEY', keys.SIFT_WEBHOOK_SECRET_KEY)


# Amplitude and GeoIP
AMPLITUDE_API_KEY = os.environ.get('AMPLITUDE_API_KEY', keys.AMPLITUDE_API_KEY)

GEOIP_PATH = os.path.join(BASE_DIR, 'analytics')

# Stripe
stripe.api_key = os.environ.get('STRIPE_API_KEY', keys.STRIPE_API_KEY)

# Reward Distribution
REWARD_TIME = os.environ.get('REWARD_TIME', '0 0 1')  # Defaults weekly

reward_time_hour, reward_time_day, reward_time_week = list(
    map(int, REWARD_TIME.split(' '))
)

if reward_time_week:
    REWARD_SCHEDULE = crontab(minute='0', hour='0', day_of_week='sunday')
elif reward_time_day:
    REWARD_SCHEDULE = crontab(minute='0', hour='0')
elif reward_time_hour:
    REWARD_SCHEDULE = crontab(minute='0', hour='*')

# GEOIP_PATH = BASE_DIR + '/utils'

# from django.contrib.gis.geoip2 import GeoIP2

# geo_ip = GeoIP2()

# Killswitch Variables
SERIALIZER_SWITCH = os.environ.get('SERIALIZER_SWITCH', True)

# CKEditor Cloud Services
CKEDITOR_CLOUD_ACCESS_KEY = os.environ.get('CKEDITOR_CLOUD_ACCESS_KEY', keys.CKEDITOR_CLOUD_ACCESS_KEY)
CKEDITOR_CLOUD_ENVIRONMENT_ID = os.environ.get('CKEDITOR_CLOUD_ENVIRONMENT_ID', keys.CKEDITOR_CLOUD_ENVIRONMENT_ID)

# Async Service API Key
ASYNC_SERVICE_API_KEY = os.environ.get("ASYNC_SERVICE_API_KEY", keys.ASYNC_SERVICE_API_KEY or 'testapikeyservice')
