# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import Mapping
from copy import copy, deepcopy
from datetime import date, time, datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import ManyToManyField, ManyToOneRel
from django.utils import six


__all__ = ('SaveTheChange', 'TrackChanges')


#: A :py:class:`set` listing known immutable types.
IMMUTABLE_TYPES = set(getattr(settings, 'STC_IMMUTABLE_TYPES', (
	type(None), bool, float, complex, Decimal,
	six.text_type, six.binary_type, tuple, frozenset,
	date, time, datetime, timedelta, tzinfo,
	UUID
) + six.integer_types + six.string_types))

INFINITELY_ITERABLE_IMMUTABLE_TYPES = set(getattr(
	settings,
	'STC_INFINITELY_ITERABLE_IMMUTABLE_TYPES',
	(six.text_type, six.binary_type) + six.string_types
))


class DoesNotExist:
	"""
	It's unlikely, but there could potentially be a time when a field is added
	to or removed from an instance. This class represents a field in a state of
	nonexistance, just in case we ever run into it.
	
	"""
	
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


class BaseChangeTracker(object):
	"""
	Adds a :py:class:`dict` named :attr:`._changed_fields` to the model, which
	stores fields that have changed. The key is the field name, and the value
	the original value of the field from the database.
	
	If the value of a field is changed back to its original value, its entry is
	removed from :attr:`._changed_fields`. Thus, overhead is kept at a minimum.
	
	A caveat: This can't do anything to help you with
	:class:`~django.db.models.ManyToManyField`\s nor reverse relationships, which
	is par for the course: they aren't handled by
	:meth:`~django.db.models.Model.save`, but are pushed to the database
	immediately when changed.
	
	"""
	
	def __init__(self, *args, **kwargs):
		super(BaseChangeTracker, self).__init__(*args, **kwargs)
		
		self._mutable_fields = {} #: A :py:class:`dict` storing likely mutable fields.
		self._changed_fields = {} #: A :py:class:`dict` storing changed fields.
		
		# Overriding __getattribute__ has not so nice performance penalties, so
		# we try to avoid doing it at all if possible. Unfortunately, due to
		# new-style classes dunder method lookup rules we've got to override it
		# at a class and not an instance level, which means if any instance has
		# a field with a mutable default all instances of that class will incur
		# the penalty.
		#
		# In practice, since most developers aren't dynamically modifying the
		# fields attached to an instance this is a penalty that would be
		# incurred for all instances anyway.
		cls = type(self)
		
		if cls.__getattribute__ != cls.___getattribute__:
			for field in self._meta.concrete_fields:
				if is_mutable(field.get_default()):
					cls.__getattribute__ = cls.___getattribute__
					break
	
	def ___getattribute__(self, name):
		"""
		Checks the returned value from fields to see if it's known to be
		immutable. If it isn't, adds it to :attr:`._mutable_fields` so we know
		to push it back to the db. This allows us to cover the case wherein a
		mutable value is accessed and then some part of that value is altered.
		
		"""
		
		value = super(BaseChangeTracker, self).__getattribute__(name)
		
		if not hasattr(value, '__call__'):
			attrs = super(BaseChangeTracker, self).__getattribute__('__dict__')
			
			# We only want to copy the value on first access, as otherwise we'd
			# be constantly overwriting our "orignal" copy.
			if '_mutable_fields' in attrs and name not in attrs['_mutable_fields']:
				try:
					field = super(BaseChangeTracker, self).__getattribute__('_meta').get_field(name)
				
				except FieldDoesNotExist:
					pass
				
				else:
					# Since we're only here to monitor mutable values that could
					# go back to the database, we care about the actual column
					# backed values.
					#
					# In practice this means that accessing and then modifying
					# an FK field's instance will not result in that field
					# showing up as changed. This is intended, as in general the
					# handling of that instance should happen within the
					# instance itself.
					if field.concrete and field.attname == name:
						# We can't just do a simple isinstance() check here
						# as a subclass could violate the immutability promise.
						if is_mutable(value):
							super(BaseChangeTracker, self).__getattribute__('_mutable_fields')[name] = deepcopy(value)
		
		return value
	
	def __setattr__(self, name, value):
		"""
		Updates :attr:`._changed_fields` when new values are set for fields.
		
		"""
		
		if hasattr(self, '_changed_fields') and name in super(BaseChangeTracker, self).__getattribute__('_meta')._forward_fields_map:
			try:
				field = self._meta.get_field(name)
			
			except FieldDoesNotExist:
				field = None
			
			different_attname = field.attname != field.name
			
			if field and not field.hidden and field.__class__ not in (ManyToManyField, ManyToOneRel):
				old = None
				new = None
				
				attold = self.__dict__.get(field.attname, DoesNotExist)
				
				if attold is not DoesNotExist and field.is_relation:
					try:
						# If we've already got a hydrated object we can stash,
						# awesome.
						hydrated_attold = getattr(self, getattr(self.__class__, field.name).cache_name)
						
						if hydrated_attold.pk != attold:
							attold = DoesNotExist
						
						else:
							old = hydrated_attold
					
					except AttributeError:
						attold = DoesNotExist
				
				if old is None:
					old = self.__dict__.get(field.name, DoesNotExist) if different_attname else attold
				
				# A parent's __setattr__ may change value.
				super(BaseChangeTracker, self).__setattr__(name, value)
				
				attnew = self.__dict__.get(field.attname, DoesNotExist)
				
				if attnew is not DoesNotExist and field.is_relation:
					try:
						# If we've already got a hydrated object we can stash,
						# awesome.
						hydrated_attnew = getattr(self, getattr(self.__class__, field.name).cache_name)
						
						if hydrated_attnew.pk != attnew:
							attnew = DoesNotExist
						
						else:
							new = hydrated_attnew
					
					except AttributeError:
						attnew = DoesNotExist
				
				if new is None:
					new = self.__dict__.get(field.name, DoesNotExist) if different_attname else attnew
				
				try:
					changed = (attold != attnew)
				
				except Exception: # pragma: no cover (covers naive/aware datetime comparison failure; unreachable in py3)
					changed = True
				
				if changed:
					if name == field.name:
						if field.name in self._changed_fields:
							if self._changed_fields[field.name] == new:
								self._changed_fields.pop(field.name, None)
								
								if field.attname != field.name:
									self._changed_fields.pop(field.attname, None)
						
						else:
							# If this was a mutable, column backed field then we
							# want to store the old value in _mutable_fields if
							# the original is not already there.
							if name == field.attname and is_mutable(old):
								if field.attname not in self._mutable_fields:
									self._mutable_fields[field.attname] = deepcopy(attold)
							
							else:
								self._changed_fields[field.name] = copy(old)
								
								if different_attname:
									self._changed_fields[field.attname] = copy(attold)
					
					elif name == field.attname:
						if field.attname in self._changed_fields:
							if self._changed_fields[field.attname] == attnew:
								self._changed_fields.pop(field.attname, None)
						
						else:
							self._changed_fields[field.attname] = copy(attold)
			
			else:
				super(BaseChangeTracker, self).__setattr__(name, value)
		
		else:
			super(BaseChangeTracker, self).__setattr__(name, value)
	
	def save(self, *args, **kwargs):
		"""
		Clears :attr:`._changed_fields`.
		
		"""
		
		super(BaseChangeTracker, self).save(*args, **kwargs)
		
		self._mutable_fields = {}
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
		
		if self.pk and hasattr(self, '_changed_fields') and hasattr(self, '_mutable_fields') and 'update_fields' not in kwargs and not kwargs.get('force_insert', False):
			kwargs['update_fields'] = (
				[key for key, value in six.iteritems(self._changed_fields)] +
				[key for key, value in six.iteritems(self._mutable_fields) if hasattr(self, key) and getattr(self, key) != value]
			)
		
		super(SaveTheChange, self).save(*args, **kwargs)


class OldValues(Mapping):
	def __init__(self, instance):
		self.instance = instance
	
	def __getitem__(self, field_name):
		field = self.instance._meta._forward_fields_map[field_name]
		
		try:
			if field.attname in self.instance._mutable_fields:
				return self.instance._mutable_fields[field.attname]
			
			elif field_name in self.instance._changed_fields:
				return self.instance._changed_fields[field_name]
			
			elif field.is_relation and field.name in self.instance._changed_fields:
				return self.instance._changed_fields[field.name]
			
			else:
				return getattr(self.instance, field_name)
		
		except (AttributeError, KeyError):
			raise KeyError(field_name)
	
	def __iter__(self):
		for field in self.instance._meta.get_fields():
			yield field.name
	
	def __len__(self):
		return len(self.instance._meta.get_fields())
	
	def __repr__(self):
		return '<OldValues: %s>' % repr(self.instance)


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
		
		return (
			bool(self._changed_fields) or
			any(getattr(self, name) != value for name, value in six.iteritems(self._mutable_fields))
		)
	
	@property
	def changed_fields(self):
		"""
		A :py:obj:`set` of changed fields.
		
		"""
		
		return (
			set(self._meta._forward_fields_map[name].name for name in six.iterkeys(self._changed_fields)) |
			set(self._meta._forward_fields_map[name].name for name, value in six.iteritems(self._mutable_fields) if getattr(self, name) != value)
		)
	
	@property
	def old_values(self):
		"""
		A :py:class:`dict` of the old field values.
		
		"""
		
		return OldValues(self)
	
	def revert_fields(self, field_names=None):
		"""
		Reverts supplied fields to their original values.
		
		:param list fields: Fields to revert.
		
		"""
		
		if not field_names:
			for field_name in self.changed_fields:
				self.revert_field(field_name)
		
		else:
			for field_name in field_names:
				self.revert_field(field_name)
	
	def revert_field(self, field_name):
		if field_name in self._meta._forward_fields_map:
			field = self._meta._forward_fields_map[field_name]
			
			if field.name in self._changed_fields:
				# Bypass our __setattr__ since we know what the result will be.
				self.__dict__[field.name] = self._changed_fields[field.name]
				del(self._changed_fields[field.name])
			
			if field.attname in self._changed_fields:
				self.__dict__[field.attname] = self._changed_fields[field.attname]
				
				# If you don't have a hydrated instance and you set a related
				# field to None, the field cache is also set to None. Since
				# when reverting a dehydrated instance we only set the pk
				# attribute, we have to also clear the cache ourselves if the
				# instance in it is None or otherwise incorrect to restore
				# expected behavior.
				if field.is_relation:
					hydrated_old = getattr(self, getattr(self.__class__, field.name).cache_name, DoesNotExist)
					
					if hydrated_old is not DoesNotExist and (hydrated_old is None or hydrated_old.pk != self._changed_fields[field.attname]):
						delattr(self, getattr(self.__class__, field.name).cache_name)
				
				del(self._changed_fields[field.attname])
			
			if field.attname in self._mutable_fields:
				self.__dict__[field.name] = self._mutable_fields[field.name]
				del(self._mutable_fields[field.name])


class HideMetaOpts(models.base.ModelBase):
	"""
	A metaclass that hides added attributes from a class' ``Meta``, since
	otherwise Django's fascistic Meta options sanitizer will throw an
	exception. Default values can be set with default_meta_opts. By default
	only opts defined in default_meta_opts will be hidden from Django; if you
	want to hide everything unknown, set hide_unknown_opts to ``True``.
	
	(If you have another mixin that adds to your model's ``Meta``, create a
	``metaclass`` that inherits from both this and the other
	mixin's ``metaclass``.)
	
	"""
	
	default_meta_opts = {
		'update_together': (),
	}
	
	hide_unknown_opts = False
	
	def __new__(cls, name, bases, attrs):
		if not [b for b in bases if isinstance(b, HideMetaOpts)]:
			return super(HideMetaOpts, cls).__new__(cls, name, bases, attrs)
		
		else:
			meta_opts = deepcopy(cls.default_meta_opts)
			
			# Deferred fields won't have our model's Meta.
			if 'Meta' in attrs and attrs['Meta'].__module__ != 'django.db.models.query_utils':
				meta = attrs.get('Meta')
			
			else:
				# Meta is at a class level, and could be in any of the bases.
				for base in bases:
					meta = getattr(base, '_meta', None)
					
					if meta:
						break
			
			# If there's no _meta then we're falling back to defaults.
			if meta:
				for opt, value in vars(meta).items():
					if opt not in models.options.DEFAULT_NAMES and (cls.hide_unknown_opts or opt in meta_opts):
						meta_opts[opt] = value
						delattr(meta, opt)
			
			new_class = super(HideMetaOpts, cls).__new__(cls, name, bases, attrs)
			
			if meta:
				for opt in meta_opts:
					setattr(meta, opt, meta_opts[opt])
			
			# We theoretically don't have to set this twice, but just in case.
			for opt in meta_opts:
				setattr(new_class._meta, opt, meta_opts[opt])
			
			return new_class


#class UpdateTogetherModel(BaseChangeTracker, models.Model, six.with_metaclass(HideMetaOpts)):
#	"""
#	A replacement for :class:`~django.db.models.Model` which allows you to
#	specify the ``Meta`` attribute ``update_together``: a
#	:py:obj:`list`/:py:obj:`tuple` of :py:obj:`list`\s/:py:obj:`tuple`\s
#	defining fields that should always be updated together if any of
#	them change.
#	
#	"""
#	
#	def save(self, *args, **kwargs):
#		if 'update_fields' in kwargs:
#			update_fields = set(kwargs['update_fields'])
#			
#			for field in kwargs['update_fields']:
#				update_fields.update(self._meta.update_together.get(field, []))
#			
#			kwargs['update_fields'] = list(update_fields)
#		
#		super(UpdateTogetherModel, self).save(*args, **kwargs)
#	
#	class Meta:
#		abstract = True
