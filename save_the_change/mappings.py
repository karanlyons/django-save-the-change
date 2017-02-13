# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import Mapping


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
