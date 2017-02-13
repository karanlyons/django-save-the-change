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


Usage
=====

Just add :class:`~save_the_change.mixins.SaveTheChange` to your model:

.. code-block:: python

	from django.db import models
	from save_the_change.mixins import SaveTheChange
	
	class Knight(SaveTheChange, models.model):
		...


And that's it! Keep using Django like you always have, Save The Change will take
care of you.


How It Works
============

Save The Change overloads ``__setattr__`` and keeps track of what fields have
changed from their stored value in your database. When you
call :meth:`~django.db.models.Model.save`, Save The Change passes those
changed fields through Django's ``update_fields`` ``kwarg``, and Django does the
rest, sending only those fields back to the database.


Caveats
=======

Save The Change can't help you with :class:`~django.db.models.ManyToManyField`\s
nor reverse relations, as those aren't handled
through :meth:`~django.db.models.Model.save`. But everything else'll work.


Goodies
=======

Save The Change also comes with a second mixin,
:class:`~save_the_change.mixins.TrackChanges`. Adding
:class:`~save_the_change.mixins.TrackChanges` to your model will expose a few
new properties and methods for tracking and manually reverting changes to your
model before you save it.

You can also use :class:`~save_the_change.mixins.UpdateTogetherModel` in place of
:class:`~django.db.models.Model` to add the new field ``update_together`` to your
model's ``Meta``, which allows you to specify that certain fields are dependent on
the values of other fields in your model.


Developer Interface
===================

.. automodule:: save_the_change.mixins
	:members: SaveTheChange, TrackChanges
	:undoc-members:

.. autoclass:: save_the_change.mixins.UpdateTogetherModel

.. autoclass:: save_the_change.mixins.DoesNotExist

.. autoclass:: save_the_change.mixins.BaseChangeTracker
	:members: __setattr__, save

.. autoclass:: save_the_change.mixins.UpdateTogetherMeta


.. include:: ../HISTORY.rst
