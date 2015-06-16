# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import sys


sys.path.insert(0, '..')

DEBUG = TEMPLATE_DEBUG = True

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': 'test_database'
	},
}

TIME_ZONE = 'UTC'
USE_TZ = True

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'uploads')

SECRET_KEY = 'q+xn9-%#q-u2zu*)utsl)wde%&k6ci88hqpjo1w9=2*@l*3ydl'

INSTALLED_APPS = (
	'testproject.testapp',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
