# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testapp.settings')
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
