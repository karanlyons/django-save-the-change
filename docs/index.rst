###############
Save The Change
###############

.. image:: https://badge.fury.io/py/django-save-the-change.png
	:target: http://badge.fury.io/py/django-save-the-change
.. image:: https://travis-ci.org/karanlyons/django-save-the-change.png?branch=master
	:target: https://travis-ci.org/karanlyons/django-save-the-change/
.. image:: https://coveralls.io/repos/karanlyons/django-save-the-change/badge.png?branch=master
	:target: https://coveralls.io/r/karanlyons/django-save-the-change

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

Save The Change can't help you with :class:`~django.db.models.ManyToManyField`
nor reverse relations, as those aren't handled
through :meth:`~django.db.models.Model.save`. But everything else'll work.


Goodies
=======

Save The Change also comes with a second mixin,
:class:`~save_the_change.mixins.TrackChanges`. Adding
:class:`~save_the_change.mixins.TrackChanges` to your model will expose a few
new properties and methods for tracking and manually reverting changes to your
model before you save it.


Developer Interface
===================

.. automodule:: save_the_change.mixins
	:members: SaveTheChange, TrackChanges, DoesNotExist,
	:undoc-members:

.. autoclass:: save_the_change.mixins.BaseChangeTracker
	:members: __setattr__, save


.. include:: ../HISTORY.rst
