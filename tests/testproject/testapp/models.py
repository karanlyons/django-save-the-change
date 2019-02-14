# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os

import django
from django.db import models

from save_the_change.decorators import SaveTheChange, TrackChanges, UpdateTogether


@TrackChanges
@SaveTheChange
class Enlightenment(models.Model):
	"""
	A model to test ForeignKeys.
	
	"""
	
	aspect = models.CharField(max_length=32)
	
	def __unicode__(self):
		return self.aspect


@UpdateTogether(('chaos', 'fire'))
@SaveTheChange
@UpdateTogether(('fire', 'brimstone'))
@SaveTheChange
class Disorder(models.Model):
	"""
	A model to test out of order and duplicate decorators.
	
	"""
	
	chaos = models.BooleanField()
	fire = models.BooleanField()
	brimstone = models.BooleanField()


@SaveTheChange
@TrackChanges
@UpdateTogether(('big_integer', 'small_integer'))
class EnlightenedModel(models.Model):
	"""
	A model to test (almost) everything else.
	
	"""
	
	big_integer = models.BigIntegerField()
	boolean = models.BooleanField()
	char = models.CharField(max_length=32)
	if django.VERSION < (2, 0):
		comma_seperated_integer = models.CommaSeparatedIntegerField(max_length=32)
	date = models.DateField()
	date_time = models.DateTimeField()
	decimal = models.DecimalField(max_digits=3, decimal_places=2)
	email = models.EmailField()
	enlightenment = models.ForeignKey(Enlightenment, related_name='enlightened_models', on_delete=models.CASCADE)
	holism = models.ManyToManyField(Enlightenment)
	file = models.FileField(upload_to='./')
	file_path = models.FilePathField(path=os.path.join(__file__, '..', 'uploads'))
	float = models.FloatField()
	image = models.ImageField(upload_to='./')
	integer = models.IntegerField()
	if django.VERSION < (1, 11):
		# Removed in Django 1.11
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
	
	def __init__(self, *args, **kwargs):
		self.init_started = True
		
		super(EnlightenedModel, self).__init__(*args, **kwargs)
		
		self.init_ended = True
	
	def refresh_from_db(self, using=None, fields=None):
		self.refresh_from_db_started = True
		
		super(EnlightenedModel, self).refresh_from_db(using, fields)
		
		self.refresh_from_db_ended = True
	
	def save(self, *args, **kwargs):
		self.save_started = True
		
		super(EnlightenedModel, self).save(*args, **kwargs)
		
		self.save_ended = True
