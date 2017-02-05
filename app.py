from flask import Flask, request, render_template, g
import os
import json
import urllib2
from bs4 import BeautifulSoup

from indexer import Indexer

app = Flask(__name__)

sec_k = os.urandom(24)
app.secret_key = sec_k


@app.route('/')
def index():
	return render_template('search.html', items_dict={}, search_query_dict={})

@app.route('/search')
def search():
	return render_template('search.html')

def make_product_loopkup_api_call(search_query):
	search_query = search_query.replace(' ', '%20')
	url = "http://api.walmartlabs.com/v1/search?apiKey=vydf8ym75f468rbgwy5k5xwp&query=" + search_query
	data = json.load(urllib2.urlopen(url))
	return_dict = {}

	for item in data['items']:
		item_name = item['name']
		item_url = item['productUrl']
		item_id = item['itemId']
		item_description = item['longDescription']
		item_description = BeautifulSoup(item_description).text

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
	review_data = json.load(urllib2.urlopen(review_url))
	for review in review_data['reviews']:
		reviews.append(review['reviewText'])

	print ('Indexing Reviews...')
	indexer = Indexer(reviews)
	indexer.index_documents()
	print ('Done Indexing Reviews.')
	return {'reviews' : reviews}

@app.route('/request_handler', methods=['GET', 'POST'])
def request_handler():
	search_query = request.form['search_query']
	items_dict = make_product_loopkup_api_call(search_query)
	search_query_dict={'search_query' : search_query}
	return render_template('search.html', items_dict=items_dict, search_query_dict=search_query_dict)


@app.route('/review_request_handler/<string:review_item_id>', methods=['POST'])
def review_request_handler(review_item_id):
	review_query = request.form['review_query']
	reviews_dict = make_product_reviews_api_call(review_item_id)
	reviews_dict['review_query'] = review_query
	return render_template('reviews.html', reviews_dict=reviews_dict)

if __name__ == '__main__':
	app.run(debug=True)