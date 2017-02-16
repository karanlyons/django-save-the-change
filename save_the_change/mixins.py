# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import warnings

from django.db import models


"""
These are just stubs to prevent migrations from failing after upgrading from
STC v1 to v2, and also to warn developers who may blindly upgrade about the
changes to the API.

"""


class UpdateTogetherModel(models.Model):
	def __init__(self, *args, **kwargs):
		leaf = self.__class__.mro()[0]
		
		warnings.warn(
			"%s.%s: mixins.UpdateTogetherModel is no longer supported, instead use the decorator decorators.UpdateTogether." % (
				leaf.__module__,
				leaf.__name__,
			),
			RuntimeWarning,
		)
		
		super(UpdateTogetherModel, self).__init__(*args, **kwargs)
	
	class Meta:
		abstract = True


class SaveTheChange(object):
	def __init__(self, *args, **kwargs):
		leaf = self.__class__.mro()[0]
		
		warnings.warn(
			"%s.%s: mixins.SaveTheChange is no longer supported, instead use the decorator decorators.SaveTheChange." % (
				leaf.__module__,
				leaf.__name__,
			),
			RuntimeWarning,
		)
		
		super(SaveTheChange, self).__init__(*args, **kwargs)


class TrackChanges(object):
	def __init__(self, *args, **kwargs):
		leaf = self.__class__.mro()[0]
		
		warnings.warn(
			"%s.%s: mixins.TrackChanges is no longer supported, instead use the decorator decorators.TrackChanges." % (
				leaf.__module__,
				leaf.__name__,
			),
			RuntimeWarning,
		)
		
		super(TrackChanges, self).__init__(*args, **kwargs)
