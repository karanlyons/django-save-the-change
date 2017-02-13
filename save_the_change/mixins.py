# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import defaultdict

from django import VERSION
from django.utils import six

from .util import DoesNotExist
from .mappings import OldValues

if VERSION[:2] < (1, 10):
	from .descriptors_1_8 import inject_descriptors

else:
	from .descriptors_1_10 import inject_descriptors


def BaseChangeTracker(cls):
	if not hasattr(cls._meta, 'stc_injected'):
		
		original__init__ = cls.__init__
		original_save = cls.save
		
		inject_descriptors(cls)
		
		def __init__(self, *args, **kwargs):
			self._changed_fields = {}
			self._mutable_fields = {}
			
			original__init__(self, *args, **kwargs)
		cls.__init__ = __init__
		
		def save(self, *args, **kwargs):
			original_save(self, *args, **kwargs)
			self._mutable_fields = {}
			self._changed_fields = {}
		cls.save = save
		
		cls._meta.stc_injected = True
	
	return cls


def SaveTheChange(cls):
	cls = BaseChangeTracker(cls)
	
	original_save = cls.save
	
	def save(self, *args, **kwargs):
		if not self._state.adding and hasattr(self, '_changed_fields') and hasattr(self, '_mutable_fields') and 'update_fields' not in kwargs and not kwargs.get('force_insert', False):
			kwargs['update_fields'] = (
				[name for name, value in six.iteritems(self._changed_fields)] +
				[name for name, value in six.iteritems(self._mutable_fields) if hasattr(self, name) and getattr(self, name) != value]
			)
			
			if kwargs['update_fields']:
				original_save(self, *args, **kwargs)
		
		else:
			original_save(self, *args, **kwargs)
	cls.save = save
	
	return cls


def TrackChanges(cls):
	cls = BaseChangeTracker(cls)
	
	def has_changed(self):
		return (
			bool(self._changed_fields) or
			any(getattr(self, name) != value for name, value in six.iteritems(self._mutable_fields))
		)
	
	cls.has_changed = property(has_changed)
	
	def changed_fields(self):
		return (
			set(name for name in six.iterkeys(self._changed_fields)) |
			set(name for name, value in six.iteritems(self._mutable_fields) if getattr(self, name, DoesNotExist) != value)
		)
	
	cls.changed_fields = property(changed_fields)
	
	def old_values(self):
		return OldValues(self)
	
	cls.old_values = property(old_values)
	
	def revert_field(self, name):
		setattr(self, name, self.old_values[name])
	
	cls.revert_field = revert_field
	
	def revert_fields(self, names=None):
		if names is None:
			names = list(self._mutable_fields) + list(self._changed_fields)
		
		for name in names:
			setattr(self, name, self.old_values[name])
	
	cls.revert_fields = revert_fields
	
	return cls


def UpdateTogether(*groups):
	def UpdateTogether(cls, groups=groups):
		cls = BaseChangeTracker(cls)
		
		cls._meta.update_together = defaultdict(set)
		field_names = {field.name for field in cls._meta.fields if field.concrete}
		
		neighbors = defaultdict(set)
		seen_nodes = set()
		
		for group in (
			{field for field in group if field in field_names}
			for group in groups
		):
			for node in group:
				neighbors[node].update(group)
		
		for node in neighbors:
			sqaushed_group = set()
			
			if node not in seen_nodes:
				nodes = set([node])
				
				while nodes:
					node = nodes.pop()
					seen_nodes.add(node)
					nodes |= neighbors[node] - seen_nodes
					sqaushed_group.add(node)
				
				for grouped_node in sqaushed_group:
					cls._meta.update_together[grouped_node] = sqaushed_group
		
		original_save = cls.save
		
		def save(self, *args, **kwargs):
			if 'update_fields' in kwargs:
				new_update_fields = set(kwargs['update_fields'])
				
				for field in kwargs['update_fields']:
					new_update_fields.update(self._meta.update_together.get(field, []))
				
				kwargs['update_fields'] = list(new_update_fields)
			
			original_save(self, *args, **kwargs)
		cls.save = save
		
		return cls
	
	return UpdateTogether
