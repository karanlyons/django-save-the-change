# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import imp
import os
import sys

if sys.version_info >= (3,):
	save_the_change = imp.load_source('save_the_change', os.path.abspath(os.path.join(__file__, '..', '..', 'build', 'lib', 'save_the_change', '__init__.py')))


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

from django.test.utils import get_runner
from django.conf import settings


def run_tests():
	sys.exit(bool(get_runner(settings)(verbosity=1, interactive=True).run_tests(['testapp'])))

if __name__ == '__main__':
	run_tests()
