from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from io import StringIO
import pandas as pd
import json
import os

from search.models import EuIndex

class Command(BaseCommand):
    help = 'Instantiates and populates the EuIndex model class.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Started population process within Django model.'))

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
        all_df.index.name = 'link'
        all_df = all_df.reset_index()

        for index, row in all_df.iterrows():
            question_and_answer = EuIndex()
            question_and_answer.title = row.title
            question_and_answer.link = row.link
            question_and_answer.description = row.description
            question_and_answer.category = row.category
            question_and_answer.pubdate = row.pubdate
            question_and_answer.question = row.question
            question_and_answer.answer = row.answer
            question_and_answer.save()

        self.stdout.write(self.style.SUCCESS('Finished population process.'))
