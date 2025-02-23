import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'development')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

INFURA_PROJECT_ID = os.environ.get('INFURA_PROJECT_ID', '')
INFURA_PROJECT_SECRET = os.environ.get('INFURA_PROJECT_SECRET', '')
INFURA_RINKEBY_ENDPOINT = f'https://rinkeby.infura.io/v3/{INFURA_PROJECT_ID}'

ORCID_CLIENT_ID = os.environ.get('ORCID_CLIENT_ID')
ORCID_CLIENT_SECRET = os.environ.get('ORCID_CLIENT_SECRET')
ORCID_ACCESS_TOKEN = os.environ.get('ORCID_ACCESS_TOKEN')

MAILCHIMP_KEY = os.environ.get('MAILCHIMP_KEY', '')
MAILCHIMP_LIST_ID = os.environ.get('MAILCHIMP_LIST_ID', '')

RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

SIFT_ACCOUNT_ID = os.environ.get('SIFT_ACCOUNT_ID', '')
SIFT_REST_API_KEY = os.environ.get('SIFT_REST_API_KEY', '')
SIFT_WEBHOOK_SECRET_KEY = os.environ.get('SIFT_WEBHOOK_SECRET_KEY', '')

AMPLITUDE_API_KEY = os.environ.get('AMPLITUDE_API_KEY', '')

STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', '')

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

APM_URL = os.environ.get('APM_URL', '')

ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST', '')

CKEDITOR_CLOUD_ACCESS_KEY = os.environ.get('CKEDITOR_CLOUD_ACCESS_KEY', '')
CKEDITOR_CLOUD_ENVIRONMENT_ID = os.environ.get('CKEDITOR_CLOUD_ENVIRONMENT_ID', '')

ASYNC_SERVICE_API_KEY = os.environ.get('ASYNC_SERVICE_API_KEY', '')

MORALIS_API_KEY = os.environ.get('MORALIS_API_KEY', '')
