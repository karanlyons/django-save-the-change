# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('_themes'))

sys.path.append(os.path.abspath('../tests'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

from save_the_change import __copyright__, __title__, __version__


project = __title__
copyright = __copyright__
version = release = __version__
language = 'English'

extensions = [
	'sphinx.ext.intersphinx',
	'sphinx.ext.autodoc',
	'sphinx.ext.viewcode',
]

intersphinx_mapping = {
	'python': ('http://docs.python.org/2.7', None),
	'django': ('https://docs.djangoproject.com/en/1.10', 'https://docs.djangoproject.com/en/1.10/_objects'),
}

templates_path = ['_templates']
exclude_patterns = ['_build']
html_theme_path = ['_themes']
html_static_path = ['_static']
source_suffix = '.rst'
master_doc = 'index'

add_function_parentheses = True
add_module_names = True
pygments_style = 'sphinx'

htmlhelp_basename = 'save_the_change_docs'
html_title = "{title} {version} Documentation".format(title=project, version=version)
html_short_title = project
html_last_updated_fmt = ''
html_show_sphinx = False
html_domain_indices = False
html_use_modindex = False
html_use_index = False

if os.environ.get('READTHEDOCS', None) == 'True':
	html_theme = 'default'

else:
	html_theme = 'sphinx_rtd_theme'

html_theme_options = {
	'sticky_navigation': True,
}
