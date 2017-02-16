API
###

Developer Interface
===================

.. autofunction:: save_the_change.decorators.SaveTheChange

.. autofunction:: save_the_change.decorators.UpdateTogether

.. autofunction:: save_the_change.decorators.TrackChanges

.. autoclass:: save_the_change.mappings.OldValues


Internals
=========

.. autoclass:: save_the_change.decorators.STCMixin

.. autofunction:: save_the_change.decorators._inject_stc

.. autofunction:: save_the_change.decorators._save_the_change_save_hook

.. autofunction:: save_the_change.decorators._update_together_save_hook

.. autoclass:: save_the_change.descriptors.ChangeTrackingDescriptor

.. autofunction:: save_the_change.descriptors._inject_descriptors

.. autofunction:: save_the_change.util.is_mutable
