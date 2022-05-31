from django.http import HttpResponse
from django.shortcuts import render
from elasticsearch_dsl import Q

from haystack.document_stores import ElasticsearchDocumentStore
from haystack.nodes import EmbeddingRetriever
from sentence_transformers import SentenceTransformer
from haystack.pipelines import FAQPipeline
from haystack.utils import print_answers

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from search.serializers import EuIndexSerializer
from search.documents import EuIndexDocument
from search.models import EuIndex
from django.template import loader
import json
import os

def results_view(request):
    """ 
    Process user query results, query Elastic Cloud using Elastic Index and Haystack and return results to user
    """
    template = loader.get_template('search/search.html')
    if request.method == "POST":        
        searched = request.POST["searched"]

        # Haystack with Elasticsearch stored data
        host_es = "e726e710c33242529ed43fafa9eab3e0.euinforetrieval.es.europe-west2.gcp.elastic-cloud.com"
        ELASTIC_USER = os.environ.get('ELASTIC_USER')
        ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD')

        document_store = ElasticsearchDocumentStore(
            host= host_es,
            port="9243",
            scheme='https',
            search_fields='question',
            content_field='question',
            name_field='question',
            verify_certs=False,
            username=ELASTIC_USER,
            password=ELASTIC_PASSWORD,
            index="eu-questions-index-embeddings",
            embedding_field="question_emb",
            embedding_dim=768,
            excluded_meta_data=["question_emb"],
            similarity='cosine',
            duplicate_documents='overwrite'
        )

        retriever = EmbeddingRetriever(document_store=document_store, embedding_model="deepset/sentence_bert", 
                use_gpu=True)
        pipe = FAQPipeline(retriever=retriever)
        prediction = pipe.run(query=searched, params={"Retriever": {"top_k": 5}})

        results_haystack_list = []
        for result in prediction['documents']:
            results_haystack_dict = dict()
            results_haystack_dict['title'] = result.meta['title']
            results_haystack_dict['link'] = result.meta['link']
            results_haystack_dict['description'] = result.meta['description']   
            results_haystack_dict['category'] = result.meta['category']
            results_haystack_dict['pubdate'] = result.meta['pubdate']
            results_haystack_dict['question'] = result.content
            results_haystack_dict['answer'] = result.meta['answer']
            results_haystack_list.append(results_haystack_dict)

        # Elasticsearch
        q = Q("multi_match",
            # type='most_fields',
            type='best_fields',
            query=searched, 
            fuzziness=1,
            fields=['question', 'answer', 'description^2', 'title^3', 'category'])

        document_class = EuIndexDocument
        search = document_class.search().extra(size=5).query(q)
        response = search.execute()

        results_list = []
        for result in response.hits:
            result_dict = dict()
            result_dict['title'] = result.title
            result_dict['link'] = result.link
            result_dict['description'] = result.description
            result_dict['category'] = result.category
            result_dict['pubdate'] = result.pubdate
            result_dict['question'] = result.question
            result_dict['answer'] = result.answer
            results_list.append(result_dict)
          
        not_empty_results = (len(results_list) != 0 or len(results_haystack_list) != 0)

        context = {"searched": searched,
                   "results": results_list,
                   "not_empty_results": not_empty_results,
                   "results_haystack": results_haystack_list}
        return render(request, 'search/search.html', context)
    else:
        return HttpResponse(template.render({}, request))

def index(request):
    template = loader.get_template('search/index.html')
    context = {
        'question': 'What is this?',
    }
    # return HttpResponse("Hello, world. You're at the polls index.")
    return HttpResponse(template.render(context, request))


class EuSearchView(APIView, LimitOffsetPagination):
    serializer_class = EuIndexSerializer
    document_class = EuIndexDocument

    def generate_q_expression(self, query):
        q = Q("multi_match",
                type='most_fields',
                query=query, 
                fields=['question', 'answer', 'description^2', 'title^3'],
                fuzziness=1)
        return q

    def get(self, request, query):
        try:
            q = self.generate_q_expression(query)
            search = self.document_class.search().extra(size=5).query(q)
            response = search.execute()

            print(f'Found {response.hits.total.value} hit(s) for query: "{query}"')

            results = self.paginate_queryset(response, request, view=self)
            serializer = self.serializer_class(results, many=True)
            # return self.get_paginated_response(serializer.data)
            return HttpResponse(search)
            # return search
        except Exception as e:
            return HttpResponse(e, status=500)