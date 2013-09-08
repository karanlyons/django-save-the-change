# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from copy import copy

from django.db.models import ManyToManyField
from django.db.models.related import RelatedObject
from django.utils.six import iteritems


__all__ = ('SaveTheChange', 'TrackChanges')


class DoesNotExist:
	"""
	It's unlikely, but there could potentially be a time when a field is added
	to or removed from an instance. This class represents a field in a state of
	nonexistance, just in case we ever run into it.
	
	"""
	
	pass


class BaseChangeTracker(object):
	"""
	Adds a :py:class:`dict` named :attr:`._changed_fields` to the model, which
	stores fields that have changed. The key is the field name, and the value
	the original value of the field from the database.
	
	If the value of a field is changed back to its original value, its entry is
	removed from :attr:`._changed_fields`. Thus, overhead is kept at a minimum.
	
	A caveat: This can't do anything to help you with
	:class:`~django.db.models.ManyToManyField` nor reverse relationships, which
	is par for the course: they aren't handled by
	:meth:`~django.db.models.Model.save`, but are pushed to the database
	immediately when changed.
	
	"""
	
	def __init__(self, *args, **kwargs):
		super(BaseChangeTracker, self).__init__(*args, **kwargs)
		
		self._changed_fields = {} #: A :py:class:`dict` storing changed fields.
	
	def __setattr__(self, name, value):
		"""
		Updates :attr:`._changed_fields` when new values are set for fields.
		
		"""
		
		if hasattr(self, '_changed_fields'):
			try:
				name_map = self._meta._name_map
			
			except AttributeError:
				name_map = self._meta.init_name_map()
			
			if name in name_map and name_map[name][0].__class__ not in (ManyToManyField, RelatedObject):
				old = getattr(self, name, DoesNotExist)
				super(BaseChangeTracker, self).__setattr__(name, value) # A parent's __setattr__ may change value.
				new = getattr(self, name, DoesNotExist)
				
				try:
					changed = (old != new)
				
				except: # pragma: no cover (covers naive/aware datetime comparison failure; unreachable in py3)
					changed = True
				
				if changed:
					changed_fields = self._changed_fields
					
					if name in changed_fields:
						if changed_fields[name] == new:
							# We've changed this field back to its original value from the database. No need to push it back up.
							changed_fields.pop(name)
					
					else:
						changed_fields[name] = copy(old)
			
			else:
				super(BaseChangeTracker, self).__setattr__(name, value)
		
		else:
			super(BaseChangeTracker, self).__setattr__(name, value)
	
	def save(self, *args, **kwargs):
		"""
		Clears :attr:`._changed_fields`.
		
		"""
		
		super(BaseChangeTracker, self).save(*args, **kwargs)
		
		self._changed_fields = {}


class SaveTheChange(BaseChangeTracker):
	"""
	A model mixin that keeps track of fields that have changed since model
	instantiation, and when saved updates only those fields.
	
	If :meth:`~django.db.models.Model.save` is called with ``update_fields``,
	the passed ``kwarg`` is given precedence. Similarly, if ``force_insert`` is
	set, ``update_fields`` will not be.
	
	"""
	
	def save(self, *args, **kwargs):
		"""
		Builds and passes the ``update_fields`` kwarg to Django.
		
		"""
		
		if self.pk and hasattr(self, '_changed_fields') and 'update_fields' not in kwargs and not kwargs.get('force_insert', False):
			kwargs['update_fields'] = [key for key, value in iteritems(self._changed_fields) if hasattr(self, key)]
		
		super(SaveTheChange, self).save(*args, **kwargs)


class TrackChanges(BaseChangeTracker):
	"""
	A model mixin that tracks model fields' values and provide some properties
	and methods to work with the old/new values.
	
	"""
	
	@property
	def has_changed(self):
		"""
		A :py:obj:`bool` indicating if any fields have changed.
		
		"""
		
		return bool(self._changed_fields)
	
	@property
	def changed_fields(self):
		"""
		A :py:obj:`tuple` of changed fields.
		
		"""
		
		return tuple(self._changed_fields.keys())
	
	@property
	def old_values(self):
		"""
		A :py:class:`dict` of the old field values.
		
		"""
		
		old_values = self.new_values
		old_values.update(self._changed_fields)
		
		return old_values
	
	@property
	def new_values(self):
		"""
		A :py:class:`dict` of the new field values.
		
		"""
		
		try:
			name_map = self._meta._name_map
		
		except AttributeError:
			name_map = self._meta.init_name_map()
		
		return dict([(field, getattr(self, field)) for field in name_map])
	
	def revert_fields(self, fields=None):
		"""
		Reverts supplied fields to their original values.
		
		:param list fields: Fields to revert.
		
		"""
		
		for field in fields:
			if field in self._changed_fields:
				setattr(self, field, self._changed_fields[field])
