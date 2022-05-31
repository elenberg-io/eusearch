import datetime
from haystack import indexes
from search.models import EmbeddingsIndex


class EmbeddingsSearchIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    content = indexes.CharField(model_attr='content')
    answer = indexes.CharField(model_attr='answer')
    question_emb = indexes.CharField(model_attr='question_emb')

    def get_model(self):
        return EmbeddingsIndex
    def index_queryset(self, using=None):
        return self.get_model().objects.all()