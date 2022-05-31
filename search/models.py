from django.db import models

# Create your models here.
class EuIndex(models.Model):
    """ Elasticsearch model"""
    title = models.TextField()
    link = models.TextField()
    description = models.TextField()
    category = models.TextField()
    pubdate = models.TextField()
    question = models.TextField()
    answer = models.TextField()

# Create your models here.
class EmbeddingsIndex(models.Model):
    """ Haystack Embeddings model"""
    content = models.TextField()
    answer = models.TextField()
    question_emb = models.TextField()
    
    def save(self, *args, **kwargs):
        return super(EmbeddingsIndex, self).save(*args, **kwargs)