from django.contrib.auth.models import User
from django.db import models
from haystack import signals


class UserOnlySignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        # Listen only to the ``User`` model.
        models.signals.post_save.connect(self.handle_save, sender=EmbeddingsIndex)
        models.signals.post_delete.connect(self.handle_delete, sender=EmbeddingsIndex)

    def teardown(self):
        # Disconnect only for the ``User`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=EmbeddingsIndex)
        models.signals.post_delete.disconnect(self.handle_delete, sender=EmbeddingsIndex)