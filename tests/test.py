# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

from django.test.utils import get_runner
from django.conf import settings


def run_tests():
        import django
        if django.VERSION[:2] >= (1, 7):
                django.setup()
	sys.exit(bool(get_runner(settings)(verbosity=1, interactive=True).run_tests(['testapp'])))


if __name__ == '__main__':
	run_tests()
