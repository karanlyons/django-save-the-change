# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from copy import copy, deepcopy

from .util import DoesNotExist, is_mutable


class ChangeTrackingDescriptor(object):
	def __init__(self, name, field):
		self.name = name
		self.field = field
	
	def __get__(self, instance=None, owner=None):
		value = instance.__dict__.get(self.name, DoesNotExist)
		
		if value is DoesNotExist and self.field.is_relation:
			value_id = instance.__class__.__dict__[self.field.attname].__get__(instance, owner)
			value = self.field.related_model.objects.get(pk=value_id)
		
		if (
			self.name not in instance.__dict__['_changed_fields'] and
			self.name not in instance.__dict__['_mutable_fields'] and is_mutable(value)
		):
			instance.__dict__['_mutable_fields'][self.name] = deepcopy(value)
		
		return value
	
	def __set__(self, instance, value):
		if self.name not in instance.__dict__['_mutable_fields']:
			old_value = instance.__dict__.get(self.name, DoesNotExist)
			
			if old_value is not DoesNotExist:
				if instance.__dict__['_changed_fields'].get(self.name, DoesNotExist) == value:
					instance.__dict__['_changed_fields'].pop(self.name, None)
				
				elif value != old_value:
					instance.__dict__['_changed_fields'].setdefault(self.name, copy(old_value))
		
		instance.__dict__[self.name] = value
		
		if self.name != self.field.attname:
			setattr(instance, self.field.attname, value.id)


def inject_descriptors(cls):
	for field in cls._meta.concrete_fields:
		setattr(cls, field.attname, ChangeTrackingDescriptor(field.attname, field))
		
		if field.attname != field.name:
			setattr(cls, field.name, ChangeTrackingDescriptor(field.name, field))
