import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-39we2s&c#!11v@(yifk4p2*flu=_cprkn*6$lt9*y1xxfjvkc$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'tawhtawhaa-madarasa-30ebae930b8d.herokuapp.com',
    '.herokuapp.com',
    'localhost',
    '127.0.0.1',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

 'django.contrib.humanize',
 
    # "unfold",                        # ← must be FIRST for styling to apply
    # "unfold.contrib.filters",        # optional but recommended — better filters
    # "unfold.contrib.forms",          # optional — nicer form widgets
    # "unfold.contrib.inlines",

    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',

    'core',

]


# Crispy Forms Configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
 'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'tawhtawhaa_madarasa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # <-- ROOT templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.navbar_context',

            ],
        },
    },
]

WSGI_APPLICATION = 'tawhtawhaa_madarasa.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases




DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'

STATICFILES_DIRS = [ BASE_DIR / 'static',]
STATIC_ROOT = BASE_DIR / 'staticfiles'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# settings.py additions

# Contact email settings
CONTACT_EMAIL = 'contact@tawhaa.edu.bd'  # Where contact form submissions go
ADMIN_EMAIL = 'admin@tawhaa.edu.bd'  # Main admin email
SUPPORT_EMAIL = 'support@tawhaa.edu.bd'  # Technical support email

# Auto-response settings
CONTACT_AUTO_RESPONSE = True
CONTACT_RESPONSE_TIME = '24-48 hours'  # Displayed to users

# File upload settings
MAX_UPLOAD_SIZE = 5242880  # 5MB in bytes
ALLOWED_UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']

# reCAPTCHA settings (optional)
RECAPTCHA_PUBLIC_KEY = 'your-recaptcha-site-key'
RECAPTCHA_PRIVATE_KEY = 'your-recaptcha-secret-key'
USE_RECAPTCHA = False

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Custom error handlers
HANDLER403 = 'django.views.defaults.permission_denied'
HANDLER404 = 'django.views.defaults.page_not_found'
HANDLER405 = 'django.views.defaults.bad_request'
HANDLER500 = 'django.views.defaults.server_error'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
