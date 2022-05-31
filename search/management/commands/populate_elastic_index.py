from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from io import StringIO
import pandas as pd
import json
import os


class Command(BaseCommand):
    help = 'Populates the Elastic Search index with data outside Django model.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Started index population process.'))

        with open(os.path.join('data', 'questions_and_asnwers.json')) as outfile:
            questions_and_asnwers_json = json.load(outfile)
        questions_and_answers_df = pd.read_json(StringIO(questions_and_asnwers_json), orient='index')
        questions_and_answers_df = pd.DataFrame(questions_and_answers_df.stack())
        questions_and_answers_df.reset_index(-1, inplace=True)
        questions_and_answers_df.columns = ['question', 'answer']
                
        topics_df = pd.read_csv(os.path.join('data', 'topics.csv'))
        topics_df.set_index('link', inplace=True)

        all_df = topics_df.join(questions_and_answers_df, how='inner')
        all_df['description'] = all_df.description.str.strip()
        all_df['pubdate'] = pd.to_datetime(all_df.pubdate, format='%Y-%m-%d').dt.date

        API_KEY = os.environ.get('encoded_api_key')
        CLOUD_ID = os.environ.get('CLOUD_ID')
        ELASTIC_USER = os.environ.get('ELASTIC_USER')
        ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD')

        # Create the client instance
        es = Elasticsearch(
            cloud_id=CLOUD_ID,
            basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            api_key= API_KEY
        )

        # delete index if it exists before creating index and loading documents 
        if es.indices.exists(index="eu-questions-index"):
            es.indices.delete(index='eu-questions-index')

        eu_mapping = {
            "properties": {
                "title": {"type": "text"},
                "link": {"type": "text"},
                "description": {"type": "text"},
                "category": {"type": "text"},
                "pubdate": {"type": "text"},
                "question": {"type": "text"},
                "answer": {"type": "text"}
            }
        }


        k = 1
        for index, row in all_df.iterrows():
            doc = {
                "title": row.title,
                "link": index,
                "description": row.description,
                "category": row.category,
                "pubdate": row.pubdate,
                "question": row.question,
                "answer": row.answer
            }
            es.index(index="eu-questions-index", id=k, document=doc)
            k += 1

        assert es.indices.exists(index="eu-questions-index"), 'Index eu-questions-index doesn\'t exist'
        self.stdout.write(self.style.SUCCESS('Finished index population process.'))
