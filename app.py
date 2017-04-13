from flask import Flask, request, render_template, g
from nltk.corpus import stopwords
import os
import json
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup

from mutual_information import MutualInformation
from indexer import Indexer

app = Flask(__name__)

sec_k = os.urandom(24)
app.secret_key = sec_k

item_ids_to_reviews = {}

stop = set(stopwords.words('english'))

@app.route('/')
def index():
	return render_template('search.html', items_dict={}, search_query_dict={})

@app.route('/search')
def search():
	return render_template('search.html')

def process_multi_word_links(new_text, item_id):
	new_text_list = new_text.split(' ')
	links_list = []
	for n in new_text_list:
		if n in stop:
			links_list.append(n)
			continue
		indexer = Indexer()
		retrieved_docs = indexer.get_docs(n, item_id=item_id)
		if len(retrieved_docs) > 0:
			n = '<a target="_blank" href="' + '/review_query_request_handler/%s/%s' % (item_id, n) + '">' + n + '</a>'
		links_list.append(n)
	new_text = ' '.join(links_list)

	return new_text

def process_multi_word_links_modified(new_text, item_id):
	new_text_list = new_text.split(' ')
	links_list = []
	window_size = 3
	i = 0
	while (i < len(new_text_list)):
		txt_windows = [' '.join(new_text_list[i:i+k+1]) for k in range(window_size)]
		if txt_windows[0] in stop:
			links_list.append(txt_windows[0])
			i += 1
			continue
		indexer = Indexer()
		retrieved_docs = indexer.get_docs(txt_windows[0], item_id=item_id)
		if len(retrieved_docs) == 0:
			links_list.append(txt_windows[0])
			i += 1
		else:
			links_list.append('')
			for txt in txt_windows:
				retrieved_docs = indexer.get_docs(txt, item_id=item_id)
				if len(retrieved_docs) > 0:
					i += 1
					links_list[-1] = '<a target="_blank" href="' + '/review_query_request_handler/%s/%s' % (item_id, txt) + '">' + txt + '</a>'
				else:
					break
	new_text = ' '.join(links_list)
	return new_text


def process_item_description(item_description, item_id):
    i = 0
    new_item_description = ""
    while (i < len(item_description)):
        if item_description[i] == '<':
            while (item_description[i] != '>'):
                new_item_description += item_description[i]
                i += 1
            new_item_description += item_description[i]
            i += 1
            if (i > len(item_description)):
                break
            else:
                continue
        else:
            new_text = ""
            while (i < len(item_description) and item_description[i] != '<'):
                new_text += item_description[i]
                i += 1
            new_text = process_multi_word_links_modified(new_text, item_id)
            new_item_description += new_text
    print ('done')
    return new_item_description

def make_product_loopkup_api_call(search_query):
	search_query = search_query.replace(' ', '%20')
	url = "http://api.walmartlabs.com/v1/search?apiKey=vydf8ym75f468rbgwy5k5xwp&query=" + search_query
	data = json.load(urlopen(url))
	return_dict = {}

	for item in data['items']:
		item_name = item['name']
		item_url = item['productUrl']
		item_id = item['itemId']
		item_description = item['longDescription']
		item_description = BeautifulSoup(item_description).text
		item_reviews = make_product_reviews_api_call(item_id)
		item_ids_to_reviews[str(item_id)] = item_reviews
		item_description = process_item_description(item_description, item_id)

		return_dict[item_id] = {
			'item_name' : item_name,
			'item_id' : item_id,
			'item_url' : item_url,
			'item_description' : item_description,
		}

	return return_dict

def make_product_reviews_api_call(item_id):
	review_url = "http://api.walmartlabs.com/v1/reviews/%s?apiKey=vydf8ym75f468rbgwy5k5xwp&format=json" % str(item_id)
	reviews = []
	review_data = json.load(urlopen(review_url))
	for review in review_data['reviews']:
		reviews.append(review['reviewText'])

	indexer = Indexer(reviews, item_id)
	indexer.index_documents()
	return reviews

@app.route('/request_handler', methods=['GET', 'POST'])
def request_handler():
	search_query = request.form['search_query']
	items_dict = make_product_loopkup_api_call(search_query)
	search_query_dict={'search_query' : search_query}
	return render_template('search.html', items_dict=items_dict, search_query_dict=search_query_dict)


@app.route('/review_request_handler/<string:review_item_id>', methods=['POST'])
def review_request_handler(review_item_id):
	review_query = request.form['review_query']
	reviews = item_ids_to_reviews[review_item_id]

	mutual_info = MutualInformation(txt_data=reviews, search_query=review_query)

	reviews_dict = {'review_query' : review_query, 'reviews' : [], 'summary' : mutual_info.summary}

	indexer = Indexer()
	retrieved_review_ids = indexer.get_docs(review_query, item_id=review_item_id)

	for review_id in retrieved_review_ids:
		reviews_dict['reviews'].append(
			reviews[review_id]
		)

	return render_template('reviews.html', reviews_dict=reviews_dict)

@app.route('/review_query_request_handler/<string:review_item_id>/<string:review_query>')
def review_query_request_handler(review_item_id, review_query):
	reviews = item_ids_to_reviews[review_item_id]

	# reviews_dict = {'review_query' : review_query, 'reviews' : [], 'summary' : mutual_info.summary}
	reviews_dict = {'review_query' : review_query, 'reviews' : []}

	indexer = Indexer()
	retrieved_review_ids = indexer.get_docs(review_query, item_id=review_item_id)

	for review_id in retrieved_review_ids:
		reviews_dict['reviews'].append(
			reviews[review_id]
		)

	mutual_info = MutualInformation(txt_data=reviews, search_query=review_query)
	summary_split = mutual_info.summary.split(' ')
	summary_with_links = [
		'<a target="_blank" href="' + '/summary_handler/%s/%s/%s' % (summary_word, review_query, review_item_id) + '">' + summary_word + '</a>'
		for summary_word in summary_split
	]

	reviews_dict['summary'] = ' '.join(summary_with_links)

	return render_template('reviews.html', reviews_dict=reviews_dict)

@app.route('/summary_handler/<string:summary_word>/<string:review_query>/<string:review_item_id>')
def summary_handler(summary_word, review_query, review_item_id):
	reviews = item_ids_to_reviews[review_item_id]

	indexer = Indexer()
	retrieved_review_ids = indexer.get_docs(review_query, item_id=review_item_id)

	filtered_reviews = []
	for review_id in retrieved_review_ids:
		filtered_reviews.append(
			reviews[review_id]
		)

	review_query_terms = [re.sub(r'[^\w\s]','',s).lower() for s in review_query.split(' ')]

	annotated_reviews = []
	for review in filtered_reviews:
		filtered_review = review.split(' ')
		review = [re.sub(r'[^\w\s]','',s).lower() for s in review.split(' ')]
		
		if summary_word in review:
			summary_word_idx = review.index(summary_word)
			i = summary_word_idx
			while (review[i] not in review_query_terms):
				i -= 1

			review = filtered_review[:i] + ['<b>'] + filtered_review[i:]
			review = review[:summary_word_idx+2] + ['</b>'] + review[summary_word_idx+2:]

			annotated_reviews.append(
				' '.join(review)
			)
		else:
			annotated_reviews.append(
				' '.join(filtered_review)
			)
	
	reviews_dict = {
		'summary_word' : summary_word,
		'review_query' : review_query,
		'annotated_reviews' : annotated_reviews
	}
	return render_template('annotated_reviews.html', reviews_dict=reviews_dict)

if __name__ == '__main__':
	app.run(debug=True)