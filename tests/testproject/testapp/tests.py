# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function

import os
import datetime
import pytz
from decimal import Decimal

from django.core.files import File
from django.core.files.images import ImageFile
from django.db import models
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.test import TestCase

from testproject.testapp.models import Enlightenment, EnlightenedModel


class EnlightenedModelTestCase(TestCase):
	def setUp(self):
		super(EnlightenedModelTestCase, self).setUp()
		
		self.maxDiff = None
		
		self.penny_front = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'penny_front.png'))
		self.penny_back = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'penny_back.png'))
		
		self.uploads = os.path.abspath(os.path.join(self.penny_front, '..', 'testproject', 'uploads'))
		
		self.knowledge = Enlightenment.objects.create(aspect='knowledge')
		self.wisdom = Enlightenment.objects.create(aspect='wisdom')
		
		self.old_values = {
			'big_integer': 3735928559,
			'boolean': True,
			'char': '2 cents',
			'comma_seperated_integer': '4,8,15',
			'date': datetime.date(1999, 12, 31),
			'date_time': datetime.datetime(1999, 12, 31, 23, 59, 59),
			'decimal': Decimal('0.02'),
			'email': 'gautama@kapilavastu.org',
			'enlightenment': self.knowledge,
#			'file': File(open(self.penny_front), 'penny_front_file.png'),
			'file_path': 'uploads/penny_front_file.png',
			'float': 1.61803,
#			'image': ImageFile(open(self.penny_front), 'penny_front_image.png'),
			'integer': 42,
			'IP_address': '127.0.0.1',
			'generic_IP': '::1',
			'null_boolean': None,
			'positive_integer': 1,
			'positive_small_integer': 2,
			'slug': 'onchidiacea',
			'small_integer': 4,
			'text': 'old',
			'time': datetime.time(23, 59, 59),
			'URL': 'http://djangosnippets.org/snippets/2985/',
		}
		
		self.new_values = {
			'big_integer': 3735928495,
			'boolean': False,
			'char': 'Three fiddy',
			'comma_seperated_integer': '16,23,42',
			'date': datetime.date(2000, 1, 1),
			'date_time': pytz.utc.localize(datetime.datetime(2000, 1, 1, 0, 0, 0)),
			'decimal': Decimal('3.50'),
			'email': 'maitreya@unknown.org',
			'enlightenment': self.wisdom,
#			'file': File(open(self.penny_back), 'penny_back_file.png'),
			'file_path': 'uploads/penny_back_file.png',
			'float': 3.14159,
#			'image': ImageFile(open(self.penny_back), 'penny_back_image.png'),
			'integer': 108,
			'IP_address': '255.255.255.255',
			'generic_IP': 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
			'null_boolean': True,
			'positive_integer': 5,
			'positive_small_integer': 6,
			'slug': 'soleolifera',
			'small_integer': 9,
			'text': 'new',
			'time': datetime.time(0, 0, 0),
			'URL': 'https://github.com/karanlyons/django-save-the-change',
		}
	
	def create_initial(self):
		self.tearDown()
		
		m = EnlightenedModel(**self.old_values)
		m.save()
		
		self.old_values['id'] = m.id
		self.new_values['id'] = m.id
		
		return m
	
	def create_changed(self):
		m = self.create_initial()
		
		for field_name, value in self.new_values.items():
			setattr(m, field_name, value)
		
		return m
	
	def create_reverted(self):
		m = self.create_changed()
		
		for field_name, value in self.old_values.items():
			setattr(m, field_name, value)
		
		return m
	
	def create_saved(self):
		m = self.create_changed()
		
		m.save()
		
		self.old_values['id'] = m.id
		self.new_values['id'] = m.id
		
		return m
	
	def test_initial__changed_fields(self):
		m = self.create_initial()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_initial_changed_fields(self):
		m = self.create_initial()
		
		self.assertEquals(m.changed_fields, ())
	
	def test_initial_has_changed(self):
		m = self.create_initial()
		
		self.assertEquals(m.has_changed, False)
	
	def test_initial_new_values(self):
		m = self.create_initial()
		
		self.assertEquals(m.new_values, self.old_values)
	
	def test_initial_old_values(self):
		m = self.create_initial()
		
		self.assertEquals(m.old_values, self.old_values)
	
	def test_changed__changed_fields(self):
		m = self.create_changed()
		old_values = self.old_values
		old_values.pop('id')
		
		self.assertEquals(m._changed_fields, old_values)
	
	def test_changed_changed_fields(self):
		m = self.create_changed()
		new_values = self.new_values
		new_values.pop('id')
		
		self.assertEquals(sorted(m.changed_fields), sorted(new_values.keys()))
	
	def test_changed_has_changed(self):
		m = self.create_changed()
		
		self.assertEquals(m.has_changed, True)
	
	def test_changed_new_values(self):
		m = self.create_changed()
		
		self.assertEquals(m.new_values, self.new_values)
	
	def test_changed_old_values(self):
		m = self.create_changed()
		
		self.assertEquals(m.old_values, self.old_values)
	
	def test_changed_reverts(self):
		m = self.create_changed()
		
		m.revert_fields(self.new_values.keys())
		
		self.assertEquals(m.new_values, self.old_values)
	
	def test_reverted__changed_fields(self):
		m = self.create_reverted()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_reverted_changed_fields(self):
		m = self.create_reverted()
		
		self.assertEquals(m.changed_fields, ())
	
	def test_reverted_has_changed(self):
		m = self.create_reverted()
		
		self.assertEquals(m.has_changed, False)
	
	def test_reverted_new_values(self):
		m = self.create_reverted()
		
		self.assertEquals(m.new_values, self.old_values)
	
	def test_reverted_old_values(self):
		m = self.create_reverted()
		
		self.assertEquals(m.old_values, self.old_values)
	
	def test_saved__changed_fields(self):
		m = self.create_saved()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_saved_changed_fields(self):
		m = self.create_saved()
		
		self.assertEquals(m.changed_fields, ())
	
	def test_saved_has_changed(self):
		m = self.create_saved()
		
		self.assertEquals(m.has_changed, False)
	
	def test_saved_new_values(self):
		m = self.create_saved()
		
		self.assertEquals(m.new_values, self.new_values)
	
	def test_saved_old_values(self):
		m = self.create_saved()
		
		self.assertEquals(m.old_values, self.new_values)
	
	def test_changed_twice_new_values(self):
		m = self.create_changed()
		new_values = self.new_values
		m.text = 'newer'
		new_values['text'] = 'newer'
		
		self.assertEquals(m.new_values, new_values)
	
	#def test_updated_together_values(self):
	#	m = self.create_saved()
	#	EnlightenedModel.objects.all().update(big_integer=0)
	#	
	#	new_values = self.new_values
	#	new_values['small_integer'] = 0
	#	
	#	m.small_integer = new_values['small_integer']
	#	m.save()
	#	m = EnlightenedModel.objects.all()[0]
	#	
	#	self.assertEquals(m.new_values, new_values)
	
	#def test_updated_together_with_deferred_fields(self):
	#	m = self.create_saved()
	#	
	#	m = EnlightenedModel.objects.only('big_integer').get(pk=m.pk)
	#	
	#	self.assertEquals(m.new_values, self.new_values)
	
	"""
	Regression Tests
	
	"""
	
	def test_assign_fkey_after_init_before_save(self):
		"""
		If a required ForeignKey is assigned after the model is initialized
		but before it is saved, a field.rel.to.DoesNotExist exception should
		not be raised.
		
		"""
		
		del(self.old_values['enlightenment'])
		m = EnlightenedModel(**self.old_values)
		
		try:
			m.enlightenment = self.knowledge
		
		except Enlightenment.DoesNotExist:
			self.fail('Assigning a foreign key resulted in a DoesNotExist.')
	
	def tearDown(self):
		for file_name in os.listdir(self.uploads):
			if file_name.endswith('.png'):
				os.remove(os.path.join(os.path.join(self.uploads, file_name)))
		
		self.old_values.pop('id', None)
		self.new_values.pop('id', None)
