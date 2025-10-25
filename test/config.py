import os
from decimal import Decimal

from web.setup import env_var

#
# Application setup
# NOTE: do not run with debug turned on in production
#

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
LOG_LEVEL = "DEBUG"
URL_SCHEME = "https"
DATABASE_MODULE = None

WORKER_ENABLED = False
WORKER_INTERVAL_S = 300

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/web_test"
LOCALHOST_URL = None

ENDPOINT_HOME = None
ENDPOINT_ERROR = None
ENDPOINT_LOGIN = None
ENDPOINT_PASSWORD_RECOVERY = None

LOCALE_LANGUAGE_CODE = "nl"
LOCALE_COUNTRY_CODE = "NL"

AUTOMATE_EXTERNAL = True
AUTOMATE_STATIC = True
AUTOMATE_TIMEOUT_S = 10
OPTIMIZER_ENABLED = True

#
# Authentication
# NOTE: keep the secret key used in production secret
#

AUTH_JWT_SECRET = "secret"
AUTH_JWT_ALLOW_GUEST = True
AUTH_JWT_EXPIRES_S = 3600
AUTH_JWT_COOKIE = "access_token"
AUTH_JWT_ENCODE_ALGORITHM = "HS256"
AUTH_JWT_DECODE_ALGORITHMS = ["HS256"]
AUTH_JWT_DECODE_LEEWAY_S = 60

AUTH_CSRF_COOKIE = "csrf_token"
AUTH_CSRF_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

AUTH_KEY_HEADER = "Authorization"

#
# Email configuration
#

MAIL_METHOD = "SMTP"
MAIL_TIMEOUT_S = 10
MAIL_MAX_RECEIVERS = 100
MAIL_SENDER = env_var("MAIL_SENDER", str)
MAIL_RECEIVER = env_var("MAIL_RECEIVER", str)
MAIL_ADMIN = env_var("MAIL_ADMIN", str)

MAIL_LOG_ENABLED = False
MAIL_LOG_LEVEL = "ERROR"
MAIL_LOG_PREFIX = "Summit"

SMTP_HOSTNAME = env_var("SMTP_HOSTNAME", str)
SMTP_PORT = 587
SMTP_USERNAME = env_var("SMTP_USERNAME", str)
SMTP_PASSWORD = env_var("SMTP_PASSWORD", str)

#
# Content delivery network
#

CDN_BASE_URL = env_var("CDN_BASE_URL", str)
CDN_AUTO_NAMING = False
CDN_IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"]
CDN_AUDIO_EXTS = ["m4a", "mp3", "mp4"]
CDN_VIDEO_EXTS = ["mp4"]

FTP_HOSTNAME = env_var("FTP_HOSTNAME", str)
FTP_USERNAME = env_var("FTP_USERNAME", str)
FTP_PASSWORD = env_var("FTP_PASSWORD", str)

#
# Integrations
#

GOOGLE_API_KEY = None
GOOGLE_CLIENT_ID = None
GOOGLE_PLACE_ID = None

MOLLIE_API_KEY = None

INTIME_ENABLED = False

#
# Structured data
#

META_BRAND_NAME = None
META_WEBSITE_NAME = None
META_LOGO_URL = None
META_FAVICON_URL = None
META_COLOR_HEX = None

SOCIAL_DISCORD = None
SOCIAL_FACEBOOK = None
SOCIAL_INSTAGRAM = None
SOCIAL_PINTEREST = None
SOCIAL_TWITTER = None
SOCIAL_YOUTUBE = None

#
# Business information
# NOTE: these will be used in official documents
#

BUSINESS_NAME = None
BUSINESS_EMAIL = None
BUSINESS_LOGO_URL = None
BUSINESS_REGISTRATION_NUMBER = None
BUSINESS_VAT_NUMBER = None
BUSINESS_VAT_REVERSE_RATE = Decimal("1")
BUSINESS_STREET = None
BUSINESS_CITY = None
BUSINESS_ZIP_CODE = None
BUSINESS_COUNTRY = None
BUSINESS_COUNTRY_CODE = None
