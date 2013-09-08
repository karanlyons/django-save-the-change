# -*- coding: utf-8 -*-

import sys


try:
	from setuptools import setup

except ImportError:
	from distutils.core import setup

kwargs = {}
if sys.version_info >= (3,):
	kwargs['use_2to3'] = True

setup(
	name="django-save-the-change",
	version="1.0.0",
	description="Automatically save only changed model fields.",
	long_description="\n\n".join([open('README.rst', 'rU').read(), open('HISTORY.rst', 'rU').read()]),
	author="Karan Lyons",
	author_email="karan@karanlyons.com",
	url="https://github.com/karanlyons/django-save-the-change",
	license=open('LICENSE', 'rU').read(),
	packages=['save_the_change'],
	package_dir={'save_the_change': 'save_the_change'},
	package_data={'': ['README.rst', 'HISTORY.rst', 'LICENSE']},
	include_package_data=True,
	install_requires=[],
	zip_safe=False,
	classifiers=(
		'Development Status :: 5 - Production/Stable',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'License :: OSI Approved :: Apache Software License',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.1',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
	),
	**kwargs
)
