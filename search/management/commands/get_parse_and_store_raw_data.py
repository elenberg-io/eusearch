from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import unicodedata
import datetime
from io import StringIO
import json
import re
import os

class Command(BaseCommand):
    help = 'Parses EU commission web data and stores it.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Started reading and parsing EU Commission web data.'))
        eu_rss_URL = 'https://ec.europa.eu/commission/presscorner/api/rss?language=en&documenttype=852&commissioner=&pagesize=100'
        page = requests.get(eu_rss_URL)
        soup = BeautifulSoup(page.content, "html.parser")
        items = soup.find_all('item')

        items_list = []
        for item in items:
            item_details = dict()
            item_details['title'] = item.find('title').text.strip()
            item_details['link'] = item.find('guid').text.strip()
            item_details['description'] = item.find('description').text.strip()
            item_details['category'] = item.find('category').text.strip()
            item_details['pubdate'] = item.find('pubdate').text.strip()
            items_list.append(item_details)   
        items_df = pd.DataFrame(items_list)
        items_df['pubdate'] = pd.to_datetime(items_df.pubdate, format='%a, %d %b %Y %H:%M:%S %Z') 
        items_df['category'] = items_df.category.str[12:]
        items_df['category'] = items_df.category.str.split(',')

        links_list = items_df.link.tolist()
        questions_and_answers = dict()

        for link in links_list:
            driver = webdriver.Chrome(r"C:\Users\Ulste\Desktop\uni\Anaktisi Pliroforias\chromedriver.exe")
            driver.get(link)
            questions_and_answers[link] = dict()
            elements = driver.find_elements(By.XPATH, "//div[@class='ecl-paragraph']")
            all_q_and_a = elements[0]
            inner_html_q_and_a = all_q_and_a.get_attribute('innerHTML')
            soup_q_and_a = BeautifulSoup(inner_html_q_and_a, "html.parser")
            all_t = soup_q_and_a.find('p').find_previous_siblings() + [soup_q_and_a.find('p')] + soup_q_and_a.find('p').find_next_siblings()
            question_txt = ''
            
            for content in all_t:
                content_txt = content.text.strip() 
                content_txt = unicodedata.normalize("NFKD", content_txt) 
                if len(content_txt) == 0:
                    continue
                elif content_txt[-1] =='?':
                    question_txt = content_txt
                    question_txt = re.sub('^\d+. ', '', question_txt)
                    if question_txt in questions_and_answers[link]:
                        continue
                    else:
                        questions_and_answers[link][question_txt] = []
                elif content_txt.lower() == 'for more information':
                    break
                elif question_txt == '':
                    continue
                else:
                    questions_and_answers[link][question_txt].append(content_txt)
                
            driver.close()
        self.stdout.write(self.style.SUCCESS('Finished parsing web data.'))
        self.stdout.write(self.style.SUCCESS('Started storing web data.'))

        for url, qna in questions_and_answers.items():
            for question in qna:
                questions_and_answers[url][question] = ' '.join(
                        [x.replace('\n', '').strip() for x in questions_and_answers[url][question]])

        json_object = json.dumps(questions_and_answers)

        with open(os.path.join("data", "questions_and_asnwers.json"), "w") as outfile:
            json.dump(json_object, outfile)
        self.stdout.write(self.style.SUCCESS('Finished storing web data.'))
