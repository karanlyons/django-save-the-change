# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os

from django.db import models
from save_the_change.mixins import SaveTheChange, TrackChanges


class EnlightenedModel(SaveTheChange, TrackChanges, models.Model):
	big_integer = models.BigIntegerField()
	boolean = models.BooleanField()
	char = models.CharField(max_length=32)
	comma_seperated_integer = models.CommaSeparatedIntegerField(max_length=32)
	date = models.DateField()
	date_time = models.DateTimeField()
	decimal = models.DecimalField(max_digits=16, decimal_places=8)
	email = models.EmailField()
#	file = models.FileField(upload_to='./')
	file_path = models.FilePathField(path=os.path.join(__file__, '..', 'uploads'))
	float = models.FloatField()
#	image = models.ImageField(upload_to='./')
	integer = models.IntegerField()
	IP_address = models.IPAddressField()
	
	try:
		generic_IP = models.GenericIPAddressField()
	
	except:
		pass
	
	null_boolean = models.NullBooleanField()
	positive_integer = models.PositiveIntegerField()
	positive_small_integer = models.PositiveSmallIntegerField()
	slug = models.SlugField()
	small_integer = models.SmallIntegerField()
	text = models.TextField()
	time = models.TimeField()
	URL = models.URLField()
