"""
Django settings for pjsite project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

from clientlibs import libdefs

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'ckeditor',
    'ckeditor_uploader',
    'sorl.thumbnail',
    'clientlibs',
    'pjapp',
    'pjwidgets',
    # 'consent',
    # Add the consent app to installed apps if you wish to use custom consent forms
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pjsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'pjsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/path/to/protojourneys.sqlite3',
        'USER': '',
        'PASSWORD': '',
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = True

USE_TZ = True

BASE_URL = '/protojourneys'

LOGIN_URL = BASE_URL + '/app/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

BASE_STATIC_AND_MEDIA_DIR = os.path.abspath(BASE_DIR + "../../www")

STATIC_ROOT = BASE_STATIC_AND_MEDIA_DIR + '/static/'
STATIC_URL = BASE_URL + '/static/'

MEDIA_ROOT = BASE_STATIC_AND_MEDIA_DIR + '/media/'
MEDIA_URL = BASE_URL + '/media/'

# Clientlibs config
USE_CDN = True

# CK EDITOR
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
                    [ "Format", "Font", "FontSize" ],
                    [ "Cut", "Copy", "Paste", "Undo", "Redo" ],
                    [ "Bold", "Italic", "Underline", "TextColor" ],
                    [ "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock" ],
                    [ "NumberedList", "BulletedList", "Link", "Unlink", "Image", "Iframe" ],
                    ["Source"],
                    ],
        'entities': False,
        'width': '100%',
    },
}
CKEDITOR_JQUERY_URL = STATIC_URL + 'lib/jquery.min.js'
CKEDITOR_UPLOAD_PATH = "editor_uploads/"
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_ALLOW_NONIMAGE_FILES = False

MODULES_PROVIDING_WIDGETS = [
    'pjwidgets.widgets',
]

GOOGLE_API_KEY = ''
EMBEDLY_API_KEY = ''