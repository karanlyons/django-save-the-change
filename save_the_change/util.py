# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

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
