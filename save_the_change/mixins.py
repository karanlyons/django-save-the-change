# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import defaultdict, Mapping
from copy import copy, deepcopy
from datetime import date, time, datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import UUID

from django.utils import six


#: A :py:class:`set` listing known immutable types.
IMMUTABLE_TYPES = set((
	type(None), bool, float, complex, Decimal,
	six.text_type, six.binary_type, tuple, frozenset,
	date, time, datetime, timedelta, tzinfo,
	UUID
) + six.integer_types + six.string_types)

INFINITELY_ITERABLE_IMMUTABLE_TYPES = set(
	(six.text_type, six.binary_type) + six.string_types
)


class DoesNotExist:
	pass


def is_mutable(obj):
	if type(obj) not in IMMUTABLE_TYPES:
		return True
	
	elif type(obj) not in INFINITELY_ITERABLE_IMMUTABLE_TYPES:
		try:
			for sub_obj in iter(obj):
				if is_mutable(sub_obj):
					return True
		
		except TypeError:
			pass
	
	return False


class ChangeTrackingDescriptor(object):
	def __init__(self, name, django_descriptor):
		self.name = name
		self.django_descriptor = django_descriptor
	
	def __get__(self, instance=None, owner=None):
		value = self.django_descriptor.__get__(instance, owner)
		
		if (
			self.name not in instance.__dict__['_changed_fields'] and
			self.name not in instance.__dict__['_mutable_fields'] and is_mutable(value)
		):
			instance.__dict__['_mutable_fields'][self.name] = deepcopy(value)
		
		return value
	
	def __set__(self, instance, value):
		if self.name not in instance.__dict__['_mutable_fields']:
			old_value = instance.__dict__.get(self.name, DoesNotExist)
			
			if old_value is DoesNotExist and hasattr(self.django_descriptor, 'cache_name'):
				old_value = instance.__dict__.get(self.django_descriptor.cache_name, DoesNotExist)
			
			if old_value is not DoesNotExist:
				if instance.__dict__['_changed_fields'].get(self.name, DoesNotExist) == value:
					instance.__dict__['_changed_fields'].pop(self.name, None)
				
				elif value != old_value:
					instance.__dict__['_changed_fields'].setdefault(self.name, copy(old_value))
		
		if hasattr(self.django_descriptor, '__set__'):
			self.django_descriptor.__set__(instance, value)
		
		else:
			instance.__dict__[self.name] = value


def BaseChangeTracker(cls):
	if not hasattr(cls._meta, 'stc_injected'):
		for field in cls._meta.concrete_fields:
			setattr(cls, field.attname, ChangeTrackingDescriptor(field.attname, getattr(cls, field.attname)))
			
			if field.attname != field.name:
				setattr(cls, field.name, ChangeTrackingDescriptor(field.name, getattr(cls, field.name)))
		
		original__init__ = cls.__init__
		original_save = cls.save
		
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


class OldValues(Mapping):
	def __init__(self, instance):
		self.instance = instance
	
	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		
		except KeyError:
			raise AttributeError(name)
	
	def __getitem__(self, name):
		try:
			return self.instance._mutable_fields[name]
		
		except KeyError:
			try:
				return self.instance._changed_fields[name]
			
			except KeyError:
				try:
					return getattr(self.instance, name)
				
				except AttributeError:
					raise KeyError(name)
	
	def __iter__(self):
		for name in self.instance._meta._forward_fields_map:
			yield name
	
	def __len__(self):
		return len(self.instance._meta._forward_fields_map)
	
	def __repr__(self):
		return '<OldValues: %s>' % repr(self.instance)


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
			for name in self._mutable_fields.keys():
				self.revert_field(name)
			
			for name in self._changed_fields.keys():
				self.revert_field(name)
		
		else:
			for name in names:
				self.revert_field(name)
	
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
