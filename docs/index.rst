.. toctree::
	:hidden:
	:maxdepth: 4
	
	self
	api
	history


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

Just add the :class:`~save_the_change.decorators.SaveTheChange` decorator to
your model:

.. code-block:: python

	from django.db import models
	from save_the_change.decorators import SaveTheChange
	
	@SaveTheChange
	class Knight(models.model):
		...


And that's it! Keep using Django like you always have, Save The Change will take
care of you.


How It Works
============

Save The Change encapsulates the fields of your model with its own descriptors
that track their values for any changes. When you call
:meth:`~django.db.models.Model.save`, Save The Change passes the names of
your changed fields through Django's ``update_fields`` argument, and Django does
the rest, sending only those fields back to the database.


Caveats
=======

Save The Change can't help you with
:class:`~django.db.models.ManyToManyField`\s nor reverse relations, as
those aren't handled through :meth:`~django.db.models.Model.save`. But
everything else should work.


Goodies
=======

Save The Change also comes with two additional decorators,
:class:`~save_the_change.decorators.TrackChanges` and 
:class:`~save_the_change.decorators.UpdateTogether`.

:class:`~save_the_change.decorators.TrackChanges` provides some additional
properties and methods to keep interact with changes made to your model,
including comparing the old and new values and reverting any changes to your
model before you save it. It can be used independently
of :class:`~save_the_change.decorators.SaveTheChange`.

:class:`~save_the_change.decorators.UpdateTogether` is an additional decorator
which allows you to specify groups of fields that are dependent on each other in
your model, ensuring that if any of them change they'll all be saved together.
For example:

.. code-block:: python

	from django.db import models
	from save_the_change.decorators import SaveTheChange, UpdateTogether
	
	@SaveTheChange
	@UpdateTogether(('height_feet', 'height_inches'))
	class Knight(models.model):
		...

Now if you ever make a change to either part of our Knight's height, *both*
the feet and the inches will be sent to the database together, so that they
can't accidentally fall out of sync.
