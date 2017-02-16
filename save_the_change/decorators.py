# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from collections import defaultdict

from django.utils import six

from .util import DoesNotExist
from .mappings import OldValues

from .descriptors import _inject_descriptors


__all__ = ('SaveTheChange', 'UpdateTogether', 'TrackChanges')


class STCMixin(object):
	"""
	Hooks into :meth:`~django.db.models.Model.__init__`,
	:meth:`~django.db.models.Model.save`, and
	:meth:`~django.db.models.Model.refresh_from_db`, and adds some new, private
	attributes to the model:
	
	:attr:`_mutable_fields`
		A :class:`dict` storing a copy of potentially mutable values on
		first access.
	:attr:`_changed_fields`
		A :class:`dict` storing a copy of immutable fields' original values when
		they're changed.
	
	"""
	
	def __init__(self, *args, **kwargs):
		self._changed_fields = {}
		self._mutable_fields = {}
		self._mutability_checked = set()
		
		super(STCMixin, self).__init__(*args, **kwargs)
		
	def save(self, *args, **kwargs):
		for save_hook in self._meta._stc_save_hooks:
			continue_saving, args, kwargs = save_hook(self, *args, **kwargs)
			
			if not continue_saving:
				break
		
		else:
			super(STCMixin, self).save(*args, **kwargs)
		
		self._changed_fields = {}
		self._mutable_fields = {}
		self._mutability_checked = set()
	
	def refresh_from_db(self, using=None, fields=None):
		super(STCMixin, self).refresh_from_db(using, fields)
		
		if fields:
			for field in fields:
				self._changed_fields.pop(field, None)
				self._mutable_fields.pop(field, None)
				self._mutability_checked.discard(field)
		
		else:
			self._changed_fields = {}
			self._mutable_fields = {}
			self._mutability_checked = set()


def _inject_stc(cls):
	"""
	Wraps model attributes in descriptors to track their changes.
	
	Injects a mixin into the model's __bases__ as well to handle the
	{create,load}/change/save lifecycle, and adds some attributes to the
	model's :attr:`_meta`:
	 
	:attr:`_stc_injected`
		:const:`True` if we've already wrapped fields on this model.
	:attr:`_stc_save_hooks`
		A :class:`list` of hooks to run
		during :meth:`~django.db.models.Model.save`.
	
	"""
	
	if not hasattr(cls._meta, '_stc_injected'):
		_inject_descriptors(cls)
		
		cls.__bases__ = (STCMixin,) + cls.__bases__
		
		cls._meta._stc_injected = True
		cls._meta._stc_save_hooks = []


def _save_the_change_save_hook(instance, *args, **kwargs):
	"""
	Sets ``update_fields`` on :meth:`~django.db.models.Model.save` to only \
	what's changed.
	
	``update_fields`` is only set if it doesn't already exist and when doing so
	is safe. This means its not set if the instance is new and yet to be saved
	to the database, if the instance is being saved with a new primary key, or
	if :meth:`~django.db.models.Model.save` has been called
	with ``force_insert``.
	
	:return: (continue_saving, args, kwargs)
	:rtype: :class:`tuple`
	
	"""
	
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
	"""
	Decorator that wraps models with a save hook to save only what's changed.
	
	"""
	
	if not hasattr(cls._meta, '_stc_injected') or _save_the_change_save_hook not in cls._meta._stc_save_hooks:
		_inject_stc(cls)
		
		# We need to ensure that if SaveTheChange and UpdateTogether are both
		# used, that UpdateTogether's save hook will always run second.
		if _update_together_save_hook in cls._meta._stc_save_hooks:
			cls._meta._stc_save_hooks = [_save_the_change_save_hook, _update_together_save_hook]
		
		else:
			cls._meta._stc_save_hooks.append(_save_the_change_save_hook)
	
	return cls


def TrackChanges(cls):
	"""
	Decorator that adds some methods and properties to models for working with \
	changed fields.
	
	:attr:`~django.db.models.Model.has_changed`
		:const:`True` if any fields on the model have changed from its last
		known database representation.
	:attr:`~django.db.models.Model.changed_fields`
		A :class:`set` of the names of all changed fields on the model.
	:attr:`~django.db.models.Model.old_values`
		The model's fields in their last known database representation as a
		read-only mapping (:class:`~save_the_change.mappings.OldValues`).
	:meth:`~django.db.models.Model._meta.revert_fields`
		Reverts the given fields back to their last known
		database representation.
	
	"""
	
	_inject_stc(cls)
	
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
	
	def revert_fields(self, names=None):
		"""
		Sets ``update_fields`` on :meth:`~django.db.models.Model.save` to only \
		what's changed.
		
		:param names: The name of the field to revert or an iterable of
			multiple names.
		
		"""
		
		if names is None:
			names = list(self._mutable_fields) + list(self._changed_fields)
		
		if isinstance(names, (six.text_type, six.binary_type) + six.string_types):
			names = [names]
		
		for name in names:
			if name in self.changed_fields:
				setattr(self, name, self.old_values[name])
	
	cls.revert_fields = revert_fields
	
	return cls


def _update_together_save_hook(instance, *args, **kwargs):
	"""
	Sets ``update_fields`` on :meth:`~django.db.models.Model.save` to include \
	any fields that have been marked as needing to be updated together with \
	fields already in ``update_fields``.
	
	:return: (continue_saving, args, kwargs)
	:rtype: :class:`tuple`
	
	"""
	
	if 'update_fields' in kwargs:
		new_update_fields = set(kwargs['update_fields'])
		
		for field in kwargs['update_fields']:
			new_update_fields.update(instance._meta.update_together.get(field, []))
		
		kwargs['update_fields'] = list(new_update_fields)
	
	return(True, args, kwargs)


def UpdateTogether(*groups):
	"""
	Decorator for specifying groups of fields to be updated together.
	
	Usage:
		>>> from django.db import models
		>>> from save_the_change.decorators import SaveTheChange, UpdateTogether
		>>> 
		>>> @SaveTheChange
		>>> @UpdateTogether(
		... 	('height_feet', 'height_inches'),
		... 	('weight_pounds', 'weight_kilos')
		... )
		>>> class Knight(models.model):
		>>> 	...
	
	"""
	
	def UpdateTogether(cls, groups=groups):
		_inject_stc(cls)
		
		cls._meta.update_together_groups = getattr(cls._meta, 'update_together_groups', []) + list(groups)
		cls._meta.update_together = defaultdict(set)
		field_names = {field.name for field in cls._meta.fields if field.concrete}
		
		# Fields may be referenced in multiple groups, so we'll walk the
		# graph when the model's class is built. If this decorator is used
		# multiple times things will still work, but we'll end up doing this
		# walk multiple times as well. It's only at startup, though, so not
		# a big deal.
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
