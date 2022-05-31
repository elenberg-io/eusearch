from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.nodes import EmbeddingRetriever
from haystack.utils import launch_es
from io import StringIO
import pandas as pd
import json
import os


class Command(BaseCommand):
    help = 'Generate Q&A BERT Embeddings using Haystack and store them on Elastic Cloud'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Started generation of Q&A Embeddings.'))

        # create connection to Elastic Cloud data store
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
        # read in Q&A data
        with open(os.path.join('data', 'questions_and_asnwers.json')) as outfile:
            questions_and_asnwers_json = json.load(outfile)
        questions_and_answers_df = pd.read_json(StringIO(questions_and_asnwers_json), orient='index')
        questions_and_answers_df = pd.DataFrame(questions_and_answers_df.stack())
        questions_and_answers_df.reset_index(-1, inplace=True)
        questions_and_answers_df.columns = ['question', 'answer']
        questions_and_answers_df.rename({'question': 'content'}, axis=1, inplace=True)
        questions = list(questions_and_answers_df.content.values)

        # get embeddings for our questions from the FAQs
        retriever = EmbeddingRetriever(document_store=document_store, embedding_model="deepset/sentence_bert", use_gpu=True)
        questions_and_answers_df["question_emb"] = retriever.embed_queries(texts=questions)

        # store results
        docs_to_index = questions_and_answers_df.to_dict(orient="records")
        document_store.write_documents(docs_to_index)
        questions_and_answers_df.to_csv(os.path.join('data', 'q_and_a_with_embeddings.csv'), index=False)
    
        self.stdout.write(self.style.SUCCESS('Finished generating and storing embeddings locally and on Elastic Cloud.'))
