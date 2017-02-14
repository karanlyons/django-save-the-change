# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

from datetime import date, time, datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import UUID

from django.utils import six


#: A :class:`set` listing known immutable types.
IMMUTABLE_TYPES = set((
	type(None), bool, float, complex, Decimal,
	six.text_type, six.binary_type, tuple, frozenset,
	date, time, datetime, timedelta, tzinfo,
	UUID
) + six.integer_types + six.string_types)

#: A :class:`set` listing known immutable types that are infinitely
#: recursively iterable.
INFINITELY_ITERABLE_IMMUTABLE_TYPES = set(
	(six.text_type, six.binary_type) + six.string_types
)


class DoesNotExist:
	"""Indicates when an attribute does not exist on an object."""
	pass


def is_mutable(obj):
	"""
	Checks if given object is likely mutable.
	
	:param obj: object to check.
	
	We check that the object is itself a known immutable type, and then
	attempt to recursively check any objects within it. Strings are
	special cased to prevent us getting stuck in an infinite loop.
	
	:return: :const:`True` if the object is likely mutable,
		:const:`False` if it definitely is not.
	:rtype: :obj:`bool`
	
	"""
	
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
