# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from copy import deepcopy

from .util import DoesNotExist, is_mutable


class ChangeTrackingDescriptor(object):
	"""
	Descriptor that wraps model attributes to detect changes.
	
	Not all fields in older versions of Django are represented by descriptors
	themselves, so we handle both getting/setting bare attributes on the model
	and calling out to descriptors if they exist.
	
	"""
	
	def __init__(self, name, django_descriptor=None):
		self.name = name
		self.django_descriptor = django_descriptor
	
	def __get__(self, instance=None, owner=None):
		if instance is None:
			return self.django_descriptor
		
		if self.django_descriptor:
			value = self.django_descriptor.__get__(instance, owner)
		
		else:
			value = instance.__dict__.get(self.name, DoesNotExist)
		
		# We'll never have to check the value's mutability more than once, and
		# then only if it's ever accessed. If it's not mutable the only way
		# it'll change (normally) is through a call to our __set__, at which
		# point the original value will end up in _changed_fields.
		if not (
			self.name in instance.__dict__['_mutability_checked'] or
			self.name in instance.__dict__['_changed_fields'] or
			self.name in instance.__dict__['_mutable_fields']
		):
			if is_mutable(value):
				instance.__dict__['_mutable_fields'][self.name] = deepcopy(value)
			
			instance.__dict__['_mutability_checked'].add(self.name)
		
		return value
	
	def __set__(self, instance, value):
		if self.name not in instance.__dict__['_mutable_fields']:
			old_value = instance.__dict__.get(self.name, DoesNotExist)
			
			if old_value is DoesNotExist and self.django_descriptor and hasattr(self.django_descriptor, 'cache_name'):
				old_value = instance.__dict__.get(self.django_descriptor.cache_name, DoesNotExist)
			
			if old_value is not DoesNotExist:
				if instance.__dict__['_changed_fields'].get(self.name, DoesNotExist) == value:
					instance.__dict__['_changed_fields'].pop(self.name, None)
				
				elif value != old_value:
					# Unfortunately we need to make a deep copy here, which is
					# a bit more expensive than a shallow copy. This is to
					# avoid situations like:
					# 
					# 	>>> m = Model.objects.get(pk=1)
					# 	... m.mutable_attr
					# 	[1, 2, 3]
					# 	>>> reference = m.mutable_attr
					# 	>>> m.mutable_attr = None
					# 	>>> reference.append(4)
					# 	>>> reference
					# 	[1, 2, 3, 4]
					# 	>>> m.revert_fields('mutable_attr')
					# 	>>> m.mutable_attr == reference
					# 	True
					# 
					# It's an edge case, to be sure, but one we can't see coming
					# without likely worse solutions (such as checking *all*
					# attributes for immutability on model
					# instantiation/refresh).
					instance.__dict__['_changed_fields'].setdefault(self.name, deepcopy(old_value))
		
		if self.django_descriptor and hasattr(self.django_descriptor, '__set__'):
			self.django_descriptor.__set__(instance, value)
		
		else:
			instance.__dict__[self.name] = value


def _inject_descriptors(cls):
	"""
	Iterates over concrete fields in a model and wraps them in a descriptor to \
	track their changes.
	
	"""
	
	for field in cls._meta.concrete_fields:
		setattr(cls, field.attname, ChangeTrackingDescriptor(field.attname, cls.__dict__.get(field.attname)))
		
		if field.attname != field.name:
			setattr(cls, field.name, ChangeTrackingDescriptor(field.name, cls.__dict__.get(field.name)))
