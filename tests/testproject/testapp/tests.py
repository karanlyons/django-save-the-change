# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import datetime
import os
import pytz
import warnings
from decimal import Decimal

from django.core.files import File
from django.core.files.images import ImageFile
from django.test import TestCase

from testproject.testapp.models import Enlightenment, EnlightenedModel, Disorder

from save_the_change.decorators import _save_the_change_save_hook, _update_together_save_hook
from save_the_change.mixins import SaveTheChange, TrackChanges, UpdateTogetherModel


ATTR_MISSING = object()


class EnlightenedModelTestCase(TestCase):
	def setUp(self):
		super(EnlightenedModelTestCase, self).setUp()
		
		self.maxDiff = None
		
		self.penny_front = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'penny_front.png'))
		self.penny_back = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'penny_back.png'))
		
		self.uploads = os.path.abspath(os.path.join(self.penny_front, '..', 'testproject', 'uploads'))
		
		self.knowledge = Enlightenment.objects.create(id=100, aspect='knowledge')
		self.wisdom = Enlightenment.objects.create(id=200, aspect='wisdom')
		
		self.old_values = {
			'big_integer': 3735928559,
			'boolean': True,
			'char': '2 cents',
			'comma_seperated_integer': '4,8,15',
			'date': datetime.date(1999, 12, 31),
			'date_time': pytz.utc.localize(datetime.datetime(1999, 12, 31, 23, 59, 59)),
			'decimal': Decimal('0.02'),
			'email': 'gautama@kapilavastu.org',
			'enlightenment': self.knowledge,
			'enlightenment_id': self.knowledge.id,
			'file': File(open(self.penny_front, 'rbU'), 'penny_front_file.png'),
			'file_path': 'uploads/penny_front_file.png',
			'float': 1.61803,
			'image': ImageFile(open(self.penny_front, 'rbU'), 'penny_front_image.png'),
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
			'enlightenment_id': self.wisdom.id,
			'file': File(open(self.penny_back, 'rbU'), 'penny_back_file.png'),
			'file_path': 'uploads/penny_back_file.png',
			'float': 3.14159,
			'image': ImageFile(open(self.penny_back, 'rbU'), 'penny_back_image.png'),
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
		
		self.old_public_values = {k: v for k, v in self.old_values.items() if not k.endswith('_id')}
		self.new_public_values = {k: v for k, v in self.new_values.items() if not k.endswith('_id')}
		
		# When assigning a file initially to {File,Image}Field, Django replaces
		# it with a FieldFile instance. We need to grab that instance for
		# testing, which trips our mutability checks. This isn't at all a bug,
		# but requires some extra boilerplate for equality tests.
		self.always_in__mutable_fields = {'file': self.old_values['file'], 'image': self.old_values['image']}
	
	def create_initial(self):
		self.tearDown()
		
		m = EnlightenedModel(**self.old_public_values)
		m.save()
		
		self.old_values['id'] = self.old_public_values['id'] = m.id
		self.new_values['id'] = self.new_public_values['id'] = m.id
		
		self.old_values['holism'] = self.old_public_values['holism'] = m.holism
		self.new_values['holism'] = self.new_public_values['holism'] = m.holism
		
		# The aforementioned _mutable_fields side effects happen here.
		self.old_values['file'] = self.old_public_values['file'] = m.file
		self.old_values['image'] = self.old_public_values['image'] = m.image
		self.always_in__mutable_fields = {'file': self.old_values['file'], 'image': self.old_values['image']}
		
		return m
	
	def create_changed(self):
		m = self.create_initial()
		
		for field_name, value in self.new_values.items():
			if not hasattr(value, '__call__'):
				setattr(m, field_name, value)
		
		self.new_values['file'] = self.new_public_values['file'] = m.file
		self.new_values['image'] = self.new_public_values['image'] = m.image
		
		return m
	
	def create_reverted(self):
		m = self.create_changed()
		
		for field_name, value in self.old_values.items():
			if not hasattr(value, '__call__'):
				setattr(m, field_name, value)
		
		return m
	
	def create_saved(self):
		m = self.create_changed()
		
		m.save()
		
		return m
	
	def get_model_attrs(self, model):
		return {attr: getattr(model, attr, ATTR_MISSING) for attr in self.new_values}
	
	def test_initial__changed_fields(self):
		m = self.create_initial()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_initial_changed_fields(self):
		m = self.create_initial()
		
		self.assertEquals(m.changed_fields, set())
	
	def test_initial_has_changed(self):
		m = self.create_initial()
		
		self.assertEquals(m.has_changed, False)
	
	def test_initial_new_values(self):
		m = self.create_initial()
		
		self.assertEquals(self.get_model_attrs(m), self.old_values)
	
	def test_initial_old_values(self):
		m = self.create_initial()
		
		self.assertEquals(dict(m.old_values), self.old_values)
	
	def test_old_values_with_bad_key(self):
		m = self.create_initial()
		
		self.assertRaises(KeyError, lambda: m.old_values['bad_key'])
	
	def test_old_values_with_bad_attr(self):
		m = self.create_initial()
		
		self.assertRaises(AttributeError, lambda: m.old_values.bad_key)
	
	def test_initial_saved_without_changes(self):
		m = self.create_initial()
		
		self.assertNumQueries(0, lambda: m.save())
	
	def test_initial_saved_with_changed_id(self):
		m = self.create_initial()
		m.pk += 100
		
		self.assertEqual(m.changed_fields, {'id'})
		self.assertEqual(m.old_values.id, self.old_values['id'])
		
		m.save()
		
		self.assertEqual(m, EnlightenedModel.objects.get(pk=m.pk))
	
	def test_changed__changed_fields(self):
		m = self.create_changed()
		old_values = self.old_values
		del(old_values['id'])
		del(old_values['holism'])
		del(old_values['file'])
		del(old_values['image'])
		
		self.assertEquals(m._changed_fields, old_values)
	
	def test_touched_mutable_field__mutable_fields(self):
		m = self.create_initial()
		m.enlightenment
		m.holism.all()
		mutable_fields = {'enlightenment': self.old_values['enlightenment']}
		mutable_fields.update(self.always_in__mutable_fields)
		
		self.assertEquals(m._mutable_fields, mutable_fields)
	
	def test_changed_inside_mutable_field__mutable_fields(self):
		m = self.create_initial()
		m.enlightenment.aspect = 'Holistic'
		old_values = {'enlightenment': self.old_values['enlightenment']}
		old_values.update(self.always_in__mutable_fields)
		
		self.assertEquals(m._mutable_fields, old_values)
	
	def test_touched_then_changed_inside_mutable_field__mutable_fields(self):
		m = self.create_initial()
		m.enlightenment
		m.enlightenment = self.new_values['enlightenment']
		mutable_fields = {'enlightenment': self.old_values['enlightenment']}
		mutable_fields.update(self.always_in__mutable_fields)
		
		self.assertEquals(m._mutable_fields, mutable_fields)
	
	def test_touched_immutable_field_with_mutable_element__mutable_fields(self):
		m = self.create_initial()
		m.comma_seperated_integer = (1, [0], 1)
		m._changed_fields = {}
		m.comma_seperated_integer
		mutable_fields = {'comma_seperated_integer': (1, [0], 1)}
		mutable_fields.update(self.always_in__mutable_fields)
		
		self.assertEquals(m._mutable_fields, mutable_fields)
	
	def test_touched_immutable_field_with_immutable_elements__changed_fields(self):
		m = self.create_initial()
		m.comma_seperated_integer = (1, 1, 1)
		m._changed_fields = {}
		m.comma_seperated_integer
		
		self.assertEquals(m._changed_fields, {})
	
	def test_changed_changed_fields(self):
		m = self.create_changed()
		new_values = self.new_values
		del(new_values['id'])
		del(new_values['holism'])
		
		self.assertEquals(sorted(m.changed_fields), sorted(new_values.keys()))
	
	def test_changed_has_changed(self):
		m = self.create_changed()
		
		self.assertEquals(m.has_changed, True)
	
	def test_changed_new_values(self):
		m = self.create_changed()
		
		self.assertEquals(self.get_model_attrs(m), self.new_values)
	
	def test_changed_old_values(self):
		m = self.create_changed()
		
		self.assertEquals(dict(m.old_values), self.old_values)
	
	def test_changed_reverts(self):
		m = self.create_changed()
		m.revert_fields(self.new_values.keys())
		
		self.assertEquals(self.get_model_attrs(m), self.old_values)
	
	def test_changed_revert_nonexistent_field(self):
		m = self.create_changed()
		m.revert_fields('not_a_field')
		
		self.assertEquals(self.get_model_attrs(m), self.new_values)
	
	def test_changed_reverts_all(self):
		m = self.create_changed()
		m.revert_fields('enlightenment')
		m.enlightenment.aspect = 'Holistic'
		m.revert_fields()
		
		self.assertEquals(self.get_model_attrs(m), self.old_values)
	
	def test_reverted__changed_fields(self):
		m = self.create_reverted()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_reverted_changed_fields(self):
		m = self.create_reverted()
		
		self.assertEquals(m.changed_fields, set())
	
	def test_reverted_has_changed(self):
		m = self.create_reverted()
		
		self.assertEquals(m.has_changed, False)
	
	def test_reverted_new_values(self):
		m = self.create_reverted()
		
		self.assertEquals(self.get_model_attrs(m), self.old_values)
	
	def test_reverted_old_values(self):
		m = self.create_reverted()
		
		self.assertEquals(dict(m.old_values), self.old_values)
	
	def test_saved__changed_fields(self):
		m = self.create_saved()
		
		self.assertEquals(m._changed_fields, {})
	
	def test_saved_changed_fields(self):
		m = self.create_saved()
		
		self.assertEquals(m.changed_fields, set())
	
	def test_saved_has_changed(self):
		m = self.create_saved()
		
		self.assertEquals(m.has_changed, False)
	
	def test_saved_new_values(self):
		m = self.create_saved()
		
		self.assertEquals(self.get_model_attrs(m), self.new_values)
	
	def test_saved_old_values(self):
		m = self.create_saved()
		
		self.assertEquals(dict(m.old_values), self.new_values)
	
	def test_changed_twice_new_values(self):
		m = self.create_changed()
		new_values = self.new_values
		m.text = 'newer'
		new_values['text'] = 'newer'
		
		self.assertEquals(self.get_model_attrs(m), new_values)
	
	def test_updated_together_values(self):
		m = self.create_saved()
		EnlightenedModel.objects.filter(pk=m.pk).update(big_integer=0)
		
		new_values = self.new_values
		new_values['small_integer'] = 0
		
		m.small_integer = new_values['small_integer']
		m.save()
		m.refresh_from_db()
		
		self.assertEquals(self.get_model_attrs(m), new_values)
	
	def test_updated_together_with_deferred_fields(self):
		m = self.create_saved()
		
		m = EnlightenedModel.objects.only('big_integer').get(pk=m.pk)
		
		self.assertEquals(self.get_model_attrs(m), self.new_values)
	
	def test_save_hook_order(self):
		self.assertEquals(EnlightenedModel._meta._stc_save_hooks, [_save_the_change_save_hook, _update_together_save_hook])
	
	def test_save_hook_order_with_out_of_order_decorators(self):
		self.assertEquals(Disorder._meta._stc_save_hooks, [_save_the_change_save_hook, _update_together_save_hook])
	
	def update_together_with_multiple_decorators(self):
		together = {'chaos', 'fire', 'brimstone'}
		self.assertEquals(Disorder._meta.update_together, {field: together for field in together})
	
	def test_altered_file_field(self):
		m = self.create_initial()
		
		m.file.delete(save=False)
		m.file.save('penny_back_file.png', File(open(self.penny_back, 'rbU')), save=False)
		
		self.assertEquals(m.changed_fields, {'file'})
		
		m.file.save('penny_front_file.png', File(open(self.penny_front, 'rbU')), save=False)
		
		self.assertEquals(m.changed_fields, set())
	
	def test_refresh_from_db(self):
		m = self.create_changed()
		m.refresh_from_db()
		
		self.assertEquals(m._changed_fields, {})
		self.assertEquals(m._mutable_fields, {})
		self.assertEquals(m._mutability_checked, set())
	
	def test_refresh_single_field_from_db(self):
		m = self.create_initial()
		m.small_integer = self.new_values['small_integer']
		m.big_integer = self.new_values['big_integer']
		m.refresh_from_db(fields=('small_integer',))
		
		self.assertEquals(m._changed_fields, {'big_integer': self.old_values['big_integer']})
		self.assertEquals(m._mutable_fields, self.always_in__mutable_fields)
		
		# A side effect of create_initial is that 'id' will end up in _mutability_checked.
		self.assertEquals(m._mutability_checked, {'id'} | set(self.always_in__mutable_fields.keys()))
	
	def test_mixins_warnings(self):
		with warnings.catch_warnings(record=True) as w:
			warnings.simplefilter('always')
			
			SaveTheChange()
			TrackChanges()
			UpdateTogetherModel()
			
			self.assertEquals(len(w), 3)
			self.assertEquals(w[0].category, RuntimeWarning)
			self.assertEquals(
				str(w[0].message),
				"save_the_change.mixins.SaveTheChange: mixins.SaveTheChange is no longer supported, instead use the decorator decorators.SaveTheChange."
			)
			self.assertEquals(w[1].category, RuntimeWarning)
			self.assertEquals(
				str(w[1].message),
				"save_the_change.mixins.TrackChanges: mixins.TrackChanges is no longer supported, instead use the decorator decorators.TrackChanges."
			)
			self.assertEquals(w[2].category, RuntimeWarning)
			self.assertEquals(
				str(w[2].message),
				"save_the_change.mixins.UpdateTogetherModel: mixins.UpdateTogetherModel is no longer supported, instead use the decorator decorators.UpdateTogether."
			)
	
	"""
	Regression Tests
	
	"""
	
	def tearDown(self):
		for file_name in os.listdir(self.uploads):
			if file_name.endswith('.png'):
				os.remove(os.path.join(os.path.join(self.uploads, file_name)))
		
		self.old_values.pop('id', None)
		self.new_values.pop('id', None)
