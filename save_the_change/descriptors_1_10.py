# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from copy import copy, deepcopy

from .util import DoesNotExist, is_mutable


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


def inject_descriptors(cls):
	for field in cls._meta.concrete_fields:
		setattr(cls, field.attname, ChangeTrackingDescriptor(field.attname, getattr(cls, field.attname)))
		
		if field.attname != field.name:
			setattr(cls, field.name, ChangeTrackingDescriptor(field.name, getattr(cls, field.name)))
