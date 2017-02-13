###############
Save The Change
###############

.. image:: https://img.shields.io/pypi/v/django-save-the-change.svg
	:target: https://pypi.python.org/pypi/django-save-the-change
.. image:: https://travis-ci.org/karanlyons/django-save-the-change.svg?branch=master
	:target: https://travis-ci.org/karanlyons/django-save-the-change
.. image:: https://codecov.io/github/karanlyons/django-save-the-change/coverage.svg?branch=master
	:target: https://codecov.io/github/karanlyons/django-save-the-change

Save The Change takes this:

.. code-block:: pycon

	>>> lancelot = Knight.objects.get(name="Sir Lancelot")
	>>> lancelot.favorite_color = "Blue"
	>>> lancelot.save()


And does this:

.. code-block:: sql

	UPDATE "roundtable_knight"
	SET "favorite_color" = 'Blue'


Instead of this:

.. code-block:: sql

	UPDATE "roundtable_knight"
	SET "name" = 'Sir Lancelot',
	    "from" = 'Camelot',
	    "quest" = 'To seek the Holy Grail.',
	    "favorite_color" = 'Blue',
	    "epithet" = 'The brave',
	    "actor" = 'John Cleese',
	    "full_name" = 'John Marwood Cleese',
	    "height" = '6''11"',
	    "birth_date" = '1939-10-27',
	    "birth_union" = 'UK',
	    "birth_country" = 'England',
	    "birth_county" = 'Somerset',
	    "birth_town" = 'Weston-Super-Mare',
	    "facial_hair" = 'mustache',
	    "graduated" = true,
	    "university" = 'Cambridge University',
	    "degree" = 'LL.B.',


Installation
============

Install Save The Change just like everything else:

.. code-block:: bash

	$ pip install django-save-the-change


Documentation
=============

Full documentation is available at
`ReadTheDocs <https://django-save-the-change.readthedocs.org/en/latest/>`_.
