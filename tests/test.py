# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

import django
from django.test.utils import get_runner
from django.conf import settings


def run_tests():
	django.setup()
	sys.exit(bool(get_runner(settings)(verbosity=1, interactive=True).run_tests(['testproject.testapp'])))


if __name__ == '__main__':
	run_tests()
