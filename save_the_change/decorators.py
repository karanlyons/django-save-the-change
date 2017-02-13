# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import defaultdict

from django import VERSION
from django.utils import six

from .util import DoesNotExist
from .mappings import OldValues

if VERSION[:2] < (1, 10):
	from .descriptors_1_8 import _inject_descriptors

else:
	from .descriptors_1_10 import _inject_descriptors


def BaseChangeTracker(cls):
	if not hasattr(cls._meta, '_stc_injected'):
		original__init__ = cls.__init__
		original_save = cls.save
		
		_inject_descriptors(cls)
		
		def __init__(self, *args, **kwargs):
			self._changed_fields = {}
			self._mutable_fields = {}
			self._mutability_checked = set()
			
			original__init__(self, *args, **kwargs)
		cls.__init__ = __init__
		
		def save(self, *args, **kwargs):
			for save_hook in self._meta._stc_save_hooks:
				save, args, kwargs = save_hook(self, *args, **kwargs)
				
				if not save:
					break
			
			else:
				original_save(self, *args, **kwargs)
			
			self._changed_fields = {}
			self._mutable_fields = {}
			self._mutability_checked = set()
		cls.save = save
		
		cls._meta._stc_injected = True
		cls._meta._stc_save_hooks = []
	
	return cls


def _save_the_change_save_hook(instance, *args, **kwargs):
	if (
		not instance._state.adding and
		hasattr(instance, '_changed_fields') and
		hasattr(instance, '_mutable_fields') and
		'update_fields' not in kwargs and
		not kwargs.get('force_insert', False) and
		instance._meta.pk.attname not in instance._changed_fields
	):
		kwargs['update_fields'] = (
			[name for name, value in six.iteritems(instance._changed_fields)] +
			[name for name, value in six.iteritems(instance._mutable_fields) if hasattr(instance, name) and getattr(instance, name) != value]
		)
		
		return (bool(kwargs['update_fields']), args, kwargs)
	
	return (True, args, kwargs)


def SaveTheChange(cls):
	if not hasattr(cls._meta, '_stc_injected') or _save_the_change_save_hook not in cls._meta._stc_save_hooks:
		cls = BaseChangeTracker(cls)
		
		if _update_together_save_hook in cls._meta._stc_save_hooks:
			cls._meta._stc_save_hooks = [_save_the_change_save_hook, _update_together_save_hook]
		
		else:
			cls._meta._stc_save_hooks.append(_save_the_change_save_hook)
	
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
		if name in self.changed_fields:
			setattr(self, name, self.old_values[name])
	
	cls.revert_field = revert_field
	
	def revert_fields(self, names=None):
		if names is None:
			names = list(self._mutable_fields) + list(self._changed_fields)
		
		for name in names:
			if name in self.changed_fields:
				setattr(self, name, self.old_values[name])
	
	cls.revert_fields = revert_fields
	
	return cls


def _update_together_save_hook(instance, *args, **kwargs):
	if 'update_fields' in kwargs:
		new_update_fields = set(kwargs['update_fields'])
		
		for field in kwargs['update_fields']:
			new_update_fields.update(instance._meta.update_together.get(field, []))
		
		kwargs['update_fields'] = list(new_update_fields)
	
	return(True, args, kwargs)


def UpdateTogether(*groups):
	def UpdateTogether(cls, groups=groups):
		cls = BaseChangeTracker(cls)
		
		cls._meta.update_together_groups = getattr(cls._meta, 'update_together_groups', []) + list(groups)
		cls._meta.update_together = defaultdict(set)
		field_names = {field.name for field in cls._meta.fields if field.concrete}
		
		neighbors = defaultdict(set)
		seen_nodes = set()
		
		for group in (
			{field for field in group if field in field_names}
			for group in cls._meta.update_together_groups
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
		
		if not hasattr(cls._meta, '_stc_injected') or _update_together_save_hook not in cls._meta._stc_save_hooks:
			cls._meta._stc_save_hooks.append(_update_together_save_hook)
		
		return cls
	
	return UpdateTogether
