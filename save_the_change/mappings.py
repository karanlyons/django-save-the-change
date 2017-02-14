# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import Mapping


class OldValues(Mapping):
	"""
	A read-only :class:`~collections.Mapping` of the original values for \
	its model.
	
	Attributes can be accessed with either dot or bracket notation.
	
	"""
	
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
		for field in self.instance._meta.get_fields():
			yield field.name
			
			if field.name != field.attname:
				yield field.attname
	
	def __len__(self):
		return len(self.instance._meta.get_fields())
	
	def __repr__(self):
		return '<OldValues: %s>' % repr(self.instance)
