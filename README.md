# EUSEARCH 

EUSEARCH is a Django Search App that uses web data parsed from the EU Commission website to create a search engine
based on Elastic Cloud as data store and Elastic Index and Haystack with BERT embeddings to power the search engines. A pre-trained BERT model is used to generate embeddings based on the questions from the Q&A data and they're used in the Haystack Q&A search functionality.

## Getting the data

Scraping, parsing and uploading to Elastic Cloud the data from the EU commission website. Elastic Cloud is
used as a data store for the search data and the embeddings for Elastic Index search and Haystack search.

```python
# Scrape the Q&A and metadata from EU commission website and store it locally into a .json file
python manage.py get_parse_and_store_raw_data

# Instantiate and populate the Elastic Search Django model class that automatically uploads 
# data into Elastic Cloud for use in search with Elastic Index
python manage.py load_es_data

# Populate the Elastic Search Index with Q&A and metadata outside of a Django model
python manage.py populate_elastic_index

# Generate Q&A BERT Embeddings using Haystack and store them on Elastic Cloud for use in Haystack Q&A search
python manage.py get_store_haystack_embeddings
```

## Running the app

Use the Django utility manage.py to run the local development server to get the search engine running locally.

```python
python manage.py runserver
```

## UI Look & Feel

![Link text Here](staticfiles\search\look_and_feel.jpg)