"""
Django settings for phyad project.

Settings for the pre-admissions test server sadbdev.physics.ox.ac.uk.
"""

# Import defaults
from phyad.settings.base import *

DATABASES.update({
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'preads_database',
        'USER': 'preads',
        'PASSWORD': DATABASE_PWD,
        'HOST': '',
        'PORT': '',
    },
})

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s % (process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'admissions.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# Login/logout URLs
LOGIN_URL = "/webauth/login/"
LOGOUT_URL = "/webauth/logout/"

WSGI_APPLICATION = "phyad.wsgi.sadbdev.application"

