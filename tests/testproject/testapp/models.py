# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os

from django.db import models

from save_the_change.decorators import SaveTheChange, TrackChanges, UpdateTogether


class Enlightenment(models.Model):
	"""
	A model to test ForeignKeys.
	
	"""
	
	aspect = models.CharField(max_length=32)
	
	def __unicode__(self):
		return self.aspect


@SaveTheChange
@TrackChanges
@UpdateTogether(('big_integer', 'small_integer'))
class EnlightenedModel(models.Model):
	"""
	A model to test (almost) everything else.
	
	TODO: Figure out a way to properly test {File,Image}Fields.
	
	"""
	
	big_integer = models.BigIntegerField()
	boolean = models.BooleanField()
	char = models.CharField(max_length=32)
	comma_seperated_integer = models.CommaSeparatedIntegerField(max_length=32)
	date = models.DateField()
	date_time = models.DateTimeField()
	decimal = models.DecimalField(max_digits=3, decimal_places=2)
	email = models.EmailField()
	enlightenment = models.ForeignKey(Enlightenment)
	holism = models.ManyToManyField(Enlightenment)
#	file = models.FileField(upload_to='./')
	file_path = models.FilePathField(path=os.path.join(__file__, '..', 'uploads'))
	float = models.FloatField()
#	image = models.ImageField(upload_to='./')
	integer = models.IntegerField()
	IP_address = models.IPAddressField()
	generic_IP = models.GenericIPAddressField()
	null_boolean = models.NullBooleanField()
	positive_integer = models.PositiveIntegerField()
	positive_small_integer = models.PositiveSmallIntegerField()
	slug = models.SlugField()
	small_integer = models.SmallIntegerField()
	text = models.TextField()
	time = models.TimeField()
	URL = models.URLField()


@UpdateTogether(('chaos', 'fire'))
@SaveTheChange
@UpdateTogether(('fire', 'brimstone'))
@SaveTheChange
class Disorder(models.Model):
	chaos = models.BooleanField()
	fire = models.BooleanField()
	brimstone = models.BooleanField()
