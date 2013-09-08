# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from copy import copy

from django.db.models import ManyToManyField
from django.db.models.related import RelatedObject


__all__ = ('SaveTheChange', 'TrackChanges')


class DoesNotExist:
	"""
	It's unlikely, but there could potentially be a time when a field is added
	to or removed from an instance. We need some representation for those cases.
	
	"""
	
	pass


class BaseChangeTracker(object):
	def __init__(self, *args, **kwargs):
		super(BaseChangeTracker, self).__init__(*args, **kwargs)
		
		self._changed_fields = {}
	
	def __setattr__(self, name, value):
		if hasattr(self, '_changed_fields'):
			try:
				name_map = self._meta._name_map
			
			except AttributeError:
				name_map = self._meta.init_name_map()
			
			if name in name_map and name_map[name][0].__class__ not in (ManyToManyField, RelatedObject):
				old = getattr(self, name, DoesNotExist)
				super(BaseChangeTracker, self).__setattr__(name, value) # A parent's __setattr__ may change value.
				new = getattr(self, name, DoesNotExist)
				
				if old != new:
					changed_fields = self._changed_fields
					
					if name in changed_fields:
						if changed_fields[name] == new:
							# We've changed this field back to its original value from the db. No need to push it back up.
							changed_fields.pop(name)
					
					else:
						changed_fields[name] = copy(old)
			
			else:
				super(BaseChangeTracker, self).__setattr__(name, value)
		
		else:
			super(BaseChangeTracker, self).__setattr__(name, value)
	
	def save(self, *args, **kwargs):
		super(BaseChangeTracker, self).save(*args, **kwargs)
		
		self._changed_fields = {}


class SaveTheChange(BaseChangeTracker):
	"""
	Keeps track of fields that have changed since model instantiation, and on
	save updates only those fields.
	
	If save is called with update_fields, the passed kwarg is given precedence.
	
	A caveat: This can't do anything to help you with ManyToManyFields nor
	reverse relationships, which is par for the course: they aren't handled by
	save(), but are pushed to the db immediately on change.
	
	"""
	
	def save(self, *args, **kwargs):
		if self.pk and self._changed_fields and 'update_fields' not in kwargs and not kwargs.get('force_insert', False):
			kwargs['update_fields'] = [key for key, value in self._changed_fields.iteritems() if value is not DoesNotExist]
		
		super(SaveTheChange, self).save(*args, **kwargs)


class TrackChanges(BaseChangeTracker):
	"""
	A model mixin that tracks model fields' values and provide some properties
	and methods to work with the old/new values.
	
	"""
	
	@property
	def has_changed(self):
		"""
		A bool indicating if any fields have changed.
		
		"""
		
		return bool(self._changed_fields)
	
	@property
	def changed_fields(self):
		"""
		A list of changed fields.
		
		"""
		
		return self._changed_fields.keys()
	
	@property
	def old_values(self):
		"""
		A dict of the old field values.
		
		"""
		
		old_values = self.new_values
		old_values.update(self._changed_fields)
		
		return old_values
	
	@property
	def new_values(self):
		"""
		A dict of the new field values.
		
		"""
		
		try:
			name_map = self._meta._name_map
		
		except AttributeError:
			name_map = self._meta.init_name_map()
		
		return dict([(field, getattr(self, field)) for field in name_map])
	
	def revert_fields(self, fields=None):
		"""
		Reverts supplied fields to their original values.
		
		:param list fields: A list of field names to revert.
		
		"""
		
		for field in fields:
			if field in self._changed_fields:
				setattr(self, field, self._changed_fields[field])
